from __future__ import annotations

import argparse
import json

from vacancy_pipeline_py import paths, settings
from vacancy_pipeline_py.telegram_sender import TelegramConfig, build_batch_text, send_telegram_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send vacancy digest to Telegram")
    parser.add_argument("--send", action="store_true", help="actually send to Telegram (default: dry-run)")
    parser.add_argument("--min-score", type=float, default=60.0, help="minimum score to include in digest")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    env = settings.load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    topic_id = env.get("TELEGRAM_TOPIC_ID")

    scored_path = paths.scored_vacancies_path()
    if not scored_path.exists():
        print(f"File not found: {scored_path}")
        return

    scored = json.loads(scored_path.read_text(encoding="utf-8-sig"))
    relevant = [
        vacancy
        for vacancy in scored
        if isinstance(vacancy, dict)
        and isinstance(vacancy.get("score"), (int, float))
        and vacancy["score"] >= args.min_score
    ]

    if not relevant:
        print(f"No vacancies found with score >= {args.min_score}")
        return

    text = build_batch_text(relevant[:25], title=f"Relevant vacancies (score >= {args.min_score})")
    cfg = TelegramConfig(bot_token=token, chat_id=chat_id, topic_id=topic_id)

    if args.send and (not token or not chat_id):
        raise SystemExit("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")

    result = send_telegram_text(cfg, text=text, dry_run=not args.send)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
