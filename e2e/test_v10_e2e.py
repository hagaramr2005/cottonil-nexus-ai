"""V10 browser tests. Needs: backend on :8000 (auth off), backend on :8001 (NEXUS_AUTH_ENABLED=1, users exec:Demo-pass-1:viewer;root:Admin-pass-1:admin),
Vite on :5173 (-> 8000) and :5174 (NEXUS_API=http://127.0.0.1:8001).  See docs/V10_BRAND_AND_ARABIC_UX_REPORT.md for exact commands."""
import os, re, urllib.request
import pytest
from playwright.sync_api import sync_playwright

OPEN, AUTH = os.getenv('NEXUS_URL', 'http://localhost:5173/'), os.getenv('NEXUS_AUTH_URL', 'http://localhost:5174/')
AR = {'overview': 'مركز القيادة التنفيذية', 'sales': 'أداء الأعمال', 'briefing': 'الملخص التنفيذي', 'change': 'التحليل المتعمق للإيرادات', 'money': 'تحليل الفروع',
      'sku': 'تحليل أداء المنتجات', 'anomaly': 'رصد الأنماط غير المعتادة', 'risk': 'مؤشرات المخاطر', 'ai': 'المساعد الذكي للأعمال', 'cases': 'مساحة التحقيقات',
      'recommend': 'مركز الإجراءات', 'decision': 'مركز إدارة القرارات', 'reports': 'التقارير التنفيذية', 'passport': 'موثوقية البيانات', 'trust': 'سجل المؤشرات ومصادرها',
      'graph': 'مسار مصدر المنتج', 'settings': 'الإعدادات'}
ALLOW = re.compile(r'^(Cottonil|COTTONIL|EGP|SKU\w*|MAD|CSV|PDF|Excel|JSON|English|POS|NEX|UOM|Z|X|Ray|ID|AI)$', re.I)

@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(); yield b; b.close()

def page(browser, lang, url=OPEN, w=1440, h=900):
    c = browser.new_context(viewport={'width': w, 'height': h})
    c.add_init_script(f"try{{localStorage.setItem('cottonil-language','{lang}')}}catch(e){{}}")
    pg = c.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(url); pg.errs = errs
    return pg

def nav(pg, text): pg.locator('.sidebar nav button', has_text=text).first.click(); pg.wait_for_timeout(900)

@pytest.mark.parametrize('lang', ['ar', 'en'])
def test_login_validation_failure_and_success(browser, lang):
    pg = page(browser, lang, AUTH); pg.wait_for_selector('form')
    assert pg.evaluate('document.documentElement.dir') == ('rtl' if lang == 'ar' else 'ltr')
    pg.click('button[type=submit]'); assert pg.locator('.fielderr').count() == 2
    pg.fill('input[autocomplete=username]', 'exec'); pg.fill('input[autocomplete=current-password]', 'wrong'); pg.click('button[type=submit]')
    pg.wait_for_selector('[role=alert]'); assert pg.locator('.kpi').count() == 0
    pg.fill('input[autocomplete=current-password]', 'Demo-pass-1'); pg.click('button[type=submit]')
    pg.wait_for_selector('.kpi strong', timeout=15000); assert not pg.errs

def test_viewer_has_no_admin_nav_and_server_blocks_diagnostics(browser):
    pg = page(browser, 'en', AUTH); pg.wait_for_selector('form')
    pg.fill('input[autocomplete=username]', 'exec'); pg.fill('input[autocomplete=current-password]', 'Demo-pass-1'); pg.click('button[type=submit]'); pg.wait_for_selector('.kpi strong')
    assert pg.locator('.sidebar nav button', has_text='Operational readiness').count() == 0
    assert pg.evaluate("sessionStorage.getItem('nexus-auth')") is None
    for path in ('/api/cv/status', '/api/product/readiness'):
        assert pg.request.get('http://localhost:5174' + path).status == 403

def test_no_model_center_in_client_navigation(browser):
    pg = page(browser, 'en'); pg.wait_for_selector('.kpi strong')
    assert not re.search(r'model center|مركز النماذج', pg.inner_text('.sidebar'), re.I)

def test_language_switch_keeps_page_and_never_changes_figures(browser):
    pg = page(browser, 'en'); pg.wait_for_selector('.kpi strong'); nav(pg, 'Business Performance'); pg.wait_for_selector('.chart')
    pg.wait_for_function("[...document.querySelectorAll('.kpi strong')].every(e=>/\\d/.test(e.innerText))", timeout=20000)
    en = pg.locator('.kpi strong').all_inner_texts()
    pg.click('.langswitch button[lang=ar]'); pg.wait_for_timeout(600)
    assert pg.evaluate('document.documentElement.dir') == 'rtl' and pg.locator('.sidebar nav button.active').inner_text().strip() == AR['sales']
    ar = pg.locator('.kpi strong').all_inner_texts()
    digits = lambda xs: [(re.search(r'\d[\d,]*(?:\.\d+)?', x) or [''])[0] for x in xs]
    assert digits(en) == digits(ar) and any(digits(ar))

def test_overview_ar_figures_match_backend_and_chart_chronology(browser):
    pg = page(browser, 'ar'); pg.wait_for_selector('.kpi strong')
    assert '841.27' in pg.locator('.kpi.lead strong').inner_text()
    pg.wait_for_selector('.recharts-area-curve'); ticks = pg.locator('.recharts-xAxis .recharts-cartesian-axis-tick-value').all_text_contents()
    ticks = [t for t in ticks if re.match(r'\d{4}-\d\d-\d\d', t)]; assert ticks == sorted(ticks) and len(ticks) >= 3   # oldest -> newest in RTL

def test_every_arabic_page_renders_without_english_leftovers(browser):
    pg = page(browser, 'ar'); pg.wait_for_selector('.kpi strong'); bad = {}
    for k, label in AR.items():
        nav(pg, label); pg.wait_for_timeout(500)
        words = {w for w in re.findall(r"[A-Za-z][A-Za-z_\-\.']{2,}", pg.inner_text('main')) if not ALLOW.match(w) and not re.search(r'\d|_|\.csv|^NEX|^SKU', w)}
        if words: bad[k] = sorted(words)[:8]
    assert not bad and not pg.errs, bad

def test_nexus_ai_supported_question_and_link_suggestions(browser):
    pg = page(browser, 'ar'); pg.wait_for_selector('.kpi strong'); nav(pg, AR['ai'])
    pg.locator('.chip').first.click(); pg.wait_for_selector('.bubble.bot', timeout=15000)
    assert not re.search(r'NEXUS_LLM|[A-Za-z]{6,} [A-Za-z]{6,} [A-Za-z]{6,}', pg.locator('.bubble.bot').inner_text())
    pg.locator('.chip', has_text=AR['change']).first.click(); pg.wait_for_timeout(600)
    assert pg.locator('.sidebar nav button.active').inner_text().strip() == AR['change']   # unsupported analysis is routed to the verified tool

def test_story_mode_navigation_follows_reading_direction(browser):
    for lang, fwd in (('ar', 'ArrowLeft'), ('en', 'ArrowRight')):
        pg = page(browser, lang); pg.wait_for_selector('.kpi strong')
        nav(pg, 'الملخص التنفيذي' if lang == 'ar' else 'Executive Briefing'); pg.click('button.primary'); pg.wait_for_selector('.presentationFrame')
        assert '1 / 5' in pg.inner_text('.presentationBody').replace('\u200f', '')
        pg.keyboard.press(fwd); pg.wait_for_timeout(200); assert '2 / 5' in pg.inner_text('.presentationBody')
        pg.keyboard.press('Escape'); pg.wait_for_selector('.presentationFrame', state='detached')

@pytest.mark.parametrize('lang', ['ar', 'en'])
def test_pdf_export_both_languages(lang):
    r = urllib.request.urlopen(f'http://localhost:8000/api/reports/executive.pdf?lang={lang}')
    body = r.read(); assert r.headers['content-type'] == 'application/pdf' and body[:5] == b'%PDF-' and (lang == 'en' or b'IBMPlexSansArabic' in body)

@pytest.mark.parametrize('lang', ['ar', 'en'])
def test_mobile_no_horizontal_overflow_and_menu(browser, lang):
    pg = page(browser, lang, w=390, h=844); pg.wait_for_selector('.kpi strong')
    assert not pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth')
    pg.click('.mobileMenu'); pg.wait_for_timeout(400); assert pg.locator('.sidebar.expanded').count() == 1
