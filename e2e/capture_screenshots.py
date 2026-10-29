import sys, json
from playwright.sync_api import sync_playwright
OUT='/home/claude/v9/cottonil-nexus-ai/docs/screenshots/'
def ctx(b,lang,w=1440,h=900):
    c=b.new_context(viewport={'width':w,'height':h},locale='ar-EG' if lang=='ar' else 'en-US')
    c.add_init_script(f"try{{localStorage.setItem('cottonil-language','{lang}')}}catch(e){{}}")
    return c
log=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for lang in ('ar','en'):
        pg=ctx(b,lang).new_page(); errs=[]
        pg.on('console',lambda m,e=errs:e.append(m.text) if m.type=='error' else None)
        pg.goto('http://localhost:5174/'); pg.wait_for_selector('form')
        pg.screenshot(path=OUT+f'01_login_{lang}.png')
        # validation state
        pg.click('button[type=submit]'); pg.wait_for_selector('.fielderr'); pg.screenshot(path=OUT+f'01b_login_validation_{lang}.png')
        pg.fill('input[autocomplete=username]','exec'); pg.fill('input[autocomplete=current-password]','bad')
        pg.click('button[type=submit]'); pg.wait_for_selector('[role=alert]'); pg.screenshot(path=OUT+f'01c_login_bad_{lang}.png')
        pg.fill('input[autocomplete=current-password]','Demo-pass-1'); pg.click('button[type=submit]')
        pg.wait_for_selector('.kpi',timeout=15000); pg.wait_for_timeout(1200)
        pg.screenshot(path=OUT+f'03_overview_{lang}_authed.png')
        log.append((lang,'login-flow ok',errs[:3]))
    for lang in ('ar','en'):
        pg=ctx(b,lang).new_page(); errs=[]
        pg.on('console',lambda m,e=errs:e.append(m.text) if m.type=='error' else None)
        pg.goto('http://localhost:5173/'); pg.wait_for_selector('.kpi strong'); pg.wait_for_timeout(1500)
        pg.screenshot(path=OUT+f'03_overview_{lang}.png',full_page=True)
        pg.click('.kpi.lead .explainBtn'); pg.wait_for_selector('.storyDrawer'); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT+f'03b_explain_drawer_{lang}.png'); pg.keyboard.press('Escape'); pg.click('.storyDrawer .drawerClose')
        # nav helper
        def go(idx_text): pg.locator('.sidebar nav button',has_text=idx_text).first.click(); pg.wait_for_timeout(1200)
        go('أداء الأعمال' if lang=='ar' else 'Business Performance'); pg.wait_for_selector('.chart'); pg.screenshot(path=OUT+f'05_revenue_{lang}.png',full_page=True)
        go('المساعد الذكي' if lang=='ar' else 'AI Business'); 
        pg.locator('.chip').first.click(); pg.wait_for_selector('.bubble.bot',timeout=15000); pg.wait_for_timeout(1500)
        pg.screenshot(path=OUT+f'06_nexus_ai_{lang}.png',full_page=True)
        go('الملخص التنفيذي' if lang=='ar' else 'Executive Briefing'); pg.wait_for_timeout(800)
        pg.click('button.primary'); pg.wait_for_selector('.presentationFrame'); pg.wait_for_timeout(600)
        pg.screenshot(path=OUT+f'07_story_1_{lang}.png')
        pg.click('.presentationControls button.primary'); pg.wait_for_timeout(300); pg.click('.presentationControls button.primary'); pg.wait_for_timeout(300)
        pg.screenshot(path=OUT+f'07_story_3_{lang}.png')
        log.append((lang,'desktop screens ok',errs[:3]))
    # mobile
    for lang in ('ar','en'):
        pg=ctx(b,lang,390,844).new_page()
        pg.goto('http://localhost:5173/'); pg.wait_for_selector('.kpi strong'); pg.wait_for_timeout(1200)
        pg.screenshot(path=OUT+f'08_mobile_overview_{lang}.png')
        pg.click('.mobileMenu'); pg.wait_for_timeout(500); pg.screenshot(path=OUT+f'08_mobile_menu_{lang}.png')
        ov=pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth'); log.append((lang,'mobile horizontal overflow',ov))
        pg2=ctx(b,lang,390,844).new_page(); pg2.goto('http://localhost:5174/'); pg2.wait_for_selector('form'); pg2.screenshot(path=OUT+f'08_mobile_login_{lang}.png')
    b.close()
print(json.dumps(log,ensure_ascii=False,indent=1))
