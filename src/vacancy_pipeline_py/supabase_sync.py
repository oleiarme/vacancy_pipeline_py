from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class SupabaseConfig:
    url: str
    key: str
    table: str = "vacancies"


def to_supabase_row(v: dict[str, Any]) -> dict[str, Any]:
    # ??????? ????? ?? ??????????? ??????? ????????? ? ????? ??????? Supabase
    return {
        "id": v.get("id"),
        "title": v.get("title"),
        "company": v.get("company"),
        "location": v.get("location"),
        "link": v.get("link"),
        "posted": v.get("posted"),
        "score": v.get("score"),
        "source": v.get("source") or "glassdoor",
        "relevant": bool(v.get("relevant", False)),
        "reasoning": v.get("reasoning"),
    }


def sync_vacancies(
    cfg: SupabaseConfig,
    vacancies: list[dict[str, Any]],
    dry_run: bool = True,
) -> dict[str, Any]:
    # ????????? ? ??????????? ??????
    rows = [to_supabase_row(v) for v in vacancies if isinstance(v, dict) and v.get("id")]

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "rows_count": len(rows),
            "sample": rows[:3],
        }

    if not cfg.url or not cfg.key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

    # ????????? endpoint ??? PostgREST API (Supabase)
    endpoint = f"{cfg.url.rstrip('/')}/rest/v1/{cfg.table}"
    headers = {
        "apikey": cfg.key,
        "Authorization": f"Bearer {cfg.key}",
        "Content-Type": "application/json",
        # resolution=merge-duplicates ?????????? ?????? UPSERT ?? ?????????? ????? (id)
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(endpoint, headers=headers, json=rows)

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase API {resp.status_code}: {resp.text[:400]}")

    data = resp.json() if resp.text else []
    return {
        "ok": True,
        "dry_run": False,
        "rows_count": len(rows),
        "response_count": len(data) if isinstance(data, list) else 1,
    }
