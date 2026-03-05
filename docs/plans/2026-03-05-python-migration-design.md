# Python Migration Design

**Date:** 2026-03-05

## Goal

Turn the repository into a clean Python-first project after the Node.js migration:
- installable package via `pyproject.toml`
- stable CLI entry points
- centralized settings and paths
- runtime artifacts removed from tracked source tree
- CI and local verification aligned with the package interface

## Current Problems

- The project uses `src/` layout but is not packaged.
- CLI scripts in `scripts/` mutate `sys.path` and act as the real entry points.
- Production code depends directly on repository-relative paths spread across modules.
- Generated files in `data/` are tracked by git, producing noisy diffs.
- Secrets and OAuth tokens live in top-level directories instead of a local runtime area.
- CI verifies by running a script file directly instead of installing and testing the package.

## Design Summary

The repository will remain a single Python package under `src/vacancy_pipeline_py`, with a small internal CLI layer and a dedicated runtime area under `var/`.

### Directory Layout

```text
src/vacancy_pipeline_py/
  cli/
  paths.py
  settings.py
  gmail_client.py
  gmail_parser.py
  merge.py
  orchestrate.py
  scoring.py
  supabase_sync.py
  telegram_sender.py
  vacancy_utils.py

config/
  search_config.json

tests/
  fixtures/

docs/
  ops/
  plans/

var/
  auth/
  data/
  runs/
```

## Architecture

### Packaging

- Add `pyproject.toml` using setuptools.
- Define console scripts instead of `scripts/*.py`.
- Install locally with `pip install -e .[dev]`.

### CLI

Create `src/vacancy_pipeline_py/cli/` modules for:
- `vacancy-orchestrate`
- `vacancy-verify`
- `vacancy-send-telegram`
- `vacancy-sync-supabase`

The CLI layer will parse arguments and call package functions. No runtime behavior should depend on `sys.path` hacks or execution from the repo root.

### Paths and Settings

- Add `paths.py` as the single source of truth for repo-level paths.
- Add `settings.py` for `.env` loading and environment access.
- Runtime files move to `var/`:
  - `var/data/last_run.json`
  - `var/data/vacancies*.json`
  - `var/runs/run_<timestamp>.json`
  - `var/auth/gmail_token.json`

### Data Policy

- Keep only deterministic fixtures in git.
- Ignore runtime artifacts and local auth state.
- Add `.env.example` for required settings.

### CI and Local Verification

- GitHub Actions installs the package and runs:
  - `pytest -q`
  - `vacancy-verify`
- Pre-commit hook uses the CLI command, not a script path.

## Migration Approach

Recommended approach: package-first migration without preserving legacy commands.

Rationale:
- avoids maintaining two entry-point systems
- reduces future cleanup work
- matches the user's request to move fully to the new structure

## Testing Strategy

- Preserve and update existing tests to reflect new runtime paths.
- Add focused tests for new path helpers and CLI wiring where necessary.
- Use TDD for behavioral changes, especially path resolution and verification.

## Risks and Controls

- Risk: path regressions when moving runtime files.
  - Control: add path-focused tests before refactor.
- Risk: CI drift after packaging changes.
  - Control: update workflow in the same migration and verify locally.
- Risk: hidden dependencies on tracked `data/` files.
  - Control: move runtime file creation behind centralized path helpers and verification checks.
