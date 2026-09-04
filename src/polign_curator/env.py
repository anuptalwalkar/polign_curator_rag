from __future__ import annotations

import os
from pathlib import Path


def load_project_env(path: Path) -> bool:
    """Load a simple KEY=VALUE file without overriding exported variables.

    This keeps credentials in the ignored project-local `.env` file and
    avoids adding a runtime dependency solely for configuration loading.
    """

    if not path.is_file():
        return False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        if key and key.replace("_", "").isalnum():
            os.environ.setdefault(key, value)
    return True

