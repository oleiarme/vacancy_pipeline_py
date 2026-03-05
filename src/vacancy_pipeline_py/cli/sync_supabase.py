from __future__ import annotations

import argparse
import json

from vacancy_pipeline_py import paths, settings
from vacancy_pipeline_py.cli.output import emit_json
from vacancy_pipeline_py.supabase_sync import SupabaseConfig, sync_vacancies


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync scored vacancies with Supabase database")
    parser.add_argument("--send", action="store_true", help="actually send to Supabase (default: dry-run)")
    parser.add_argument("--only-relevant", action="store_true", help="sync only vacancies marked as relevant")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    env = settings.load_env()
    cfg = SupabaseConfig(
        url=env.get("SUPABASE_URL", ""),
        key=env.get("SUPABASE_KEY", ""),
        table=env.get("SUPABASE_TABLE", "vacancies"),
    )

    scored_path = paths.scored_vacancies_path()
    if not scored_path.exists():
        print(f"File not found: {scored_path}")
        return

    scored = json.loads(scored_path.read_text(encoding="utf-8-sig"))
    rows = [vacancy for vacancy in scored if isinstance(vacancy, dict)]

    if args.only_relevant:
        rows = [vacancy for vacancy in rows if bool(vacancy.get("relevant"))]

    if args.send and (not cfg.url or not cfg.key):
        raise SystemExit("Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")

    result = sync_vacancies(cfg, rows, dry_run=not args.send)
    emit_json(result)


if __name__ == "__main__":
    main()
