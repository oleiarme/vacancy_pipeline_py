# Python Runbook

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
git config core.hooksPath .githooks
```

## Daily Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\vacancy-verify.exe
```

## Main Commands

Fixture mode:

```powershell
.\.venv\Scripts\vacancy-orchestrate.exe --source fixture
```

Gmail mode with fixture fallback:

```powershell
.\.venv\Scripts\vacancy-orchestrate.exe --source gmail
```

Telegram dry-run:

```powershell
.\.venv\Scripts\vacancy-send-telegram.exe
```

Telegram send:

```powershell
.\.venv\Scripts\vacancy-send-telegram.exe --send
```

Supabase dry-run:

```powershell
.\.venv\Scripts\vacancy-sync-supabase.exe
```

Supabase send:

```powershell
.\.venv\Scripts\vacancy-sync-supabase.exe --send
```

Gmail OAuth bootstrap:

```powershell
pip install -e .[gmail]
.\.venv\Scripts\vacancy-gmail-auth.exe
```

## Runtime Files

Generated runtime state lives under `var/`:
- `var/data/last_run.json`
- `var/data/vacancies_mail_glassdoor.json`
- `var/data/vacancies.json`
- `var/data/scored_vacancies.json`
- `var/runs/run_<timestamp>.json`
- `var/auth/gmail_token.json`

## Required Environment

Minimum for verification:

```env
GMAIL_GLASSDOOR_TIME_WINDOW=today
```

Optional Telegram variables:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_TOPIC_ID`

Optional Supabase variables:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_TABLE`
