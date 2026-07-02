"""One-shot CLI: check the UIT LMS for new/updated lectures and download them.

For scheduled runs and Telegram delivery, use ``bot.py`` instead.
"""

import sys

import redis

import config
from runner import run
from state import HashStore


def main() -> int:
    store = HashStore()
    try:
        store.ping()
    except redis.RedisError as exc:
        print(f"[-] Could not connect to Redis at {config.REDIS_URL}: {exc}")
        return 1

    try:
        results = run(store, log=lambda m: print(f"[*] {m}"))
    except RuntimeError as exc:
        print(f"[-] {exc}")
        return 1

    print(f"\n[*] Done. {len(results)} new/updated file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
