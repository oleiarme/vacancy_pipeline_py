from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from vacancy_pipeline_py.gmail_parser import (
    build_location_signals,
    filter_vacancies_by_location,
    parse_job_cards_from_html,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RUNS_DIR = DATA_DIR / "runs"
FIXTURE_HTML = ROOT / "tests" / "fixtures" / "email_jobs_sample.html"
CONFIG_PATH = ROOT / "config" / "search_config.json"

MAIL_PATH = DATA_DIR / "vacancies_mail_glassdoor.json"
MERGED_PATH = DATA_DIR / "vacancies.json"
SCORED_PATH = DATA_DIR / "scored_vacancies.json"
LAST_RUN_PATH = DATA_DIR / "last_run.json"

@dataclass
class RunSummary:
    run_id: str
    started_at: str
    finished_at: str
    ok: bool
    total_mail: int
    total_merged: int
    total_scored: int
    verification_ok: bool
    issues: list[str]

def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))

def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _score_stub(vacancies: list[dict]) -> list[dict]:
    out = []
    for v in vacancies:
        score = 70 if "senior" in str(v.get("title", "")).lower() else 62
        row = dict(v)
        row["score"] = score
        row["relevant"] = score >= 60
        row["reasoning"] = "stub-score"
        out.append(row)
    return out

def _run_verify() -> bool:
    # ?????? ??????? ??????????? ??? ???????? ????????
    res = subprocess.run(
        [sys.executable, "scripts/verify_pipeline.py"],
        cwd=ROOT,
        check=False,
    )
    return res.returncode == 0

def run() -> RunSummary:
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    issues: list[str] = []

    config = _read_json(CONFIG_PATH, {})
    signals = build_location_signals(config)

    if not FIXTURE_HTML.exists():
        raise RuntimeError(f"Fixture not found: {FIXTURE_HTML}")

    html = FIXTURE_HTML.read_text(encoding="utf-8")
    cards = parse_job_cards_from_html(html)
    mail_filtered = filter_vacancies_by_location(cards, signals)

    _write_json(MAIL_PATH, mail_filtered)
    _write_json(MERGED_PATH, mail_filtered)

    scored = _score_stub(mail_filtered)
    _write_json(SCORED_PATH, scored)

    verification_ok = _run_verify()
    if not verification_ok:
        issues.append("verify_pipeline failed")

    finished = datetime.now(timezone.utc)
    summary = RunSummary(
        run_id=run_id,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        ok=verification_ok,
        total_mail=len(mail_filtered),
        total_merged=len(mail_filtered),
        total_scored=len(scored),
        verification_ok=verification_ok,
        issues=issues,
    )

    run_path = RUNS_DIR / f"run_{run_id}.json"
    _write_json(run_path, asdict(summary))
    _write_json(LAST_RUN_PATH, asdict(summary))
    return summary

if __name__ == "__main__":
    result = run()
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
