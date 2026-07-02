"""Minimal Telegram Bot API client (send messages/documents, long-poll)."""

import os

import requests

import config


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, token: str = config.TELEGRAM_BOT_TOKEN):
        if not token:
            raise TelegramError("TELEGRAM_BOT_TOKEN is not set.")
        self.base = f"https://api.telegram.org/bot{token}"
        self.session = requests.Session()

    def _call(self, method: str, *, timeout: int = 30, **kwargs):
        resp = self.session.post(f"{self.base}/{method}", timeout=timeout, **kwargs)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("ok"):
            raise TelegramError(f"{method} failed: {payload.get('description')}")
        return payload.get("result")

    def send_message(self, chat_id, text: str):
        return self._call(
            "sendMessage",
            data={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )

    def send_document(self, chat_id, path: str, caption: str | None = None):
        with open(path, "rb") as fh:
            files = {"document": (os.path.basename(path), fh)}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            return self._call("sendDocument", data=data, files=files, timeout=180)

    def get_updates(self, offset: int | None = None, timeout: int = 10):
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        resp = self.session.get(
            f"{self.base}/getUpdates", params=params, timeout=timeout + 15
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("ok"):
            raise TelegramError(f"getUpdates failed: {payload.get('description')}")
        return payload.get("result", [])
