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

def is_useful_article(title, summary):
    text = (title + " " + summary).lower()
    
    # 1. ЖЕСТКИЙ БАН: Если это новость про выход машины или продажи
    for bad_word in EXCLUDE_KEYWORDS:
        if bad_word in text:
            return False
            
    # 2. ПОИСК ПОЛЬЗЫ: Статья должна содержать либо симптом, либо процесс ремонта
    has_tech = any(k in text for k in TECH_KEYWORDS)
    has_symptom = any(k in text for k in SYMPTOMS_KEYWORDS)
    
    # Пропускаем только если есть техническая конкретика или описание проблемы
    return has_tech or has_symptom

def extract_symptoms(title, summary):
    text = (title + " " + summary).lower()
    # Ищем текстовые симптомы
    found = [s for s in SYMPTOMS_KEYWORDS if s.lower() in text]
    # Ищем коды ошибок (P0123, P0300)
    error_codes = re.findall(r'\b[PpBcCuU][0-9]{4}\b', text)
    found.extend([code.upper() for code in error_codes])
    return list(set(found))[:10]

def extract_image(entry):
    # YouTube Thumbnail (High Res)
    if 'youtube.com' in entry.get('link', ''):
        if 'media_group' in entry and 'media_thumbnail' in entry.media_group[0]:
            return entry.media_group[0]['media_thumbnail'][0]['url']
    
    # RSS Enclosures
    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): return enc.href
            
    # HTML Content extraction
    content = ''
    if hasattr(entry, 'content'): content = entry.content[0].value
    elif hasattr(entry, 'summary'): content = entry.summary
    
    match = re.search(r'<img[^>]*src=["\'](.*?)["\']', content)
    if match: return match.group(1)
    return None

def clean_html(text):
    if not text: return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_full_text(entry):
    content = ''
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
                
                # ГЛАВНЫЙ ФИЛЬТР
                if not title or not is_useful_article(title, summary):
                    continue
                
                # Оформление заголовка (добавляем тип контента)
                final_title = title
                if "YouTube" in source['name']:
                    final_title = f"🎬 {title}"
                elif "Drive2" in source['name']:
                    final_title = f"🛠️ {title}"

                item = {
                    'title': final_title,
                    'summary': summary[:2000] + '...' if len(summary) > 2000 else summary,
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
        print(f"✅ {count} инструкций")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return news_list

def main():
    print(f"🚀 Сбор базы знаний... Источников: {len(NEWS_SOURCES)}")
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
        print(f"\n💾 База обновлена! Добавлено {len(all_news)} решений.")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка сохранения: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
