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
    
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    
    print(f"Длина HTML: {len(resp.text)} символов")

    items = []
    seen_ids = set()

    # Ищем все ссылки
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True)
        
        # Пропускаем короткие ссылки (меньше 20 символов)
        if len(text) < 20:
            continue
        
        # Пропускаем ссылки с символами "#" или "tel:" или "mailto:"
        href = link.get("href", "")
        if href.startswith("#") or href.startswith("tel:") or href.startswith("mailto:"):
            continue
        
        title = text.strip()
        url_full = urljoin(url, href)
        
        # Ищем дату рядом со ссылкой
        parent = link.parent
        date_str = "Дата неизвестна"
        
        # Проверяем текст вокруг ссылки
        if parent:
            parent_text = parent.get_text()
            # Ищем дату в формате "08 Июн" или "08.06.2026"
            date_match = re.search(r'(\d{2}\s+[А-Яа-я]{3,}|[\d]{2}\.[\d]{2}\.[\d]{4})', parent_text)
            if date_match:
                date_str = date_match.group(0)
        
        # Если даты нет, ищем в родителе родителя
        if date_str == "Дата неизвестна":
            grandparent = parent.parent if parent else None
            if grandparent:
                grandparent_text = grandparent.get_text()
                date_match = re.search(r'(\d{2}\s+[А-Яа-я]{3,}|[\d]{2}\.[\d]{2}\.[\d]{4})', grandparent_text)
                if date_match:
                    date_str = date_match.group(0)

        uid = url_full if url_full else title

        if uid in seen_ids:
            continue
        seen_ids.add(uid)

        print(f"Найдена ссылка: {title[:50]}... (дата: {date_str})")

        items.append({
            "id": uid,
            "date": date_str,
            "title": title,
            "link": url_full
        })

    print(f"Найдено новостей: {len(items)}")
    return items[:10]
