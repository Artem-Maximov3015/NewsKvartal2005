# -*- coding: utf-8 -*-
"""
Главный скрипт: проверяет раздел новостей квартал2005.рф и отправляет
ещё не отправленные новости в Telegram.

Запускается вручную (python bot/main.py) или по расписанию через
GitHub Actions (см. .github/workflows/check_news.yml).
"""

import html
import json
import os
import sys
from pathlib import Path

from scraper import fetch_news
from telegram_sender import send_message, TelegramSendError

NEWS_URL = os.environ.get(
    "NEWS_URL", "https://xn--2005-43dam7dm2cwa.xn--p1ai/novosti"
)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "seen_news.json"
MAX_STATE_ITEMS = 500


def load_seen_ids() -> list:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save_seen_ids(ids: list) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    trimmed = ids[-MAX_STATE_ITEMS:]
    STATE_FILE.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def format_message(item: dict) -> str:
    title = html.escape(item["title"])
    date = html.escape(item["date"])
    link = html.escape(item["link"])
    return (
        f"🏠 <b>Квартал-2005 — новость</b>\n"
        f"📅 {date}\n\n"
        f"{title}\n\n"
        f"🔗 {link}"
    )


def main() -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print(
            "Не заданы переменные TELEGRAM_BOT_TOKEN и/или TELEGRAM_CHAT_ID.",
            file=sys.stderr,
        )
        sys.exit(1)

    seen = load_seen_ids()
    seen_set = set(seen)

    try:
        items = fetch_news(NEWS_URL)
    except Exception as exc:
        print(f"Не удалось получить страницу новостей: {exc}", file=sys.stderr)
        sys.exit(1)

    if not items:
        print(
            "Новости на странице не найдены. Возможно, верстка сайта "
            "отличается от ожидаемой — см. README, раздел "
            "'Если парсер не находит новости'."
        )
        return

    new_items = [item for item in items if item["id"] not in seen_set]

    if not new_items:
        print("Новых новостей нет.")
        return

    # Отправляем от старых к новым, чтобы в чате порядок был естественным
    sent_any = False
    for item in reversed(new_items):
        try:
            send_message(BOT_TOKEN, CHAT_ID, format_message(item))
            print(f"Отправлено: {item['title']}")
            seen.append(item["id"])
            sent_any = True
        except TelegramSendError as exc:
            print(f"Ошибка Telegram при отправке '{item['title']}': {exc}", file=sys.stderr)

    if sent_any:
        save_seen_ids(seen)


if __name__ == "__main__":
    main()
