#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import json
import sys
import os
import re
import html
from datetime import datetime

# Подключаем конфиг
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    NEWS_SOURCES, MAX_NEWS_PER_SOURCE, MAX_TOTAL_NEWS,
    EXCLUDE_KEYWORDS, TECH_KEYWORDS, SYMPTOMS_KEYWORDS, OUTPUT_FILE
)

# === МАСКИРОВКА ПОД БРАУЗЕР ===
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def is_technical(title, summary):
    text = (title + " " + summary).lower()
    # Строгий фильтр стоп-слов
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text:
            return False
    # Мягкий фильтр: если есть тех. слова - берем
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False

def extract_symptoms(title, summary):
    text = (title + " " + summary).lower()
    found = [s for s in SYMPTOMS_KEYWORDS if s.lower() in text]
    return list(set(found))[:8]

def extract_image(entry):
    # 1. YouTube (высокое качество)
    if 'youtube.com' in entry.get('link', ''):
        if 'media_group' in entry and 'media_thumbnail' in entry.media_group[0]:
            return entry.media_group[0]['media_thumbnail'][0]['url']
    
    # 2. Стандартные поля RSS
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url', '')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.type.startswith('image/'):
                return enc.href

    # 3. Поиск картинки внутри HTML текста
    if 'summary' in entry:
        match = re.search(r'<img[^>]*src=["\'](.*?)["\']', entry.summary)
        if match:
            return match.group(1)
    if 'content' in entry:
        for c in entry.content:
            match = re.search(r'<img[^>]*src=["\'](.*?)["\']', c.value)
            if match:
                return match.group(1)
                
    return None

def clean_html(text):
    if not text: return ''
    
    # 1. Декодируем HTML сущности (&nbsp; -> пробел, &quot; -> " и т.д.)
    text = html.unescape(text)
    
    # 2. Удаляем HTML теги
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 3. Исправляем спецсимволы, которые могли остаться
    text = text.replace('\xa0', ' ') # Неразрывный пробел
    text = text.replace('&nbsp;', ' ')
    
    # 4. Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def get_full_text(entry):
    """Пытается найти максимально полный текст в RSS"""
    content = ''
    
    # 1. Проверяем поле fulltext (иногда бывает)
    if hasattr(entry, 'content'):
        # Обычно content - это список словарей {'type': 'text/html', 'value': '...'}
        for c in entry.content:
            if c.value and len(c.value) > len(content):
                content = c.value
    
    # 2. Если content пуст, берем summary
    if not content and hasattr(entry, 'summary'):
        content = entry.summary
        
    # 3. Если все пусто, берем description
    if not content and hasattr(entry, 'description'):
        content = entry.description
        
    return clean_html(content)

def parse_rss_feed(source):
    news_list = []
    print(f"📥 {source['name']}...", end=' ')
    
    try:
        d = feedparser.parse(source['url'], request_headers=HEADERS)
        
        if not d.entries:
            print("❌ Пусто")
            return news_list

        count = 0
        for entry in d.entries[:MAX_NEWS_PER_SOURCE]:
            try:
                title = clean_html(entry.get('title', ''))
                # Используем новую функцию для получения полного текста
                summary = get_full_text(entry)
                
                # Фильтрация
                if not title or not is_technical(title, summary):
                    continue
                
                # Ограничиваем длину текста, чтобы JSON не раздувался до гигабайтов,
                # но делаем лимит большим (1500 символов), чтобы влезла инструкция.
                if len(summary) > 1500:
                    summary = summary[:1500].rsplit(' ', 1)[0] + '... (Читать далее в источнике)'

                item = {
                    'title': title,
                    'summary': summary,
                    'link': entry.get('link', ''),
                    'source': source['name'],
                    'category': source['category'],
                    'symptoms': extract_symptoms(title, summary),
                    'image': extract_image(entry),
                    'published': entry.get('published', datetime.now().isoformat())
                }
                news_list.append(item)
                count += 1
            except Exception as e:
                continue
        
        print(f"✅ {count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return news_list

def main():
    print(f"🚀 Запуск парсера... Источников: {len(NEWS_SOURCES)}")
    all_news = []
    
    for source in NEWS_SOURCES:
        all_news.extend(parse_rss_feed(source))
    
    # Сортировка по дате
    all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
    all_news = all_news[:MAX_TOTAL_NEWS]
    
    # Сохранение
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        output = {
            'news': all_news,
            'lastUpdated': datetime.now().isoformat(),
            'totalItems': len(all_news)
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 База сохранена! Всего статей: {len(all_news)}")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка сохранения: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
