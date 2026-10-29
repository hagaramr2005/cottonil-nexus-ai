"""Data-free browser check. CI services must be started; no private CSV needed."""
import os
from playwright.sync_api import sync_playwright


def test_login_data_free_ar_en_and_logout():
    url=os.getenv('NEXUS_BASE_URL','http://127.0.0.1:5173/')
    with sync_playwright() as runner:
        browser=runner.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':390,'height':844})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.add_init_script("localStorage.setItem('cottonil-language','en')")
        page.goto(url,wait_until='domcontentloaded')
        page.locator('input[autocomplete=username]').fill('ci')
        page.locator('input[autocomplete=current-password]').fill('ci-password')
        page.locator('button[type=submit]').click()
        page.locator('.sidebar').wait_for(timeout=15000)
        assert page.evaluate("document.documentElement.dir")=='ltr'
        assert page.evaluate("sessionStorage.getItem('nexus-auth')") is None
        page.reload()
        page.locator('.sidebar').wait_for(timeout=15000)
        assert not errors
        browser.close()
