"""One-shot run for cron / CI: scrape once and send new/updated lectures.

Unlike ``bot.py`` there is no long-polling or in-process scheduler — run this
on an external schedule (e.g. a GitHub Actions cron) or with the "Run workflow"
button. All configuration comes from environment variables / secrets.

It stays quiet when there is nothing new, so scheduled runs don't spam the chat.
"""

import sys

import redis

import config
import notify
from runner import run
from state import HashStore
from telegram_client import TelegramClient, TelegramError


def main() -> int:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[-] TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        return 1

    store = HashStore()
    try:
        store.ping()
    except redis.RedisError as exc:
        print(f"[-] Could not connect to Redis at {config.REDIS_URL}: {exc}")
        return 1

    try:
        tg = TelegramClient()
    except TelegramError as exc:
        print(f"[-] {exc}")
        return 1

    chat_id = config.TELEGRAM_CHAT_ID
    try:
        results = run(
            store,
            on_file=lambda df: notify.send_file(tg, chat_id, df),
            log=lambda m: print(f"[*] {m}"),
        )
    except RuntimeError as exc:
        print(f"[-] {exc}")
        try:
            tg.send_message(chat_id, f"❌ Scheduled run failed: {exc}")
        except Exception:
            pass
        return 1

    print(f"[*] Done. {len(results)} new/updated file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
