#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 ПАРСЕР v4.0 - Структурированная БД
"""

import feedparser
import json
import sys
import os
import re
import html
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    NEWS_SOURCES, MAX_NEWS_PER_SOURCE, MAX_TOTAL_NEWS,
    EXCLUDE_KEYWORDS, INSTRUCTION_KEYWORDS, ERROR_CODES, PROBLEM_CATEGORIES,
    VEHICLE_BRANDS, OUTPUT_FILE, VEHICLES_FILE, ERROR_CODES_FILE
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("\n" + "=" * 80)
print("🔧 ПАРСЕР МАСТЕРСКОЙ АВТОЭЛЕКТРИКА v4.0")
print("=" * 80 + "\n")

def clean_html(text):
    if not text: return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_best_text(entry):
    candidates = []
    if hasattr(entry, "content"):
        for c in entry.content:
            if getattr(c, "value", ""): candidates.append(c.value)
    if getattr(entry, "summary", ""): candidates.append(entry.summary)
    if getattr(entry, "description", ""): candidates.append(entry.description)
    best = max(candidates, key=len) if candidates else ""
    return clean_html(best)[:2500]

def is_useful_content(title, summary, source_name):
    text = (title + " " + summary).lower()
    for bad in EXCLUDE_KEYWORDS:
        if bad in text: return False
    if "drive2" in source_name.lower() or "youtube" in source_name.lower():
        return True
    return any(k in text for k in INSTRUCTION_KEYWORDS)

def extract_error_codes(text):
    upper = text.upper()
    codes = []
    for code in ERROR_CODES.keys():
        if code in upper: codes.append(code)
    codes += re.findall(r"\b[PBUC][0-9]{4}\b", upper)
    return sorted(set(codes))

def extract_brands(text):
    text_lower = text.lower()
    brands = []
    for brand_key, brand_info in VEHICLE_BRANDS.items():
        if brand_key in text_lower or brand_info["name"].lower() in text_lower:
            brands.append(brand_key)
        for model in brand_info["models"]:
            if model.lower() in text_lower:
                brands.append(brand_key)
                break
    return list(set(brands))

def tag_by_problem(title, summary):
    text = (title + " " + summary).lower()
    tags = []
    for cat, keywords in PROBLEM_CATEGORIES.items():
        if any(k in text for k in keywords):
            tags.append(cat)
    return tags or ["📚 Справка"]

def extract_content_type(source_name):
    name = source_name.lower()
    if "youtube" in name: return "🎬 Видео"
    if "drive2" in name: return "💬 Форум"
    if "yt" in name: return "🎬 Видео"
    return "📚 Статья"

def extract_image(entry):
    link = entry.get("link", "")
    if "youtube.com" in link:
        if hasattr(entry, "media_group"):
            try: return entry.media_group[0]["media_thumbnail"][0]["url"]
            except: pass
    if hasattr(entry, "enclosures"):
        for enc in entry.enclosures:
            if getattr(enc, "type", "").startswith("image/"):
                return getattr(enc, "href", None)
    raw = ""
    if hasattr(entry, "content") and entry.content: raw = entry.content[0].value
    elif getattr(entry, "summary", ""): raw = entry.summary
    m = re.search(r'<img[^>]*src=["\'](.*?)["\']', raw or "")
    return m.group(1) if m else None

def parse_rss_source(source):
    results = []
    name = source["name"]
    print(f"📥 {name[:50]:<50}", end=" ", flush=True)
    
    try:
        feed = feedparser.parse(source["url"], request_headers=HEADERS)
        if not feed.entries:
            print("⚠️  пусто")
            return results
            
        count = 0
        for entry in feed.entries[:MAX_NEWS_PER_SOURCE]:
            try:
                title = clean_html(entry.get("title", ""))
                summary = get_best_text(entry)
                
                if not title or len(title) < 5: continue
                if not is_useful_content(title, summary, name): continue
                
                error_codes = extract_error_codes(title + " " + summary)
                brands = extract_brands(title + " " + summary)
                
                article = {
                    "id": f"{len(results)}_{int(datetime.now().timestamp())}",
                    "title": title,
                    "summary": summary,
                    "link": entry.get("link", ""),
                    "source": name,
                    "sourceType": source.get("type", "unknown"),
                    "category": source["category"],
                    "contentType": extract_content_type(name),
                    "problemTags": tag_by_problem(title, summary),
                    "errorCodes": error_codes,
                    "brands": brands,
                    "image": extract_image(entry),
                    "published": entry.get("published", datetime.now().isoformat()),
                    "views": 0,
                    "helpful": 0,
                }
                results.append(article)
                count += 1
            except: continue
            
        print(f"✅ {count}")
    except:
        print(f"❌ Ошибка")
        
    return results

def main():
    all_articles = []
    print(f"Источников: {len(NEWS_SOURCES)}\n")
    
    for src in NEWS_SOURCES:
        all_articles.extend(parse_rss_source(src))
        
    all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    all_articles = all_articles[:MAX_TOTAL_NEWS]
    
    # === ГЕНЕРИРУЕМ ИНДЕКСЫ ===
    
    # Индекс марок
    brand_index = {}
    for article in all_articles:
        for brand in article.get("brands", []):
            if brand not in brand_index:
                brand_index[brand] = []
            brand_index[brand].append(article["id"])
    
    # Индекс кодов ошибок
    error_code_index = {}
    for article in all_articles:
        for code in article.get("errorCodes", []):
            if code not in error_code_index:
                error_code_index[code] = []
            error_code_index[code].append(article["id"])
    
    # Индекс проблем
    problem_index = {}
    for article in all_articles:
        for tag in article.get("problemTags", []):
            if tag not in problem_index:
                problem_index[tag] = []
            problem_index[tag].append(article["id"])
    
    stats = {
        "totalArticles": len(all_articles),
        "totalSources": len({a["source"] for a in all_articles}),
        "totalBrands": len(brand_index),
        "totalErrorCodes": len(error_code_index),
    }
    
    print("\n" + "=" * 80)
    print(f"✅ ИТОГО: {stats['totalArticles']} статей")
    print(f"📊 Марок: {stats['totalBrands']} | Ошибок: {stats['totalErrorCodes']}")
    print("=" * 80 + "\n")
    
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        # Основная БД
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "articles": all_articles,
                "indexes": {
                    "brands": brand_index,
                    "errorCodes": error_code_index,
                    "problems": problem_index,
                },
                "stats": stats,
                "lastUpdated": datetime.now().isoformat(),
                "version": "4.0",
            }, f, ensure_ascii=False, indent=2)
        
        # Справочник кодов
        with open(ERROR_CODES_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "errorCodes": ERROR_CODES,
                "count": len(ERROR_CODES),
            }, f, ensure_ascii=False, indent=2)
        
        # Справочник марок
        with open(VEHICLES_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "brands": VEHICLE_BRANDS,
                "count": len(VEHICLE_BRANDS),
            }, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
