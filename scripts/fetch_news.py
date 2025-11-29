#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Мастерская Автоэлектрика - Парсер новостей
Автоматический сбор статей по автоэлектрике из 50+ источников
с фильтрацией, извлечением симптомов и сохранением в JSON
"""

import feedparser
import json
import sys
import os
import re
from datetime import datetime
from urllib.parse import urlparse

# Импортируем конфиг
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    NEWS_SOURCES,
    MAX_NEWS_PER_SOURCE,
    MAX_TOTAL_NEWS,
    EXCLUDE_KEYWORDS,
    TECH_KEYWORDS,
    SYMPTOMS_KEYWORDS,
    OUTPUT_FILE,
    PROJECT_ROOT
)

# ============================================
# ЦВЕТА ДЛЯ КОНСОЛИ
# ============================================

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

# ============================================
# ФУНКЦИИ ФИЛЬТРАЦИИ
# ============================================

def is_technical(title, summary):
    """Проверяет, является ли новость технической (по автоэлектрике)"""
    text = (title + " " + summary).lower()
    
    # Проверяем стоп-слова
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text:
            return False
    
    # Считаем техно-слова
    tech_count = 0
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in text:
            tech_count += 1
    
    # Требуем минимум 1-2 техно-слова
    return tech_count >= 1

def extract_symptoms(title, summary):
    """Извлекает симптомы неисправности из текста"""
    text = (title + " " + summary).lower()
    found_symptoms = []
    
    for symptom in SYMPTOMS_KEYWORDS:
        if symptom.lower() in text:
            found_symptoms.append(symptom)
    
    # Убираем дубликаты
    return list(set(found_symptoms))

def extract_image(entry):
    """Извлекает изображение из RSS entry"""
    # Ищем в media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url', '')
    
    # Ищем в media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    
    # Ищем img в summary
    if 'summary' in entry:
        img_match = re.search(r'<img[^>]*src=["\'](.*?)["\']', entry.summary)
        if img_match:
            return img_match.group(1)
    
    return None

def clean_html(text):
    """Очищает HTML теги и сущности"""
    if not text:
        return ''
    
    # Убираем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Убираем HTML entities
    entities = {
        '&nbsp;': ' ',
        '&quot;': '"',
        '&apos;': "'",
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&#39;': "'",
        '<br': ' ',
        '</br>': ' ',
        '</p>': ' ',
        '</div>': ' ',
    }
    
    for entity, char in entities.items():
        text = text.replace(entity, char)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text[:500]  # Макс 500 символов

def shorten_text(text, max_length=200):
    """Сокращает текст до определённой длины"""
    if len(text) > max_length:
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    return text

# ============================================
# ПАРСИНГ RSS
# ============================================

def parse_rss_feed(source):
    """Парсит один RSS источник и возвращает список новостей"""
    news_list = []
    
    try:
        print(f"  📥 Парсю: {source['name']}...")
        feed = feedparser.parse(source['url'])
        
        if feed.bozo:
            print(f"    ⚠️  Ошибка парсинга: {feed.bozo_exception}")
            return news_list
        
        if not feed.entries:
            print(f"    ⚠️  Нет записей в источнике")
            return news_list
        
        for entry in feed.entries[:MAX_NEWS_PER_SOURCE]:
            try:
                title = entry.get('title', 'Без заголовка')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # Очищаем текст
                title = clean_html(title)
                summary = clean_html(summary)
                summary = shorten_text(summary, 200)
                
                # Проверяем, техническая ли новость
                if not is_technical(title, summary):
                    continue
                
                # Извлекаем симптомы
                symptoms = extract_symptoms(title, summary)
                
                # Извлекаем изображение
                image = extract_image(entry)
                
                news_item = {
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'source': source['name'],
                    'category': source['category'],
                    'symptoms': symptoms,
                    'image': image,
                    'published': published,
                }
                
                news_list.append(news_item)
                
            except Exception as e:
                print(f"    ❌ Ошибка обработки записи: {e}")
                continue
        
        print(f"    ✅ Загружено {len(news_list)} статей")
        
    except Exception as e:
        print(f"    ❌ Ошибка парсинга источника: {e}")
    
    return news_list

def fetch_all_news():
    """Загружает новости из всех источников"""
    all_news = []
    
    print(f"{Colors.BOLD}{Colors.BLUE}🔧 Мастерская Автоэлектрика - Парсер новостей{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"⏱️  Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Источников: {len(NEWS_SOURCES)}")
    print(f"{'=' * 60}{Colors.END}\n")
    
    for source in NEWS_SOURCES:
        news = parse_rss_feed(source)
        all_news.extend(news)
    
    # Сортируем по дате (новые первыми)
    all_news.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    # Ограничиваем общее количество
    all_news = all_news[:MAX_TOTAL_NEWS]
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.GREEN}✅ Успешно загружено статей: {len(all_news)}{Colors.END}")
    
    return all_news

# ============================================
# СОХРАНЕНИЕ В JSON
# ============================================

def save_news_to_json(news_list):
    """Сохраняет список новостей в JSON файл"""
    try:
        output_data = {
            'news': news_list,
            'lastUpdated': datetime.now().isoformat(),
            'totalItems': len(news_list),
            'totalSources': len(set(n['source'] for n in news_list)),
        }
        
        # Создаём директорию, если её нет
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"{Colors.GREEN}💾 Сохранено в: {OUTPUT_FILE}{Colors.END}")
        print(f"   Размер файла: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка при сохранении: {e}{Colors.END}")
        return False

# ============================================
# СТАТИСТИКА
# ============================================

def print_statistics(news_list):
    """Выводит статистику по собранным новостям"""
    print(f"\n{Colors.BOLD}📊 СТАТИСТИКА{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}")
    
    # Общая статистика
    print(f"📝 Всего статей: {len(news_list)}")
    
    # По категориям
    categories = {}
    for item in news_list:
        cat = item.get('category', 'Неизвестно')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📂 По категориям:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {cat}: {count}")
    
    # По симптомам
    symptoms_count = {}
    for item in news_list:
        for symptom in item.get('symptoms', []):
            symptoms_count[symptom] = symptoms_count.get(symptom, 0) + 1
    
    print(f"\n🏷️  Топ симптомов:")
    for symptom, count in sorted(symptoms_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {symptom}: {count}")
    
    # По источникам
    sources = {}
    for item in news_list:
        src = item.get('source', 'Неизвестно')
        sources[src] = sources.get(src, 0) + 1
    
    print(f"\n📌 Активных источников: {len(sources)}")
    
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Главная функция"""
    try:
        # Парсим все источники
        news = fetch_all_news()
        
        if not news:
            print(f"{Colors.RED}❌ Ошибка: не удалось загрузить новости{Colors.END}")
            sys.exit(1)
        
        # Выводим статистику
        print_statistics(news)
        
        # Сохраняем в JSON
        if not save_news_to_json(news):
            sys.exit(1)
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ПАРСИНГ ЗАВЕРШЁН УСПЕШНО{Colors.END}")
        print(f"⏱️  Конец: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ КРИТИЧЕСКАЯ ОШИБКА: {e}{Colors.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()
