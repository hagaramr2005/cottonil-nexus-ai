"""Layered readiness report. Every field is observed, never assumed.

Levels (each independent so the UI can say exactly what is missing):
  process_alive -> database_connected -> schema_ready -> datasets_ingested
  -> sales_mart_ready -> metrics_certified -> llm (configured/reachable/model_available)
"""
import os
from fastapi import APIRouter
from . import auth, copilot, core

router = APIRouter()

REQUIRED_TABLES = {'datasets', 'metrics', 'cases', 'events', 'decisions', 'daily_sales',
                   'sku_sales', 'branch_sales', 'sku_purchases', 'source_samples'}


def _check(name: str, ok: bool, detail: str, code: str | None = None) -> dict:
    return {'name': name, 'ok': bool(ok), 'detail': detail, 'code': None if ok else code}


def snapshot() -> dict:
    checks = [_check('process_alive', True, 'API process is serving requests.')]
    tables, trust, n_datasets, db_ok = set(), {}, 0, False
    try:
        conn = core.db()  # creates schema if absent; non-destructive CREATE IF NOT EXISTS
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            n_datasets = conn.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]
            for r in conn.execute('SELECT trust, COUNT(*) FROM metrics GROUP BY trust'):
                trust[r[0]] = r[1]
        finally:
            conn.close()
        db_ok = True
    except Exception as exc:  # report class only: never leak paths or SQL to clients
        checks.append(_check('database_connected', False, f'Database unavailable ({type(exc).__name__}).', 'DB_UNAVAILABLE'))
    if db_ok:
        checks.append(_check('database_connected', True, 'SQLite connection opened.'))
        missing = sorted(REQUIRED_TABLES - tables)
        checks.append(_check('schema_ready', not missing, 'Core schema present.' if not missing else f'Missing tables: {", ".join(missing)}', 'SCHEMA_MISSING'))
        checks.append(_check('datasets_ingested', n_datasets > 0,
                             f'{n_datasets} source dataset(s) registered.' if n_datasets else 'No business datasets ingested. Authorized data import required (data not connected).',
                             'DATA_NOT_CONNECTED'))
        checks.append(_check('sales_mart_ready', 'sales_mart' in tables,
                             'Sales mart built.' if 'sales_mart' in tables else 'Sales mart not built; sales/product intelligence endpoints return 503.', 'SALES_MART_MISSING'))
        verified = trust.get('verified', 0)
        total = sum(trust.values())
        # No metric is "certified" by this codebase: certification needs stakeholder sign-off.
        checks.append(_check('metrics_certified', False,
                             f'0 certified; {verified} of {total} metrics are source-count verified only. Business certification requires Cottonil approval.' if total else 'No metrics computed.',
                             'METRICS_UNCERTIFIED'))
    llm = copilot.status_snapshot()
    checks.append(_check('llm_configured', llm.get('configured'), 'LLM endpoint configured.' if llm.get('configured') else 'LLM not configured; Copilot uses deterministic fallback.', 'LLM_NOT_CONFIGURED'))
    checks.append(_check('llm_reachable_and_model_available', llm.get('available') is True, llm.get('reason') or 'Model available.', 'LLM_UNAVAILABLE'))
    ready = all(c['ok'] for c in checks if c['name'] in ('database_connected', 'schema_ready', 'datasets_ingested', 'sales_mart_ready'))
    return {
        'overall': 'ready' if ready else ('degraded' if db_ok else 'not_ready'),
        'data_state': 'populated' if n_datasets else 'data_not_connected',
        'checks': checks,
        'optional_modules': {'llm': llm.get('mode'), 'fashion_cv': 'disabled (no trained checkpoint)'},
        'security': {'auth_enabled': auth.enabled(), 'production_mode': auth.production_mode(),
                     'write_token_configured': bool(os.getenv('NEXUS_WRITE_TOKEN')),
                     'branch_scoped_authorization': True, 'branch_scope_policy': 'deny non-scope-aware endpoints; allow restricted branches and sales mart' },
        'metric_trust_counts': trust,
    }


@router.get('/api/readiness')
def readiness():
    return snapshot()
