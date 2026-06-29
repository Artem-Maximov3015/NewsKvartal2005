# -*- coding: utf-8 -*-
"""
Парсер раздела "Новости" сайта квартал2005.рф.
"""

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": "https://квартал2005.рф/",
}


def _clean_title(text: str, date_str: str) -> str:
    """Очищает заголовок от даты и лишних символов."""
    title = text.replace(date_str, "")
    for sep in ["-", "—", "|", "•", "·"]:
        title = title.strip(sep)
    return title.strip()


def fetch_news(url: str, timeout: int = 15):
    """
    Возвращает список новостей со страницы в виде словарей:
        {"id": str, "date": str, "title": str, "link": str}
    """
    # Кодируем URL с русскими буквами
    encoded_url = url.encode('utf-8').decode('ascii', 'ignore')
    
    resp = requests.get(encoded_url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    seen_ids = set()

    # Ищем все блоки, которые могут содержать новость
    for block in soup.find_all(["article", "div", "li", "tr", "section"]):
        block_text = block.get_text(" ", strip=True)
        if not block_text:
            continue

        m = DATE_RE.search(block_text)
        if not m:
            continue

        date_str = m.group(0)

        link_tag = block.find("a", href=True)
        if not link_tag:
            continue

        title = link_tag.get_text(" ", strip=True)
        if not title or len(title) < 5:
            title = _clean_title(block_text, date_str)

        if not title:
            continue

        title = _clean_title(title, date_str)
        if not title:
            continue

        link = urljoin(url, link_tag["href"])
        uid = link if link else f"{date_str}:{title[:80]}"

        if uid in seen_ids:
            continue
        seen_ids.add(uid)

        items.append({
            "id": uid,
            "date": date_str,
            "title": title,
            "link": link
        })

    # Запасная стратегия
    if not items:
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
            items.append({
                "id": link,
                "date": date_str,
                "title": title,
                "link": link
            })

    return items[:10]
