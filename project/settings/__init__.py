"""
Settings config
"""

from os import environ as env

from dotenv import load_dotenv

load_dotenv()

env_state = env.get("ENV", "local").strip().lower()

if env_state in {"prod", "production"}:
    from project.settings.production import *
elif env_state in {"stage", "staging"}:
    from project.settings.staging import *
elif env_state in {"dev", "development"}:
    from project.settings.development import *
else:
    from project.settings.local import *
