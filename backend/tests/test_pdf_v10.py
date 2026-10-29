from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_pdf_both_languages_render():
    for lang in ('en','ar'):
        r=c.get('/api/reports/executive.pdf?lang='+lang)
        assert r.status_code==200 and r.content[:5]==b'%PDF-' and len(r.content)>8000
def test_pdf_rejects_unknown_language():
    assert c.get('/api/reports/executive.pdf?lang=fr').status_code==422
def test_arabic_pdf_embeds_arabic_font():
    from pathlib import Path
    from app import report_pdf
    r=c.get('/api/reports/executive.pdf?lang=ar')
    assert r.status_code == 200
    # Verify a real TrueType font was embedded, even when bundled font assets
    # are absent and the generator uses an Arabic-capable system font instead.
    assert b'/FontFile2' in r.content
    if (report_pdf.ASSETS / 'fonts' / 'IBMPlexSansArabic-Regular.ttf').is_file():
        assert b'IBMPlexSansArabic' in r.content
