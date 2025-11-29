#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 DB Builder v2.0 - Объединяет YouTube + Habr + Форумы + Community
"""

import json
import os
import glob
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_community_solutions():
    solutions = []
    solutions_dir = os.path.join(PROJECT_ROOT, "db", "solutions")
    
    if not os.path.exists(solutions_dir):
        return solutions
    
    md_files = glob.glob(os.path.join(solutions_dir, "**", "*.md"), recursive=True)
    
    for md_file in md_files:
        if "README" in md_file:
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                lines = content.split('\n')
                title = lines[0].replace('# ', '').strip() if lines else "Unknown"
                
                author = "Unknown"
                date_added = datetime.fromtimestamp(os.path.getmtime(md_file)).isoformat()
                marques = []
                
                for line in lines[1:10]:
                    if "Автор:" in line:
                        parts = line.split("**")
                        author = parts[1] if len(parts) > 1 else "Unknown"
                    if "Дата добавления:" in line:
                        parts = line.split("**")
                        date_added = parts[1] if len(parts) > 1 else date_added
                    if "Марки авто:" in line:
                        parts = line.split("**")
                        if len(parts) > 1:
                            marques = [m.strip() for m in parts[1].split(",")]
                
                summary = '\n'.join([l for l in lines[10:20] if l.strip()])[:400]
                
                rel_path = os.path.relpath(md_file, solutions_dir)
                category = rel_path.split('/')[0].replace('_', ' ').title()
                
                solution = {
                    "id": f"community_{os.path.splitext(os.path.basename(md_file))[0]}",
                    "title": title,
                    "summary": summary,
                    "link": f"#{os.path.splitext(os.path.basename(md_file))[0]}",
                    "source": f"{author} (Community)",
                    "sourceType": "article",
                    "contentType": "📖 Статья",
                    "category": f"🤝 {category}",
                    "published": date_added,
                    "image": None,
                    "type": "community",
                    "brands": marques
                }
                solutions.append(solution)
        except Exception as e:
            print(f"⚠️  Ошибка при чтении {md_file}: {e}")
            continue
    
    return solutions

def build_db():
    print("🔧 DB Builder v2.0\n")
    
    all_items = []
    
    # YouTube
    print("📥 Загружаю YouTube видео...")
    yt_data = load_json_file(os.path.join(PROJECT_ROOT, "api-cache", "youtube-videos.json"))
    if yt_data and yt_data.get("videos"):
        all_items.extend(yt_data.get("videos", []))
        print(f"   ✅ {len(yt_data.get('videos', []))} видео")
    else:
        print(f"   ⚠️  0 видео")
    
    # Habr
    print("📥 Загружаю Habr статьи...")
    habr_data = load_json_file(os.path.join(PROJECT_ROOT, "api-cache", "habr-articles.json"))
    if habr_data and habr_data.get("articles"):
        all_items.extend(habr_data.get("articles", []))
        print(f"   ✅ {len(habr_data.get('articles', []))} статей")
    else:
        print(f"   ⚠️  0 статей")
    
    # Форумы RSS
    print("📥 Загружаю посты из форумов (RSS)...")
    forums_rss_data = load_json_file(os.path.join(PROJECT_ROOT, "api-cache", "forums-rss.json"))
    if forums_rss_data and forums_rss_data.get("posts"):
        all_items.extend(forums_rss_data.get("posts", []))
        print(f"   ✅ {len(forums_rss_data.get('posts', []))} постов")
    else:
        print(f"   ⚠️  0 постов RSS")
    
    # Форумы HTML
    print("📥 Загружаю посты из HTML форумов...")
    forums_html_data = load_json_file(os.path.join(PROJECT_ROOT, "api-cache", "forums-html.json"))
    if forums_html_data and forums_html_data.get("posts"):
        all_items.extend(forums_html_data.get("posts", []))
        print(f"   ✅ {len(forums_html_data.get('posts', []))} вопросов")
    else:
        print(f"   ⚠️  0 вопросов HTML")
    
    # Community Solutions
    print("📥 Загружаю решения сообщества...")
    community = load_community_solutions()
    all_items.extend(community)
    print(f"   ✅ {len(community)} решений")
    
    if not all_items:
        print("\n⚠️  НЕ НАЙДЕНО НИКАКИХ МАТЕРИАЛОВ!")
        return False
    
    # Строим индексы
    print("\n🔨 Строю индексы...")
    
    category_index = {}
    source_index = {}
    type_index = {}
    brand_index = {}
    
    for item in all_items:
        cat = item.get("category", "Без категории")
        src = item.get("source", "Unknown")
        typ = item.get("type", "unknown")
        
        if cat not in category_index:
            category_index[cat] = []
        category_index[cat].append(item["id"])
        
        if src not in source_index:
            source_index[src] = []
        source_index[src].append(item["id"])
        
        if typ not in type_index:
            type_index[typ] = []
        type_index[typ].append(item["id"])
        
        for brand in item.get("brands", []):
            if brand not in brand_index:
                brand_index[brand] = []
            brand_index[brand].append(item["id"])
    
    all_items.sort(key=lambda x: x.get("published", ""), reverse=True)
    
    db = {
        "articles": all_items,
        "indexes": {
            "categories": category_index,
            "sources": source_index,
            "types": type_index,
            "brands": brand_index,
        },
        "stats": {
            "totalArticles": len(all_items),
            "totalCategories": len(category_index),
            "totalSources": len(source_index),
            "youtube": len([a for a in all_items if a.get("type") in ["youtube_search", "youtube_channel"]]),
            "habr": len([a for a in all_items if a.get("type") == "habr"]),
            "forums": len([a for a in all_items if a.get("type") in ["forum_rss", "forum_html"]]),
            "community": len([a for a in all_items if a.get("type") == "community"]),
        },
        "lastUpdated": datetime.now().isoformat(),
        "version": "5.2-forums"
    }
    
    output_file = os.path.join(PROJECT_ROOT, "db.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ ГОТОВО!")
    print(f"   📊 Всего материалов: {db['stats']['totalArticles']}")
    print(f"   🎬 YouTube видео: {db['stats']['youtube']}")
    print(f"   📚 Habr статьи: {db['stats']['habr']}")
    print(f"   💬 Посты из форумов: {db['stats']['forums']}")
    print(f"   🤝 Community решения: {db['stats']['community']}")
    
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if build_db() else 1)
