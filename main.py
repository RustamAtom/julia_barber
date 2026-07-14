from datetime import datetime, timedelta
import telebot
from telebot import types
from telebot.types import InputMediaPhoto
from apscheduler.schedulers.background import BackgroundScheduler
import database

TOKEN = "8961646222:AAENFuTWtfrX1LTRP5Pjpud7QN6RO1DVtUE"
ADMIN_ID = 5068250115

bot = telebot.TeleBot(TOKEN)

# Временные данные сессий
user_data = {}
admin_temp = {}

# Сетка времени для быстрого добавления барбером (шаг 30 минут)
HOURS_GRID = [
    "08:00",
    "08:30",
    "09:00",
    "09:30",
    "10:00",
    "10:30",
    "11:00",
    "11:30",
    "12:00",
    "12:30",
    "13:00",
    "13:30",
    "14:00",
    "14:30",
    "15:00",
    "15:30",
    "16:00",
    "16:30",
    "17:00",
    "17:30",
    "18:00",
    "18:30",
    "19:00",
    "19:30",
    "20:00",
    "20:30",
    "21:00",
]

WELCOME_TEXT = "Привет! На связи Юлия. Твой стиль — это моя работа. ✂️\n\nЯ создаю не просто стрижки, а образ, который придает уверенности. В этом боте ты можешь записаться на удобное время, посмотреть мои работы и узнать актуальный прайс."


# --- СТАРТ ---
@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.id == ADMIN_ID:
        admin_menu(message.chat.id)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🖊 Записаться", callback_data="start_z"),
            types.InlineKeyboardButton("📸 Примеры работ", callback_data="portfolio"),
        )
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=markup)


# ПРИМЕРЫ РАБОТ
@bot.callback_query_handler(func=lambda call: call.data == "portfolio")
def portfolio(call):
    try:
        media = []
        opened_files = []
        for i in range(1, 11):
            f = open(f"img{i}.jpg", "rb")
            opened_files.append(f)
            media.append(InputMediaPhoto(f))  # type: ignore

        bot.send_media_group(call.message.chat.id, media)

        for f in opened_files:
            f.close()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🖊 Записаться", callback_data="start_z"))
        bot.send_message(
            call.message.chat.id,
            "Выбирай свой стиль и бронируй время!",
            reply_markup=markup,
        )
    except FileNotFoundError:
        bot.send_message(
            call.message.chat.id,
            "📸 Фотографии работ сейчас обновляются, заходите позже!",
        )


# --- АДМИН ПАНЕЛЬ ---
def admin_menu(chat_id=ADMIN_ID):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📅 Добавить слоты", callback_data="add_slot"),
        types.InlineKeyboardButton("📝 Заявки", callback_data="list"),
    )
    bot.send_message(chat_id, "⚙️ Админ-панель", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def back_to_admin_callback(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📅 Добавить слоты", callback_data="add_slot"),
        types.InlineKeyboardButton("📝 Заявки", callback_data="list"),
    )
    bot.edit_message_text(
        "⚙️ Админ-панель",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


# --- КЛИЕНТ: ЗАПИСЬ (НАЧАЛО) ---
@bot.callback_query_handler(func=lambda call: call.data == "start_z")
def start_booking(call):
    chat_id = call.message.chat.id
    user_data[chat_id] = {"timestamp": datetime.now().timestamp()}
    msg = bot.send_message(chat_id, "👤 Введите ваше имя:")
    bot.register_next_step_handler(msg, get_name)


# --- ЛОГИКА ЗАПИСИ (КЛИЕНТ) ---
def get_name(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return

    user_data[chat_id]["name"] = message.text
    user_data[chat_id]["timestamp"] = datetime.now().timestamp()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("Поделиться номером телефона", request_contact=True)
    markup.add(btn)
    msg = bot.send_message(
        chat_id,
        "📞 Поделитесь номером телефона или введите его вручную:",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, get_phone)


def get_phone(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    user_data[chat_id]["phone"] = phone
    user_data[chat_id]["timestamp"] = datetime.now().timestamp()

    # ТВОЙ ОРИГИНАЛЬНЫЙ ФОРМАТ УСЛУГ (КЛИЕНТ ВИДИТ ВСЁ ПОЛНОСТЬЮ)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        "Установка системы замещения волос | 8.000 рублей | 3 часа",
        "Стрижка мужская | 1.500 рублей | 1 час",
        "Тонировка седины на голове | 1.500 рублей | 30 минут",
        "Стрижка налысо | 1.000 рублей | 30 минут",
        "Окантовка стрижки | 800 рублей | 20 минут",
        "Восковая депиляция | 500 рублей | 10 минут",
        "Ламинирование бровей | 1.500 рублей | 30 минут",
        "Оформление бровей | 1.000 рублей | 40 минут",
        "Стрижка женская | 1.500 рублей | 1 час",
        "Укладка афрокудри | 3.000 рублей | 1 час 30 минут",
        "LPG массаж лица | 1.000 рублей | 30 минут",
        "Женский массаж LPG | 1.500 рублей | 50 минут",
        "Мужской массаж LPG | от 2.000 рублей | 1 час",
        "Укладка | 700 рублей | 20 минут",
        "Оконтовка бороды | 500 рублей | 15 минут",
        "Оформление бороды и усов | 1.000 рублей | 30 минут",
    )
    msg = bot.send_message(
        chat_id,
        "🎫 Выберите услугу:\n<i>Внизу предоставлены услуги в формате УСЛУГА | ЦЕНА | ДЛИТЕЛЬНОСТЬ РАБОТЫ</i>",
        reply_markup=markup,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, get_service)


def get_service(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return

    user_data[chat_id]["usluga"] = message.text
    user_data[chat_id]["timestamp"] = datetime.now().timestamp()

    days = database.get_available_days()
    if not days:
        bot.send_message(
            chat_id,
            "❌ Свободных дат пока нет.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return

    # Красиво удаляем Reply-клавиатуру перед переходом на инлайн-шаг
    bot.send_message(
        chat_id,
        "Принято! Теперь выберите день...",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    # Строим инлайн-кнопки для дней
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days
    ]
    markup.add(*buttons)

    bot.send_message(chat_id, "📅 Выберите желаемый день:", reply_markup=markup)


# --- ОБРАБОТКА ВЫБОРА ДНЯ (КЛИЕНТ) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def handle_select_day(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.send_message(
            chat_id, "⚠️ Сессия устарела. Начните запись заново через /start"
        )
        return

    day = call.data.split("_")[1]
    user_data[chat_id]["day"] = day
    user_data[chat_id]["timestamp"] = datetime.now().timestamp()

    times = database.get_free_slot(day)
    if not times:
        bot.edit_message_text(
            "❌ На этот день свободного времени не осталось.",
            chat_id,
            call.message.message_id,
        )
        return

    # Строим инлайн-кнопки для времени
    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [types.InlineKeyboardButton(t, callback_data=f"time_{t}") for t in times]
    markup.add(*buttons)

    bot.edit_message_text(
        "🕐 Выберите удобное время:",
        chat_id,
        call.message.message_id,
        reply_markup=markup,
    )


# --- ЗАВЕРШЕНИЕ ЗАПИСИ (КЛИЕНТ) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def handle_select_time(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.send_message(
            chat_id, "⚠️ Сессия устарела. Начните запись заново через /start"
        )
        return

    t_val = call.data.split("_")[1]
    user_data[chat_id]["time"] = t_val
    d = user_data[chat_id]
    database.save_zayvka(
        chat_id, d["name"], d["phone"], d["usluga"], d["day"], d["time"]
    )
    database.book_slot(d["day"], d["time"])

    user_data.pop(chat_id, None)

    bot.edit_message_text(
        f"✅ <b>Вы успешно записаны!</b>\n\n"
        f"👤 Имя: {d['name']}\n"
        f"🎫 Услуга: {d['usluga']}\n"
        f"📅 Дата: {d['day']} в {d['time']}\n\n"
        f"📍 Адрес: Сочи, Тепличная улица, 71/6, квартира 29\n\n"
        f"<i>Введите команду /my_record, чтобы просмотреть или отменить запись.</i>",
        chat_id,
        call.message.message_id,
        parse_mode="HTML",
    )

    bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Новая запись!</b>\n👤 {d['name']} ({d['phone']})\n🎫 {d['usluga']}\n📅 {d['day']} в {d['time']}",
        parse_mode="HTML",
    )


# --- КЛИЕНТСКАЯ ОТМЕНА ЗАПИСИ ---
@bot.message_handler(commands=["my_record"])
def my_record(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Это команда для клиентов")
    else:
        record = database.get_active_zayvka(message.from_user.id)
        if record:
            day, time_val, usluga = record
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton(
                    "❌ Отменить запись", callback_data="cancel_my_visit"
                )
            )
            bot.send_message(
                message.chat.id,
                f"Вы записаны на {day} в {time_val}\nУслуга: {usluga}",
                reply_markup=kb,
            )
        else:
            bot.send_message(message.chat.id, "У вас нет активных записей.")


@bot.callback_query_handler(func=lambda call: call.data == "cancel_my_visit")
def handle_cancel(call):
    if database.cancel_zayvka(call.from_user.id):
        bot.edit_message_text(
            "✅ Ваша запись успешно отменена!",
            call.message.chat.id,
            call.message.message_id,
        )
        bot.send_message(
            ADMIN_ID, f"⚠️ Клиент @{call.from_user.username} отменил запись!"
        )
    else:
        bot.answer_callback_query(call.id, "Запись не найдена или уже отменена.")


# --- АДМИН: ПРОСМОТР ЗАЯВОК ---
@bot.callback_query_handler(func=lambda call: call.data == "list")
def list_zayvki(call):
    clients = database.get_all_zayvki()
    if not clients:
        bot.send_message(ADMIN_ID, "😔 Заявок нет")
    else:
        for c in clients:
            u_id, name, phone, usluga, day, time_val, status = c
            text = f"👤 {name}\n📞 {phone}\n🎫 {usluga}\n📅 {day} в {time_val}\nℹ️ {status}"
            bot.send_message(ADMIN_ID, text)


# --- АДМИН: ИНЛАЙН ДОБАВЛЕНИЕ СЛОТОВ (БЕЗ РУЧНОГО ВВОДА) ---


# Шаг 1: Показываем инлайн-кнопки с датами (ближайшие 10 дней)
@bot.callback_query_handler(func=lambda call: call.data == "add_slot")
def start_add_slot(call):
    now = datetime.now()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []

    for i in range(10):
        day_str = (now + timedelta(days=i)).strftime("%d.%m")
        buttons.append(
            types.InlineKeyboardButton(day_str, callback_data=f"adm_date_{day_str}")
        )

    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🚪 В меню", callback_data="back_to_admin"))

    bot.edit_message_text(
        "📅 Выберите дату, на которую хотите добавить свободное время:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


# Шаг 2: Показываем сетку времени и список уже добавленных слотов на выбранную дату
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_date_"))
def handle_admin_select_date(call):
    day = call.data.split("_")[2]
    admin_temp[call.message.chat.id] = {"day": day}

    existing_slots = database.get_free_slot(day)
    slots_text = ", ".join(existing_slots) if existing_slots else "нет свободных слотов"

    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [
        types.InlineKeyboardButton(t, callback_data=f"adm_add_time_{t}")
        for t in HOURS_GRID
    ]
    markup.add(*buttons)
    markup.add(
        types.InlineKeyboardButton("🔙 К выбору даты", callback_data="add_slot"),
        types.InlineKeyboardButton("✅ Готово", callback_data="back_to_admin"),
    )

    bot.edit_message_text(
        f"📅 <b>Дата: {day}</b>\n"
        f"🟢 Сейчас активны слоты: <code>{slots_text}</code>\n\n"
        f"👇 Нажмите на время ниже, чтобы добавить его в расписание:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML",
    )


# Шаг 3: Добавляем время по клику и мгновенно обновляем интерфейс
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_add_time_"))
def handle_admin_add_time(call):
    chat_id = call.message.chat.id
    if chat_id not in admin_temp or "day" not in admin_temp[chat_id]:
        bot.answer_callback_query(
            call.id, "❌ Сессия устарела. Выберите дату заново.", show_alert=True
        )
        return

    day = admin_temp[chat_id]["day"]
    time_val = call.data.split("_")[3]

    added = database.add_slot(day, time_val)

    if added:
        bot.answer_callback_query(call.id, f"✅ Слот {time_val} добавлен!")
    else:
        bot.answer_callback_query(call.id, f"⚠️ Слот {time_val} уже есть.")

    # Мгновенно обновляем список слотов на экране, сохраняя сетку кнопок
    existing_slots = database.get_free_slot(day)
    slots_text = ", ".join(existing_slots) if existing_slots else "нет свободных слотов"

    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [
        types.InlineKeyboardButton(t, callback_data=f"adm_add_time_{t}")
        for t in HOURS_GRID
    ]
    markup.add(*buttons)
    markup.add(
        types.InlineKeyboardButton("🔙 К выбору даты", callback_data="add_slot"),
        types.InlineKeyboardButton("✅ Готово", callback_data="back_to_admin"),
    )

    try:
        bot.edit_message_text(
            f"📅 <b>Дата: {day}</b>\n"
            f"🟢 Сейчас активны слоты: <code>{slots_text}</code>\n\n"
            f"👇 Нажмите на время ниже, чтобы добавить его в расписание:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
    except Exception:
        pass


# --- АВТОМАТИЧЕСКИЕ ЗАДАЧИ ---
def reminders():
    clients = database.get_clients_for_reminder(datetime.now())
    for user_id, name, time_val in clients:
        try:
            bot.send_message(
                user_id,
                f"⏰ Напоминание! Вы записаны на {time_val}\n🚶Приходите по адресу Сочи, Тепличная улица, 71/6, квартира 29",
            )
        except Exception:
            pass


def clear_old():
    database.clear_old_records()


def auto_cancel_sessions():
    now = datetime.now().timestamp()
    expired_users = []
    for chat_id, data in list(user_data.items()):
        if now - data.get("timestamp", now) > 600:
            expired_users.append(chat_id)

    for chat_id in expired_users:
        user_data.pop(chat_id, None)
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
            bot.send_message(
                chat_id,
                "⚠️ Запись отменена из-за неактивности. Вы можете начать процесс заново с помощью команды /start.",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        except Exception:
            pass


scheduler = BackgroundScheduler()
scheduler.add_job(reminders, "interval", minutes=1)
scheduler.add_job(clear_old, "interval", minutes=10)
scheduler.add_job(auto_cancel_sessions, "interval", minutes=1)
scheduler.start()


if __name__ == "__main__":
    print("🚀 Бот запущен и готов разрывать!")
    bot.polling(non_stop=True)
