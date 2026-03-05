# Location And Date Policy

## Purpose
Filters are configurable, but must remain consistent across parser, merge and scoring outputs.

## Rules
1. Any filter change requires re-check:
   - `python scripts/verify_pipeline.py`
2. Task is not complete until verification is green.
3. Filter semantics must be reflected in docs and tests.

## Active Sources Of Truth
1. Location profile: `config/search_config.json -> filters.locations`
2. Date profile: environment/config (to be finalized in parser module)

## Verification Gate
Run:
```bash
python scripts/verify_pipeline.py
```

Expected: all checks PASS.
