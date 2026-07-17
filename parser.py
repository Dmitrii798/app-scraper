# ============================================================
# parser.py - Логика парсинга отзывов из App Store
# ============================================================

import re
import time
import random
import requests
import pandas as pd
from typing import List, Dict, Optional, Tuple

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/json",
}


def parse_appstore_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Извлекает страну и ID приложения из ссылки"""
    pattern = r"apps\.apple\.com/([a-z]{2})/.*/id(\d+)"
    match = re.search(pattern, url)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def fetch_reviews(app_url: str, max_reviews: int = 500, progress_callback=None) -> Tuple[pd.DataFrame, str]:
    """
    Собирает отзывы из App Store

    Args:
        app_url: Ссылка на приложение
        max_reviews: Максимальное количество отзывов
        progress_callback: Функция для обновления прогресса в UI

    Returns:
        DataFrame с отзывами и имя файла
    """

    # Извлекаем страну и ID
    country, app_id = parse_appstore_url(app_url)

    if country is None:
        raise ValueError("Неверная ссылка App Store!")

    reviews = []
    page = 1

    while len(reviews) < max_reviews:
        # Формируем URL для текущей страницы
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                break

            data = response.json()

        except Exception as e:
            print(f"Ошибка: {e}")
            break

        # Проверяем наличие данных
        if "feed" not in data:
            break

        entries = data["feed"].get("entry", [])

        if not entries:
            break

        # Фильтруем отзывы (первый элемент служебный)
        current_reviews = [item for item in entries if "author" in item]

        if not current_reviews:
            break

        # Обрабатываем каждый отзыв
        for item in current_reviews:
            if len(reviews) >= max_reviews:
                break

            review_text = item.get("content", {}).get("label", "").strip()

            if not review_text:
                continue

            reviews.append({
                "userName": item.get("author", {}).get("name", {}).get("label", ""),
                "rating": item.get("im:rating", {}).get("label", ""),
                "title": item.get("title", {}).get("label", ""),
                "review": review_text,
                "date": item.get("updated", {}).get("label", ""),
                "version": item.get("im:version", {}).get("label", "")
            })

        # Обновляем прогресс
        if progress_callback:
            progress = min(len(reviews) / max_reviews, 1.0)
            progress_callback(f"Собрано {len(reviews)} отзывов", progress)

        page += 1

        # Задержка между запросами
        time.sleep(random.uniform(2.0, 3.0))

    if not reviews:
        raise ValueError("Отзывы не найдены!")

    # Создаем DataFrame
    df = pd.DataFrame(reviews, columns=["userName", "rating", "title", "review", "date", "version"])

    # Генерируем имя файла
    filename = f"appstore_reviews_{app_id}_{country}.csv"

    return df, filename