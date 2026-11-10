"""conftest.py for tests/ — adds app/ to sys.path at collection time so that
module-level imports like `from agent import ...` resolve correctly."""
import sys
from pathlib import Path

_app_path = str(Path(__file__).parent.parent / "app")
if _app_path not in sys.path:
    sys.path.insert(0, _app_path)
