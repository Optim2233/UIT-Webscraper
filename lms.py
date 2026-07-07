"""Session creation and login helpers for the UIT LMS."""

from __future__ import annotations

import requests
import urllib3
from bs4 import BeautifulSoup

import config


def create_session() -> requests.Session:
    session = requests.Session()
    session.verify = config.VERIFY_SSL
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        }
    )
    if not config.VERIFY_SSL:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session


def login(session: requests.Session) -> bool:
    if not config.USERNAME or not config.PASSWORD:
        return False

    try:
        page = session.get(config.LOGIN_URL, timeout=30)
        page.raise_for_status()
    except requests.RequestException:
        return False

    soup = BeautifulSoup(page.text, "html.parser")
    payload = {"username": config.USERNAME, "password": config.PASSWORD}
    token = soup.select_one("input[name='logintoken']")
    if token and token.get("value"):
        payload["logintoken"] = token["value"]

    try:
        resp = session.post(config.LOGIN_URL, data=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return False

    lower = resp.text.lower()
    if "login/index.php" in resp.url and "name=\"username\"" in lower:
        return False
    return True
