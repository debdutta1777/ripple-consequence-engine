"""Chromium routed through real FastAPI TestClient (no external network or credits)."""
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from app.main import app

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'fixtures'/'screenshots'
OUT.mkdir(parents=True,exist_ok=True)
HTML=(ROOT/'web'/'try.html').read_text(encoding='utf-8')
HTML=HTML.replace('<link rel="stylesheet" href="/assets/try.css"/>','').replace('<script src="/assets/try.js" defer></script>','')
CSS='\n'.join(line for line in (ROOT/'web/try.css').read_text(encoding='utf-8').splitlines() if not line.startswith('@import '))
JS=(ROOT/'web/try.js').read_text(encoding='utf-8')


def open_try(browser,client,width,errors):
    page=browser.new_page(viewport={'width':width,'height':900},accept_downloads=True)
    page.on('pageerror',lambda e:errors.append(str(e)))
    def bridge(source,request):
        path=request['path']
        if request.get('kind')=='pdf':
            file=(request['name'],bytes(request['bytes']),'application/pdf')
            response=client.post(path,files={'file':file})
            return {'ok':response.is_success,'status':response.status_code,'body':response.json()}
        if request.get('method')=='POST':
            response=client.post(path,content=request['body'],headers={'Content-Type':'application/json'})
            return {'ok':response.is_success,'status':response.status_code,'body':response.json()}
        response=client.get(path)
        return {'ok':response.is_success,'status':response.status_code,'bytes':list(response.content)}
    page.expose_binding('__realApi',bridge)
    page.set_content(HTML)
    page.add_style_tag(content=CSS)
    page.evaluate("""window.fetch=async (path,opts={})=>{
      const req={path,method:opts.method||'GET'};
      if(path==='/api/parse-pdf'){
         const file=opts.body.get('file');
         req.kind='pdf';req.name=file.name;req.bytes=Array.from(new Uint8Array(await file.arrayBuffer()));
      }else if(req.method==='POST')req.body=opts.body;
      const r=await window.__realApi(req);
      return {ok:r.ok,status:r.status,json:async()=>r.body,blob:async()=>new Blob([new Uint8Array(r.bytes||[])],{type:'application/pdf'})};
    }; void 0;""")
    page.add_script_tag(content=JS)
    return page


def main():
    errors=[]
    with TestClient(app) as client,sync_playwright() as p:
        opts={'headless':True,'args':['--no-sandbox']}
        if os.getenv('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
        browser=p.chromium.launch(**opts)
        page=open_try(browser,client,1440,errors)
        assert page.locator('#previous-drop').count()==1
        assert page.locator('#updated-drop').count()==1
        page.locator('#load-samples-top').click()
        page.wait_for_function("document.getElementById('previous-status').classList.contains('success') && document.getElementById('updated-status').classList.contains('success')")
        page.locator('#start-analysis').click()
        page.locator('#results').wait_for(state='visible',timeout=25000)
        assert page.locator('#metric-total').inner_text()=='16'
        assert page.locator('#metric-lost').inner_text()=='4'
        assert page.locator('#metric-gained').inner_text()=='4'
        assert page.locator('#metric-review').inner_text()=='0'
        assert page.locator('#change-list .change-item').count()>=2
        page.locator('[data-filter="lost"]').click()
        assert page.locator('#case-rows tr').count()==4
        page.locator('#case-rows .inspect-btn').first.click()
        assert page.locator('#case-detail').is_visible()
        assert page.locator('#case-detail .evidence-cols a').count()==2
        with page.expect_download() as download:page.locator('#download-results').click()
        assert download.value.suggested_filename=='ripple-policy-impact.csv'
        page.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
        page.screenshot(path=str(OUT/'ripple-try-desktop.png'),full_page=True)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'applicants.csv'
            path.write_text('id,name,gpa,income\nA1,Custom Applicant 1,3.3,40000\nA2,Custom Applicant 2,3.8,55000\n')
            page.locator('input[name="cohort-mode"][value="csv"]').check()
            page.locator('#cohort-file').set_input_files(str(path))
            page.wait_for_function("document.getElementById('cohort-status').textContent.includes('2 applicant')")
            page.locator('#start-analysis').click()
            page.wait_for_function("document.getElementById('metric-total').textContent==='2'",timeout=25000)
            assert page.locator('#metric-lost').inner_text()=='1'
            assert page.locator('#metric-gained').inner_text()=='1'
            assert 'uploaded CSV' in page.locator('#analysis-notice').inner_text()
        page.locator('#theme-toggle').click()
        assert page.evaluate('document.documentElement.dataset.theme')=='dark'
        page.locator('#theme-toggle').click()
        assert page.evaluate('document.documentElement.dataset.theme')=='light'
        assert page.evaluate('document.documentElement.scrollWidth')<=1440
        page.close()
        for width in (390,768,1024):
            pg=open_try(browser,client,width,errors)
            assert pg.evaluate('document.documentElement.scrollWidth')<=width,f'horizontal overflow at {width}px'
            if width==390:pg.screenshot(path=str(OUT/'ripple-try-mobile.png'),full_page=True)
            pg.close()
        assert not errors,errors
        browser.close()
    print('PASS: real FastAPI PDF upload, rule comparison, 16 or CSV cohort, charts, filters, evidence, export, theme, mobile.')

if __name__=='__main__':main()