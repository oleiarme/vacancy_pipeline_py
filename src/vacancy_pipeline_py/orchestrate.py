from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vacancy_pipeline_py.gmail_client import GmailClient
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
ENV_PATH = ROOT / ".env"
TOKEN_PATH = ROOT / "auth" / "gmail_token.json"

MAIL_PATH = DATA_DIR / "vacancies_mail_glassdoor.json"
MERGED_PATH = DATA_DIR / "vacancies.json"
SCORED_PATH = DATA_DIR / "scored_vacancies.json"
LAST_RUN_PATH = DATA_DIR / "last_run.json"


@dataclass
class RunSummary:
    run_id: str
    source_requested: str
    source_used: str
    started_at: str
    finished_at: str
    ok: bool
    total_mail: int
    total_merged: int
    total_scored: int
    verification_ok: bool
    matched_emails: int
    issues: list[str]


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    if not ENV_PATH.exists():
        return out
    for raw in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


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
    res = subprocess.run(
        [sys.executable, "scripts/verify_pipeline.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return res.returncode == 0


def _decode_b64url(data: str) -> str:
    s = str(data or "").replace("-", "+").replace("_", "/")
    s += "=" * ((4 - len(s) % 4) % 4)
    raw = base64.b64decode(s.encode("ascii"))
    return raw.decode("utf-8", errors="replace")


def _collect_html_parts(payload: dict[str, Any] | None, out: list[str]):
    if not isinstance(payload, dict):
        return
    mime = str(payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = body.get("data")
    if isinstance(data, str) and data.strip():
        decoded = _decode_b64url(data)
        if "text/html" in mime:
            out.append(decoded)
        elif "text/plain" in mime:
            out.append(decoded)
    for part in payload.get("parts") or []:
        _collect_html_parts(part, out)


def _dedupe_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for c in cards:
        cid = str(c.get("id") or "").strip()
        key = cid or str(c.get("link") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _fixture_cards(signals: list[str]) -> list[dict[str, Any]]:
    html = FIXTURE_HTML.read_text(encoding="utf-8")
    cards = parse_job_cards_from_html(html)
    return filter_vacancies_by_location(cards, signals)


def _gmail_cards(
    signals: list[str],
    label_name: str,
    query: str,
    max_emails: int,
) -> tuple[list[dict[str, Any]], int]:
    envv = _load_env()
    token = str(os.getenv("GMAIL_ACCESS_TOKEN") or envv.get("GMAIL_ACCESS_TOKEN") or "").strip()

    if not token and TOKEN_PATH.exists():
        token_json = _read_json(TOKEN_PATH, {})
        token = str((token_json or {}).get("access_token") or "").strip()

    if not token:
        raise RuntimeError("Missing Gmail access token (GMAIL_ACCESS_TOKEN or auth/gmail_token.json)")

    client = GmailClient(access_token=token)
    label_id = client.find_label_id(label_name)
    if not label_id:
        raise RuntimeError(f"Gmail label not found: {label_name}")

    messages = client.list_messages(label_id=label_id, query=query, max_results=max_emails)
    all_cards: list[dict[str, Any]] = []

    for msg in messages:
        msg_id = str(msg.get("id") or "").strip()
        if not msg_id:
            continue
        full = client.get_message_full(msg_id)
        html_parts: list[str] = []
        _collect_html_parts(full.get("payload"), html_parts)

        if not html_parts:
            snippet = str(full.get("snippet") or "")
            if snippet:
                html_parts.append(snippet)

        for html in html_parts:
            all_cards.extend(parse_job_cards_from_html(html))

    all_cards = _dedupe_cards(all_cards)
    all_cards = filter_vacancies_by_location(all_cards, signals)
    return all_cards, len(messages)


def run(
    source: str = "fixture",
    gmail_label: str = "glassdoor",
    gmail_query: str = "",
    gmail_max_emails: int = 20,
    fallback_fixture: bool = True,
) -> RunSummary:
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    issues: list[str] = []

    config = _read_json(CONFIG_PATH, {})
    signals = build_location_signals(config)
    if not signals:
        raise RuntimeError("config.filters.locations is empty")

    source_requested = source
    source_used = source
    matched_emails = 0

    if source == "gmail":
        try:
            cards, matched_emails = _gmail_cards(
                signals=signals,
                label_name=gmail_label,
                query=gmail_query,
                max_emails=gmail_max_emails,
            )
            if not cards and fallback_fixture:
                cards = _fixture_cards(signals)
                source_used = "fixture-fallback"
                issues.append("gmail produced 0 cards, fallback fixture used")
        except Exception as e:
            if not fallback_fixture:
                raise
            cards = _fixture_cards(signals)
            source_used = "fixture-fallback"
            issues.append(f"gmail failed, fallback fixture used: {e}")
    else:
        cards = _fixture_cards(signals)

    _write_json(MAIL_PATH, cards)
    _write_json(MERGED_PATH, cards)

    scored = _score_stub(cards)
    _write_json(SCORED_PATH, scored)

    verification_ok = _run_verify()
    if not verification_ok:
        issues.append("verify_pipeline failed")

    finished = datetime.now(timezone.utc)
    summary = RunSummary(
        run_id=run_id,
        source_requested=source_requested,
        source_used=source_used,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        ok=verification_ok,
        total_mail=len(cards),
        total_merged=len(cards),
        total_scored=len(scored),
        verification_ok=verification_ok,
        matched_emails=matched_emails,
        issues=issues,
    )

    run_path = RUNS_DIR / f"run_{run_id}.json"
    _write_json(run_path, asdict(summary))
    _write_json(LAST_RUN_PATH, asdict(summary))
    return summary


if __name__ == "__main__":
    result = run()
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))