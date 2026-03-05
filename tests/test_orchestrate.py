import json
from pathlib import Path
import shutil

from vacancy_pipeline_py.orchestrate import run

ROOT = Path(__file__).resolve().parents[1]


def _make_state_dir(name: str) -> Path:
    target = ROOT / ".tmp-test-state" / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_orchestrate_generates_run_artifacts(monkeypatch):
    state_dir = _make_state_dir("orchestrate")
    monkeypatch.setenv("VACANCY_PIPELINE_STATE_DIR", str(state_dir))
    monkeypatch.setenv("GMAIL_GLASSDOOR_TIME_WINDOW", "today")

    summary = run()

    last_run = state_dir / "data" / "last_run.json"
    assert last_run.exists()

    payload = json.loads(last_run.read_text(encoding="utf-8-sig"))
    assert summary.verification_ok is True
    assert payload["verification_ok"] is True
    assert payload["total_mail"] >= 1
    assert payload["total_scored"] == payload["total_merged"]

    runs_dir = state_dir / "runs"
    assert runs_dir.exists()
    run_files = list(runs_dir.glob("run_*.json"))
    assert len(run_files) >= 1


def test_orchestrate_accepts_2d_time_window(monkeypatch):
    state_dir = _make_state_dir("orchestrate-2d")
    monkeypatch.setenv("VACANCY_PIPELINE_STATE_DIR", str(state_dir))
    monkeypatch.setenv("GMAIL_GLASSDOOR_TIME_WINDOW", "2d")

    summary = run()

    assert summary.verification_ok is True

