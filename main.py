# from datetime import datetime
# import datetime
# import telebot
# from telebot import types
# from telebot.types import InputMediaPhoto
# from apscheduler.schedulers.background import BackgroundScheduler
# import database
import telebot
from telebot import types
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import database
from telebot.types import InputMediaPhoto
import threading
import time

TOKEN = "8961646222:AAENFuTWtfrX1LTRP5Pjpud7QN6RO1DVtUE"
ADMIN_ID = 5068250115

bot = telebot.TeleBot(TOKEN)

# user_data теперь хранит timestamp через datetime.now().timestamp()
user_data = {}
admin_temp = {}

# --- СПИСОК УСЛУГ ---
SERVICES = [
    {
        "name": "Установка системы замещения волос",
        "price": "8.000",
        "duration": "3 часа",
    },
    {"name": "Стрижка мужская", "price": "1.500", "duration": "1 час"},
    {"name": "Тонировка седины на голове", "price": "1.500", "duration": "30 минут"},
    {"name": "Стрижка налысо", "price": "1.000", "duration": "30 минут"},
    {"name": "Окантовка стрижки", "price": "800", "duration": "20 минут"},
    {"name": "Восковая депиляция", "price": "500", "duration": "10 минут"},
    {"name": "Ламинирование бровей", "price": "1.500", "duration": "30 минут"},
    {"name": "Оформление бровей", "price": "1.000", "duration": "40 минут"},
    {"name": "Стрижка женская", "price": "1.500", "duration": "1 час"},
    {"name": "Укладка афрокудри", "price": "3.000", "duration": "1 час 30 минут"},
    {"name": "LPG массаж лица", "price": "1.000", "duration": "30 минут"},
    {"name": "Женский массаж LPG", "price": "1.500", "duration": "50 минут"},
    {"name": "Мужской массаж LPG", "price": "от 2.000", "duration": "1 час"},
    {"name": "Укладка", "price": "700", "duration": "20 минут"},
    {"name": "Оконтовка бороды", "price": "500", "duration": "15 минут"},
    {"name": "Оформление бороды и усов", "price": "1.000", "duration": "30 минут"},
]

WELCOME_TEXT = "Привет! На связи Юлия. Твой стиль — это моя работа. ✂️\n\nЯ создаю не просто стрижки, а образ, который придает уверенности. В этом боте ты можешь записаться на удобное время, посмотреть мои работы и узнать актуальный прайс."


# --- СТАРТ ---
@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.id == ADMIN_ID:
        admin_menu()
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
def admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📅 Добавить слот", callback_data="add_slot"),
        types.InlineKeyboardButton("📝 Заявки", callback_data="list"),
    )
    bot.send_message(ADMIN_ID, "⚙️ Админ-панель", reply_markup=markup)


# --- КНОПКА «ЗАПИСАТЬСЯ» ---
@bot.callback_query_handler(func=lambda call: call.data == "start_z")
def start_booking(call):
    chat_id = call.message.chat.id
    # Заменяем time.time() на datetime.now().timestamp()
    user_data[chat_id] = {"timestamp": datetime.now().timestamp()}
    msg = bot.send_message(chat_id, "👤 Введите ваше имя:")
    bot.register_next_step_handler(msg, get_name)


# --- ЛОГИКА ЗАПИСИ ---
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

    bot.send_message(
        chat_id,
        "Отлично! Переходим к выбору услуг...",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, svc in enumerate(SERVICES):
        btn_text = f"{svc['name']} | {svc['price']} ₽ ({svc['duration']})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"svc_{i}"))

    bot.send_message(chat_id, "🎫 Выберите услугу из списка:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("svc_"))
def handle_select_service(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.send_message(
            chat_id, "⚠️ Сессия устарела. Начните запись заново через /start"
        )
        return

    svc_index = int(call.data.split("_")[1])
    selected_svc = SERVICES[svc_index]
    user_data[chat_id]["usluga"] = f"{selected_svc['name']} | {selected_svc['price']} ₽"
    user_data[chat_id]["timestamp"] = datetime.now().timestamp()

    days = database.get_available_days()
    if not days:
        bot.edit_message_text(
            "❌ Извините, свободных дней для записи пока нет.",
            chat_id,
            call.message.message_id,
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days
    ]
    markup.add(*buttons)

    bot.edit_message_text(
        "📅 Выберите желаемый день:",
        chat_id,
        call.message.message_id,
        reply_markup=markup,
    )


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

    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [types.InlineKeyboardButton(t, callback_data=f"time_{t}") for t in times]
    markup.add(*buttons)

    bot.edit_message_text(
        "🕐 Выберите удобное время:",
        chat_id,
        call.message.message_id,
        reply_markup=markup,
    )


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


# --- АДМИН: ДОБАВЛЕНИЕ СЛОТОВ ---
@bot.callback_query_handler(func=lambda call: call.data == "add_slot")
def start_add_slot(call):
    msg = bot.send_message(ADMIN_ID, "📅 Введите дату в формате ДД.ММ:")
    bot.register_next_step_handler(msg, add_slot_date)


def add_slot_date(message):
    date_str = message.text.strip()
    try:
        current_year = datetime.now().year
        input_date = datetime.strptime(f"{date_str}.{current_year}", "%d.%m.%Y")
        if input_date.date() < datetime.now().date():
            msg = bot.send_message(
                ADMIN_ID, "❌ Эта дата уже в прошлом!\nВведите дату ещё раз:"
            )
            bot.register_next_step_handler(msg, add_slot_date)
            return

        admin_temp[message.chat.id] = {"day": date_str}
        msg = bot.send_message(
            ADMIN_ID, "🕰 Введите время через запятую (напр. 10:00, 11:30):"
        )
        bot.register_next_step_handler(msg, add_slot_times)
    except ValueError:
        msg = bot.send_message(
            ADMIN_ID, "❌ Неверный формат даты. Используй ДД.ММ. Введите еще раз:"
        )
        bot.register_next_step_handler(msg, add_slot_date)


def add_slot_times(message):
    day = admin_temp[message.chat.id]["day"]
    times = [t.strip() for t in message.text.split(",")]
    added, skipped = 0, 0

    for t in times:
        if database.add_slot(day, t):
            added += 1
        else:
            skipped += 1

    bot.send_message(ADMIN_ID, f"✅ Добавлено: {added}\n⚠️ Дубликаты: {skipped}")
    admin_menu()


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


# Сброс зависших сессий через datetime
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
