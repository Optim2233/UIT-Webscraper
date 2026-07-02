# UIT Webscraper

A scraper + Telegram bot for the UIT Moodle LMS (<https://lms.uit.edu.mm>). It
logs in, crawls the configured courses, identifies lecture **files** and
**folders**, downloads only the ones that are **new or updated** since the last
run, and delivers them straight into a **Telegram chat** — on a schedule or on
demand.

Update detection uses a content hash (SHA-256) stored in **Redis**, so
unchanged lectures are skipped and never re-downloaded or re-sent.

## How it works

```
login -> crawl each course -> find resource/folder activities
      -> download each file -> hash it -> compare with Redis
      -> save + remember the hash only if new or changed
      -> send new/updated files to Telegram
```

## Setup

Install dependencies (with [uv](https://docs.astral.sh/uv/)):

```bash
uv sync
```

You also need a running **Redis** instance and (for the bot) a **Telegram bot
token** from [@BotFather](https://t.me/BotFather).

## Configuration

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

| Variable              | Required          | Purpose                                       |
| --------------------- | ----------------- | --------------------------------------------- |
| `UIT_USERNAME`        | yes               | Your LMS username                             |
| `UIT_PASSWORD`        | yes               | Your LMS password                             |
| `REDIS_URL`           | yes               | Redis connection (e.g. `redis://host:6379/0`) |
| `TELEGRAM_BOT_TOKEN`  | for the bot       | Token from @BotFather                         |
| `TELEGRAM_CHAT_ID`    | for the bot       | Chat that receives lectures / may command it  |
| `UIT_SCHEDULE_TIMES`  | no                | Daily run times, e.g. `08:00,18:00`           |
| `UIT_DOWNLOAD_DIR`    | no                | Where lectures are saved (default `downloads`)|
| `UIT_REQUEST_DELAY`   | no                | Seconds between requests (default `1.0`)      |
| `UIT_VERIFY_SSL`      | no                | Verify the LMS certificate (default `false`)  |

Finding your `TELEGRAM_CHAT_ID`: message your bot once, then open
`https://api.telegram.org/bot<TOKEN>/getUpdates` and read `message.chat.id`.

The list of courses to crawl lives in `COURSE_URLS` in `config.py`.

## Run

**One-shot download (no Telegram):**

```bash
uv run python main.py
```

**Telegram bot (scheduled + on-demand delivery):**

```bash
uv run python bot.py
```

The bot long-polls Telegram and runs a scrape at each time in
`UIT_SCHEDULE_TIMES`. Commands (only accepted from `TELEGRAM_CHAT_ID`):

| Command    | Action                                            |
| ---------- | ------------------------------------------------- |
| `/update`  | Check for new/updated lectures now and send them  |
| `/status`  | Show the last run's result                        |
| `/help`    | Show usage                                        |

Downloaded files are also saved locally as `downloads/<course title>/<filename>`.
Files above Telegram's 50 MB upload limit are reported (with their local path)
rather than sent.

> Scheduled times use the **server's local time zone**. Keep the bot process
> running (e.g. under `systemd`, `tmux`, or a container) for schedules to fire.

## Project layout

| File                 | Responsibility                                     |
| -------------------- | -------------------------------------------------- |
| `main.py`            | One-shot CLI run                                   |
| `bot.py`             | Telegram bot: scheduling, commands, delivery       |
| `runner.py`          | Shared scrape-and-download logic                    |
| `telegram_client.py` | Minimal Telegram Bot API client                    |
| `config.py`          | Environment-driven configuration                   |
| `lms.py`             | Session creation and login                         |
| `downloader.py`      | Finding activities and downloading their files     |
| `state.py`           | Redis-backed content-hash store                    |

## ⚠️ Note

BE GENTLE WITH THE SCRAPING. You are solely responsible if you get banned.
Keep `UIT_REQUEST_DELAY` reasonable and don't run it in a tight loop.
