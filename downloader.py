"""Lecture discovery and download helpers for Moodle course pages."""

from __future__ import annotations

import hashlib
import os
import re
import time
from email.message import Message
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import config


def _sanitize(name: str) -> str:
    safe = re.sub(r"[^\w\s\-.()]+", "_", name, flags=re.UNICODE).strip()
    safe = re.sub(r"\s+", " ", safe)
    return safe or "course"


def course_id(course_url: str) -> str:
    parsed = urlparse(course_url)
    cid = parse_qs(parsed.query).get("id", ["unknown"])[0]
    return cid


def get_course_title(soup: BeautifulSoup, course_url: str) -> str:
    title = soup.select_one("h1, h2.page-header-headings, title")
    if title and title.get_text(strip=True):
        return _sanitize(title.get_text(strip=True))
    return f"course-{course_id(course_url)}"


def find_activities(soup: BeautifulSoup):
    return soup.select("li.activity.resource, li.activity.folder")


def _resp_filename(resp: requests.Response, fallback_url: str) -> str:
    header = resp.headers.get("content-disposition", "")
    if header:
        msg = Message()
        msg["content-disposition"] = header
        filename = msg.get_param("filename", header="content-disposition")
        if filename:
            return filename

    path_name = os.path.basename(urlparse(resp.url or fallback_url).path)
    if path_name:
        return path_name
    return "download.bin"


def _request(session: requests.Session, url: str) -> requests.Response:
    resp = session.get(url, timeout=60)
    time.sleep(config.REQUEST_DELAY)
    resp.raise_for_status()
    return resp


def _download_binary(resp: requests.Response):
    ctype = (resp.headers.get("content-type") or "").lower()
    if "text/html" in ctype:
        return None
    filename = _sanitize(_resp_filename(resp, resp.url))
    return filename, resp.content


def fetch_files(session: requests.Session, activity):
    seen: set[str] = set()

    for a in activity.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        url = urljoin(config.BASE_URL + "/", href)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = _request(session, url)
        except requests.RequestException:
            continue

        binary = _download_binary(resp)
        if binary is not None:
            yield binary
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for file_link in soup.select("a[href*='/pluginfile.php/']"):
            f_url = urljoin(config.BASE_URL + "/", file_link.get("href", ""))
            if not f_url or f_url in seen:
                continue
            seen.add(f_url)
            try:
                f_resp = _request(session, f_url)
            except requests.RequestException:
                continue
            binary = _download_binary(f_resp)
            if binary is not None:
                yield binary


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_file(course_dir: str, filename: str, data: bytes) -> str:
    os.makedirs(course_dir, exist_ok=True)
    safe_name = _sanitize(filename)
    path = os.path.join(course_dir, safe_name)
    with open(path, "wb") as fh:
        fh.write(data)
    return path
