import os
from celery import Celery
from dotenv import load_dotenv
from pathlib import Path

# Resolve folders
CURRENT = Path(__file__).resolve()
BASE_DIR = CURRENT.parent
PROJECT_ROOT = BASE_DIR.parent

# Load .env from both likely locations
try:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv((PROJECT_ROOT / ".." / ".env").resolve())
except Exception:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
