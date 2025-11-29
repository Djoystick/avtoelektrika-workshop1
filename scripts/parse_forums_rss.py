#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💬 Forums RSS Parser v1.0 - Вытягивает вопросы и ответы из форумов с RSS
"""

import feedparser
import json
import os
from datetime import datetime

FORUM_FEEDS = [
    # Русские форумы
    {
        "name": "Drive2 - Электрика",
        "url": "https://www.drive2.ru/r/rss/electrics/",
        "category": "💬 Drive2",
        "lang": "ru"
    },
    {
        "name": "Drive2 - Поломки",
        "url": "https://www.drive2.ru/r/rss/breakdown/",
        "category": "💬 Drive2",
        "lang": "ru"
    },
    
    # Иностранные форумы
    {
        "name": "E46Zone - BMW Forum",
        "url": "https://www.e46zone.com/forum/rss/2-e46-zone-forum-posts.xml/",
        "category": "🅱️ BMW Forum",
        "lang": "en"
    },
    {
        "name": "Reddit - Autos",
        "url": "https://www.reddit.com/r/Autos/.rss",
        "category": "🔗 Reddit",
        "lang": "en"
    },
    {
        "name": "FocusFanatics",
        "url": "https://www.focusfanatics.com/forums/-/index.rss",
        "category": "🚙 FocusFanatics",
        "lang": "en"
    },
]

def parse_forum_feed(forum_info):
    """Парсит RSS ленту форума"""
    try:
        feed = feedparser.parse(forum_info["url"])
        
        posts = []
        for entry in feed.entries[:25]:
            try:
                post = {
                    "id": f"forum_{forum_info['name'].replace(' ', '_')}_{entry.id.split('/')[-1] if hasattr(entry, 'id') else len(posts)}",
                    "title": entry.title,
                    "summary": entry.summary[:500] if hasattr(entry, 'summary') else "",
                    "link": entry.link,
                    "source": forum_info["name"],
                    "sourceType": "forum",
                    "contentType": "💬 Форум",
                    "category": forum_info["category"],
                    "published": entry.published if hasattr(entry, 'published') else datetime.now().isoformat(),
                    "image": None,
                    "type": "forum_rss",
                    "language": forum_info["lang"]
                }
                posts.append(post)
            except:
                continue
        
        return posts
    except Exception as e:
        print(f"❌ Ошибка при парсинге '{forum_info['name']}': {e}")
        return []

def main():
    all_posts = []
    
    print("💬 Forums RSS Parser v1.0\n")
    
    for forum_info in FORUM_FEEDS:
        posts = parse_forum_feed(forum_info)
        all_posts.extend(posts)
        
        if posts:
            print(f"✅ {forum_info['name']}: {len(posts)} постов")
        else:
            print(f"⚠️  {forum_info['name']}: 0 постов")
    
    seen_ids = set()
    unique_posts = []
    for post in all_posts:
        if post['id'] not in seen_ids:
            seen_ids.add(post['id'])
            unique_posts.append(post)
    
    all_posts = unique_posts
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "api-cache")
    output_file = os.path.join(output_dir, "forums-rss.json")
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "posts": all_posts,
            "count": len(all_posts),
            "lastUpdated": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Сохранено: {len(all_posts)} постов из форумов")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
