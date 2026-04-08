import sqlite3
import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.command import Command

# Токен бота
TOKEN = "8554026235:AAFWr7P42yvLqtgxvrY1l_1q04Nnplv8c9I"


# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Исправлено: prymary -> primary
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()


def add_user(user_id, username, full_name):
    """Добавление пользователя в базу"""
    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        # Проверяем, есть ли уже такой пользователь
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
            # Добавляем нового пользователя
            cursor.execute(
                "INSERT INTO users (id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )
            conn.commit()
            print(f"Добавлен пользователь: {user_id} - {username}")
        else:
            print(f"Пользователь {user_id} уже существует")

    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
    finally:
        conn.close()


# Инициализируем БД при запуске
init_db()

# СОЗДАНИЕ КЛАВИАТУР
# Reply клавиатура (обычные кнопки)
reply_builder = ReplyKeyboardBuilder()
reply_builder.button(text="/start")
reply_builder.button(text="/help")
reply_builder.adjust(1)
reply_kb = reply_builder.as_markup(resize_keyboard=True)

# Inline клавиатура (кнопки под сообщением)
builder = InlineKeyboardBuilder()
builder.button(text=" Каталог", callback_data="catalog")
builder.button(text=" Помощь", callback_data="help_realtors")
builder.button(text=" Жалоба", callback_data="complaint")
builder.button(text=" Предложения", callback_data="suggestions")
builder.adjust(1)  # по одной кнопке в ряд
inline_kb = builder.as_markup()

dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Сохраняем пользователя в БД
    add_user(user_id, username, full_name)

    # Приветственное сообщение
    await message.answer(
        f"Привет, {full_name}! 👋\n\n"
        "Я Риэлтор бот. Я помогу вам найти "
        "подходящий вариант для покупки или аренды жилой площади.\n\n",
        reply_markup=reply_kb
    )

    await message.answer(
        "🏠 Пройдите по следующим выборам...\n\n"
        "Выберите действие:",
        reply_markup=inline_kb
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    help_text = """
    🤖 *Команды бота:*
    /start - начать работу
    /help - показать это сообщение

    📌 *Как пользоваться:*
    Используйте кнопки под сообщением для навигации

    💬 *По вопросам:* @nen312
    """
    await message.answer(help_text, parse_mode="Markdown")


#  ОБРАБОТЧИКИ INLINE КНОПОК
@dp.callback_query(F.data == "catalog")
async def catalog_handler(callback: CallbackQuery) -> None:
    # Обязательно отвечаем на callback
    await callback.answer("Открываю каталог...")

    # Создаем кнопку "Назад" для возврата в главное меню
    back_builder = InlineKeyboardBuilder()
    back_builder.button(text="◀️ Назад в меню", callback_data="back_to_menu")

    # Отправляем новое сообщение с каталогом
    catalog_text = """
    📚 *Каталог недвижимости*

    🏢 *Квартиры*
    • 1-комнатные от 3 500 000 ₽
    • 2-комнатные от 5 200 000 ₽
    • 3-комнатные от 7 800 000 ₽

    🏠 *Дома*
    • Таунхаусы от 6 500 000 ₽
    • Коттеджи от 9 000 000 ₽

    🏭 *Коммерческая*
    • Офисы от 2 500 000 ₽
    • Склады от 4 000 000 ₽

    Для подробной информации напишите /help
    """

    await callback.message.answer(
        catalog_text,
        parse_mode="Markdown",
        reply_markup=back_builder.as_markup()
    )


@dp.callback_query(F.data == "help_realtors")
async def help_handler(callback: CallbackQuery) -> None:
    await callback.answer("Помощь")

    help_text = """
    ❓ *Помощь и поддержка*

    Что я умею:
    • Поиск недвижимости по параметрам
    • Консультация по документам
    • Помощь в оформлении сделки
    • Расчет ипотеки

    📞 *Связаться с агентом:* @realty_agent
    """

    await callback.message.answer(help_text, parse_mode="Markdown")


@dp.callback_query(F.data == "complaint")
async def complaint_handler(callback: CallbackQuery) -> None:
    await callback.answer("Форма жалобы")

    # Создаем клавиатуру для выбора типа жалобы
    complaint_builder = InlineKeyboardBuilder()
    complaint_builder.button(text=" На риэлтора", callback_data="complaint_realtor")
    complaint_builder.button(text=" На объект", callback_data="complaint_property")
    complaint_builder.button(text=" На работу бота", callback_data="complaint_bot")
    complaint_builder.button(text="◀️ Назад", callback_data="back_to_menu")
    complaint_builder.adjust(1)

    await callback.message.answer(
        "⚠️ *Пожаловаться*\n\nВыберите тип жалобы:",
        parse_mode="Markdown",
        reply_markup=complaint_builder.as_markup()
    )


@dp.callback_query(F.data == "suggestions")
async def suggestions_handler(callback: CallbackQuery) -> None:
    await callback.answer("Форма предложений")

    await callback.message.answer(
        "💡 *Предложения и идеи*\n\n"
        "Будем рады вашим идеям по улучшению бота!\n\n"
        "Напишите их сюда: @nen312\n\n"
        "Спасибо за обратную связь! 🙏",
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery) -> None:
    """Возврат в главное меню"""
    await callback.answer("Возврат в меню")

    # Удаляем текущее сообщение
    await callback.message.delete()

    # Отправляем главное меню
    await callback.message.answer(
        "🏠 *Главное меню*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=inline_kb
    )


# Обработчики для подкатегорий жалоб
@dp.callback_query(F.data.startswith("complaint_"))
async def complaint_type_handler(callback: CallbackQuery) -> None:
    complaint_type = callback.data.split("_")[1]

    if complaint_type == "realtor":
        await callback.answer("Жалоба на риэлтора принята")
        await callback.message.edit_text(
            "Ваша жалоба на риэлтора отправлена администрации.\n"
            "Мы рассмотрим её в течение 24 часов.\n\n"
            "Спасибо за обратную связь! 🙏"
        )
    elif complaint_type == "property":
        await callback.answer("Жалоба на объект принята")
        await callback.message.edit_text(
            "Ваша жалоба на объект недвижимости отправлена.\n"
            "Мы проверим информацию и исправим неточности.\n\n"
            "Спасибо за помощь! "
        )
    else:  # bot
        await callback.answer("Жалоба на бота принята")
        await callback.message.edit_text(
            "Спасибо за обратную связь о работе бота!\n"
            "Мы обязательно учтем ваше замечание.\n\n"
            "Извините за доставленные неудобства! "
        )

    # Кнопка "Вернуться в меню"
    back_builder = InlineKeyboardBuilder()
    back_builder.button(text="◀️ Вернуться в меню", callback_data="back_to_menu")

    await callback.message.edit_reply_markup(
        reply_markup=back_builder.as_markup()
    )


# ========== ЗАПУСК БОТА ==========
async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())