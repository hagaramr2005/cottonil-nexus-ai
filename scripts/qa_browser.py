"""Browser QA for V10 (Playwright, Chromium). Needs: backend :8000 (auth off), backend :8001 (auth on, users
exec/Demo-pass-1 viewer, root/Admin-pass-1 admin), Vite :5173 -> :8000 and Vite :5174 -> :8001 (NEXUS_API=...).
Exit code != 0 when any check fails. Screenshots go to docs/screenshots/."""
import json, sys, os
from playwright.sync_api import sync_playwright
OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'screenshots') + os.sep
os.makedirs(OUT, exist_ok=True)
results = []
def check(name, ok, detail=''):
    results.append((name, bool(ok), detail)); print(('PASS ' if ok else 'FAIL ') + name, detail if not ok else '')
def ctx(b, lang, w=1440, h=900):
    c = b.new_context(viewport={'width': w, 'height': h}, locale='ar-EG' if lang == 'ar' else 'en-US')
    c.add_init_script(f"try{{localStorage.setItem('cottonil-language','{lang}')}}catch(e){{}}")
    return c
def attach(pg):
    errs = []; pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e))); return errs
def nav(pg, text): pg.locator('.sidebar nav button', has_text=text).first.click(); pg.wait_for_timeout(1200)
T = {'ar': dict(sales='أداء الأعمال', ai='المساعد الذكي', brief='الملخص التنفيذي', change='التحليل المتعمق', rep='التقارير التنفيذية', cases='مساحة التحقيقات', health='جاهزية التشغيل'),
     'en': dict(sales='Business Performance', ai='AI Business', brief='Executive Briefing', change='Revenue X-Ray', rep='Executive Reports', cases='Investigation Workspace', health='Operational readiness')}
with sync_playwright() as p:
    b = p.chromium.launch()
    for lang in ('ar', 'en'):
        pg = ctx(b, lang).new_page(); errs = attach(pg)
        pg.goto('http://localhost:5174/'); pg.wait_for_selector('form')
        check(f'{lang} login: dir', pg.evaluate('document.documentElement.dir') == ('rtl' if lang == 'ar' else 'ltr'))
        pg.wait_for_function("document.querySelector('.logoplate img').complete"); check(f'{lang} login: logo aspect preserved', pg.evaluate("(()=>{const i=document.querySelector('.logoplate img');const r=i.getBoundingClientRect();return Math.abs(r.width/r.height-i.naturalWidth/i.naturalHeight)<0.02})()"))
        pg.screenshot(path=OUT + f'01_login_{lang}.png')
        pg.click('button[type=submit]'); pg.wait_for_selector('.fielderr'); check(f'{lang} login: empty validation', pg.locator('.fielderr').count() == 2)
        pg.screenshot(path=OUT + f'01b_login_validation_{lang}.png')
        pg.fill('input[autocomplete=username]', 'exec'); pg.fill('input[autocomplete=current-password]', 'bad'); pg.click('button[type=submit]')
        pg.wait_for_selector('[role=alert]'); check(f'{lang} login: bad password rejected', pg.locator('.sidebar').count() == 0); errs.clear()
        pg.screenshot(path=OUT + f'01c_login_bad_{lang}.png')
        pg.fill('input[autocomplete=current-password]', 'Demo-pass-1'); pg.click('button[type=submit]'); pg.wait_for_selector('.kpi strong', timeout=15000); pg.wait_for_timeout(1200)
        check(f'{lang} login: success reaches dashboard', True)
        check(f'{lang} viewer: admin readiness hidden', pg.locator('.sidebar nav button', has_text=T[lang]['health']).count() == 0)
        check(f'{lang} viewer: no console/network errors', not errs, errs[:2])
        pg.screenshot(path=OUT + f'03_overview_{lang}_authed.png')
        pg.context.close()
    for lang in ('ar', 'en'):
        c = ctx(b, lang); pg = c.new_page(); errs = attach(pg); t = T[lang]
        pg.goto('http://localhost:5173/'); pg.wait_for_selector('.kpi strong'); pg.wait_for_timeout(1500)
        net = pg.locator('.kpi.lead strong').inner_text()
        check(f'{lang} overview: net sales value 841.27', '841.27' in net, net)
        check(f'{lang} overview: chart svg rendered', pg.locator('.chart svg path').count() > 0)
        check(f'{lang} overview: no horizontal overflow', not pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth'))
        if lang == 'ar':
            body = pg.locator('main').inner_text()
            import re; leftovers = re.findall(r'\b(?:units|orders|Unavailable|Review:|Evidence-backed)\b', body)
            check('ar overview: no English UI leftovers', not leftovers, leftovers)
            check('ar overview: nav dir rtl, sidebar on right', pg.evaluate("document.querySelector('.sidebar').getBoundingClientRect().left>innerWidth/2"))
        else:
            check('en overview: sidebar on left', pg.evaluate("document.querySelector('.sidebar').getBoundingClientRect().left<5"))
        pg.screenshot(path=OUT + f'03_overview_{lang}.png', full_page=True)
        pg.click('.kpi.lead .explainBtn'); pg.wait_for_selector('.storyDrawer'); pg.wait_for_timeout(500)
        check(f'{lang} drawer opens from inline-end edge', pg.evaluate("(()=>{const r=document.querySelector('.storyDrawer').getBoundingClientRect();return document.dir==='rtl'? r.left<5 : r.right>innerWidth-5})()"))
        pg.screenshot(path=OUT + f'03b_explain_drawer_{lang}.png')
        pg.keyboard.press('Escape'); pg.click('.storyDrawer .drawerClose')
        nav(pg, t['sales']); pg.wait_for_selector('.chart'); check(f'{lang} revenue page chart', pg.locator('.chart svg').count() > 0); pg.screenshot(path=OUT + f'05_revenue_{lang}.png', full_page=True)
        nav(pg, t['change']); pg.screenshot(path=OUT + f'05b_xray_{lang}.png', full_page=True)
        nav(pg, t['cases']); pg.wait_for_timeout(500); pg.locator('.caseRow').first.click(); pg.wait_for_timeout(800); pg.screenshot(path=OUT + f'05c_cases_{lang}.png', full_page=True)
        nav(pg, t['ai']); pg.locator('.chip').first.click(); pg.wait_for_selector('.bubble.bot', timeout=15000); pg.wait_for_timeout(1200)
        check(f'{lang} ai: answered', pg.locator('.bubble.bot').count() >= 1)
        if lang == 'ar': check('ar ai: no env-var leak / English answer', 'NEXUS_LLM' not in pg.locator('.chat').inner_text() and 'Calculated from' not in pg.locator('.chat').inner_text())
        pg.screenshot(path=OUT + f'06_nexus_ai_{lang}.png', full_page=True)
        nav(pg, t['brief']); pg.click('main button.primary'); pg.wait_for_selector('.presentationFrame'); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT + f'07_story_1_{lang}.png')
        first = pg.locator('.presentationBody h2').inner_text()
        pg.keyboard.press('ArrowLeft' if lang == 'ar' else 'ArrowRight'); pg.wait_for_timeout(300)
        check(f'{lang} story: arrow key follows reading direction', pg.locator('.presentationBody h2').inner_text() != first)
        pg.keyboard.press('ArrowLeft' if lang == 'ar' else 'ArrowRight'); pg.wait_for_timeout(300); pg.screenshot(path=OUT + f'07_story_3_{lang}.png')
        pg.keyboard.press('Escape'); pg.wait_for_selector('.presentationFrame', state='detached'); check(f'{lang} story: Escape closes', True)
        nav(pg, t['rep']); pg.screenshot(path=OUT + f'09_reports_{lang}.png')
        # language switch keeps page & context
        pg.locator('.langswitch button').nth(1 if lang == 'ar' else 0).click(); pg.wait_for_timeout(500)
        check(f'{lang}: language switch keeps current page', pg.locator('.sidebar nav button.active').count() == 1 and pg.locator('.card h3').count() > 0)
        check(f'{lang}: console clean', not errs, errs[:2])
        c.close()
    for lang in ('ar', 'en'):
        pg = ctx(b, lang, 390, 844).new_page(); pg.goto('http://localhost:5173/'); pg.wait_for_selector('.kpi strong'); pg.wait_for_timeout(1200)
        check(f'{lang} mobile: no horizontal overflow', not pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth'))
        pg.screenshot(path=OUT + f'08_mobile_overview_{lang}.png'); pg.click('.mobileMenu'); pg.wait_for_timeout(500); pg.screenshot(path=OUT + f'08_mobile_menu_{lang}.png')
        pg2 = ctx(b, lang, 390, 844).new_page(); pg2.goto('http://localhost:5174/'); pg2.wait_for_selector('form'); pg2.screenshot(path=OUT + f'08_mobile_login_{lang}.png')
        check(f'{lang} mobile login: no overflow', not pg2.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth'))
    b.close()
bad = [r for r in results if not r[1]]
print(f'\n{len(results)-len(bad)}/{len(results)} checks passed'); sys.exit(1 if bad else 0)
