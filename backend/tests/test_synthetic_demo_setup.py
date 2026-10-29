"""Safety test for opt-in local synthetic demo bootstrap."""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'seed_synthetic_demo.py'


def test_seed_creates_isolated_synthetic_demo_and_refuses_overwrite(tmp_path):
    output = tmp_path/'synthetic'
    env = dict(os.environ, NEXUS_ENV='development')
    run = subprocess.run([sys.executable, str(SCRIPT), '--directory', str(output)], env=env,
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr
    assert 'NOT real Cottonil' in run.stdout
    assert (output/'demo.sqlite').exists()
    assert (output/'SYNTHETIC_DEMO_NOT_COMPANY_DATA.txt').exists()
    again = subprocess.run([sys.executable, str(SCRIPT), '--directory', str(output)], env=env,
                           capture_output=True, text=True, timeout=30)
    assert again.returncode != 0
    assert 'Refusing to overwrite' in again.stderr


def test_seed_refuses_production(tmp_path):
    output = tmp_path/'synthetic'
    env = dict(os.environ, NEXUS_ENV='production')
    run = subprocess.run([sys.executable, str(SCRIPT), '--directory', str(output)], env=env,
                         capture_output=True, text=True, timeout=30)
    assert run.returncode != 0 and not output.exists()
