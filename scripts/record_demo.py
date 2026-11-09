"""Record a reproducible OFFLINE visual walkthrough using synthetic API fixtures.

Never uses real Clocked endpoints, passwords, or private policy documents. The
recording must be described as a fictional demonstration, not as a live API run.
"""
import os
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.demo import make_demo
from app.pdf_ingest import parse_policy_pdf

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get('RIPPLE_VIDEO_OUT', str(ROOT / 'fixtures' / 'demo-video')))
OUT.mkdir(parents=True, exist_ok=True)
HTML = (ROOT / 'web' / 'studio.html').read_text(encoding='utf-8')
HTML = HTML.replace('<link rel="stylesheet" href="/assets/styles.css" />', '')
HTML = HTML.replace('<script src="/assets/app.js" defer></script>', '')
CSS = '\n'.join(s for s in (ROOT / 'web/styles.css').read_text(encoding='utf-8').splitlines() if not s.startswith('@import '))
JS = (ROOT / 'web/app.js').read_text(encoding='utf-8')


def main():
    with sync_playwright() as p:
        opts={'headless':False,'args':['--no-sandbox','--window-size=1440,900','--start-maximized','--hide-scrollbars']}
        if os.environ.get('CHROMIUM_PATH'):
            opts['executable_path']=os.environ['CHROMIUM_PATH']
        browser=p.chromium.launch(**opts)
        context=browser.new_context(viewport={'width':1440,'height':900}, device_scale_factor=1, reduced_motion='reduce', accept_downloads=True)
        page=context.new_page()
        # External ffmpeg captures the visible Xvfb screen; no Playwright browser
        # download or secrets are required. Only synthetic fixture content is shown.
        output_video=OUT/'ripple-synthetic-walkthrough.mp4'
        ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','x11grab','-draw_mouse','0',
          '-video_size','1440x900','-framerate','20','-i',os.environ['DISPLAY'],
          '-vf','scale=1280:800','-c:v','libx264','-preset','ultrafast',
          '-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(output_video)],
          stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(HTML,wait_until='domcontentloaded')
        page.add_style_tag(content=CSS)
        page.evaluate("""window.fetch = async (url) => ({ok:true,json:async()=>url==='/api/demo'?JSON.parse(window.__fixture):url==='/api/parse-pdf'?JSON.parse(window.__pdfFixture):{status:'ok',live_enabled:false}})""")
        page.evaluate('data=>window.__fixture=JSON.stringify(data)',make_demo())
        page.evaluate('data=>window.__pdfFixture=JSON.stringify(data)',parse_policy_pdf((ROOT/'web/samples/previous-policy.pdf').read_bytes()))
        page.add_script_tag(content=JS)
        page.wait_for_selector('#case-matrix button')
        page.evaluate('window.scrollTo(0,0)')
        page.wait_for_timeout(4800)
        page.locator('#tour-start').click()
        page.wait_for_timeout(3100)
        page.locator('#tour-next').click()
        page.wait_for_timeout(2400)
        page.locator('#tour-close').click()
        page.locator('#consequence-flow').scroll_into_view_if_needed()
        page.wait_for_timeout(3300)
        page.locator('#consequence-flow .flow-case[data-case-id="A01"]').click()
        page.wait_for_timeout(2600)
        page.locator('#rule-lab').scroll_into_view_if_needed()
        page.wait_for_timeout(1900)
        page.locator('#preset-tighten').click()
        page.wait_for_timeout(3700)
        page.locator('#preset-expand').click()
        page.wait_for_timeout(3700)
        page.locator('#reset-rules').click()
        page.wait_for_timeout(1500)
        page.locator('[data-filter="lost"]').click()
        page.wait_for_timeout(1900)
        page.locator('#case-matrix button').first.click()
        page.wait_for_timeout(2900)
        page.locator('#apply-flip').click()
        page.wait_for_timeout(3200)
        page.locator('[data-source="new"][data-rule="gpa_evidence"]').click()
        page.wait_for_timeout(3300)
        page.locator('#source-lens').scroll_into_view_if_needed()
        page.wait_for_timeout(3000)
        page.locator('#source-lens #export-case').click()
        page.wait_for_timeout(2000)
        page.locator('#method').scroll_into_view_if_needed()
        page.wait_for_timeout(2500)
        page.locator('#toggle-trace').click()
        page.wait_for_timeout(2800)
        page.evaluate('window.scrollTo(0,0)')
        page.wait_for_timeout(3000)
        assert not errors,errors
        context.close()
        browser.close()
        ff.terminate()
        try:
            ff.wait(timeout=12)
        except subprocess.TimeoutExpired:
            ff.kill()
            ff.wait()
        print('Video saved:',output_video,'size',output_video.stat().st_size if output_video.exists() else None)


if __name__=='__main__':
    main()