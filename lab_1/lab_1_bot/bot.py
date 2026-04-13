import json
import logging
import os
import random
from pathlib import Path
from typing import Any

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Состояния диалога
START_CONFIRM, TOUR_LENGTH, INTEREST_CHOICE, RATING = range(4)

YES_BUTTON = "Да!"
SHORT_TOUR = "Короткая"
DETAILED_TOUR = "Подробная"
VALID_LENGTHS = {SHORT_TOUR, DETAILED_TOUR}

INTEREST_OPTIONS = {"История", "Сюжет", "Биография", "Живопись"}

DATA_FILE = Path(__file__).with_name("paintings.json")
ENV_FILE = Path(__file__).with_name(".env")
ENV_EXAMPLE_FILE = Path(__file__).with_name(".env.example")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def get_token() -> str:
    """Читает токен из переменных окружения или файла .env без сторонних пакетов."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        return token

    for env_path in (ENV_FILE, ENV_EXAMPLE_FILE):
        if not env_path.exists():
            continue
        with env_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == "TELEGRAM_BOT_TOKEN":
                    value = value.strip().strip('"').strip("'")
                    if value:
                        return value

    raise ValueError(
        "Не задан TELEGRAM_BOT_TOKEN в переменных окружения, .env или .env.example"
    )


def load_paintings() -> list[dict[str, Any]]:
    """Загружает данные картин из JSON-файла."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Файл с данными не найден: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as f:
        paintings = json.load(f)

    if not isinstance(paintings, list):
        raise ValueError("Некорректный формат paintings.json: ожидается список")
    return paintings


def build_tour_text(painting: dict[str, Any], interest: str) -> str:
    """Формирует заглушку описания для выбранной картины."""
    title = painting["title"]
    artist = painting["artist"]
    year = painting["year"]
    return (
        f"«{title}», {artist} ({year}) — "
        f"вот тут будет описание про {interest.lower()}."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Стартовая команда: приветствие и предложение начать экскурсию."""
    keyboard = [[YES_BUTTON]]
    await update.message.reply_text(
        "Здравствуйте! Я бот-гид по картинной галерее Русского музея.\n\n"
        "Начать экскурсию?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return START_CONFIRM


async def start_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает подтверждение начала экскурсии."""
    user_text = (update.message.text or "").strip()
    if user_text != YES_BUTTON:
        await update.message.reply_text(
            "Чтобы начать экскурсию, нажмите кнопку «Да!»."
        )
        return START_CONFIRM

    keyboard = [[SHORT_TOUR, DETAILED_TOUR]]
    await update.message.reply_text(
        "Какую экскурсию вы хотите?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return TOUR_LENGTH


async def choose_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет тип экскурсии и спрашивает интерес пользователя."""
    tour_length = (update.message.text or "").strip()
    if tour_length not in VALID_LENGTHS:
        await update.message.reply_text(
            "Пожалуйста, выберите вариант кнопкой: «Короткая» или «Подробная»."
        )
        return TOUR_LENGTH

    context.user_data["tour_length"] = tour_length

    keyboard = [["История", "Сюжет"], ["Биография", "Живопись"]]
    await update.message.reply_text(
        "Что вас интересует больше всего?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return INTEREST_CHOICE


async def choose_interest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Формирует и отправляет экскурсию из 3 случайных картин."""
    interest = (update.message.text or "").strip()
    if interest not in INTEREST_OPTIONS:
        await update.message.reply_text(
            "Выберите интерес с помощью кнопок: История, Сюжет, Биография, Живопись."
        )
        return INTEREST_CHOICE

    context.user_data["interest"] = interest

    paintings = context.application.bot_data.get("paintings", [])
    if len(paintings) < 3:
        await update.message.reply_text(
            "Недостаточно данных о картинах. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    selected = random.sample(paintings, 3)
    tour_length = context.user_data.get("tour_length", SHORT_TOUR)

    await update.message.reply_text(
        f"Отлично! Вы выбрали экскурсию: {tour_length}.",
        reply_markup=ReplyKeyboardRemove(),
    )

    for index, painting in enumerate(selected, start=1):
        text = build_tour_text(painting, interest)
        await update.message.reply_text(f"{index}. {text}")

    await update.message.reply_text(
        "Оцените экскурсию от 1 до 5 (просто отправьте цифру)."
    )
    return RATING


async def save_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Принимает оценку и предлагает начать новую экскурсию."""
    rating_text = (update.message.text or "").strip()
    if rating_text not in {"1", "2", "3", "4", "5"}:
        await update.message.reply_text("Пожалуйста, отправьте цифру от 1 до 5.")
        return RATING

    context.user_data["rating"] = int(rating_text)

    keyboard = [[YES_BUTTON]]
    await update.message.reply_text(
        "Спасибо за оценку! Готовы к новой экскурсии?\n\nНачать экскурсию?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return START_CONFIRM


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text(
        "Экскурсия завершена. Если захотите снова — отправьте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальная обработка ошибок."""
    logger.exception("Ошибка при обработке обновления: %s", context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Попробуйте еще раз или отправьте /start."
        )


def main() -> None:
    """Точка входа."""
    token = get_token()

    paintings = load_paintings()

    application = Application.builder().token(token).build()
    application.bot_data["paintings"] = paintings

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_confirm)],
            TOUR_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_length)],
            INTEREST_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_interest)],
            RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_rating)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    logger.info("Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()
