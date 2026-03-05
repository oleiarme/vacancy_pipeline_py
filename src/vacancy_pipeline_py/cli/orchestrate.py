from __future__ import annotations

import argparse
import dataclasses

from vacancy_pipeline_py.cli.output import emit_json
from vacancy_pipeline_py.orchestrate import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vacancy Pipeline Orchestrator CLI")
    parser.add_argument(
        "--source",
        choices=["fixture", "gmail"],
        default="fixture",
        help="Data source: local fixture or live Gmail API",
    )
    parser.add_argument(
        "--gmail-label",
        default="glassdoor",
        help="Gmail label to search for (default: glassdoor)",
    )
    parser.add_argument(
        "--gmail-query",
        default="",
        help="Additional Gmail search query (e.g. 'after:2026/03/01')",
    )
    parser.add_argument(
        "--gmail-max-emails",
        type=int,
        default=20,
        help="Max number of emails to process",
    )
    parser.add_argument(
        "--no-fallback-fixture",
        action="store_true",
        help="Disable automatic fallback to fixtures if Gmail fails",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run(
        source=args.source,
        gmail_label=args.gmail_label,
        gmail_query=args.gmail_query,
        gmail_max_emails=args.gmail_max_emails,
        fallback_fixture=not args.no_fallback_fixture,
    )
    emit_json(dataclasses.asdict(summary))


if __name__ == "__main__":
    main()
