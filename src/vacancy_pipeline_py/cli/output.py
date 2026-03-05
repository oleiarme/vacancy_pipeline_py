from __future__ import annotations

import json
import sys
from typing import Any, TextIO


def emit_json(payload: Any, *, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    target.write(json.dumps(payload, ensure_ascii=True, indent=2))
    target.write("\n")
