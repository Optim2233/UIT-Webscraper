"""UIT LMS lecture scraper.

Logs into the UIT Moodle LMS, crawls the configured courses, identifies file
and folder lectures, and downloads only the ones that are new or have changed
since the last run. Content hashes are stored in Redis to decide what is
"updated".
"""

import os
import sys

import redis

import config
import downloader
import lms
from state import HashStore


def process_course(session, store: HashStore, course_url: str) -> None:
    print(f"\n[*] Checking course: {course_url}")
    resp = session.get(course_url)

    if resp.status_code != 200:
        print(f"[-] Failed to fetch course. Status code: {resp.status_code}")
        return

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(resp.text, "html.parser")
    title = downloader.get_course_title(soup, course_url)
    cid = downloader.course_id(course_url)
    print(f"[*] Course title: {title}")

    course_dir = os.path.join(config.DOWNLOAD_DIR, downloader._sanitize(title))
    activities = downloader.find_activities(soup)
    print(f"[*] Found {len(activities)} lecture activities.")

    for activity in activities:
        print(f"  [*] {activity.kind}: {activity.name}")
        try:
            files = list(downloader.fetch_files(session, activity))
        except Exception as exc:
            print(f"    [-] Error fetching '{activity.name}': {exc}")
            continue

        if not files:
            print("    [-] No downloadable files found.")
            continue

        for filename, data in files:
            identity = f"{cid}/{filename}"
            digest = downloader.content_hash(data)

            if not store.is_new_or_changed(identity, digest):
                print(f"    [=] Unchanged: {filename}")
                continue

            existed = store.get(identity) is not None
            path = downloader.save_file(course_dir, filename, data)
            store.set(identity, digest)
            state = "Updated" if existed else "New"
            print(f"    [+] {state}: {filename} -> {path}")


def main() -> int:
    store = HashStore()
    try:
        store.ping()
    except redis.RedisError as exc:
        print(f"[-] Could not connect to Redis at {config.REDIS_URL}: {exc}")
        return 1

    session = lms.create_session()
    if not lms.login(session):
        return 1
    print("[*] Logged in successfully.")

    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

    for course_url in config.COURSE_URLS:
        try:
            process_course(session, store, course_url)
        except Exception as exc:
            print(f"[-] Error processing {course_url}: {exc}")

    print("\n[*] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
