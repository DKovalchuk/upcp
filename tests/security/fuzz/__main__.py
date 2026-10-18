"""Module entry point — enables both invocation styles:

python -m tests.security.fuzz --out <path.json>
python tests/security/fuzz/__main__.py --out <path.json>
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Direct script execution: put the repo root on sys.path first.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.security.fuzz.runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
