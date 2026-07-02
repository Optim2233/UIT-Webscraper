"""Core scrape-and-download run, shared by the CLI and the Telegram bot.

Logs into the LMS, crawls the configured courses, downloads only new or changed
lectures (deciding via the Redis hash store) and returns what was downloaded.
An optional ``on_file`` callback is invoked as each file is downloaded so a
caller (e.g. the bot) can forward it immediately.
"""

import os
from dataclasses import dataclass
from typing import Callable, Optional

from bs4 import BeautifulSoup

import config
import downloader
import lms
from state import HashStore


@dataclass
class DownloadedFile:
    """A lecture file that was newly downloaded or updated during a run."""

    course_title: str
    filename: str
    path: str
    status: str  # "new" or "updated"
    size: int


LogFn = Callable[[str], None]
FileFn = Callable[[DownloadedFile], None]


def _process_course(
    session,
    store: HashStore,
    course_url: str,
    on_file: Optional[FileFn],
    log: LogFn,
) -> list[DownloadedFile]:
    downloaded: list[DownloadedFile] = []

    resp = session.get(course_url)
    if resp.status_code != 200:
        log(f"Failed to fetch course ({resp.status_code}): {course_url}")
        return downloaded

    soup = BeautifulSoup(resp.text, "html.parser")
    title = downloader.get_course_title(soup, course_url)
    cid = downloader.course_id(course_url)
    course_dir = os.path.join(config.DOWNLOAD_DIR, downloader._sanitize(title))

    for activity in downloader.find_activities(soup):
        try:
            files = list(downloader.fetch_files(session, activity))
        except Exception as exc:
            log(f"Error fetching '{activity.name}': {exc}")
            continue

        for filename, data in files:
            identity = f"{cid}/{filename}"
            digest = downloader.content_hash(data)
            if not store.is_new_or_changed(identity, digest):
                continue

            existed = store.get(identity) is not None
            path = downloader.save_file(course_dir, filename, data)
            store.set(identity, digest)

            df = DownloadedFile(
                course_title=title,
                filename=filename,
                path=path,
                status="updated" if existed else "new",
                size=len(data),
            )
            downloaded.append(df)
            log(f"{df.status.upper()}: {title} / {filename}")
            if on_file is not None:
                try:
                    on_file(df)
                except Exception as exc:
                    log(f"on_file callback error for {filename}: {exc}")

    return downloaded


def run(
    store: HashStore,
    on_file: Optional[FileFn] = None,
    log: LogFn = print,
) -> list[DownloadedFile]:
    """Run a full scrape and return the list of new/updated files."""
    session = lms.create_session()
    if not lms.login(session):
        raise RuntimeError("LMS login failed. Check UIT_USERNAME / UIT_PASSWORD.")
    log("Logged in to LMS.")

    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

    downloaded: list[DownloadedFile] = []
    for course_url in config.COURSE_URLS:
        try:
            downloaded.extend(
                _process_course(session, store, course_url, on_file, log)
            )
        except Exception as exc:
            log(f"Error processing {course_url}: {exc}")

    return downloaded
