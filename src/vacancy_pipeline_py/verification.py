from __future__ import annotations

import json
import re
from typing import Callable
from urllib.parse import unquote

from vacancy_pipeline_py import paths, settings


def _normalize(value: str) -> str:
    normalized = str(value or "").lower()
    normalized = unquote(normalized)
    normalized = normalized.replace("+", " ").replace("%20", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _read_json(path, label: str):
    if not path.exists():
        raise RuntimeError(f"{label} missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"{label} invalid JSON: {exc}") from exc


def _build_location_signals(config: dict) -> list[str]:
    locations = (((config.get("filters") or {}).get("locations")) or [])
    if not isinstance(locations, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in locations:
        normalized = _normalize(str(item))
        if len(normalized) >= 2 and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out


def _text_has_signal(text: str, signals: list[str]) -> bool:
    normalized = _normalize(text)
    return any(signal in normalized for signal in signals)


def _vacancy_matches_signals(vacancy: dict, signals: list[str]) -> bool:
    blob = " ".join(str(vacancy.get(key, "")) for key in ("location", "title", "description", "link"))
    return _text_has_signal(blob, signals)


def run_verification(*, emit_output: bool = True) -> bool:
    results = []
    time_window = settings.get_env("GMAIL_GLASSDOOR_TIME_WINDOW", "").strip().lower()
    allowed_time_windows = {"today", "1d", "3d", "all"}

    config = {}
    signals: list[str] = []
    vacancies = []
    mail = []
    scored = []

    def emit(line: str) -> None:
        if emit_output:
            print(line)

    def run_check(name: str, fn: Callable[[], None]) -> None:
        try:
            fn()
            emit(f"PASS: {name}")
            results.append((name, True, ""))
        except Exception as exc:
            emit(f"FAIL: {name}")
            emit(f"  {exc}")
            results.append((name, False, str(exc)))

    def check_time_window() -> None:
        if not time_window:
            raise RuntimeError("GMAIL_GLASSDOOR_TIME_WINDOW is empty")
        if time_window not in allowed_time_windows:
            raise RuntimeError(f"Unsupported GMAIL_GLASSDOOR_TIME_WINDOW={time_window}")

    def check_config_and_signals() -> None:
        nonlocal config, signals
        config = _read_json(paths.search_config_path(), "search_config.json")
        if not isinstance(config, dict):
            raise RuntimeError("search_config.json must be object")
        signals = _build_location_signals(config)
        if not signals:
            raise RuntimeError("config.filters.locations must be non-empty list")

    def check_urls_match_profile() -> None:
        portals = config.get("portals") or []
        if not isinstance(portals, list):
            raise RuntimeError("config.portals must be list")
        for portal in portals:
            if not isinstance(portal, dict):
                continue
            name = portal.get("name", "unknown")
            urls = portal.get("searchUrls") or []
            if not isinstance(urls, list):
                raise RuntimeError(f"{name}.searchUrls must be list")
            bad = [url for url in urls if not _text_has_signal(str(url), signals)]
            if bad:
                raise RuntimeError(f"{name} has URLs outside location profile: {bad}")

    def check_data_arrays() -> None:
        nonlocal vacancies, mail, scored
        paths.ensure_dir(paths.data_dir())

        for target in (paths.merged_vacancies_path(), paths.vacancies_mail_path(), paths.scored_vacancies_path()):
            if not target.exists():
                paths.ensure_parent(target)
                target.write_text("[]", encoding="utf-8")

        vacancies = _read_json(paths.merged_vacancies_path(), "vacancies.json")
        mail = _read_json(paths.vacancies_mail_path(), "vacancies_mail_glassdoor.json")
        scored = _read_json(paths.scored_vacancies_path(), "scored_vacancies.json")

        for name, payload in (("vacancies", vacancies), ("mail", mail), ("scored", scored)):
            if not isinstance(payload, list):
                raise RuntimeError(f"{name} must be array")

    def check_location_profile_data() -> None:
        for name, payload in (("vacancies", vacancies), ("mail", mail), ("scored", scored)):
            bad = [vacancy for vacancy in payload if isinstance(vacancy, dict) and not _vacancy_matches_signals(vacancy, signals)]
            if bad:
                raise RuntimeError(f"{name} has {len(bad)} records outside location profile")

    def check_links_and_scores() -> None:
        bad_links = [
            vacancy
            for vacancy in vacancies
            if isinstance(vacancy, dict) and not re.match(r"^https?://\S+$", str(vacancy.get("link", "")).strip())
        ]
        if bad_links:
            raise RuntimeError(f"vacancies has {len(bad_links)} invalid links")
        bad_scores = [
            vacancy
            for vacancy in scored
            if isinstance(vacancy, dict)
            and ("score" in vacancy)
            and (not isinstance(vacancy["score"], (int, float)) or vacancy["score"] < 0 or vacancy["score"] > 100)
        ]
        if bad_scores:
            raise RuntimeError(f"scored has {len(bad_scores)} invalid score values")

    def check_dedup_ids() -> None:
        seen = set()
        duplicates = 0
        for vacancy in vacancies:
            if not isinstance(vacancy, dict):
                continue
            vacancy_id = str(vacancy.get("id", "")).strip()
            if not vacancy_id:
                continue
            if vacancy_id in seen:
                duplicates += 1
            seen.add(vacancy_id)
        if duplicates:
            raise RuntimeError(f"vacancies has duplicate ids: {duplicates}")

    run_check("Gmail time window is configured", check_time_window)
    run_check("search_config has active location profile", check_config_and_signals)
    run_check("search_config URLs match active location profile", check_urls_match_profile)
    run_check("data files exist and are arrays", check_data_arrays)
    run_check("data matches active location profile", check_location_profile_data)
    run_check("merged links and scored values are valid", check_links_and_scores)
    run_check("merged vacancies are deduplicated by id", check_dedup_ids)

    failed = [item for item in results if not item[1]]
    if failed:
        emit(f"\nVerification failed: {len(failed)} check(s).")
        return False

    emit("\nVerification passed: all checks are green.")
    return True
