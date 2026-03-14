from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

existing_pythonpath = os.environ.get("PYTHONPATH", "")
pythonpath_parts = [str(REPO_ROOT)]
if existing_pythonpath:
    pythonpath_parts.append(existing_pythonpath)
os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)


if __name__ == "__main__":
    uvicorn.run(
        "demo.backend.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
