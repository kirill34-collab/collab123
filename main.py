import sqlite3
import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.command import Command


TOKEN = ""


def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()


    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')


    cursor.execute('''
    CREATE TABLE IF NOT EXISTS properties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT CHECK(type IN ('buy', 'rent_daily', 'rent_long')),
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
        description TEXT,
        contact TEXT,
        location TEXT,
        price TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()


def add_user(user_id, username, full_name):

    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
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


def add_property(user_id, prop_type, description, contact, location, price):

    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO properties 
               (user_id, type, description, contact, location, price) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, prop_type, description, contact, location, price)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Ошибка при добавлении объявления: {e}")
        return None
    finally:
        conn.close()


def get_properties_by_type(prop_type, status='active'):

    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, description, contact, location, price, status, user_id 
               FROM properties 
               WHERE type = ? AND status = ?
               ORDER BY created_at DESC""",
            (prop_type, status)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении объявлений: {e}")
        return []
    finally:
        conn.close()


def get_property_by_id(prop_id):

    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, type, description, contact, location, price, status, user_id 
               FROM properties WHERE id = ?""",
            (prop_id,)
        )
        return cursor.fetchone()
    except Exception as e:
        print(f"Ошибка при получении объявления: {e}")
        return None
    finally:
        conn.close()


def update_property_status(prop_id, new_status):

    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE properties SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, prop_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении статуса: {e}")
        return False
    finally:
        conn.close()



init_db()


reply_builder = ReplyKeyboardBuilder()
reply_builder.button(text="/start")
reply_builder.button(text="/Contact")
reply_builder.button(text="/My_ads")
reply_builder.button(text="/add_ad")
reply_builder.adjust(2)
reply_kb = reply_builder.as_markup(resize_keyboard=True)

builder = InlineKeyboardBuilder()
builder.button(text=" Каталог", callback_data="catalog")
builder.button(text=" Жалоба", callback_data="complaint")
builder.button(text=" Предложения", callback_data="suggestions")
builder.adjust(1)
inline_kb = builder.as_markup()

dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


user_states = {}


@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    add_user(user_id, username, full_name)

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


@dp.message(Command("Contact"))
async def command_contact_handler(message: Message) -> None:
    contact_text = """
*Связаться с администратором*

📞 *Телефон:* +79600493455
💬 *Telegram:* @nen312

Мы всегда рады помочь вам! 🤝
    """
    await message.answer(contact_text, parse_mode="Markdown")


@dp.message(Command("My_ads"))
async def command_my_ads_handler(message: Message) -> None:

    user_id = message.from_user.id

    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, type, description, status, price, location 
               FROM properties 
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            (user_id,)
        )
        ads = cursor.fetchall()

        if not ads:
            await message.answer(
                "📭 У вас пока нет объявлений.\n\n"
                "Создайте новое объявление через команду /add_ad!"
            )
            return

        await message.answer(f"📋 *Ваши объявления ({len(ads)})*", parse_mode="Markdown")

        for ad in ads:
            ad_id, ad_type, description, status, price, location = ad
            status_emoji = "✅" if status == "active" else "❌"
            status_text = "Активно" if status == "active" else "Неактивно"
            type_names = {
                "buy": "🏠 Покупка",
                "rent_daily": "🏨 Аренда посуточно",
                "rent_long": "🏘️ Аренда надолго"
            }

            ad_text = f"""
*{type_names.get(ad_type, ad_type)}* #{ad_id}
Статус: {status_emoji} *{status_text}*
💰 Цена: {price} ₽
📍 Локация: {location}
📝 Описание: {description[:150]}...
            """

            control_builder = InlineKeyboardBuilder()

            if status == "active":
                control_builder.button(text=" Деактивировать", callback_data=f"deactivate_{ad_id}")
            else:
                control_builder.button(text=" Активировать", callback_data=f"activate_{ad_id}")

            control_builder.button(text=" Удалить", callback_data=f"delete_ad_{ad_id}")
            control_builder.adjust(1)

            await message.answer(ad_text, parse_mode="Markdown", reply_markup=control_builder.as_markup())

    except Exception as e:
        print(f"Ошибка при получении объявлений: {e}")
        await message.answer("❌ Произошла ошибка при загрузке объявлений")
    finally:
        conn.close()


@dp.message(Command("add_ad"))
async def command_add_ad_handler(message: Message) -> None:
    """Начало создания объявления"""
    user_id = message.from_user.id

    if user_id in user_states:
        await message.answer(
            "⚠️ Вы уже создаете объявление.\n"
            "Завершите текущее создание или отмените его через /cancel"
        )
        return

    type_builder = InlineKeyboardBuilder()
    type_builder.button(text="🏠 Купить", callback_data="create_buy")
    type_builder.button(text="🏨 Снять посуточно", callback_data="create_rent_daily")
    type_builder.button(text="🏘️ Снять надолго", callback_data="create_rent_long")
    type_builder.button(text="❌ Отмена", callback_data="cancel_create")
    type_builder.adjust(1)

    await message.answer(
        "📝 *Создание нового объявления*\n\n"
        "Выберите тип услуги:",
        parse_mode="Markdown",
        reply_markup=type_builder.as_markup()
    )


@dp.message(Command("cancel"))
async def command_cancel_handler(message: Message) -> None:
    """Отмена создания объявления"""
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        await message.answer("✅ Создание объявления отменено")
    else:
        await message.answer("ℹ️ У вас нет активных процессов")


@dp.callback_query(F.data.startswith("create_"))
async def create_ad_type_handler(callback: CallbackQuery) -> None:

    user_id = callback.from_user.id
    prop_type = callback.data.split("_")[1]

    if prop_type == "cancel":
        if user_id in user_states:
            del user_states[user_id]
        await callback.answer("Создание объявления отменено")
        await callback.message.delete()
        await callback.message.answer("🏠 Главное меню:", reply_markup=inline_kb)
        return


    user_states[user_id] = {
        "step": "description",
        "type": prop_type,
        "data": {}
    }

    type_names = {
        "buy": "🏠 Покупка",
        "rent_daily": "🏨 Аренда посуточно",
        "rent_long": "🏘️ Аренда надолго"
    }

    await callback.answer(f"Выбран тип: {type_names.get(prop_type, prop_type)}")
    await callback.message.edit_text(
        f"📝 *Шаг 1 из 4: Описание*\n\n"
        f"Вы выбрали: {type_names.get(prop_type, prop_type)}\n\n"
        f"Введите подробное описание вашего предложения:\n"
        f"(Например: количество комнат, площадь, этаж, состояние и т.д.)",
        parse_mode="Markdown"
    )


@dp.message(F.text)
async def handle_text_messages(message: Message) -> None:

    user_id = message.from_user.id


    if user_id not in user_states:
        return

    state = user_states[user_id]
    step = state["step"]

    if step == "description":
        state["data"]["description"] = message.text
        state["step"] = "price"

        await message.answer(
            f"📝 *Шаг 2 из 4: Цена*\n\n"
            f"Введите стоимость в рублях:\n"
            f"(Например: 5000000 или 15000)\n\n"
            f"*Для отмены введите:* /cancel",
            parse_mode="Markdown"
        )

    elif step == "price":
        try:
            price = int(message.text.replace(" ", "").replace(",", ""))
            state["data"]["price"] = str(price)
            state["step"] = "location"

            await message.answer(
                f"📝 *Шаг 3 из 4: Местоположение*\n\n"
                f"Введите адрес объекта:\n"
                f"(Например: г. Москва, ул. Тверская, д. 15)",
                parse_mode="Markdown"
            )
        except ValueError:
            await message.answer("❌ Пожалуйста, введите число (только цифры)")

    elif step == "location":
        state["data"]["location"] = message.text
        state["step"] = "contact"

        await message.answer(
            f"📝 *Шаг 4 из 4: Контактная информация*\n\n"
            f"Введите контактный телефон или другой способ связи:",
            parse_mode="Markdown"
        )

    elif step == "contact":
        state["data"]["contact"] = message.text


        prop_id = add_property(
            user_id,
            state["type"],
            state["data"]["description"],
            state["data"]["contact"],
            state["data"]["location"],
            state["data"]["price"]
        )


        del user_states[user_id]

        type_names = {
            "buy": "🏠 Покупка",
            "rent_daily": "🏨 Аренда посуточно",
            "rent_long": "🏘️ Аренда надолго"
        }

        if prop_id:
            await message.answer(
                f"✅ *Объявление успешно создано!*\n\n"
                f"📋 ID объявления: {prop_id}\n"
                f"📌 Тип: {type_names.get(state['type'], state['type'])}\n"
                f"💰 Цена: {state['data']['price']} ₽\n"
                f"📍 Локация: {state['data']['location']}\n"
                f"📞 Контакт: {state['data']['contact']}\n\n"
                f"📝 Описание:\n{state['data']['description']}\n\n"
                f"Вы можете управлять им через /My_ads",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при создании объявления. Попробуйте позже.",
                parse_mode="Markdown"
            )


@dp.callback_query(F.data == "catalog")
async def catalog_handler(callback: CallbackQuery) -> None:
    await callback.answer("Открываю каталог...")

    catalog_builder = InlineKeyboardBuilder()
    catalog_builder.button(text="🏠 Купить", callback_data="view_buy")
    catalog_builder.button(text="🏨 Снять посуточно", callback_data="view_rent_daily")
    catalog_builder.button(text="🏘️ Снять надолго", callback_data="view_rent_long")
    catalog_builder.button(text="➕ Создать объявление", callback_data="create_ad")
    catalog_builder.button(text="◀️ Назад", callback_data="back_to_menu")
    catalog_builder.adjust(1)

    await callback.message.answer(
        "📋 *Каталог услуг*\n\nВыберите категорию или создайте новое объявление:",
        parse_mode="Markdown",
        reply_markup=catalog_builder.as_markup()
    )


@dp.callback_query(F.data == "create_ad")
async def create_ad_from_catalog_handler(callback: CallbackQuery) -> None:
    """Создание нового объявления из каталога"""
    user_id = callback.from_user.id

    if user_id in user_states:
        await callback.answer("⚠️ Вы уже создаете объявление")
        return

    await callback.answer("Начинаем создание объявления")
    await callback.message.delete()

    type_builder = InlineKeyboardBuilder()
    type_builder.button(text="🏠 Купить", callback_data="create_buy")
    type_builder.button(text="🏨 Снять посуточно", callback_data="create_rent_daily")
    type_builder.button(text="🏘️ Снять надолго", callback_data="create_rent_long")
    type_builder.button(text="❌ Отмена", callback_data="cancel_create")
    type_builder.adjust(1)

    await callback.message.answer(
        "📝 *Создание нового объявления*\n\n"
        "Выберите тип услуги:",
        parse_mode="Markdown",
        reply_markup=type_builder.as_markup()
    )


@dp.callback_query(F.data.startswith("view_"))
async def view_properties_handler(callback: CallbackQuery) -> None:

    prop_type = callback.data.split("_")[1]

    type_names = {
        "buy": "🏠 Покупка",
        "rent_daily": "🏨 Аренда посуточно",
        "rent_long": "🏘️ Аренда надолго"
    }

    properties = get_properties_by_type(prop_type)

    if not properties:
        await callback.answer("Нет активных объявлений")

        back_builder = InlineKeyboardBuilder()
        back_builder.button(text="◀️ Назад в каталог", callback_data="catalog")

        await callback.message.edit_text(
            f"{type_names.get(prop_type, prop_type)}\n\n"
            "📭 К сожалению, активных объявлений в этой категории нет.\n\n"
            "Вы можете создать свое объявление через /add_ad",
            parse_mode="Markdown",
            reply_markup=back_builder.as_markup()
        )
        return

    await callback.answer(f"Показываю {len(properties)} объявлений")


    for i, prop in enumerate(properties):
        prop_id, description, contact, location, price, status, user_id = prop

        ad_text = f"""
*{type_names.get(prop_type, prop_type)}* #{prop_id}

📍 *Локация:* {location}
💰 *Цена:* {price} ₽
📞 *Контакт:* {contact}

📝 *Описание:*
{description}

Статус: ✅ Активно
        """


        ad_builder = InlineKeyboardBuilder()
        ad_builder.button(text="📞 Связаться с продавцом", callback_data=f"contact_seller_{prop_id}")

        if i < len(properties) - 1:
            ad_builder.button(text="➡️ Следующее", callback_data=f"view_next_{prop_type}_{i + 1}")

        ad_builder.button(text="◀️ Назад в каталог", callback_data="catalog")
        ad_builder.adjust(1)

        await callback.message.answer(ad_text, parse_mode="Markdown", reply_markup=ad_builder.as_markup())


@dp.callback_query(F.data.startswith("view_next_"))
async def view_next_property_handler(callback: CallbackQuery) -> None:

    data = callback.data.split("_")
    prop_type = data[2]
    index = int(data[3])

    properties = get_properties_by_type(prop_type)

    if index >= len(properties):
        await callback.answer("Это последнее объявление")
        return

    prop = properties[index]
    prop_id, description, contact, location, price, status, user_id = prop

    type_names = {
        "buy": "🏠 Покупка",
        "rent_daily": "🏨 Аренда посуточно",
        "rent_long": "🏘️ Аренда надолго"
    }

    ad_text = f"""
*{type_names.get(prop_type, prop_type)}* #{prop_id}

📍 *Локация:* {location}
💰 *Цена:* {price} ₽
📞 *Контакт:* {contact}

📝 *Описание:*
{description}

Статус: ✅ Активно
    """

    ad_builder = InlineKeyboardBuilder()
    ad_builder.button(text="📞 Связаться с продавцом", callback_data=f"contact_seller_{prop_id}")

    if index < len(properties) - 1:
        ad_builder.button(text="➡️ Следующее", callback_data=f"view_next_{prop_type}_{index + 1}")

    ad_builder.button(text="◀️ Назад в каталог", callback_data="catalog")
    ad_builder.adjust(1)

    await callback.message.answer(ad_text, parse_mode="Markdown", reply_markup=ad_builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("contact_seller_"))
async def contact_seller_handler(callback: CallbackQuery) -> None:

    prop_id = int(callback.data.split("_")[2])
    property_info = get_property_by_id(prop_id)

    if property_info:
        prop_id, prop_type, description, contact, location, price, status, user_id = property_info

        await callback.answer("📞 Контакт продавца:")
        await callback.message.answer(
            f"📞 *Контакт продавца*\n\n"
            f"Для объявления #{prop_id}:\n\n"
            f"*{contact}*\n\n"
            f"Вы можете связаться по указанному контакту.",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Объявление не найдено")


@dp.callback_query(F.data.startswith("activate_"))
async def activate_ad_handler(callback: CallbackQuery) -> None:

    prop_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    prop = get_property_by_id(prop_id)
    if not prop or prop[7] != user_id:
        await callback.answer("❌ У вас нет прав на это действие")
        return

    success = update_property_status(prop_id, "active")
    if success:
        await callback.answer("✅ Объявление активировано")
        await callback.message.delete()
    else:
        await callback.answer("❌ Ошибка при активации")


@dp.callback_query(F.data.startswith("deactivate_"))
async def deactivate_ad_handler(callback: CallbackQuery) -> None:

    prop_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    prop = get_property_by_id(prop_id)
    if not prop or prop[7] != user_id:
        await callback.answer("❌ У вас нет прав на это действие")
        return

    success = update_property_status(prop_id, "inactive")
    if success:
        await callback.answer("🔴 Объявление деактивировано")
        await callback.message.delete()
    else:
        await callback.answer("❌ Ошибка при деактивации")


@dp.callback_query(F.data.startswith("delete_ad_"))
async def delete_ad_handler(callback: CallbackQuery) -> None:

    prop_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    prop = get_property_by_id(prop_id)
    if not prop or prop[7] != user_id:
        await callback.answer("❌ У вас нет прав на это действие")
        return


    success = update_property_status(prop_id, "inactive")
    if success:
        await callback.answer("🗑️ Объявление удалено")
        await callback.message.delete()
    else:
        await callback.answer("❌ Ошибка при удалении")


@dp.callback_query(F.data == "cancel_create")
async def cancel_create_handler(callback: CallbackQuery) -> None:

    user_id = callback.from_user.id
    if user_id in user_states:
        del user_states[user_id]

    await callback.answer("Создание объявления отменено")
    await callback.message.delete()
    await callback.message.answer("🏠 Главное меню:", reply_markup=inline_kb)


@dp.callback_query(F.data == "complaint")
async def complaint_handler(callback: CallbackQuery) -> None:
    await callback.answer("Форма жалобы")

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
        "📝 Напишите их сюда: @nen312\n\n"
        "Спасибо за обратную связь! 🎉",
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery) -> None:
    await callback.answer("Возврат в меню")
    await callback.message.delete()

    await callback.message.answer(
        "🏠 *Главное меню*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=inline_kb
    )


@dp.callback_query(F.data.startswith("complaint_"))
async def complaint_type_handler(callback: CallbackQuery) -> None:
    complaint_type = callback.data.split("_")[1]

    messages = {
        "realtor": {
            "answer": "Жалоба на риэлтора принята",
            "text": "Ваша жалоба на риэлтора отправлена администрации.\n"
                    "Мы рассмотрим её в течение 24 часов.\n\n"
                    "Спасибо за обратную связь! "
        },
        "property": {
            "answer": "Жалоба на объект принята",
            "text": "Ваша жалоба на объект недвижимости отправлена.\n"
                    "Мы проверим информацию и исправим неточности.\n\n"
                    "Спасибо за помощь! 🤝"
        },
        "bot": {
            "answer": "Жалоба на бота принята",
            "text": "Спасибо за обратную связь о работе бота!\n"
                    "Мы обязательно учтем ваше замечание.\n\n"
                    "Извините за доставленные неудобства! "
        }
    }

    if complaint_type in messages:
        await callback.answer(messages[complaint_type]["answer"])
        await callback.message.edit_text(messages[complaint_type]["text"])

    back_builder = InlineKeyboardBuilder()
    back_builder.button(text="◀️ Вернуться в меню", callback_data="back_to_menu")

    await callback.message.edit_reply_markup(
        reply_markup=back_builder.as_markup()
    )


async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())