#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💬 Forums HTML Parser v1.0 - Вытягивает вопросы и ответы через HTML парсинг
"""

import json
import os
from datetime import datetime
from urllib.request import urlopen
from urllib.parse import urljoin
import re

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

def parse_2carpros():
    """Парсит 2CarPros.com (простой парсинг)"""
    posts = []
    
    if not HAS_BS4:
        return posts
    
    try:
        url = "https://www.2carpros.com/questions/"
        response = urlopen(url, timeout=10)
        soup = BeautifulSoup(response.read(), 'html.parser')
        
        # Ищем вопросы на странице
        questions = soup.find_all('div', class_='question-item')
        
        for q in questions[:20]:
            try:
                title_elem = q.find('a', class_='question-title')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = urljoin(url, title_elem.get('href', ''))
                summary = q.find('p', class_='question-snippet')
                summary_text = summary.get_text(strip=True)[:300] if summary else ""
                
                post = {
                    "id": f"forum_2carpros_{len(posts)}",
                    "title": title,
                    "summary": summary_text,
                    "link": link,
                    "source": "2CarPros.com",
                    "sourceType": "forum",
                    "contentType": "💬 Форум",
                    "category": "🔧 2CarPros",
                    "published": datetime.now().isoformat(),
                    "image": None,
                    "type": "forum_html",
                    "language": "en"
                }
                posts.append(post)
            except:
                continue
        
        return posts
    except Exception as e:
        print(f"❌ Ошибка при парсинге 2CarPros: {e}")
        return []

def main():
    all_posts = []
    
    print("💬 Forums HTML Parser v1.0\n")
    
    if not HAS_BS4:
        print("⚠️  Beautiful Soup не установлен!")
        print("    GitHub Actions автоматически установит его")
        print("    HTML парсинг будет пропущен в этом запуске")
    else:
        print("📥 Парсинг 2CarPros.com...")
        posts = parse_2carpros()
        all_posts.extend(posts)
        if posts:
            print(f"   ✅ {len(posts)} вопросов")
        else:
            print(f"   ⚠️  0 вопросов")
    
    if not all_posts:
        print("\n⚠️  HTML парсинг не дал результатов")
        return True  # Не считаем это ошибкой
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "api-cache")
    output_file = os.path.join(output_dir, "forums-html.json")
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "posts": all_posts,
            "count": len(all_posts),
            "lastUpdated": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Сохранено: {len(all_posts)} постов из HTML форумов")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
