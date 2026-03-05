from __future__ import annotations

import hashlib
import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def build_location_signals(config: dict[str, Any]) -> list[str]:
    locs = (((config.get("filters") or {}).get("locations")) or [])
    out: list[str] = []
    seen = set()
    for x in locs:
        s = normalize(x)
        if len(s) >= 2 and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def text_has_signal(text: str, signals: list[str]) -> bool:
    n = normalize(text)
    return any(sig in n for sig in signals)


def vacancy_matches_signals(v: dict[str, Any], signals: list[str]) -> bool:
    blob = " ".join(str(v.get(k, "")) for k in ("location", "title", "description", "link"))
    return text_has_signal(blob, signals)


def filter_vacancies_by_location(vacancies: list[dict[str, Any]], signals: list[str]) -> list[dict[str, Any]]:
    return [v for v in vacancies if vacancy_matches_signals(v, signals)]


def _vacancy_id_from_link(link: str) -> str:
    parsed = urlparse(link)
    q = parse_qs(parsed.query)
    jl = (q.get("jl") or q.get("jobListingId") or [""])[0]
    if jl:
        return f"gd_{jl}"
    digest = hashlib.sha1(link.encode("utf-8")).hexdigest()[:16]
    return f"gdm_{digest}"


def _clean_html_text(value: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", value or "", flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _match_first(block: str, pattern: str) -> str:
    match = re.search(pattern, block, flags=re.I | re.S)
    return _clean_html_text(match.group(1)) if match else ""


def _extract_react_email_cards(html: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    anchor_pattern = re.compile(
        r'<a\b[^>]*href="([^"]*(?:jobListingId=|/partner/jobListing\.htm|/Job/)[^"]*)"[^>]*>(.*?)</a>',
        flags=re.I | re.S,
    )
    posted_pattern = r"^(?:today|just now|\d+\+? ?(?:m|h|d|w))$"

    for href, block in anchor_pattern.findall(html or ""):
        link = html_lib.unescape(href).strip()
        title = _match_first(block, r'<p[^>]*class="[^"]*gd-6c2846d4dc[^"]*"[^>]*>(.*?)</p>')
        if not title:
            paragraphs = [_clean_html_text(x) for x in re.findall(r"<p\b[^>]*>(.*?)</p>", block, flags=re.I | re.S)]
            title = next(
                (
                    p
                    for p in paragraphs
                    if p
                    and not re.match(posted_pattern, p, flags=re.I)
                    and "glassdoor est." not in p.lower()
                    and "employer est." not in p.lower()
                    and p.lower() != "easy apply"
                ),
                "",
            )
        company = _match_first(block, r'<span[^>]*class="[^"]*gd-628b46d9ce[^"]*"[^>]*>(.*?)</span>')
        if not company:
            spans = [_clean_html_text(x) for x in re.findall(r"<span\b[^>]*>(.*?)</span>", block, flags=re.I | re.S)]
            company = next((s for s in spans if s and not re.search(r"[0-9.]+\s*★", s)), "")
        posted = ""
        paragraphs = [_clean_html_text(x) for x in re.findall(r"<p\b[^>]*>(.*?)</p>", block, flags=re.I | re.S)]
        for paragraph in reversed(paragraphs):
            if re.match(posted_pattern, paragraph, flags=re.I):
                posted = paragraph
                break
        location = ""
        for paragraph in paragraphs:
            lower = paragraph.lower()
            if paragraph == title:
                continue
            if paragraph == posted:
                continue
            if "glassdoor est." in lower or "employer est." in lower:
                continue
            if lower == "easy apply":
                continue
            location = paragraph
            break
        if not (title and link):
            continue
        vacancy_id = _vacancy_id_from_link(link)
        if vacancy_id in seen_ids:
            continue
        seen_ids.add(vacancy_id)
        cards.append(
            {
                "id": vacancy_id,
                "title": title,
                "company": company or "Unknown Company",
                "location": location or None,
                "link": link,
                "posted": posted,
                "source": "glassdoor",
                "description": "",
            }
        )
    return cards


def parse_job_cards_from_html(html: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for block in re.findall(r'<div class="job-card"[^>]*>(.*?)</div>', html or "", flags=re.I | re.S):
        href_m = re.search(r'href="([^"]+)"', block, flags=re.I)
        title_m = re.search(r'<a[^>]*>(.*?)</a>', block, flags=re.I | re.S)
        company_m = re.search(r'<span class="company">(.*?)</span>', block, flags=re.I | re.S)
        location_m = re.search(r'<span class="location">(.*?)</span>', block, flags=re.I | re.S)
        posted_m = re.search(r'<span class="posted">(.*?)</span>', block, flags=re.I | re.S)

        link = (href_m.group(1).strip() if href_m else "")
        title = re.sub(r"<[^>]+>", " ", title_m.group(1)).strip() if title_m else ""
        company = re.sub(r"<[^>]+>", " ", company_m.group(1)).strip() if company_m else ""
        location = re.sub(r"<[^>]+>", " ", location_m.group(1)).strip() if location_m else ""
        posted = re.sub(r"<[^>]+>", " ", posted_m.group(1)).strip() if posted_m else ""

        if not (title and link):
            continue

        cards.append(
            {
                "id": _vacancy_id_from_link(link),
                "title": title,
                "company": company or "Unknown Company",
                "location": location or None,
                "link": link,
                "posted": posted,
                "source": "glassdoor",
                "description": "",
            }
        )
    legacy_ids = {card["id"] for card in cards}
    for card in _extract_react_email_cards(html):
        if card["id"] not in legacy_ids:
            cards.append(card)
    return cards


def is_message_allowed_by_time_window(internal_date_ms: int, time_window: str, now_utc: datetime | None = None) -> bool:
    tw = normalize(time_window)
    if tw == "all":
        return True
    if tw != "today" and not re.fullmatch(r"\d+d", tw):
        return False
    if not isinstance(internal_date_ms, int) or internal_date_ms <= 0:
        return False

    now = now_utc or datetime.now(timezone.utc)
    msg_dt = datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)

    if tw == "today":
        return (msg_dt.year, msg_dt.month, msg_dt.day) == (now.year, now.month, now.day)

    delta_hours = (now - msg_dt).total_seconds() / 3600.0
    day_match = re.fullmatch(r"(\d+)d", tw)
    if day_match:
        return delta_hours <= int(day_match.group(1)) * 24
    return False
