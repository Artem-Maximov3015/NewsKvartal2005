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
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    seen_ids = set()

    # Ищем все статьи (WordPress post)
    for article in soup.find_all("article", class_=re.compile(r"post")):
        # Ищем заголовок
        title_tag = article.find("a", class_=re.compile(r"title"))
        if not title_tag:
            continue
        
        title = title_tag.get_text(strip=True)
        if not title:
            continue

        link = urljoin(url, title_tag.get("href", ""))

        # Ищем дату
        date_tag = article.find("time")
        if date_tag:
            date_str = date_tag.get_text(strip=True)
        else:
            # Пробуем найти дату в тексте
            text = article.get_text()
            # Ищем дату в формате "08 Июн" или "08.06.2026"
            date_match = re.search(r'(\d{2}\s+[А-Яа-я]{3,}|[\d]{2}\.[\d]{2}\.[\d]{4})', text)
            date_str = date_match.group(0) if date_match else "Дата неизвестна"

        # Или пробуем найти через og:published_time
        if date_str == "Дата неизвестна":
            meta_tag = article.find("meta", {"property": "article:published_time"})
            if meta_tag:
                date_str = meta_tag.get("content", "").split("T")[0]

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

    # Если не нашли через article, ищем через entry-title
    if not items:
        for title_tag in soup.find_all("a", class_=re.compile(r"entry-title|title")):
            title = title_tag.get_text(strip=True)
            if not title:
                continue
            
            link = urljoin(url, title_tag.get("href", ""))
            
            # Ищем дату рядом
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

    return items[:10]
