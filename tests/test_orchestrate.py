import sys
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def test_orchestrate_generates_run_artifacts():
    # ?????? ????????????
    subprocess.run([sys.executable, "scripts/orchestrate.py"], cwd=ROOT, check=True)

    last_run = ROOT / "data" / "last_run.json"
    assert last_run.exists()

    payload = json.loads(last_run.read_text(encoding="utf-8-sig"))
    assert payload["verification_ok"] is True
    assert payload["total_mail"] >= 1
    assert payload["total_scored"] == payload["total_merged"]

    runs_dir = ROOT / "data" / "runs"
    assert runs_dir.exists()
    run_files = list(runs_dir.glob("run_*.json"))
    assert len(run_files) >= 1

