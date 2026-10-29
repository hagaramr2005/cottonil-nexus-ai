from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app
client=TestClient(app)

def test_analyst_grounded(synthetic_db):
    """Runs on SYNTHETIC TEST DATA; asserts structure, not company values."""
    r=client.post('/api/analyst/ask',json={'question':'What are the net sales and orders?'})
    assert r.status_code==200
    data=r.json()
    assert data['mode']=='verified-analytics'
    assert {'net_sales','sales_orders'}.issubset({m['key'] for m in data['metrics']})
    assert all('source' in m and 'trust' in m for m in data['metrics'])

def test_analyst_refuses_unsupported():
    d=client.post('/api/analyst/ask',json={'question':'Tell me the CEO favorite movie'}).json()
    assert not d['metrics'] and 'not supported' in d['answer']

def test_pdf_export():
    r=client.get('/api/reports/executive.pdf')
    assert r.status_code==200 and r.content[:4]==b'%PDF'

def test_excel_export():
    r=client.get('/api/reports/executive.xlsx')
    assert r.status_code==200 and r.content[:2]==b'PK'

def test_color_analysis():
    image=Image.new('RGB',(64,64),(190,25,25));buf=BytesIO();image.save(buf,'PNG')
    r=client.post('/api/cv/color-analysis',files={'file':('red.png',buf.getvalue(),'image/png')})
    assert r.status_code==200
    assert r.json()['dominant_color']=='red'
    assert 'heuristic' in r.json()['method']

def test_reject_non_image():
    r=client.post('/api/cv/color-analysis',files={'file':('no.txt',b'abc','text/plain')})
    assert r.status_code==415
