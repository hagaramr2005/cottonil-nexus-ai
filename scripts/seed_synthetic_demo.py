"""Create an isolated, opt-in synthetic portfolio demo (NEVER company data).

Use the deliberately small, hand-checkable fixture also used by regression tests.
Never reads existing customer data, never modifies the app's default database.
"""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description='Create isolated SYNTHETIC ONLY demo data')
    parser.add_argument('--directory', type=Path, default=ROOT/'data'/'demo_synthetic',
                        help='NEW empty directory, default ./data/demo_synthetic')
    args = parser.parse_args()
    if os.getenv('NEXUS_ENV', 'development').lower() == 'production':
        parser.error('Synthetic demo seeding is forbidden in production mode')
    target = args.directory.resolve()
    if target.exists():
        parser.error('Target already exists. Refusing to overwrite or mingle data.')
    target.mkdir(parents=True, exist_ok=False)
    # These paths are set before imports so there is no accidental interaction
    # with the configured or default application store.
    raw, database = target/'raw', target/'demo.sqlite'
    os.environ['NEXUS_DB'] = str(database)
    os.environ['NEXUS_RAW'] = str(raw)
    sys.path.insert(0, str(ROOT/'backend'))
    sys.path.insert(0, str(ROOT/'backend'/'tests'))
    sys.path.insert(0, str(ROOT/'scripts'))
    from synthetic_fixture import EXPECTED, write_fixture
    from app.core import ingest
    from build_sales_mart import build
    write_fixture(raw)
    result = ingest()
    mart = build()
    (target/'SYNTHETIC_DEMO_NOT_COMPANY_DATA.txt').write_text(
        'SYNTHETIC / DEMO DATA ONLY. Do not represent this as Cottonil company evidence.\n'
        'Test fixture: 12 fabricated orders, net EGP 1,200, 24 units.\n', encoding='utf-8')
    print('SYNTHETIC demo created. This is NOT real Cottonil data.')
    print('Datasets:', result['datasets'], '| Sales mart cells:', mart['mart_rows'])
    print('Expected hand-checkable values:', EXPECTED)
    print('To use ONLY this demo database, edit local .env to set:')
    print('NEXUS_DB=' + str(database))
    print('NEXUS_RAW=' + str(raw))
    print('Restart FastAPI; do not publish this demo as company analytics.')


if __name__ == '__main__':
    main()
