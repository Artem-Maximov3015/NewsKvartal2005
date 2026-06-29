# -*- coding: utf-8 -*-
"""
Парсер раздела "Новости" сайта квартал2005.рф.

ВАЖНО: автоматический доступ к этому сайту ограничен его robots.txt,
поэтому точную верстку страницы заранее увидеть не удалось. Парсер
работает по эвристике, которая чаще всего подходит для таких списков
новостей:

    13.04.2022   Утвержденный график проведения плановых работ...
    06.04.2022   Информация о льготах по оплате ЖКУ

То есть ищем во всём HTML текстовые блоки, где рядом стоит дата в
формате дд.мм.гггг и заголовок новости (как правило, обёрнутый в
ссылку <a>).

Если после деплоя бот упорно не находит новости (см. логи в GitHub
Actions) — значит верстка сайта отличается от ожидаемой, и нужно
донастроить функцию fetch_news() ниже под реальный HTML (см. README,
раздел "Если парсер не находит новости").
"""

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Kvartal2005NewsBot/1.0; "
        "+https://github.com/) Telegram news notifier"
    )
}


def _clean_title(text: str, date_str: str) -> str:
    title = text.replace(date_str, "")
    return title.strip(" \t\n\r·-—:|")


def fetch_news(url: str, timeout: int = 15):
    """
    Возвращает список новостей со страницы в виде словарей:
        {"id": str, "date": str, "title": str, "link": str}

    Список отдаётся в том порядке, в котором новости идут на странице
    (как правило, самые новые — первыми).
    """
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or resp.encoding
    soup = BeautifulSoup(resp.text, "lxml")

    items = []
    seen_ids = set()

    # Стратегия 1: дата и заголовок находятся прямо внутри <a href="...">
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        if not text:
            continue
        m = DATE_RE.search(text)
        if not m:
            continue
        date_str = m.group(0)
        title = _clean_title(text, date_str)
        if not title:
            continue
        link = urljoin(url, a["href"])
        if link in seen_ids:
            continue
        seen_ids.add(link)
        items.append({"id": link, "date": date_str, "title": title, "link": link})

    if items:
        return items

    # Стратегия 2 (запасная): дата лежит отдельным текстовым узлом,
    # а заголовок и ссылка — где-то рядом в том же родительском блоке.
    for text_node in soup.find_all(string=DATE_RE):
        block = text_node.find_parent(["div", "li", "tr", "article", "section"])
        if block is None:
            continue
        block_text = block.get_text(" ", strip=True)
        m = DATE_RE.search(block_text)
        if not m:
            continue
        date_str = m.group(0)
        title = _clean_title(block_text, date_str)
        if not title:
            continue

        a = block.find("a", href=True)
        link = urljoin(url, a["href"]) if a else url
        uid = link if a else f"{date_str}:{title[:80]}"

        if uid in seen_ids:
            continue
        seen_ids.add(uid)
        items.append({"id": uid, "date": date_str, "title": title, "link": link})

    return items
