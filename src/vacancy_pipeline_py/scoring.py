from __future__ import annotations

import re
from typing import Any


ROLE_PATTERNS = re.compile(r"(sre|devops|platform|site reliability|infrastructure)", re.I)
LOCATION_PATTERNS = re.compile(r"(remote|lisbon|lisboa|porto|portugal)", re.I)


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def score_vacancy(vacancy: dict[str, Any]) -> dict[str, Any]:
    title = normalize(vacancy.get("title")).lower()
    description = normalize(vacancy.get("description"))
    desc_lower = description.lower()
    location = normalize(vacancy.get("location")).lower()
    rating_raw = vacancy.get("rating")
    try:
        rating = float(rating_raw)
    except Exception:
        rating = 0.0

    reasons: list[str] = []
    tags: list[str] = []
    score = 0

    if not description:
        score += 10
        reasons.append("+10 No description available (manual review required)")
        tags.append("missing-description")
    else:
        # simple keyword richness baseline
        skill_hits = 0
        for kw in ("kubernetes", "terraform", "aws", "gcp", "linux", "python", "ci/cd", "observability"):
            if kw in desc_lower:
                skill_hits += 1
        skill_score = min(50, skill_hits * 8)
        score += skill_score
        reasons.append(f"+{skill_score} Description skill signals ({skill_hits})")

    if ROLE_PATTERNS.search(title):
        score += 15
        reasons.append("+15 Role title match")
    else:
        reasons.append("+0 Role title mismatch")

    if LOCATION_PATTERNS.search(location) or LOCATION_PATTERNS.search(desc_lower):
        score += 5
        reasons.append("+5 Location match")
    else:
        reasons.append("+0 Location mismatch")

    if rating >= 4.0:
        score += 5
        reasons.append(f"+5 Company rating ({rating})")
    elif rating >= 3.0:
        score += 3
        reasons.append(f"+3 Company rating ({rating})")
    else:
        reasons.append("+0 Company rating bonus")

    score = max(0, min(100, score))
    relevant = score >= 60

    out = dict(vacancy)
    out["score"] = score
    out["relevant"] = relevant
    out["tags"] = tags
    out["reasons"] = reasons
    out["reasoning"] = ", ".join(reasons)
    return out


def score_vacancies(vacancies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [score_vacancy(v) for v in vacancies]
