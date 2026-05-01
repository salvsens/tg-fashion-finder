# tg-fashion-finder

Проект по Научно-исследовательскому семинару «Введение в облачные технологии». Система автоматического поиска, агрегации и интеллектуальной обработки fashion-предложений из Telegram-каналов.

**Бот в Telegram:** [@fashion_daemon_bot](https://t.me/fashion_daemon_bot)

## Состав команды
* [**Багаев Леонид**](https://github.com/salvsens) — Core, Bot, ML Logic
* [**Камышников Святослав**](https://github.com/SvytosDosvidos) — ML Logic
* [**Бутенко Владислав**](https://github.com/vbutenko-dev) — Crawler

---

## Возможности

* **Поиск и навигация:**
    * `/start` — приветствие и онбординг.
    * `/search <запрос>` — полнотекстовый поиск по базе товаров с выводом карточек (до 5 позиций).
    * Интерактивная система «Лайков» для сохранения айтемов в избранное.
* **Автоматизация и парсинг:**
    * Мониторинг Telegram-каналов в реальном времени по «белому списку» (Whitelist).
    * Сбор текста, прямых ссылок на посты и изображений товаров.
* **Интеллектуальная обработка (ML Logic):**
    * **Advanced Price Extraction**: распознавание цен в разных форматах (например, «15.5к», «2000р», «$100») и валютах.
    * **NLP Pipeline**: токенизация и стемминг (NLTK) для корректного поиска с учетом морфологии русского языка.
    * **Fuzzy Matching**: нечеткое сопоставление категорий (обувь, куртки и т.д.), устойчивое к опечаткам и сленгу.
    * Автоматическое определение статуса «Продано» при анализе текста.

---

## Архитектура

Проект разделен на логические модули, взаимодействующие через единую базу данных:

* **Bot** — интерфейс взаимодействия с пользователем и фоновый планировщик задач.
* **Crawler** — сервис сбора контента из внешних Telegram-источников.
* **ML Logic** — модуль очистки данных и классификации товаров по категориям.
* **Core** — центральное ядро системы, отвечающее за управление БД SQLite.

**Схема пути даных**
[![Схема пути данных](https://mermaid.ink/img/pako:eNpFUd1rgzAQ_1fCPW1g26i1mWEMpm1fZgfbOgZTH0K9VUGTEiPrB_3fF23p7uG4-33cHdwJNqpA4LDVYleS5D2TxMZzusYaLdaQuBRSYt3mZDR6IlEaa_Fbo84vwmhA4_Tu4y2pDJJ5dH9lYvLYU_N0lZBEbasNJ6_J-mWy7I7Hw1efbsJet_jfGClzpRYDtUw_W9Rk0qLQmzIHxx5bFcB_RN2iAw3qRvQ9nHpXBqbEBjPgttRYdPsMMnm2rp2Q30o1wI3urE-rblvepnS7QhicV6I_4YZqlAXqWHXSAHepT4cpwE-wtz3zxzPPnVHXDWhIXcYcOFj4gY1p4E0p9fww9IKpd3bgOCymY8YCZoV-4IVWw3wHsKiM0qvLF4ZnnP8AZrN4gg?type=png)](https://mermaid.live/edit#pako:eNpFUd1rgzAQ_1fCPW1g26i1mWEMpm1fZgfbOgZTH0K9VUGTEiPrB_3fF23p7uG4-33cHdwJNqpA4LDVYleS5D2TxMZzusYaLdaQuBRSYt3mZDR6IlEaa_Fbo84vwmhA4_Tu4y2pDJJ5dH9lYvLYU_N0lZBEbasNJ6_J-mWy7I7Hw1efbsJet_jfGClzpRYDtUw_W9Rk0qLQmzIHxx5bFcB_RN2iAw3qRvQ9nHpXBqbEBjPgttRYdPsMMnm2rp2Q30o1wI3urE-rblvepnS7QhicV6I_4YZqlAXqWHXSAHepT4cpwE-wtz3zxzPPnVHXDWhIXcYcOFj4gY1p4E0p9fww9IKpd3bgOCymY8YCZoV-4IVWw3wHsKiM0qvLF4ZnnP8AZrN4gg)

**Схема обработки сырого текста**
[![Схема обработки сырого текста](https://mermaid.ink/img/pako:eNptlM1u2kAQx19ltVFEIpkP24DLBqFKTXppm0sjVWrgYOI1WDE2so1CEkVK2rQ9RFWUqqccGrWH3iqRDwQhQF5h_SZ9hM6uMQ0kSIa1mf9_fjM763285RoUE2za7s5WXfcCtLFadhB8FhcR-8Huw0PWZTdw3cE1Yn3WReFR-AEWd-Epgn_4T_iR9SBgzK4i7Zat-_4qNZEf6DWKTMu2yYJZMCU_8NxtShZUVZ2skzuWEdSJ0myvzGkNPdBjqfmk1NB9QPb0XYJyKAf6yOFtAHUsbbJv4SdAugHqMbtFwNxlA86O2D0biyI6lWWUTJZAQZvyZrFaYn_4U3aPZALVh19YX8QNWKeYrpaKVS9d8mjKb1UJr_kGQh-05Ssbinw91pd4k47CE9GUgYSeQzQkhYA-RHeE4rYS4cbQgDCFUWZgFID5xY0muXqsE34GNOh_H7GforLhxPt6Crr-euMVYB6CRY9dcsQJKCcAvmjDYMlNOBzUygYIsoxBNILwx4TKlFCdIVSB8BwMO7xsMDqGRIOYckr0srW3t_uOfxEO0YX-dkV3oRkzCLBEQs8ruxY84MOGj3hUwbPmGJtLMKyXYquvHuwJO2PficjNfouHUbXn89bLlXh4-Nhf8IfQz254GJ7A4IgejqC0YxE_jAoDoyUxSacAPYpSglNks9bWG02bwlBZpQQ7B9VYtIbjQb1o3dqm6O_F2QUKUg2a9nWbJoppq1RByVQ8kDNOSuQ0eOTkgNO8VJmRqk9JYZoSCMITft2l_ryBGrdDnMYIRxLOUtR2cbAfnthpxVIMHC9UcZJXsIRrnmVgYuq2TyXcoF5D5_d4n9uUcVCnDVrGBJYeNVrtMi47B6Bq6s57121gEngt0Hluq1afurSaYE5XLb3m6f9DqGNQ74XbcgJMZEUTHpjs4zbcPlNSeUXO5QvZDFzZjCLhXUyymVQmp2TlgpLXsnJGyx9IeE9kzaQ0LafJmqbmlALEaKqEqWEFrvcmenWKN-jBP8HydDM?type=png)](https://mermaid.live/edit#pako:eNptlM1u2kAQx19ltVFEIpkP24DLBqFKTXppm0sjVWrgYOI1WDE2so1CEkVK2rQ9RFWUqqccGrWH3iqRDwQhQF5h_SZ9hM6uMQ0kSIa1mf9_fjM763285RoUE2za7s5WXfcCtLFadhB8FhcR-8Huw0PWZTdw3cE1Yn3WReFR-AEWd-Epgn_4T_iR9SBgzK4i7Zat-_4qNZEf6DWKTMu2yYJZMCU_8NxtShZUVZ2skzuWEdSJ0myvzGkNPdBjqfmk1NB9QPb0XYJyKAf6yOFtAHUsbbJv4SdAugHqMbtFwNxlA86O2D0biyI6lWWUTJZAQZvyZrFaYn_4U3aPZALVh19YX8QNWKeYrpaKVS9d8mjKb1UJr_kGQh-05Ssbinw91pd4k47CE9GUgYSeQzQkhYA-RHeE4rYS4cbQgDCFUWZgFID5xY0muXqsE34GNOh_H7GforLhxPt6Crr-euMVYB6CRY9dcsQJKCcAvmjDYMlNOBzUygYIsoxBNILwx4TKlFCdIVSB8BwMO7xsMDqGRIOYckr0srW3t_uOfxEO0YX-dkV3oRkzCLBEQs8ruxY84MOGj3hUwbPmGJtLMKyXYquvHuwJO2PficjNfouHUbXn89bLlXh4-Nhf8IfQz254GJ7A4IgejqC0YxE_jAoDoyUxSacAPYpSglNks9bWG02bwlBZpQQ7B9VYtIbjQb1o3dqm6O_F2QUKUg2a9nWbJoppq1RByVQ8kDNOSuQ0eOTkgNO8VJmRqk9JYZoSCMITft2l_ryBGrdDnMYIRxLOUtR2cbAfnthpxVIMHC9UcZJXsIRrnmVgYuq2TyXcoF5D5_d4n9uUcVCnDVrGBJYeNVrtMi47B6Bq6s57121gEngt0Hluq1afurSaYE5XLb3m6f9DqGNQ74XbcgJMZEUTHpjs4zbcPlNSeUXO5QvZDFzZjCLhXUyymVQmp2TlgpLXsnJGyx9IeE9kzaQ0LafJmqbmlALEaKqEqWEFrvcmenWKN-jBP8HydDM)

---

## Стек технологий

* **Python 3.11** — основной язык разработки.
* **Aiogram 3.x** — асинхронный фреймворк для реализации Bot API.
* **Aiosqlite** — асинхронное управление базой данных SQLite.
* **NLTK (Natural Language Toolkit)** — лингвистический анализ и предобработка текста.
* **FuzzyWuzzy** — алгоритмы нечеткого сравнения строк.
* **Asyncio** — управление конкурентными задачами и планировщиком.

---

## Конфигурация

Параметры системы задаются через файл `.env`.

| Переменная | Описание | Значение по умолчанию |
| :--- | :--- | :--- |
| `BOT_TOKEN` | Токен Telegram-бота из BotFather | обязательно |
| `CHANNEL_IDS`| ID обрабатываемых каналов | обязательно |

---

## Структура проекта

```text
bot/                # Интерфейс пользователя и запуск (main.py)
crawler/            # Модуль парсинга Telegram-каналов
ml_logic/           # Модуль NLP и обработки цен (NLTK, FuzzyWuzzy)
core/               # Ядро системы и логика запросов к БД
data/               # Хранилище базы данных SQLite (*.db)
```

---

## Технические детали

* **Безопасность**: Реализовано экранирование HTML-тегов для предотвращения ошибок рендеринга в Telegram.
* **Отказоустойчивость**: Использование фоновых воркеров (Scheduler) позволяет обогащать данные без блокировки основного потока обработки сообщений.
* **ML-процессинг**: Система поддерживает автоматическую фильтрацию аномальных значений цен и очистку текста от эмодзи и ссылок.
