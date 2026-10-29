import importlib.util, os, sys, tempfile
from pathlib import Path
import pytest

# Point the whole session at a throwaway location BEFORE app modules import, so no test can
# create or modify the repo's data/nexus.sqlite (a user's real database lives there).
_SESSION_TMP = Path(tempfile.mkdtemp(prefix="nexus_test_"))
os.environ["NEXUS_DB"] = str(_SESSION_TMP / "session.sqlite")
os.environ["NEXUS_RAW"] = str(_SESSION_TMP / "raw")

TESTS = Path(__file__).parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))


@pytest.fixture
def synthetic_db(tmp_path, monkeypatch):
    """Isolated DB + RAW in tmp_path populated with SYNTHETIC TEST DATA. Never touches data/."""
    from app import core
    from synthetic_fixture import write_fixture
    raw = tmp_path / "raw"
    write_fixture(raw)
    monkeypatch.setattr(core, "DB", tmp_path / "synthetic.sqlite")
    monkeypatch.setattr(core, "RAW", raw)
    spec = importlib.util.spec_from_file_location("build_sales_mart", TESTS.parents[1] / "scripts" / "build_sales_mart.py")
    mart = importlib.util.module_from_spec(spec); spec.loader.exec_module(mart)
    monkeypatch.setattr(mart, "DB", core.DB)
    monkeypatch.setattr(mart, "RAW", raw)
    core.ingest()
    mart.build()
    return core.DB


@pytest.fixture
def empty_db(tmp_path, monkeypatch):
    """Data-free mode: a brand-new empty database, no CSVs."""
    from app import core
    monkeypatch.setattr(core, "DB", tmp_path / "empty.sqlite")
    monkeypatch.setattr(core, "RAW", tmp_path / "no_raw")
    return core.DB


@pytest.fixture(autouse=True)
def _never_touch_real_db(tmp_path, monkeypatch):
    """Per-test isolated default DB; synthetic_db/empty_db override this when requested."""
    from app import core
    monkeypatch.setattr(core, "DB", tmp_path / "default_isolated.sqlite")
    monkeypatch.setattr(core, "RAW", tmp_path / "default_raw")
