"""DATA-DEPENDENT VERIFICATION — requires the authorized Cottonil datasets.

NOT collected by default (filename lacks test_ prefix). Run only after authorized data is
loaded into the configured NEXUS_DB:
    NEXUS_REAL_DATA_VERIFY=1 python -m pytest tests/data_dependent_real_data.py
The 841,274,176.32 figure is a PREVIOUSLY OBSERVED baseline, not certified truth; a mismatch
must be investigated, not silently "fixed".
"""
import os, pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.skipif(os.getenv("NEXUS_REAL_DATA_VERIFY") != "1", reason="needs authorized real data")
client = TestClient(app)


def test_previous_net_sales_baseline():
    d = client.get("/api/sales/intelligence").json()
    assert abs(d["totals"]["net"] - 841274176.32) < .01
