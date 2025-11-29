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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def is_technical(title, summary):
    text = (title + " " + summary).lower()
    for k in EXCLUDE_KEYWORDS:
        if k.lower() in text: return False
    for k in TECH_KEYWORDS:
        if k.lower() in text: return True
    return False

def extract_symptoms(title, summary):
    text = (title + " " + summary).lower()
    # Ищем совпадения симптомов
    found = [s for s in SYMPTOMS_KEYWORDS if s.lower() in text]
    
    # Дополнительно: ищем коды ошибок (P0123, P0300 и т.д.)
    error_codes = re.findall(r'\b[PpBcCuU][0-9]{4}\b', text)
    found.extend([code.upper() for code in error_codes])
    
    return list(set(found))[:10]

def extract_image(entry):
    # YouTube (Max Resolution)
    if 'youtube.com' in entry.get('link', ''):
        if 'media_group' in entry and 'media_thumbnail' in entry.media_group[0]:
            return entry.media_group[0]['media_thumbnail'][0]['url']
    
    # RSS Enclosures
    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): return enc.href
    
    # HTML Content
    content = ''
    if hasattr(entry, 'content'): content = entry.content[0].value
    elif hasattr(entry, 'summary'): content = entry.summary
    
    match = re.search(r'<img[^>]*src=["\'](.*?)["\']', content)
    if match: return match.group(1)
    
    return None

def clean_html(text):
    if not text: return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text) # Удаляем теги
    text = re.sub(r'http\S+', '', text) # Удаляем ссылки
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_full_text(entry):
    content = ''
    # Приоритет: Content -> Summary -> Description
    if hasattr(entry, 'content'):
        for c in entry.content:
            if c.value and len(c.value) > len(content): content = c.value
    if not content and hasattr(entry, 'summary'): content = entry.summary
    if not content and hasattr(entry, 'description'): content = entry.description
    
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
                summary = get_full_text(entry)
                
                if not title or not is_technical(title, summary):
                    continue
                
                # Лимит текста для JSON (чтобы не вешал браузер, но было информативно)
                if len(summary) > 2000:
                    summary = summary[:2000] + '... (Читать далее в источнике)'

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
    print(f"🚀 Запуск парсера решений... Источников: {len(NEWS_SOURCES)}")
    all_news = []
    
    for source in NEWS_SOURCES:
        all_news.extend(parse_rss_feed(source))
    
    all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
    all_news = all_news[:MAX_TOTAL_NEWS]
    
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        output = {
            'news': all_news,
            'lastUpdated': datetime.now().isoformat(),
            'totalItems': len(all_news)
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено {len(all_news)} решений/инструкций.")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка сохранения: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
