#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📚 Habr Parser v1.0 - Статьи по DIY и электронике
"""

import feedparser
import json
import os
from datetime import datetime

HABR_FEEDS = [
    ("DIY", "https://habr.com/ru/rss/hubs/diy/articles/"),
    ("Электроника", "https://habr.com/ru/rss/hubs/electronics/articles/"),
]

def parse_habr_feed(name, url):
    try:
        feed = feedparser.parse(url)
        
        articles = []
        for entry in feed.entries[:20]:
            try:
                article_id = entry.link.split('/')[-2] if entry.link else str(len(articles))
                
                article = {
                    "id": f"habr_{article_id}",
                    "title": entry.title,
                    "summary": entry.summary[:400] if hasattr(entry, 'summary') else "",
                    "link": entry.link,
                    "source": "Habr.com",
                    "sourceType": "article",
                    "contentType": "📚 Статья",
                    "category": f"📚 {name}",
                    "published": entry.published if hasattr(entry, 'published') else datetime.now().isoformat(),
                    "image": None,
                    "type": "habr"
                }
                articles.append(article)
            except:
                continue
        
        return articles
    except Exception as e:
        print(f"❌ Ошибка при парсинге '{name}': {e}")
        return []

def main():
    all_articles = []
    
    print("📚 Habr Parser v1.0\n")
    
    for name, url in HABR_FEEDS:
        articles = parse_habr_feed(name, url)
        all_articles.extend(articles)
        if articles:
            print(f"✅ {name}: {len(articles)} статей")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "api-cache")
    output_file = os.path.join(output_dir, "habr-articles.json")
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "articles": all_articles,
            "count": len(all_articles),
            "lastUpdated": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Сохранено: {len(all_articles)} статей")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
