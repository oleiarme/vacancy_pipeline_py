from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def normalize_text(value: Any) -> str:
    # [UPDATED] ????????? ????????? ? Unicode ????/????
    if not value:
        return ""
    return re.sub(r"[^\w\d]", "", str(value).lower(), flags=re.UNICODE)


def stable_stringify(value: Any) -> str:
    if value is None or isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return "[" + ",".join(stable_stringify(v) for v in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: str(kv[0]))
        return "{" + ",".join(f"{json.dumps(k, ensure_ascii=False)}:{stable_stringify(v)}" for k, v in items) + "}"
    return json.dumps(str(value), ensure_ascii=False)


def get_vacancy_dedup_key(vacancy: dict[str, Any] | None) -> str:
    vacancy = vacancy or {}
    title_key = normalize_text(vacancy.get("title"))
    company_key = normalize_text(vacancy.get("company"))

    if title_key and company_key:
        return f"tc_{title_key}_{company_key}"

    vacancy_id = vacancy.get("id")
    if vacancy_id:
        return f"id_{vacancy_id}"

    link = vacancy.get("link")
    if link:
        return f"link_{str(link).lower()}"

    serialized = stable_stringify(vacancy)
    digest = hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:16]
    return f"fallback_{digest}"


def normalize_posted(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_posted_age(posted_value: Any) -> dict[str, Any]:
    posted = normalize_posted(posted_value).lower()
    if not posted:
        return {"is_urgent": False, "unit": None, "value": None, "raw": ""}

    h_match = re.search(r"(\d+)\s*h", posted)
    if h_match:
        hours = int(h_match.group(1))
        return {"is_urgent": True, "unit": "h", "value": hours, "raw": posted}

    d_match = re.search(r"(\d+)\s*d", posted)
    if d_match:
        days = int(d_match.group(1))
        return {"is_urgent": days <= 5, "unit": "d", "value": days, "raw": posted}

    return {"is_urgent": False, "unit": None, "value": None, "raw": posted}


def get_posted_days(posted_value: Any) -> int | None:
    parsed = parse_posted_age(posted_value)
    value = parsed.get("value")
    unit = parsed.get("unit")
    if not isinstance(value, int):
        return None
    if unit == "d":
        return value
    if unit == "h":
        return (value + 23) // 24
    return None
