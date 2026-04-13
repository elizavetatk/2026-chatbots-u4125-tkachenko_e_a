University: [ITMO University](https://itmo.ru/ru/)
Faculty: [FICT](https://fict.itmo.ru)
Course: [Vibe Coding: AI-боты для бизнеса](https://github.com/itmo-ict-faculty/vibe-coding-for-business)
Year: 2025/2026
Group: u4125
Author: Tkachenko Elizaveta Andreevna
Lab: Lab2
Date of create: 13.04.2026
Date of finished:

# Лабораторная работа №2: Подключение бота к данным

## Описание интеграции

**Какой источник данных?**
CSV-файл с описаниями картин Русского музея.

**Почему именно этот?**
- Не требует внешних API
- Легко редактировать
- Можно быстро сгенерировать описания через LLM
- Удобная структура для выбора текста по двум параметрам (длина и интерес)

**Структура данных (CSV):**

| Колонка | Описание |
|---------|----------|
| title | Название картины |
| artist | Художник |
| short_history | Коротко об истории создания |
| short_plot | Коротко о сюжете |
| short_biography | Коротко о биографии художника |
| short_painting | Коротко о художественных приёмах |
| detailed_history | Подробно об истории |
| detailed_plot | Подробно о сюжете |
| detailed_biography | Подробно о биографии |
| detailed_painting | Подробно о живописи |

Данные были сгенерированы в самом курсоре.

Результат работы в видео: https://drive.google.com/file/d/1wXWKeJFG0MEzmmOPoCGtb5wBH9_t0ike/view?usp=drive_link
