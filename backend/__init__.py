import sys
from pathlib import Path

# Absolute path to the repository root (directory that contains `backend/`).
ROOT_DIR: Path = Path(__file__).resolve().parent.parent

# Ensure the root directory is on `sys.path` so that standalone scripts
# executed from sub-folders can still import the project as a package.
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

__all__ = ["ROOT_DIR"]