# UIT Webscraper

A scraper for the UIT Moodle LMS (<https://lms.uit.edu.mm>). It logs in, crawls
the configured courses, identifies lecture **files** and **folders**, and
downloads only the ones that are **new or updated** since the last run.

Update detection uses a content hash (SHA-256) stored in **Redis**, so
unchanged lectures are skipped and never re-downloaded.

## How it works

```
login -> crawl each course -> find resource/folder activities
      -> download each file -> hash it -> compare with Redis
      -> save + remember the hash only if new or changed
```

## Setup

Install dependencies (with [uv](https://docs.astral.sh/uv/)):

```bash
uv sync
```

You also need a running Redis instance to store hashes.

## Configuration

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

| Variable              | Required | Purpose                                       |
| --------------------- | -------- | --------------------------------------------- |
| `UIT_USERNAME`        | yes      | Your LMS username                             |
| `UIT_PASSWORD`        | yes      | Your LMS password                             |
| `REDIS_URL`           | yes      | Redis connection (e.g. `redis://host:6379/0`) |
| `UIT_DOWNLOAD_DIR`    | no       | Where lectures are saved (default `downloads`)|
| `UIT_REQUEST_DELAY`   | no       | Seconds between requests (default `1.0`)      |
| `UIT_VERIFY_SSL`      | no       | Verify the LMS certificate (default `false`)  |

The list of courses to crawl lives in `COURSE_URLS` in `config.py`.

## Run

```bash
uv run python main.py
```

Downloaded files are organised as `downloads/<course title>/<filename>`.

## Project layout

| File            | Responsibility                                    |
| --------------- | ------------------------------------------------- |
| `main.py`       | Orchestrates the run                              |
| `config.py`     | Environment-driven configuration                  |
| `lms.py`        | Session creation and login                        |
| `downloader.py` | Finding activities and downloading their files    |
| `state.py`      | Redis-backed content-hash store                   |

## ⚠️ Note

BE GENTLE WITH THE SCRAPING. You are solely responsible if you get banned.
Keep `UIT_REQUEST_DELAY` reasonable and don't run it in a tight loop.
