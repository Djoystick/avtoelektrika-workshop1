#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import json
import sys
import os
import re
from datetime import datetime

# Подключаем конфиг
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    NEWS_SOURCES, MAX_NEWS_PER_SOURCE, MAX_TOTAL_NEWS,
    EXCLUDE_KEYWORDS, TECH_KEYWORDS, SYMPTOMS_KEYWORDS, OUTPUT_FILE
)

# === МАСКИРОВКА ПОД БРАУЗЕР ===
# Это поможет избежать блокировок со стороны Drive2 и других сайтов
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def is_technical(title, summary):
    text = (title + " " + summary).lower()
    # Если есть стоп-слова - сразу нет
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text:
            return False
    # Если есть технические слова - да
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False

def extract_symptoms(title, summary):
    text = (title + " " + summary).lower()
    found = [s for s in SYMPTOMS_KEYWORDS if s.lower() in text]
    return list(set(found))[:8]

def extract_image(entry):
    # YouTube
    if 'youtube.com' in entry.get('link', ''):
        # Пытаемся достать превью YouTube
        if 'media_group' in entry and 'media_thumbnail' in entry.media_group[0]:
            return entry.media_group[0]['media_thumbnail'][0]['url']
    
    # Стандартный RSS
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url', '')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    
    # Поиск в HTML
    if 'summary' in entry:
        match = re.search(r'<img[^>]*src=["\'](.*?)["\']', entry.summary)
        if match:
            return match.group(1)
    return None

def clean_html(text):
    if not text: return ''
    text = re.sub(r'<[^>]+>', '', text) # Удаляем теги
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:600] # Оставляем побольше текста для инструкций

def parse_rss_feed(source):
    news_list = []
    print(f"📥 {source['name']}...", end=' ')
    
    try:
        # Передаем заголовки (через feedparser это делается неявно, но иногда помогает request_headers)
        # Для простоты используем стандартный feedparser, он обычно справляется с RSS
        d = feedparser.parse(source['url'], request_headers=HEADERS)
        
        if d.bozo and d.bozo_exception:
             print(f"⚠️ (XML Warning)", end=' ')

        if not d.entries:
            print("❌ Пусто")
            return news_list

        count = 0
        for entry in d.entries[:MAX_NEWS_PER_SOURCE]:
            try:
                title = clean_html(entry.get('title', ''))
                summary = clean_html(entry.get('summary', ''))
                
                # Фильтрация
                if not title or not is_technical(title, summary):
                    continue

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
            except:
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
    
    # Сортировка по дате (свежие сверху)
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
