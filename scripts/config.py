#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 МАСТЕРСКАЯ АВТОЭЛЕКТРИКА v5.0
ИСТОЧНИКИ: Форумы, Видео, Бесплатные базы (CarMD Free, OBD-Codes)
"""

import os

MAX_NEWS_PER_SOURCE = 60
MAX_TOTAL_NEWS = 4000

NEWS_SOURCES = [
    # ===== БЕСПЛАТНЫЕ БАЗЫ ЗНАНИЙ (Аналоги платных API) =====
    {"name": "OBD-Codes.com", "url": "https://www.obd-codes.com/rss/", "category": "💻 Коды ошибок", "type": "guide"},
    {"name": "AutoZone - Repair Guides (RSS)", "url": "https://www.autozone.com/diy/repair-guides/rss", "category": "🛠️ Инструкции", "type": "guide"},
    {"name": "2CarPros - Вопросы", "url": "https://www.2carpros.com/questions.rss", "category": "🆘 Решения", "type": "forum"},
    {"name": "Engine-Codes.com", "url": "https://www.engine-codes.com/rss.php", "category": "💻 Коды ошибок", "type": "guide"},

    # ===== ФОРУМЫ МАРОК (Живой опыт) =====
    {"name": "VAG-COM (Ross-Tech)", "url": "https://forums.ross-tech.com/index.php?forums/-/index.rss", "category": "💻 VAG Диагностика", "type": "forum"},
    {"name": "BMW E46 Zone", "url": "https://www.e46zone.com/forum/rss/2-e46-zone-forum-posts.xml/", "category": "🅱️ BMW", "type": "forum"},
    {"name": "Ford Focus Club", "url": "https://www.focusfanatics.com/forums/-/index.rss", "category": "🚙 Ford", "type": "forum"},
    {"name": "Toyota Nation", "url": "https://www.toyotanation.com/forums/-/index.rss", "category": "🅣 Toyota", "type": "forum"},

    # ===== DRIVE2 (Лучшее на русском) =====
    {"name": "Drive2 - Электрика", "url": "https://www.drive2.ru/r/rss/electrics/", "category": "⚡ Электрика", "type": "forum"},
    {"name": "Drive2 - Поломки", "url": "https://www.drive2.ru/r/rss/breakdown/", "category": "🆘 Решения", "type": "forum"},
    {"name": "Drive2 - DIY", "url": "https://www.drive2.ru/r/rss/diy/", "category": "🛠️ Инструкции", "type": "guide"},

    # ===== YOUTUBE (Самое наглядное) =====
    {"name": "YT - Диагностика", "url": "https://www.youtube.com/feeds/videos.xml?search_query=диагностика+авто+своими+руками", "category": "💻 Диагностика", "type": "video"},
    {"name": "YT - Ремонт стартера", "url": "https://www.youtube.com/feeds/videos.xml?search_query=ремонт+стартера+разборка", "category": "⚡ Электрика", "type": "video"},
    {"name": "YT - Ремонт генератора", "url": "https://www.youtube.com/feeds/videos.xml?search_query=ремонт+генератора+замена+щеток", "category": "⚡ Электрика", "type": "video"},
    {"name": "YT - Поиск утечки", "url": "https://www.youtube.com/feeds/videos.xml?search_query=поиск+утечки+тока+мультиметром", "category": "⚡ Электрика", "type": "video"},
]

# Словарь марок для привязки статей
VEHICLE_BRANDS = {
    "lada": {"name": "LADA", "models": ["Vesta", "Granta", "Priora", "Kalina", "Niva", "Largus"]},
    "toyota": {"name": "Toyota", "models": ["Camry", "Corolla", "RAV4", "Land Cruiser", "Prado"]},
    "volkswagen": {"name": "Volkswagen", "models": ["Polo", "Golf", "Passat", "Tiguan", "Touareg"]},
    "bmw": {"name": "BMW", "models": ["X5", "X3", "3-Series", "5-Series", "E39", "E46", "E90"]},
    "ford": {"name": "Ford", "models": ["Focus", "Mondeo", "Fiesta", "Kuga", "Fusion"]},
    "hyundai": {"name": "Hyundai", "models": ["Solaris", "Creta", "Tucson", "Santa Fe", "Sonata"]},
    "kia": {"name": "Kia", "models": ["Rio", "Sportage", "Sorento", "Ceed", "Optima"]},
    "nissan": {"name": "Nissan", "models": ["Qashqai", "X-Trail", "Almera", "Juke", "Terrano"]},
    "renault": {"name": "Renault", "models": ["Logan", "Duster", "Sandero", "Kaptur", "Arkana"]},
    "chevrolet": {"name": "Chevrolet", "models": ["Cruze", "Lacetti", "Niva", "Aveo", "Tahoe"]},
}

# Ключевые слова для фильтрации "мусора"
EXCLUDE_KEYWORDS = [
    "купил", "продал", "помыл", "переобулся", "выборы", "политика", "дтп", 
    "путешествие", "отпуск", "погода", "прикол", "юмор", "обзор нового", 
    "цены на авто", "кредит", "страховка"
]

# Слова-маркеры полезного контента
INSTRUCTION_KEYWORDS = [
    "ремонт", "замена", "инструкция", "как снять", "как поставить", 
    "диагностика", "ошибка", "код", "не работает", "сломался", 
    "починил", "решение", "своими руками", "отчет", "схема", 
    "распиновка", "предохранители", "реле", "проводка"
]

# Коды ошибок (для индексации)
ERROR_CODES = {
    "P0300": "Множественные пропуски зажигания",
    "P0420": "Эффективность катализатора ниже порога",
    "P0171": "Слишком бедная смесь",
    "P0172": "Слишком богатая смесь",
    "P0301": "Пропуски зажигания в 1 цилиндре",
    "P0302": "Пропуски зажигания в 2 цилиндре",
    "P0303": "Пропуски зажигания в 3 цилиндре",
    "P0304": "Пропуски зажигания в 4 цилиндре",
    "C0035": "Датчик скорости колеса (левый передний)",
    "U0100": "Потеря связи с блоком управления двигателем",
    "B0001": "Подушка безопасности водителя (разрыв)",
}

PROBLEM_CATEGORIES = {
    "🆘 Не заводится": ["не заводится", "стартер щелкает", "нет запуска", "не крутит"],
    "⚡ Электрика": ["генератор", "аккумулятор", "проводка", "кз", "утечка тока", "лампочк"],
    "🔧 Двигатель": ["двигатель", "троит", "глохнет", "плавают обороты", "вибрация"],
    "💻 Диагностика": ["сканер", "elm327", "obd", "ошибка", "код", "check engine"],
    "🌡️ Климат": ["печка", "кондиционер", "вентилятор", "не греет", "холодно"],
    "🛑 Тормоза": ["abs", "esp", "датчик скорости", "тормоз"],
}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "db.json")
VEHICLES_FILE = os.path.join(PROJECT_ROOT, "vehicles.json")
ERROR_CODES_FILE = os.path.join(PROJECT_ROOT, "error-codes.json")
