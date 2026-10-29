"""Branded, bilingual executive PDF. Figures are printed exactly as stored; nothing is recomputed here."""
from io import BytesIO
from pathlib import Path
ASSETS = Path(__file__).parent / 'assets'
AR = {
 'title': 'التقرير التنفيذي', 'sub': 'ملخص مستند إلى الأدلة', 'period': 'فترة التقرير', 'period_v': 'كامل البيانات المتاحة',
 'generated': 'تاريخ الإنشاء', 'metrics': 'المؤشرات الرئيسية', 'reliability': 'الموثوقية', 'source': 'المصدر',
 'cases': 'التحقيقات', 'notes': 'ملاحظات حول موثوقية البيانات',
 'note1': 'التحذيرات ليست خسائر مؤكدة، والأرقام تحتفظ بحدود مصادرها الأصلية.',
 'note2': 'فروق المشتريات لا تعني خسائر فعلية ولا وحدات مادية مكافئة.',
 'page': 'صفحة', 'none': 'لا توجد تحقيقات مسجلة',
 'trust': {'verified': 'موثَّق', 'partially_verified': 'موثَّق جزئيًا', 'unverified': 'قيد المراجعة', 'blocked': 'غير معتمد', 'warning': 'يحتاج انتباهًا'},
 'status': {'open': 'مفتوح', 'investigating': 'قيد التحقيق', 'action_required': 'يتطلب إجراءً', 'resolved': 'تم الحل', 'dismissed': 'مُستبعد'},
 'm': {'net_sales': 'صافي المبيعات', 'sales_orders': 'عدد الطلبات', 'sold_units': 'الوحدات المباعة', 'purchase_sales_ratio': 'نسبة الشراء إلى المبيعات',
       'margin': 'الهامش المُسجَّل', 'purchase_line_cost': 'تكلفة بنود الشراء', 'refunds': 'المرتجعات',
       'purchased_units': 'وحدات الشراء', 'marketing_attributed_orders': 'الطلبات المنسوبة للتسويق', 'orders_before_branch_open': 'طلبات سابقة لافتتاح الفرع',
       'sku_count_both': 'منتجات مشتركة بين الشراء والبيع', 'returns': 'سجلات المرتجعات'},
 'unit': {'units': 'وحدة', 'orders': 'طلب', 'attributions': 'نسبة', 'SKUs': 'منتج', 'records': 'سجل', 'source units': 'وحدة مصدر'},
 'egp': 'ج.م',
 'case': {'Procurement versus sales unit reconciliation': 'مطابقة وحدات الشراء مع وحدات المبيعات', 'Marketing attribution exceeds recorded orders': 'الطلبات المنسوبة للتسويق تتجاوز الطلبات المسجلة', 'Orders predate branch opening dates': 'طلبات تسبق تواريخ افتتاح الفروع'}}
EN = {'title': 'Executive Report', 'sub': 'Evidence-based summary', 'period': 'Reporting period', 'period_v': 'All available data',
 'generated': 'Generated', 'metrics': 'Key metrics', 'reliability': 'Reliability', 'source': 'Source', 'cases': 'Investigations',
 'notes': 'Data reliability notes', 'note1': 'Warnings are not confirmed losses. Figures preserve the limitations of their original sources.',
 'note2': 'Procurement differences do not imply realized losses or equivalent physical units.', 'page': 'Page', 'none': 'No investigations recorded',
 'trust': {'verified': 'Verified', 'partially_verified': 'Partially verified', 'unverified': 'Pending review', 'blocked': 'Not approved', 'warning': 'Needs attention'},
 'status': {'open': 'Open', 'investigating': 'Investigating', 'action_required': 'Action required', 'resolved': 'Resolved', 'dismissed': 'Dismissed'},
 'm': {}, 'unit': {}, 'egp': 'EGP', 'case': {}}

def build(lang, metrics, cases, generated):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        arabic_reshaper = None
        get_display = None
    # Prefer the project's existing local fonts, but allow a system font fallback.
    # Font binaries are not bundled with the repaired distribution.
    import os
    windows_fonts = Path(os.getenv('WINDIR', r'C:\Windows')) / 'Fonts'
    linux_fonts = Path('/usr/share/fonts/truetype/dejavu')
    def choose_font(*options):
        for candidate in options:
            if candidate.is_file():
                return str(candidate)
        raise RuntimeError('A compatible TrueType font is required for PDF export; install a local Arabic-compatible font.')
    regular = choose_font(
        ASSETS / 'fonts' / 'IBMPlexSansArabic-Regular.ttf',
        windows_fonts / 'arial.ttf', windows_fonts / 'segoeui.ttf',
        linux_fonts / 'DejaVuSans.ttf')
    bold = choose_font(
        ASSETS / 'fonts' / 'IBMPlexSansArabic-Bold.ttf',
        windows_fonts / 'arialbd.ttf', windows_fonts / 'segoeuib.ttf',
        linux_fonts / 'DejaVuSans-Bold.ttf', Path(regular))
    semibold = choose_font(
        ASSETS / 'fonts' / 'IBMPlexSansArabic-SemiBold.ttf',
        Path(bold))
    pdfmetrics.registerFont(TTFont('Plex', regular))
    pdfmetrics.registerFont(TTFont('Plex-SB', semibold))
    pdfmetrics.registerFont(TTFont('Plex-B', bold))
    S = AR if lang == 'ar' else EN
    rtl = lang == 'ar'
    def sh(x):  # shape + visual-order Arabic; leaves Latin/digits readable
        x = str(x)
        return get_display(arabic_reshaper.reshape(x)) if (arabic_reshaper is not None and get_display is not None and (rtl or any('\u0600' <= ch <= '\u06ff' for ch in x))) else x
    BRAND = (0 / 255, 62 / 255, 139 / 255); INK = (10 / 255, 42 / 255, 85 / 255); MUTED = (74 / 255, 91 / 255, 116 / 255)
    out = BytesIO(); c = Canvas(out, pagesize=A4); W, H = A4; M = 45
    L, R = M, W - M
    def put(x_left, x_right, y, text, font='Plex', size=10, color=INK):
        c.setFont(font, size); c.setFillColorRGB(*color)
        (c.drawRightString(x_right, y, sh(text)) if rtl else c.drawString(x_left, y, sh(text)))
    def header():
        c.setFillColorRGB(*BRAND); c.rect(0, H - 8, W, 8, stroke=0, fill=1)
        logo = ImageReader(str(ASSETS / 'cottonil-logo.png')); lw = 150; lh = lw * 50 / 345   # aspect ratio preserved
        c.drawImage(logo, (R - lw) if rtl else L, H - 30 - lh, width=lw, height=lh, mask='auto')
        return H - 30 - lh - 30
    def footer(n):
        c.setFont('Plex', 8); c.setFillColorRGB(*MUTED)
        c.drawCentredString(W / 2, 28, sh(f"{S['page']} {n}") if rtl else f"{S['page']} {n}")
    page = 1; y = header()
    put(L, R, y, S['title'], 'Plex-B', 22); y -= 22
    put(L, R, y, S['sub'], 'Plex', 11, MUTED); y -= 26
    put(L, R, y, f"{S['period']}: {S['period_v']}", 'Plex', 10); y -= 16
    stamp = str(generated)[:16].replace('T', ' ') + ' UTC'
    put(L, R, y, f"{S['generated']}: {stamp}", 'Plex', 10); y -= 28
    put(L, R, y, S['metrics'], 'Plex-SB', 13, BRAND); y -= 8
    c.setStrokeColorRGB(*BRAND); c.setLineWidth(1); c.line(L, y, R, y); y -= 20
    for m in metrics:
        if y < 120: footer(page); c.showPage(); page += 1; y = header()
        name = S['m'].get(m['key'], m['key'].replace('_', ' ').title())
        unit = S['egp'] if m['unit'] == 'EGP' else ('' if m['unit'] in ('ratio', None) else S['unit'].get(m['unit'], m['unit']))
        # figures are printed exactly as stored: money/ratios keep 2 decimals, whole counts show no spurious decimals
        v = m['value']; txt = (f"{v:,.2f}" if (m['unit'] in ('EGP', 'ratio') or float(v) != int(v)) else f"{int(v):,}") if v is not None else '—'
        val = f"{txt} {unit}".strip()
        put(L, R, y, name, 'Plex-SB', 11); y -= 15
        put(L, R, y, val, 'Plex-B', 13, BRAND); y -= 15
        put(L, R, y, f"{S['reliability']}: {S['trust'].get(m['trust'], m['trust'])}", 'Plex', 9, MUTED); y -= 12
        put(L, R, y, f"{S['source']}: {str(m['source'])[:95]}", 'Plex', 8, MUTED); y -= 20
    if y < 160: footer(page); c.showPage(); page += 1; y = header()
    put(L, R, y, S['cases'], 'Plex-SB', 13, BRAND); y -= 8; c.line(L, y, R, y); y -= 18
    if not cases: put(L, R, y, S['none'], 'Plex', 10, MUTED); y -= 18
    for r in cases:
        if y < 80: footer(page); c.showPage(); page += 1; y = header()
        put(L, R, y, f"{r['id']}  ·  {S['case'].get(r['title'], str(r['title']))[:70]}  ·  {S['status'].get(r['status'], r['status'])}", 'Plex', 9); y -= 16
    if y < 110: footer(page); c.showPage(); page += 1; y = header()
    y -= 10; put(L, R, y, S['notes'], 'Plex-SB', 11, BRAND); y -= 16
    put(L, R, y, S['note1'], 'Plex', 9, MUTED); y -= 13; put(L, R, y, S['note2'], 'Plex', 9, MUTED)
    footer(page); c.save(); out.seek(0)
    return out
