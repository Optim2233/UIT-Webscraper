"""Telegram bot for the UIT lecture scraper.

Runs a scrape on a daily schedule or on demand (via the ``/update`` command)
and sends every new or updated lecture file into the configured Telegram chat.

Usage:
    uv run python bot.py
"""

import sys
import time
from datetime import datetime

import redis
import schedule

import config
import notify
from runner import run
from state import HashStore
from telegram_client import TelegramClient, TelegramError

HELP_TEXT = (
    "📚 UIT Lecture Bot\n\n"
    "/update  – check for new/updated lectures now and send them here\n"
    "/status  – show the last run's result\n"
    "/help    – show this message"
)


class Bot:
    def __init__(self, store: HashStore):
        self.tg = TelegramClient()
        self.store = store
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.offset: int | None = None
        self.running = False
        self.last_run: datetime | None = None
        self.last_count = 0

    # --- authorization -----------------------------------------------------
    def _authorized(self, chat_id) -> bool:
        return not self.chat_id or str(chat_id) == str(self.chat_id)

    # --- sending -----------------------------------------------------------
    def _send_file(self, chat_id, df) -> None:
        notify.send_file(self.tg, chat_id, df)

    # --- running -----------------------------------------------------------
    def _do_run(self, chat_id) -> None:
        if self.running:
            self.tg.send_message(chat_id, "⏳ A run is already in progress…")
            return

        self.running = True
        try:
            self.tg.send_message(chat_id, "🔎 Checking for new/updated lectures…")
            results = run(
                self.store,
                on_file=lambda df: self._send_file(chat_id, df),
                log=lambda m: print(f"[run] {m}"),
            )
            self.last_run = datetime.now()
            self.last_count = len(results)
            if results:
                self.tg.send_message(
                    chat_id, f"✅ Done. Sent {len(results)} new/updated file(s)."
                )
            else:
                self.tg.send_message(chat_id, "✅ Done. No new or updated lectures.")
        except Exception as exc:
            self.tg.send_message(chat_id, f"❌ Run failed: {exc}")
        finally:
            self.running = False

    def _scheduled_run(self) -> None:
        if not self.chat_id:
            print("[-] Skipping scheduled run: TELEGRAM_CHAT_ID not set.")
            return
        self._do_run(self.chat_id)

    # --- command handling --------------------------------------------------
    def _handle_command(self, text: str, chat_id) -> None:
        cmd = text.strip().split()[0].lstrip("/").split("@")[0].lower()
        if cmd in ("start", "help"):
            self.tg.send_message(chat_id, HELP_TEXT)
        elif cmd in ("update", "scrape", "check"):
            self._do_run(chat_id)
        elif cmd == "status":
            if self.last_run:
                self.tg.send_message(
                    chat_id,
                    f"Last run: {self.last_run:%Y-%m-%d %H:%M:%S}\n"
                    f"Files sent: {self.last_count}",
                )
            else:
                self.tg.send_message(chat_id, "No runs yet this session.")
        else:
            self.tg.send_message(chat_id, "Unknown command.\n\n" + HELP_TEXT)

    def _poll_once(self) -> None:
        for update in self.tg.get_updates(offset=self.offset, timeout=10):
            self.offset = update["update_id"] + 1
            msg = update.get("message") or update.get("edited_message")
            if not msg:
                continue
            text = msg.get("text", "")
            if not text.startswith("/"):
                continue
            chat_id = msg["chat"]["id"]
            if not self._authorized(chat_id):
                self.tg.send_message(chat_id, "🚫 Unauthorized.")
                continue
            self._handle_command(text, chat_id)

    # --- main loop ---------------------------------------------------------
    def run_forever(self) -> None:
        for run_time in config.SCHEDULE_TIMES:
            schedule.every().day.at(run_time).do(self._scheduled_run)

        print(
            f"[*] Bot started. Scheduled times: "
            f"{', '.join(config.SCHEDULE_TIMES) or 'none (command-only)'}"
        )
        if self.chat_id:
            try:
                self.tg.send_message(self.chat_id, "🤖 Bot online. " + HELP_TEXT)
            except Exception as exc:
                print(f"[-] Could not send startup message: {exc}")

        while True:
            try:
                self._poll_once()
            except Exception as exc:
                print(f"[-] Poll error: {exc}")
                time.sleep(5)
            schedule.run_pending()


def main() -> int:
    if not config.TELEGRAM_BOT_TOKEN:
        print("[-] TELEGRAM_BOT_TOKEN is not set.")
        return 1

    store = HashStore()
    try:
        store.ping()
    except redis.RedisError as exc:
        print(f"[-] Could not connect to Redis at {config.REDIS_URL}: {exc}")
        return 1

    try:
        Bot(store).run_forever()
    except TelegramError as exc:
        print(f"[-] {exc}")
        return 1
    except KeyboardInterrupt:
        print("\n[*] Bot stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
