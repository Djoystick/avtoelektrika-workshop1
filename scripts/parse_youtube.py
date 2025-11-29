#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎬 YouTube Parser v1.0 - Вытягивает реальные видео по ремонту
"""

import feedparser
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

YOUTUBE_SEARCHES = [
    "ремонт стартера",
    "замена генератора",
    "диагностика ошибок obd2",
    "как найти утечку тока",
    "замена свечей зажигания",
    "ремонт аккумулятора",
    "проверка генератора",
    "замена проводов зажигания",
    "ремонт катушки зажигания",
    "как пользоваться elm327",
]

YOUTUBE_CHANNELS = [
    ("Ильдар Авто", "UCwP0lGe7yC-v3V_q-Oq-jHw"),
    ("Гараж 54", "UCb0P2k5f77n6yGzJ6r6R78A"),
    ("В гараже у Сандро", "UCqJqV8e8t7wz_xK9y6Vq_5g"),
]

def get_video_id(link):
    try:
        if "youtube.com" in link:
            parsed = urlparse(link)
            params = parse_qs(parsed.query)
            return params.get('v', [None])[0]
    except:
        pass
    return None

def parse_youtube_search(query):
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?search_query={query.replace(' ', '+')}"
        feed = feedparser.parse(rss_url)
        
        videos = []
        for entry in feed.entries[:10]:
            try:
                video_id = get_video_id(entry.link)
                thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None
                
                video = {
                    "id": f"yt_{video_id}",
                    "title": entry.title,
                    "summary": entry.summary[:300] if hasattr(entry, 'summary') else "",
                    "link": entry.link,
                    "source": "YouTube",
                    "sourceType": "video",
                    "contentType": "🎬 Видео",
                    "category": "🎬 YouTube",
                    "published": entry.published if hasattr(entry, 'published') else datetime.now().isoformat(),
                    "image": thumbnail,
                    "type": "youtube_search"
                }
                videos.append(video)
            except:
                continue
        
        return videos
    except Exception as e:
        print(f"❌ Ошибка при парсинге поиска '{query}': {e}")
        return []

def parse_youtube_channel(channel_name, channel_id):
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(rss_url)
        
        videos = []
        for entry in feed.entries[:5]:
            try:
                video_id = get_video_id(entry.link)
                thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None
                
                video = {
                    "id": f"yt_{video_id}",
                    "title": entry.title,
                    "summary": entry.summary[:300] if hasattr(entry, 'summary') else "",
                    "link": entry.link,
                    "source": channel_name,
                    "sourceType": "video",
                    "contentType": "🎬 Видео",
                    "category": "🎬 YouTube Каналы",
                    "published": entry.published if hasattr(entry, 'published') else datetime.now().isoformat(),
                    "image": thumbnail,
                    "type": "youtube_channel"
                }
                videos.append(video)
            except:
                continue
        
        return videos
    except Exception as e:
        print(f"❌ Ошибка при парсинге канала '{channel_name}': {e}")
        return []

def main():
    all_videos = []
    
    print("🎬 YouTube Parser v1.0\n")
    
    print("📥 Парсинг поисков YouTube...")
    for search in YOUTUBE_SEARCHES:
        videos = parse_youtube_search(search)
        all_videos.extend(videos)
        if videos:
            print(f"   ✅ '{search}': {len(videos)} видео")
    
    print("\n📺 Парсинг YouTube каналов...")
    for channel_name, channel_id in YOUTUBE_CHANNELS:
        videos = parse_youtube_channel(channel_name, channel_id)
        all_videos.extend(videos)
        if videos:
            print(f"   ✅ {channel_name}: {len(videos)} видео")
    
    seen_ids = set()
    unique_videos = []
    for video in all_videos:
        if video['id'] not in seen_ids:
            seen_ids.add(video['id'])
            unique_videos.append(video)
    
    all_videos = unique_videos
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "api-cache")
    output_file = os.path.join(output_dir, "youtube-videos.json")
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "videos": all_videos,
            "count": len(all_videos),
            "lastUpdated": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Сохранено: {len(all_videos)} видео")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
