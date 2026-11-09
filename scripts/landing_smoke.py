"""Light/dark responsive landing page through Chromium and actual FastAPI demo route.
No Clocked calls, no external network, no secrets.
"""
import os
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from app.main import app

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'fixtures' / 'screenshots'
OUT.mkdir(parents=True, exist_ok=True)
HTML=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
HTML=HTML.replace('<link rel="stylesheet" href="/assets/landing.css" />','').replace('<script src="/assets/landing.js" defer></script>','')
CSS='\n'.join(line for line in (ROOT/'web'/'landing.css').read_text(encoding='utf-8').splitlines() if not line.startswith('@import '))
JS=(ROOT/'web'/'landing.js').read_text(encoding='utf-8')

def open_landing(browser, client, width, height=900):
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    page.set_content(HTML)
    page.add_style_tag(content=CSS)
    page.expose_binding('__apiDemo',lambda source: client.get('/api/demo').json())
    page.evaluate('''window.fetch = async url => ({ok:true,json: async ()=> await window.__apiDemo() });''')
    page.add_script_tag(content=JS)
    page.wait_for_selector('.lp-applicant-dot')
    return page

def main():
    errors=[]
    with TestClient(app) as client, sync_playwright() as p:
        opts={'headless':True,'args':['--no-sandbox']}
        if os.getenv('CHROMIUM_PATH'): opts['executable_path']=os.environ['CHROMIUM_PATH']
        browser=p.chromium.launch(**opts)
        desk=open_landing(browser,client,1440,900)
        desk.on('pageerror',lambda e: errors.append(str(e)))
        assert desk.locator('.lp-applicant-dot').count()==16
        assert desk.locator('#lp-eligibility-count').inner_text()=='7 / 16 eligible'
        assert desk.locator('#lp-preview-gpa').inner_text()=='3.20'
        desk.locator('#lp-version-new').click()
        assert desk.locator('#lp-preview-gpa').inner_text()=='3.50'
        assert desk.locator('#lp-eligibility-count').inner_text()=='7 / 16 eligible'
        assert '4 lost and 4 gained' in desk.locator('#lp-demo-note').inner_text()
        assert desk.locator('.lp-applicant-dot.is-eligible').count()==7
        assert desk.locator('#landing-theme').get_attribute('aria-label')=='Switch to dark mode'
        desk.locator('#landing-theme').click()
        assert desk.evaluate('document.documentElement.dataset.theme')=='dark'
        assert desk.locator('#landing-theme').get_attribute('aria-label')=='Switch to light mode'
        desk.locator('#landing-theme').click()
        assert desk.evaluate('document.documentElement.dataset.theme')=='light'
        assert desk.locator('.lp-nav-cta').get_attribute('href')=='/studio'
        assert desk.evaluate('document.documentElement.scrollWidth')<=1440
        desk.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
        desk.wait_for_timeout(150)
        desk.screenshot(path=str(OUT/'ripple-landing-desktop.png'),full_page=True)
        desk.close()
        for width in (390,768,1024,1280):
            pg=open_landing(browser,client,width,844 if width==390 else 900)
            pg.on('pageerror',lambda e: errors.append(str(e)))
            assert pg.evaluate('document.documentElement.scrollWidth')<=width, f'overflow {width}'
            if width==390:
                pg.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
                pg.wait_for_timeout(150)
                pg.screenshot(path=str(OUT/'ripple-landing-mobile.png'),full_page=True)
                pg.locator('#landing-theme').click()
                assert pg.evaluate('document.documentElement.dataset.theme')=='dark'
            pg.close()
        assert not errors,errors
        browser.close()
    print('PASS: landing page, real /api/demo, switch policy, light/dark, accessible CTA, 390-1440px responsive widths.')

if __name__=='__main__':main()