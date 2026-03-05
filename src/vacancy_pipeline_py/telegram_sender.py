from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str
    topic_id: str | None = None


def format_vacancy_message(v: dict[str, Any]) -> str:
    title = str(v.get("title") or "Untitled").strip()
    company = str(v.get("company") or "Unknown Company").strip()
    location = str(v.get("location") or "-").strip()
    score = v.get("score")
    posted = str(v.get("posted") or "-").strip()
    link = str(v.get("link") or "").strip()

    score_text = f"{score}%" if isinstance(score, (int, float)) else "-"
    lines = [
        f"[{score_text}] {title}",
        f"Company: {company}",
        f"Location: {location}",
        f"Posted: {posted}",
    ]
    if link:
        lines.append(link)
    return "\n".join(lines)


def build_batch_text(vacancies: list[dict[str, Any]], title: str = "Vacancy Digest") -> str:
    rows = [title, ""]
    for idx, v in enumerate(vacancies, start=1):
        rows.append(f"{idx}. {format_vacancy_message(v)}")
        rows.append("")
    return "\n".join(rows).strip()


def send_telegram_text(cfg: TelegramConfig, text: str, dry_run: bool = True) -> dict[str, Any]:
    payload = {
        "chat_id": cfg.chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if cfg.topic_id:
        try:
            payload["message_thread_id"] = int(cfg.topic_id)
        except Exception:
            payload["message_thread_id"] = cfg.topic_id

    if dry_run:
        return {"ok": True, "dry_run": True, "payload": payload}

    url = f"https://api.telegram.org/bot{cfg.bot_token}/sendMessage"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"Telegram API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    if not isinstance(data, dict) or not data.get("ok", False):
        raise RuntimeError(f"Telegram API response not ok: {data}")
    return {"ok": True, "dry_run": False, "response": data}
