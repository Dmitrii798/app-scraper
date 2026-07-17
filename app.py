# ============================================================
# app.py - Веб-приложение для парсинга отзывов App Store
# ============================================================

import streamlit as st
import pandas as pd
from io import BytesIO
import time
from parser import fetch_reviews, parse_appstore_url

# Настройка страницы
st.set_page_config(
    page_title="Парсер отзывов App Store",
    page_icon="🍏",
    layout="wide"
)

# Заголовок
st.title("🍏 Парсер отзывов из App Store")
st.markdown("---")

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки")

    # Ввод ссылки
    app_url = st.text_input(
        "🔗 Ссылка на приложение",
        placeholder="https://apps.apple.com/us/app/spotify/id324684580",
        help="Вставьте ссылку на приложение из App Store"
    )

    # Примеры ссылок
    with st.expander("📌 Примеры ссылок"):
        st.code("https://apps.apple.com/us/app/spotify/id324684580", language="text")
        st.code("https://apps.apple.com/ru/app/яндекс-карты/id313877526", language="text")
        st.code("https://apps.apple.com/gb/app/whatsapp-messenger/id310633997", language="text")

    # Количество отзывов
    max_reviews = st.slider(
        "📊 Количество отзывов",
        min_value=10,
        max_value=1000,
        value=100,
        step=10,
        help="Чем больше отзывов, тем дольше будет выполняться парсинг"
    )

    # Кнопка запуска
    start_button = st.button(
        "🚀 Начать парсинг",
        type="primary",
        use_container_width=True
    )

    st.markdown("---")
    st.caption("💡 Приложение собирает отзывы из открытого API Apple")

# Основная область
if start_button:
    if not app_url:
        st.error("❌ Пожалуйста, введите ссылку на приложение!")
        st.stop()

    # Проверяем ссылку
    country, app_id = parse_appstore_url(app_url)
    if country is None:
        st.error("❌ Неверная ссылка! Проверьте формат.")
        st.stop()

    # Создаем контейнеры для прогресса
    progress_container = st.container()
    status_container = st.container()
    result_container = st.container()

    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()


    # Функция для обновления прогресса
    def update_progress(message, progress):
        status_text.text(message)
        progress_bar.progress(progress)


    # Запускаем парсинг
    with st.spinner("🔄 Парсинг запущен..."):
        try:
            # Отображаем информацию о приложении
            with status_container:
                st.info(f"📱 Приложение: **{app_url}**")
                st.info(f"🌍 Страна: **{country.upper()}** | 🆔 ID: **{app_id}**")

            # Запускаем парсинг
            df, filename = fetch_reviews(
                app_url=app_url,
                max_reviews=max_reviews,
                progress_callback=update_progress
            )

            # Убираем индикатор прогресса
            progress_container.empty()

            # Показываем результат
            with result_container:
                st.success(f"✅ Собрано **{len(df)}** отзывов!")

                # Показываем статистику
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("📊 Всего отзывов", len(df))

                with col2:
                    avg_rating = df['rating'].astype(float).mean() if df['rating'].str.isnumeric().any() else 0
                    st.metric("⭐ Средний рейтинг", f"{avg_rating:.1f}")

                with col3:
                    unique_users = df['userName'].nunique()
                    st.metric("👤 Уникальных пользователей", unique_users)

                # Таблица с отзывами
                st.subheader("📋 Первые 10 отзывов")
                st.dataframe(
                    df.head(10),
                    use_container_width=True,
                    height=300
                )

                # График распределения оценок
                if df['rating'].str.isnumeric().any():
                    st.subheader("📊 Распределение оценок")
                    rating_counts = df['rating'].value_counts().sort_index()
                    st.bar_chart(rating_counts)

                # Кнопка скачивания
                csv_buffer = BytesIO()
                df.to_csv(csv_buffer, sep=";", index=False, encoding="utf-8-sig")
                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label="📥 Скачать CSV файл",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )

                # Информация о файле
                st.caption(f"💾 Файл: **{filename}** | Размер: **{len(csv_data) / 1024:.1f} KB**")

        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            st.stop()

else:
    # Инструкция при первом открытии
    st.info("👈 Введите ссылку на приложение в боковой панели и нажмите 'Начать парсинг'")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📌 Как это работает

        1. **Вставьте ссылку** на приложение
        2. **Выберите количество** отзывов
        3. **Нажмите "Начать парсинг"**
        4. **Скачайте** готовый CSV файл
        """)

    with col2:
        st.markdown("""
        ### 📊 Что вы получите

        - Имя пользователя
        - Рейтинг (⭐)
        - Заголовок отзыва
        - Текст отзыва
        - Дата отзыва
        - Версия приложения
        """)