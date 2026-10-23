from project.settings.deployed import *

SECURE_HSTS_SECONDS = int(env.get("SECURE_HSTS_SECONDS", "86400"))
