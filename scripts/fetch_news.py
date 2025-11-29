#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 ПАРСЕР МАСТЕРСКОЙ АВТОЭЛЕКТРИКИ v3.0
Вытягивает только инструкции и решения, не новости
"""

import feedparser
import json
import sys
import os
import re
import html
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    NEWS_SOURCES, MAX_NEWS_PER_SOURCE, MAX_TOTAL_NEWS,
    EXCLUDE_KEYWORDS, INSTRUCTION_KEYWORDS, ERROR_CODES, PROBLEM_CATEGORIES,
    OUTPUT_FILE
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("\n" + "="*80)
print("🔧 МАСТЕРСКАЯ АВТОЭЛЕКТРИКА v3.0 - Парсер решений")
print("="*80 + "\n")

# ==================================================
# ФИЛЬТРЫ КОНТЕНТА
# ==================================================

def is_instruction_not_news(title, summary, source_name):
    """
    Возвращает True только если это инструкция/решение, а не новость.
    Логика: 
    1. ИСКЛЮЧИТЬ если есть бан-слова
    2. ТРЕБОВАТЬ если есть слова инструкции
    """
    text = (title + " " + summary).lower()
    
    # 1. ЖЕСТКИЙ БАН
    for ban_word in EXCLUDE_KEYWORDS:
        if ban_word in text:
            return False
    
    # 2. Если это с Drive2 или YouTube - берем смелее
    if "Drive2" in source_name or "YouTube" in source_name:
        # Хотя бы одно слово про инструкцию
        return any(kw in text for kw in INSTRUCTION_KEYWORDS)
    
    # 3. Для техпорталов - строгое требование
    return any(kw in text for kw in INSTRUCTION_KEYWORDS)

def extract_error_codes(text):
    """Вытягивает коды ошибок из текста (P0300, C0001 и т.д.)"""
    codes = []
    for code in ERROR_CODES:
        if code in text.upper():
            codes.append(code)
    return codes

def tag_by_problem(title, summary):
    """Определяет, к какой категории проблемы относится статья"""
    text = (title + " " + summary).lower()
    
    matched_categories = []
    for category, keywords in PROBLEM_CATEGORIES.items():
        if any(kw in text for kw in keywords):
            matched_categories.append(category)
    
    return matched_categories if matched_categories else ["📚 Справка"]

def extract_content_type(source_name):
    """Определяет тип контента по названию источника"""
    if "YouTube" in source_name:
        return "🎬 Видео"
    elif "Drive2" in source_name:
        return "💬 Форум"
    elif "Лада" in source_name or "ABW" in source_name:
        return "📖 Справка"
    return "📚 Статья"

def clean_html(text):
    """Очищает текст от HTML-мусора"""
    if not text: return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_best_text(entry):
    """Вытягивает максимально длинный текст"""
    candidates = []
    if hasattr(entry, 'content'):
        for c in entry.content:
            if c.value:
                candidates.append(c.value)
    if hasattr(entry, 'summary') and entry.summary:
        candidates.append(entry.summary)
    if hasattr(entry, 'description') and entry.description:
        candidates.append(entry.description)
    
    # Берем самый длинный
    best = max(candidates, key=len) if candidates else ''
    return clean_html(best)[:2500]

def extract_image(entry):
    """Вытягивает картинку"""
    if 'youtube.com' in entry.get('link', ''):
        if 'media_group' in entry and 'media_thumbnail' in entry.media_group[0]:
            return entry.media_group[0]['media_thumbnail'][0]['url']
    
    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if enc.type.startswith('image/'):
                return enc.href
    
    content = get_best_text(entry)
    match = re.search(r'<img[^>]*src=["\'](.*?)["\']', content)
    if match: return match.group(1)
    return None

# ==================================================
# ПАРСИНГ ИСТОЧНИКОВ
# ==================================================

def parse_rss_source(source):
    """Парсит один RSS источник"""
    results = []
    source_name = source['name']
    
    print(f"📥 {source_name[:50]:<50}", end=' ', flush=True)
    
    try:
        feed = feedparser.parse(source['url'], request_headers=HEADERS)
        
        if not feed.entries:
            print("⚠️  Пусто")
            return results
        
        valid_count = 0
        for entry in feed.entries[:MAX_NEWS_PER_SOURCE]:
            try:
                title = clean_html(entry.get('title', ''))
                summary = get_best_text(entry)
                
                if not title:
                    continue
                
                # ГЛАВНЫЙ ФИЛЬТР
                if not is_instruction_not_news(title, summary, source_name):
                    continue
                
                # Если прошли фильтр — берем!
                error_codes = extract_error_codes(title + " " + summary)
                problem_tags = tag_by_problem(title, summary)
                content_type = extract_content_type(source_name)
                
                article = {
                    'title': title,
                    'summary': summary,
                    'link': entry.get('link', ''),
                    'source': source_name,
                    'sourceType': source.get('type', 'unknown'),
                    'category': source['category'],
                    'contentType': content_type,
                    'problemTags': problem_tags,
                    'errorCodes': error_codes,
                    'image': extract_image(entry),
                    'published': entry.get('published', datetime.now().isoformat())
                }
                
                results.append(article)
                valid_count += 1
                
            except Exception as e:
                continue
        
        print(f"✅ {valid_count} инструкций")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:50]}")
    
    return results

# ==================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ==================================================

def main():
    all_articles = []
    
    print(f"Парсинг {len(NEWS_SOURCES)} источников...\n")
    
    for source in NEWS_SOURCES:
        articles = parse_rss_source(source)
        all_articles.extend(articles)
    
    # Сортировка по дате
    all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
    all_articles = all_articles[:MAX_TOTAL_NEWS]
    
    # Подготовка статистики
    stats = {
        'totalArticles': len(all_articles),
        'totalSources': len(set(a['source'] for a in all_articles)),
        'contentTypes': dict(sorted(
            [(ct, sum(1 for a in all_articles if a['contentType'] == ct))
             for ct in set(a['contentType'] for a in all_articles)]
        )),
        'topProblemTags': dict(sorted(
            [(tag, sum(tag in a.get('problemTags', []) for a in all_articles))
             for a in all_articles 
             for tag in a.get('problemTags', [])],
            key=lambda x: x[1],
            reverse=True
        )[:10]),
    }
    
    print(f"\n{'='*80}")
    print(f"📊 СТАТИСТИКА")
    print(f"{'='*80}")
    print(f"✅ Всего инструкций: {stats['totalArticles']}")
    print(f"📡 Активных источников: {stats['totalSources']}")
    print(f"\n📺 Типы контента:")
    for ct, count in stats['contentTypes'].items():
        print(f"   {ct}: {count}")
    print(f"\n🏷️  Топ проблемы:")
    for tag, count in list(stats['topProblemTags'].items())[:5]:
        print(f"   {tag}: {count}")
    print(f"{'='*80}\n")
    
    # Сохранение
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        output = {
            'articles': all_articles,
            'stats': stats,
            'lastUpdated': datetime.now().isoformat(),
            'version': '3.0'
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"💾 База сохранена: {OUTPUT_FILE}")
        print(f"   Размер: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}\n")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
