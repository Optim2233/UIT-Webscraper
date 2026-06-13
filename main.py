import hashlib
import json

import requests
import urllib3
from bs4 import BeautifulSoup


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = "your uit username"
PASSWORD = "your uit password#"
LOGIN_URL = "https://lms.uit.edu.mm/login/index.php"
STATE_FILE = "course_state.json"

COURSE_URLS = [
    "https://lms.uit.edu.mm/course/view.php?id=2261",
    "https://lms.uit.edu.mm/course/view.php?id=2277",
    "https://lms.uit.edu.mm/course/view.php?id=2265",
    "https://lms.uit.edu.mm/course/view.php?id=2264",
    "https://lms.uit.edu.mm/course/view.php?id=2263",
    "https://lms.uit.edu.mm/course/view.php?id=2262",
    "https://lms.uit.edu.mm/course/view.php?id=2266",
    "https://lms.uit.edu.mm/course/view.php?id=1743",
    "https://lms.uit.edu.mm/course/view.php?id=1946",
    "https://lms.uit.edu.mm/course/view.php?id=1943",
    "https://lms.uit.edu.mm/course/view.php?id=2180",
]


session = requests.Session()
session.verify = False

resp = session.get(LOGIN_URL)
soup = BeautifulSoup(resp.text, "html.parser")
token = soup.find("input", {"name": "logintoken"})["value"]

payload = {
    "username": USERNAME,
    "password": PASSWORD,
    "logintoken": token,
    "anchor": "",
}
post_resp = session.post(LOGIN_URL, data=payload)

if "My courses" not in post_resp.text and "Dashboard" not in post_resp.text:
    print("[-] Login failed. Check credentials.")
    exit()

print("[*] Logged in successfully.\n")

try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        all_states = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    all_states = {}

for course_url in COURSE_URLS:
    print(f"\n[*] Checking course: {course_url}")
    resp = session.get(course_url)

    if resp.status_code != 200:
        print(f"[-] Failed to fetch course. Status code: {resp.status_code}")
        continue

    soup = BeautifulSoup(resp.text, "html.parser")

    activities = []
    course_title = ""
    title_tag = soup.select_one(".page-header-headings h1")

    if title_tag:
        course_title = title_tag.get_text(strip=True)
        print(f"[*] Course title: {course_title}")
    else:
        print("[-] Course title not found.")

    for link in soup.select(".activityinstance .aalink"):
        name_span = link.find("span", class_="instancename")

        if name_span:
            for hidden_text in name_span.select(".accesshide"):
                hidden_text.decompose()
            name = name_span.get_text(strip=True)
        else:
            name = link.get_text(strip=True)

        url = link.get("href", "")
        activities.append(f"{name}|{url}")

    activities.sort()
    content_str = f"{course_title}\n" + "\n".join(activities)
    current_hash = hashlib.md5(content_str.encode()).hexdigest()

    old_state = all_states.get(course_url, {})
    old_hash = old_state.get("hash")

    if old_hash is None:
        print("[*] First run for this course. Storing current activities.")
    elif old_hash != current_hash:
        print("[*] Course content changed. Current activities:")
    else:
        print("[*] No changes detected.")

    if old_hash != current_hash:
        for activity in activities:
            name, url = activity.split("|", 1)
            print(f"[*] Activity: {name}")
            print(f"[*] URL: {url}")

    all_states[course_url] = {
        "course_title": course_title,
        "hash": current_hash,
        "activities": activities,
    }

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(all_states, f, indent=2)

print("\n[*] All course states saved.")
