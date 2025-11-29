#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 ПАРСЕР МАСТЕРСКОЙ АВТОЭЛЕКТРИКИ v3.0
Собирает ТОЛЬКО инструкции/решения, отбрасывает новости
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
    NEWS_SOURCES,
    MAX_NEWS_PER_SOURCE,
    MAX_TOTAL_NEWS,
    EXCLUDE_KEYWORDS,
    INSTRUCTION_KEYWORDS,
    ERROR_CODES,
    PROBLEM_CATEGORIES,
    OUTPUT_FILE,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("\n" + "=" * 80)
print("🔧 МАСТЕРСКАЯ АВТОЭЛЕКТРИКА v3.0 - Парсер решений")
print("=" * 80 + "\n")


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_best_text(entry) -> str:
    candidates = []
    if hasattr(entry, "content"):
        for c in entry.content:
            if getattr(c, "value", ""):
                candidates.append(c.value)
    if getattr(entry, "summary", ""):
        candidates.append(entry.summary)
    if getattr(entry, "description", ""):
        candidates.append(entry.description)
    best = max(candidates, key=len) if candidates else ""
    return clean_html(best)[:2500]


def is_instruction_not_news(title: str, summary: str, source_name: str) -> bool:
    text = (title + " " + summary).lower()

    for bad in EXCLUDE_KEYWORDS:
        if bad in text:
            return False

    # Для Drive2/YouTube достаточно любого слова из INSTRUCTION_KEYWORDS
    if "drive2" in source_name.lower() or "youtube" in source_name.lower():
        return any(k in text for k in INSTRUCTION_KEYWORDS)

    # Для остальных источников – тоже требуем хотя бы одно "инструкционное" слово
    return any(k in text for k in INSTRUCTION_KEYWORDS)


def extract_error_codes(text: str):
    upper = text.upper()
    codes = [code for code in ERROR_CODES if code in upper]
    # плюс любые паттерны P0123
    codes += re.findall(r"\b[PBUC][0-9]{4}\b", upper)
    return sorted(set(codes))


def tag_by_problem(title: str, summary: str):
    text = (title + " " + summary).lower()
    tags = []
    for cat, keywords in PROBLEM_CATEGORIES.items():
        if any(k in text for k in keywords):
            tags.append(cat)
    return tags or ["📚 Справка"]


def extract_content_type(source_name: str) -> str:
    name = source_name.lower()
    if "youtube" in name:
        return "🎬 Видео"
    if "drive2" in name:
        return "💬 Форум"
    if "лада" in name or "ladа" in name or "abw" in name:
        return "📖 Справка"
    return "📚 Статья"


def extract_image(entry):
    link = entry.get("link", "")
    if "youtube.com" in link:
        if hasattr(entry, "media_group"):
            try:
                return entry.media_group[0]["media_thumbnail"][0]["url"]
            except Exception:
                pass

    if hasattr(entry, "enclosures"):
        for enc in entry.enclosures:
            if getattr(enc, "type", "").startswith("image/"):
                return getattr(enc, "href", None)

    raw = ""
    if hasattr(entry, "content") and entry.content:
        raw = entry.content[0].value
    elif getattr(entry, "summary", ""):
        raw = entry.summary

    m = re.search(r'<img[^>]*src=["\'](.*?)["\']', raw or "")
    return m.group(1) if m else None


def parse_rss_source(source: dict):
    results = []
    name = source["name"]
    print(f"📥 {name[:55]:<55}", end=" ", flush=True)

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
                if not title:
                    continue

                if not is_instruction_not_news(title, summary, name):
                    continue

                error_codes = extract_error_codes(title + " " + summary)
                problem_tags = tag_by_problem(title, summary)
                content_type = extract_content_type(name)

                article = {
                    "title": title,
                    "summary": summary,
                    "link": entry.get("link", ""),
                    "source": name,
                    "sourceType": source.get("type", "unknown"),
                    "category": source["category"],
                    "contentType": content_type,
                    "problemTags": problem_tags,
                    "errorCodes": error_codes,
                    "image": extract_image(entry),
                    "published": entry.get("published", datetime.now().isoformat()),
                }
                results.append(article)
                count += 1
            except Exception:
                continue

        print(f"✅ {count} шт.")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:60]}")

    return results


def main() -> bool:
    all_articles = []
    print(f"Парсинг {len(NEWS_SOURCES)} источников...\n")

    for src in NEWS_SOURCES:
        all_articles.extend(parse_rss_source(src))

    all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    all_articles = all_articles[:MAX_TOTAL_NEWS]

    stats = {
        "totalArticles": len(all_articles),
        "totalSources": len({a["source"] for a in all_articles}),
    }

    print("\n" + "=" * 80)
    print("📊 Статистика:")
    print(f"✅ инструкций: {stats['totalArticles']}")
    print(f"📡 источников: {stats['totalSources']}")
    print("=" * 80 + "\n")

    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        output = {
            "articles": all_articles,
            "stats": stats,
            "lastUpdated": datetime.now().isoformat(),
            "version": "3.0",
        }
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено в {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
