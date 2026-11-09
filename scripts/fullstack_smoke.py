"""Chromium-through-FastAPI test. No network or Clocked credentials required.

Unlike browser_smoke, this sends actual browser requests to the real FastAPI
handlers through TestClient, including multipart uploads and preview POSTs.
"""
import os
from urllib.parse import urlsplit
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from app.main import app

ROOT=Path(__file__).resolve().parent.parent


def main():
    errors=[]
    with TestClient(app) as api, sync_playwright() as p:
        settings={"headless":True,"args":["--no-sandbox"]}
        if os.getenv("CHROMIUM_PATH"):
            settings["executable_path"]=os.environ["CHROMIUM_PATH"]
        browser=p.chromium.launch(**settings)
        page=browser.new_page(viewport={"width":1366,"height":900},accept_downloads=True)
        page.on('pageerror',lambda err: errors.append(str(err)))
        log=[]
        def bridge(source, req):
            path=req['path']
            method=req.get('method','GET')
            if req.get('kind')=='pdf':
                file=(req['filename'],bytes(req['bytes']),req['mimetype'])
                response=api.post(path,files={'file':file})
            elif method=='POST':
                response=api.post(path,content=req.get('body',''),headers={'Content-Type':'application/json'})
            else:
                response=api.get(path)
            log.append((method,path,response.status_code))
            return {'ok':response.is_success,'status':response.status_code,'body':response.json()}
        page.expose_binding('__realApi',bridge)
        # The browser is network-isolated, but every response comes from the real
        # FastAPI TestClient, not a fake fixture or canned JSON.
        html=(ROOT/'web/index.html').read_text(encoding='utf-8')
        html=html.replace('<link rel="stylesheet" href="/assets/styles.css" />','')
        html=html.replace('<script src="/assets/app.js" defer></script>','')
        page.set_content(html)
        css=(ROOT/'web/styles.css').read_text(encoding='utf-8')
        css='\n'.join(line for line in css.splitlines() if not line.startswith('@import '))
        page.add_style_tag(content=css)
        page.evaluate("""window.fetch=async (path, options={})=>{
            const method=options.method||'GET';
            const req={path,method};
            if(path==='/api/parse-pdf'){
                const f=options.body.get('file');
                req.kind='pdf';req.filename=f.name;req.mimetype=f.type;
                req.bytes=Array.from(new Uint8Array(await f.arrayBuffer()));
            }else if(method==='POST')req.body=options.body;
            const response=await window.__realApi(req);
            return {ok:response.ok,status:response.status,json:async()=>response.body};
        }; void 0;""")
        page.add_script_tag(content=(ROOT/'web/app.js').read_text(encoding='utf-8'))
        page.wait_for_selector('#case-matrix button')
        assert page.locator('#case-matrix button').count()==16
        assert page.locator('#api-status').inner_text()=='Demo ready'
        assert page.locator('#analyze-live').is_disabled()
        assert page.locator('#preview-policy').is_enabled()
        page.locator('#new-pdf').set_input_files(str(ROOT/'web/samples/updated-policy.pdf'))
        page.wait_for_function("document.querySelector('#new-upload-status').classList.contains('ready')")
        assert page.locator('#unsaved-notice').is_visible()
        page.locator('#preview-policy').click()
        page.wait_for_function("document.querySelector('#mode-indicator').textContent.includes('LOCAL RULE PREVIEW')")
        assert page.locator('#unsaved-notice').is_hidden()
        assert page.locator('#stat-lost').inner_text()=='4'
        assert page.locator('#stat-gained').inner_text()=='4'
        page.locator('[data-source="new"][data-rule="gpa_evidence"]').click()
        assert page.locator('#lens-open-pdf').is_visible()
        # Explicit condition not supported => review, no fabricated decision.
        page.locator('#new-policy').fill(page.locator('#new-policy').input_value()+'\nUnless the applicant is a resident of another state.')
        page.locator('#preview-policy').click()
        page.wait_for_function("document.querySelector('#stat-review').textContent==='16'")
        assert 'LOCAL RULE PREVIEW' in page.locator('#mode-indicator').inner_text()
        assert page.locator('#review-warning').is_visible()
        assert errors==[],errors
        assert ('POST','/api/preview',200) in log
        assert ('POST','/api/parse-pdf',200) in log
        assert ('GET','/api/health',200) in log
        assert ('GET','/api/demo',200) in log
        assert all(path!='/api/analyze' for _,path,_ in log)
        browser.close()
    print('PASS: real FastAPI handlers + Chromium, PDF upload, offline preview, source navigation, ambiguous-policy review, no paid API requests.')

if __name__=='__main__':main()