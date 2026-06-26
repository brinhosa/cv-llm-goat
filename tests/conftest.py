"""Make the webapp package importable and provide shared fixtures."""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# webapp modules (app, grader, defenses, extract) + payloads.py at repo root.
sys.path.insert(0, str(ROOT / "webapp"))
sys.path.insert(0, str(ROOT))

# Force the offline mock path: never hit a real LLM during tests.
os.environ.pop("DEEPSEEK_API_KEY", None)
os.environ["BASE_PATH"] = ""
