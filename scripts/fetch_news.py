#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Мастерская Автоэлектрика - Парсер новостей v2.0
Загружает новости из 100+ источников с фильтрацией и извлечением симптомов
"""

import feedparser
import json
import sys
import os
import re
from datetime import datetime
from urllib.parse import urlparse

# Подключаем конфиг
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
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
except ImportError as e:
    print(f"❌ Ошибка импорта config: {e}")
    sys.exit(1)

# ============================================
# ЦВЕТА ДЛЯ КОНСОЛИ
# ============================================

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

# ============================================
# ФУНКЦИИ ФИЛЬТРАЦИИ
# ============================================

def is_technical(title, summary):
    """Проверяет, является ли новость технической по автоэлектрике"""
    text = (title + " " + summary).lower()
    
    # Проверяем стоп-слова (исключаем)
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text:
            return False
    
    # Считаем технические слова
    tech_count = 0
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in text:
            tech_count += 1
    
    # Требуем минимум 1 техно-слово для включения
    return tech_count >= 1

def extract_symptoms(title, summary):
    """Извлекает симптомы из текста статьи"""
    text = (title + " " + summary).lower()
    found_symptoms = []
    
    for symptom in SYMPTOMS_KEYWORDS:
        if symptom.lower() in text:
            found_symptoms.append(symptom)
    
    # Убираем дубликаты, сортируем по релевантности
    found_symptoms = list(set(found_symptoms))
    found_symptoms.sort(key=lambda x: len(x), reverse=True)
    
    # Возвращаем максимум 10 симптомов
    return found_symptoms[:10]

def extract_image(entry):
    """Извлекает первое изображение из RSS entry"""
    # Проверяем media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        try:
            return entry.media_content[0].get('url', '')
        except:
            pass
    
    # Проверяем media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        try:
            return entry.media_thumbnail[0].get('url', '')
        except:
            pass
    
    # Ищем img в summary
    if 'summary' in entry:
        try:
            img_match = re.search(r'<img[^>]*src=["\'](.*?)["\']', entry.summary)
            if img_match:
                return img_match.group(1)
        except:
            pass
    
    return None

def clean_html(text):
    """Очищает HTML теги и сущности из текста"""
    if not text:
        return ''
    
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Заменяем HTML entities
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
    
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Ограничиваем длину
    if len(text) > 500:
        text = text[:500]
    
    return text

def shorten_text(text, max_length=200):
    """Сокращает текст до определённой длины"""
    if len(text) > max_length:
        # Обрезаем и добавляем многоточие на последнем полном слове
        shortened = text[:max_length].rsplit(' ', 1)[0]
        return shortened + '...'
    return text

# ============================================
# ПАРСИНГ RSS
# ============================================

def parse_rss_feed(source, source_number, total_sources):
    """Парсит один RSS источник и возвращает список новостей"""
    news_list = []
    
    try:
        # Выводим процесс парсинга
        source_name = source['name'][:40]
        print(f"  [{source_number:3d}/{total_sources}] ", end='')
        print(f"{Colors.CYAN}📥{Colors.END} {source_name:<40} ", end='', flush=True)
        
        # Парсим RSS
        feed = feedparser.parse(source['url'])
        
        # Проверяем на ошибки
        if feed.bozo:
            print(f"{Colors.YELLOW}⚠️  Ошибка парсинга{Colors.END}")
            return news_list
        
        if not feed.entries:
            print(f"{Colors.YELLOW}⚠️  Нет записей{Colors.END}")
            return news_list
        
        valid_count = 0
        
        # Обрабатываем каждую статью
        for entry in feed.entries[:MAX_NEWS_PER_SOURCE]:
            try:
                # Извлекаем данные из entry
                title = entry.get('title', 'Без заголовка')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # Очищаем текст
                title = clean_html(title)
                summary = clean_html(summary)
                summary = shorten_text(summary, 200)
                
                # Пропускаем пустые заголовки
                if not title:
                    continue
                
                # Проверяем, техническая ли новость
                if not is_technical(title, summary):
                    continue
                
                # Извлекаем симптомы
                symptoms = extract_symptoms(title, summary)
                
                # Извлекаем изображение
                image = extract_image(entry)
                
                # Создаём элемент новости
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
                valid_count += 1
                
            except Exception as e:
                # Пропускаем ошибочные entries
                continue
        
        # Выводим результат
        if valid_count > 0:
            print(f"{Colors.GREEN}✅{Colors.END} {valid_count} статей")
        else:
            print(f"{Colors.YELLOW}⚠️  0 статей{Colors.END}")
        
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка: {str(e)[:30]}{Colors.END}")
    
    return news_list

def fetch_all_news():
    """Загружает новости из всех источников"""
    all_news = []
    
    # Выводим заголовок
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}🔧 Мастерская Автоэлектрика v2.0 - Парсер новостей{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"⏱️  Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Источников: {len(NEWS_SOURCES)}")
    print(f"📊 Максимум статей: {MAX_TOTAL_NEWS}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    # Парсим каждый источник
    for idx, source in enumerate(NEWS_SOURCES, 1):
        news = parse_rss_feed(source, idx, len(NEWS_SOURCES))
        all_news.extend(news)
    
    # Сортируем по дате (новые первыми)
    all_news.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    # Ограничиваем количество
    all_news = all_news[:MAX_TOTAL_NEWS]
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}✅ Успешно загружено статей: {len(all_news)}{Colors.END}")
    
    return all_news

# ============================================
# СОХРАНЕНИЕ В JSON
# ============================================

def save_news_to_json(news_list):
    """Сохраняет список новостей в JSON файл"""
    try:
        # Собираем метаданные
        categories = set(n['category'] for n in news_list)
        sources = set(n['source'] for n in news_list)
        all_symptoms = []
        for n in news_list:
            all_symptoms.extend(n.get('symptoms', []))
        symptoms = set(all_symptoms)
        
        output_data = {
            'news': news_list,
            'lastUpdated': datetime.now().isoformat(),
            'totalItems': len(news_list),
            'totalSources': len(sources),
            'totalCategories': len(categories),
            'totalSymptoms': len(symptoms),
        }
        
        # Создаём директорию если её нет
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        # Сохраняем JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Выводим результат
        file_size = os.path.getsize(OUTPUT_FILE) / 1024
        print(f"{Colors.GREEN}💾 Сохранено: {OUTPUT_FILE}{Colors.END}")
        print(f"   Размер: {file_size:.1f} KB")
        print(f"   Категорий: {len(categories)}")
        print(f"   Источников: {len(sources)}")
        print(f"   Симптомов: {len(symptoms)}\n")
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка при сохранении: {e}{Colors.END}\n")
        return False

# ============================================
# СТАТИСТИКА
# ============================================

def print_statistics(news_list):
    """Выводит подробную статистику по собранным новостям"""
    print(f"\n{Colors.BOLD}📊 СТАТИСТИКА{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    
    # Общая статистика
    print(f"📝 Всего статей: {len(news_list)}")
    
    # По категориям
    categories = {}
    for item in news_list:
        cat = item.get('category', 'Неизвестно')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📂 По категориям ({len(categories)}):")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"   {cat:40} {count:3d} статей")
    
    # По симптомам
    symptoms_count = {}
    for item in news_list:
        for symptom in item.get('symptoms', []):
            symptoms_count[symptom] = symptoms_count.get(symptom, 0) + 1
    
    print(f"\n🏷️  Топ симптомов ({len(symptoms_count)}):")
    for symptom, count in sorted(symptoms_count.items(), key=lambda x: x[1], reverse=True)[:12]:
        print(f"   {symptom:45} {count:3d} совпадений")
    
    # По источникам
    sources = {}
    for item in news_list:
        src = item.get('source', 'Неизвестно')
        sources[src] = sources.get(src, 0) + 1
    
    print(f"\n📌 Активных источников: {len(sources)}")
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}\n")

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Главная функция программы"""
    try:
        # Парсим все источники
        news = fetch_all_news()
        
        if not news:
            print(f"{Colors.RED}❌ Ошибка: не удалось загрузить новости{Colors.END}\n")
            sys.exit(1)
        
        # Выводим статистику
        print_statistics(news)
        
        # Сохраняем в JSON
        if not save_news_to_json(news):
            sys.exit(1)
        
        # Финальное сообщение
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ПАРСИНГ ЗАВЕРШЁН УСПЕШНО{Colors.END}")
        print(f"⏱️  Конец: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Парсинг прерван пользователем{Colors.END}\n")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ КРИТИЧЕСКАЯ ОШИБКА: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
