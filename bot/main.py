"""Baqsy Telegram bot — Phase 1 skeleton.

This file intentionally does nothing beyond logging a startup banner.
Full aiogram 3 FSM handlers arrive in Phase 3.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("baqsy.bot")


async def main() -> None:
    log.info("baqsy-bot skeleton started (Phase 1 — no handlers yet)")
    log.info("TELEGRAM_BOT_TOKEN present: %s", bool(os.environ.get("TELEGRAM_BOT_TOKEN")))
    # Keep the process alive so Docker considers the container running.
    # Phase 3 replaces this with aiogram polling loop.
    while True:
        await asyncio.sleep(60)
        log.info("baqsy-bot heartbeat")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
