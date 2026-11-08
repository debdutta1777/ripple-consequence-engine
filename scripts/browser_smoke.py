"""Offline Chromium smoke check with the synthetic API stub.

Requires: pip install playwright; a Chromium browser (set CHROMIUM_PATH or use the
standard Playwright-managed binary). Does not make real Clocked API calls.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.demo import make_demo
from app.pdf_ingest import parse_policy_pdf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
HTML = HTML.replace('<link rel="stylesheet" href="/assets/styles.css" />', "")
HTML = HTML.replace('<script src="/assets/app.js" defer></script>', "")
CSS = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
# Remove only the external font import, not the semicolons within its URL.
CSS = "\n".join(line for line in CSS.splitlines() if not line.startswith("@import "))
JS = (ROOT / "web" / "app.js").read_text(encoding="utf-8")


def setup(page):
    page.set_content(HTML, wait_until="domcontentloaded")
    page.add_style_tag(content=CSS)
    page.evaluate("""window.fetch = async (url) => ({
        ok: true,
        json: async () => url === '/api/demo' ? JSON.parse(window.__fixture) :
            url === '/api/parse-pdf' ? JSON.parse(window.__pdfFixture) : {status:'ok',live_enabled:false}
    });""")
    page.evaluate("data => window.__fixture = JSON.stringify(data)", make_demo())
    page.evaluate("data => window.__pdfFixture = JSON.stringify(data)", parse_policy_pdf((ROOT / 'web' / 'samples' / 'previous-policy.pdf').read_bytes()))
    page.add_script_tag(content=JS)
    page.wait_for_selector("#case-matrix button")


def main():
    errors = []
    with sync_playwright() as p:
        opts = {"headless": True, "args": ["--no-sandbox"]}
        if os.getenv("CHROMIUM_PATH"):
            opts["executable_path"] = os.environ["CHROMIUM_PATH"]
        browser = p.chromium.launch(**opts)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page.on("pageerror", lambda e: errors.append(str(e)))
        setup(page)
        assert page.locator("#case-matrix button").count() == 16
        assert "lost eligibility" in page.locator("#selected-transition").inner_text().lower()
        assert "3.50" in page.locator("#flip-content").inner_text()
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(246, 247, 251)", "Light mode should be default"
        assert page.get_by_role("button", name="Switch to dark mode").count() == 1
        page.get_by_role("button", name="Switch to dark mode").click()
        assert page.evaluate("document.documentElement.dataset.theme") == "dark"
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(14, 20, 33)"
        page.get_by_role("button", name="Switch to light mode").click()
        assert page.evaluate("document.documentElement.dataset.theme") == "light"
        # Upload is a free preview: policy editor changes but synthetic impacts
        # are *not* falsely recomputed, and stale source-evidence jumps are blocked.
        page.locator('#old-pdf').set_input_files(str(ROOT / 'web' / 'samples' / 'previous-policy.pdf'))
        page.wait_for_function("document.querySelector('#old-upload-status').classList.contains('ready')")
        assert '1 page' in page.locator('#old-upload-status').inner_text()
        assert 'minimum cumulative GPA of 3.2' in page.locator('#old-policy').input_value()
        assert not page.locator('#unsaved-notice').is_hidden()
        page.locator('[data-source="old"][data-rule="gpa_evidence"]').click()
        assert 'previous analysis' in page.locator('#toast').inner_text()
        page.get_by_role('button', name='Reset sample').click()
        assert page.locator('#unsaved-notice').is_hidden()
        assert 'Or paste policy text' in page.locator('#old-upload-status').inner_text()
        page.screenshot(path=str(OUT / 'ripple-desktop.png'), full_page=True)
        page.locator('[data-filter="lost"]').click()
        assert page.locator("#case-matrix button").count() == 4
        assert page.locator('[data-filter="lost"]').get_attribute("aria-pressed") == "true"
        page.locator('[data-filter="gained"]').click()
        assert page.locator("#case-matrix button").count() == 4
        page.locator('[data-filter="all"]').click()
        assert page.locator("#case-matrix button").count() == 16
        page.get_by_role('button', name='Reset sample').click()
        assert page.locator('#selected-case-title').inner_text() == 'Applicant 01'
        page.locator("#apply-flip").click()
        assert page.locator("#gpa-value").inner_text() == "3.50"
        assert "remains eligible" in page.locator("#selected-transition").inner_text().lower()
        page.locator('[data-source="new"][data-rule="gpa_evidence"]').click()
        highlighted = page.locator("#new-policy").evaluate(
            "el => el.value.substring(el.selectionStart, el.selectionEnd)"
        )
        assert "minimum cumulative GPA of 3.5" in highlighted
        page.screenshot(path=str(OUT / "ripple-evidence-jump.png"), full_page=True)
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("pageerror", lambda e: errors.append(str(e)))
        setup(mobile)
        mobile.screenshot(path=str(OUT / "ripple-mobile.png"), full_page=True)
        mobile.get_by_role("button", name="Switch to dark mode").click()
        mobile.wait_for_timeout(300)
        assert mobile.locator(".case-node").first.evaluate("el=>getComputedStyle(el).backgroundColor") != "rgb(239, 240, 255)"
        assert mobile.evaluate("document.documentElement.dataset.theme") == "dark"
        mobile.screenshot(path=str(OUT / "ripple-mobile-dark.png"), full_page=True)
        mobile.get_by_role("button", name="Switch to light mode").click()
        assert mobile.evaluate("document.documentElement.scrollWidth") <= 390, "Mobile horizontal overflow"
        for width in (768,1024,1280):
            tablet=browser.new_page(viewport={"width":width,"height":900})
            setup(tablet)
            assert tablet.evaluate("document.documentElement.scrollWidth") <= width, f"Overflow at {width}px"
            tablet.close()
        assert not errors, errors
        browser.close()
    print("PASS: light/dark mode, filters, 16 cases, decision flips, evidence selection, PDF preview and stale-result safeguards, responsive layout.")
    print("NOTE: API responses were stubbed; this was not a live-server or Clocked integration test.")


if __name__ == "__main__":
    main()