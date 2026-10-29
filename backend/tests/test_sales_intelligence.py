"""Sales intelligence tests. Values come from SYNTHETIC TEST DATA (see synthetic_fixture.py)."""
from fastapi.testclient import TestClient
from app.main import app
from synthetic_fixture import EXPECTED

client = TestClient(app)


def test_sales_mart_totals_synthetic(synthetic_db):
    r = client.get("/api/sales/intelligence")
    assert r.status_code == 200
    d = r.json()
    assert d["totals"]["mart_cells"] > 0
    assert abs(d["totals"]["net"] - EXPECTED["net"]) < .01
    assert abs(d["totals"]["units"] - EXPECTED["units"]) < .01
    assert d["trust"]["orders"] == "blocked"


def test_filters_date_ranges_synthetic(synthetic_db):
    data = client.get("/api/sales/intelligence", params={"start": "2025-01", "end": "2025-12"}).json()
    assert len(data["monthly"]) == 12
    assert all("2025-" in m["label"] for m in data["monthly"])
    half = client.get("/api/sales/intelligence", params={"start": "2025-01", "end": "2025-06"}).json()
    assert len(half["monthly"]) == 6 and abs(half["totals"]["net"] - 600) < .01


def test_bad_date():
    assert client.get("/api/sales/intelligence?start=not-a-date").status_code == 422


def test_sku_profile_synthetic(synthetic_db):
    assert client.get("/api/skus/SYN-SKU-1/profile").status_code == 200
    assert client.get("/api/skus/NOT-A-SKU/profile").status_code == 404


def test_sales_intelligence_data_free_is_503_not_500(empty_db):
    r = client.get("/api/sales/intelligence")
    assert r.status_code == 503
    assert client.get("/api/skus/ANY/profile").status_code == 503


def test_orders_before_branch_open_synthetic(synthetic_db):
    m = {x["key"]: x for x in client.get("/api/metrics").json()}
    assert m["orders_before_branch_open"]["value"] == EXPECTED["orders_before_open"]
    assert m["purchase_sales_ratio"]["trust"] == "blocked"
