# -*- coding: utf-8 -*-
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

def fetch_news(url: str, timeout: int = 15):
    print(f"Запрос к URL: {url}")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        print(f"Статус: {resp.status_code}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return []

    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    
    print(f"Длина HTML: {len(resp.text)} символов")

    items = []
    seen_ids = set()

    # Ищем все заголовки с классом entry-title
    for title_tag in soup.find_all("a", class_="entry-title"):
        title = title_tag.get_text(strip=True)
        print(f"Найден заголовок: {title}")
        
        if not title:
            continue

        link = urljoin(url, title_tag.get("href", ""))
        
        # Ищем дату
        parent = title_tag.parent
        date_str = "Дата неизвестна"
        while parent:
            time_tag = parent.find("time")
            if time_tag:
                date_str = time_tag.get_text(strip=True)
                break
            parent = parent.parent

        uid = link if link else title

        if uid in seen_ids:
            continue
        seen_ids.add(uid)

        items.append({
            "id": uid,
            "date": date_str,
            "title": title,
            "link": link
        })

    print(f"Найдено новостей: {len(items)}")
    return items[:10]
