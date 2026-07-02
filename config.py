"""Configuration for the UIT LMS scraper.

All secrets and environment-specific values are read from environment
variables (optionally loaded from a local, git-ignored ``.env`` file).
See ``.env.example`` for the full list of supported settings.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional; env vars still work without it.
    pass


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# --- Credentials -----------------------------------------------------------
USERNAME = os.environ.get("UIT_USERNAME", "")
PASSWORD = os.environ.get("UIT_PASSWORD", "")

# --- LMS endpoints ---------------------------------------------------------
BASE_URL = os.environ.get("UIT_BASE_URL", "https://lms.uit.edu.mm").rstrip("/")
LOGIN_URL = os.environ.get("UIT_LOGIN_URL", f"{BASE_URL}/login/index.php")

# --- Storage ---------------------------------------------------------------
# Redis is used to remember the content hash of every downloaded file so that
# only new or changed lectures are downloaded on subsequent runs.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_NAMESPACE = os.environ.get("UIT_REDIS_NAMESPACE", "uit:lecture")

# Local directory where downloaded lectures are stored.
DOWNLOAD_DIR = os.environ.get("UIT_DOWNLOAD_DIR", "downloads")

# --- Behaviour -------------------------------------------------------------
# The LMS uses a self-signed / mis-configured certificate, so verification is
# disabled by default. Set UIT_VERIFY_SSL=true if the certificate is valid.
VERIFY_SSL = _env_bool("UIT_VERIFY_SSL", False)

# Be gentle: pause (seconds) between HTTP requests to avoid hammering the LMS.
REQUEST_DELAY = float(os.environ.get("UIT_REQUEST_DELAY", "1.0"))

# --- Telegram bot ----------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_MAX_FILE_MB = float(os.environ.get("TELEGRAM_MAX_FILE_MB", "50"))

SCHEDULE_TIMES = [
    t.strip()
    for t in os.environ.get("UIT_SCHEDULE_TIMES", "").split(",")
    if t.strip()
]

# --- Courses to crawl ------------------------------------------------------
# These are currently produced by a separate scraper and pasted here. A future
# improvement is to discover them automatically from the dashboard.
COURSE_URLS = [
    f"{BASE_URL}/course/view.php?id=2261",
    f"{BASE_URL}/course/view.php?id=2277",
    f"{BASE_URL}/course/view.php?id=2265",
    f"{BASE_URL}/course/view.php?id=2264",
    f"{BASE_URL}/course/view.php?id=2263",
    f"{BASE_URL}/course/view.php?id=2262",
    f"{BASE_URL}/course/view.php?id=2266",
    f"{BASE_URL}/course/view.php?id=1743",
    f"{BASE_URL}/course/view.php?id=1946",
    f"{BASE_URL}/course/view.php?id=1943",
    f"{BASE_URL}/course/view.php?id=2180",
]
