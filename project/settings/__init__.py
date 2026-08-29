"""
Settings config
"""

from os import R_OK, access, environ as env
from pathlib import Path

from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parents[2] / ".env"
if dotenv_path.is_file() and access(dotenv_path, R_OK):
    load_dotenv(dotenv_path)

env_state = env.get("ENV", "local").strip().lower()

if env_state in {"prod", "production"}:
    from project.settings.production import *
elif env_state in {"stage", "staging"}:
    from project.settings.staging import *
elif env_state in {"dev", "development"}:
    from project.settings.development import *
else:
    from project.settings.local import *
