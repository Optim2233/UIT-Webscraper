"""Shared helper for delivering a downloaded lecture file to Telegram.

Used by both the long-running bot (``bot.py``) and the one-shot CI entry point
(``send_once.py``) so the caption format and oversized-file handling stay in
one place.
"""

import config
from runner import DownloadedFile
from telegram_client import TelegramClient


def send_file(tg: TelegramClient, chat_id, df: DownloadedFile) -> None:
    label = "🆕 New" if df.status == "new" else "♻️ Updated"
    caption = f"{label}: {df.course_title}\n{df.filename}"
    size_mb = df.size / (1024 * 1024)

    if size_mb > config.TELEGRAM_MAX_FILE_MB:
        tg.send_message(
            chat_id,
            f"{caption}\n(⚠️ {size_mb:.1f} MB is over Telegram's "
            f"{config.TELEGRAM_MAX_FILE_MB:.0f} MB limit — not sent)",
        )
        return

    try:
        tg.send_document(chat_id, df.path, caption=caption)
    except Exception as exc:
        tg.send_message(chat_id, f"Failed to send {df.filename}: {exc}")
