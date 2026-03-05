from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ????????? src ? path, ????? ??????? ???????? ??? ?????? ???????
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vacancy_pipeline_py.telegram_sender import (
    TelegramConfig,
    build_batch_text,
    send_telegram_text,
)

SCORED_PATH = ROOT / "data" / "scored_vacancies.json"
ENV_PATH = ROOT / ".env"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return values if 'values' in locals() else out # Small fix for robustness


def main():
    p = argparse.ArgumentParser(description="Send vacancy digest to Telegram")
    p.add_argument("--send", action="store_true", help="actually send to Telegram (default: dry-run)")
    p.add_argument("--min-score", type=float, default=60.0, help="minimum score to include in digest")
    args = p.parse_args()

    env = load_env(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    topic_id = env.get("TELEGRAM_TOPIC_ID")

    if not SCORED_PATH.exists():
        print(f"File not found: {SCORED_PATH}")
        return

    scored = json.loads(SCORED_PATH.read_text(encoding="utf-8-sig"))
    relevant = [v for v in scored if isinstance(v, dict) and isinstance(v.get("score"), (int, float)) and v["score"] >= args.min_score]

    if not relevant:
        print(f"No vacancies found with score >= {args.min_score}")
        return

    # ????? ???-25, ????? ?? ????? ?? ????? 4096 ???????? Telegram
    text = build_batch_text(relevant[:25], title=f"Relevant vacancies (score >= {args.min_score})")
    cfg = TelegramConfig(bot_token=token, chat_id=chat_id, topic_id=topic_id)

    if args.send and (not token or not chat_id):
        raise SystemExit("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")

    result = send_telegram_text(cfg, text=text, dry_run=not args.send)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
