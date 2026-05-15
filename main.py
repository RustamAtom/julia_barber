from pickletools import float8

import telebot
from telebot import types
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import database
from telebot.types import InputMediaPhoto

TOKEN = "8961646222:AAENFuTWtfrX1LTRP5Pjpud7QN6RO1DVtUE"
ADMIN_ID = 5068250115

bot = telebot.TeleBot(TOKEN)
user_data = {}
admin_temp = {}

# --- ТЕКСТЫ ---
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
        # Если файла нет, просто отправь текст (но аватарку-то мы сделали!)
        # try:
        #     with open("watermarked_img_4037167827574499669.png", "rb") as photo:
        #         bot.send_photo(message.chat.id, photo, caption=WELCOME_TEXT, reply_markup=markup)
        # except:
        #     bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=markup)
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=markup)


# ПРИМЕРЫ РАБОТ (Требование №5)
@bot.callback_query_handler(func=lambda call: call.data == "portfolio")
def portfolio(call):
    # Чтобы не было красных линий, сначала открываем файлы,
    # а потом передаем их в список
    try:
        # Убедись, что эти файлы РЕАЛЬНО лежат в папке с ботом
        f1 = open("img1.jpg", "rb")
        f2 = open("img2.jpg", "rb")
        f3 = open("img3.jpg", "rb")
        f4 = open("img4.jpg", "rb")
        f5 = open("img5.jpg", "rb")
        f6 = open("img6.jpg", "rb")
        f7 = open("img7.jpg", "rb")
        f8 = open("img8.jpg", "rb")
        f9 = open("img9.jpg", "rb")
        f10 = open("img10.jpg", "rb")

        media = [
            InputMediaPhoto(f1),  # type: ignore
            InputMediaPhoto(f2),  # type: ignore
            InputMediaPhoto(f3),  # type: ignore
            InputMediaPhoto(f4),  # type: ignore
            InputMediaPhoto(f5),  # type: ignore
            InputMediaPhoto(f6),  # type: ignore
            InputMediaPhoto(f7),  # type: ignore
            InputMediaPhoto(f8),  # type: ignore
            InputMediaPhoto(f9),  # type: ignore
            InputMediaPhoto(f10),  # type: ignore
        ]

        bot.send_media_group(call.message.chat.id, media)  # type: ignore

        # Важно: после отправки файлы лучше закрыть, но для простоты можно оставить так.
        # Если хочешь совсем по красоте — кнопка записи после фото:
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


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "start_z":
        msg = bot.send_message(call.message.chat.id, "👤 Введите ваше имя:")
        bot.register_next_step_handler(msg, get_name)

    elif call.data == "add_slot":
        msg = bot.send_message(ADMIN_ID, "📅 Введите дату (например: 15.05):")
        bot.register_next_step_handler(msg, add_slot_date)

    elif call.data == "list":
        clients = database.get_all_zayvki()
        if not clients:
            bot.send_message(ADMIN_ID, "😔 Заявок нет")
        else:
            for c in clients:
                u_id, name, phone, usluga, day, time, status = c
                text = f"👤 {name}\n📞 {phone}\n🎫 {usluga}\n📅 {day} в {time}\nℹ️ {status}"
                bot.send_message(ADMIN_ID, text)


# --- ЛОГИКА ЗАПИСИ ---
def get_name(message):
    user_data[message.chat.id] = {"name": message.text}
    msg = bot.send_message(message.chat.id, "📞 Введите номер телефона:")
    bot.register_next_step_handler(msg, get_phone)


def get_phone(message):
    user_data[message.chat.id]["phone"] = message.text
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
        message.chat.id,
        "🎫 Выберите услугу:\n<i>Внизу предоставлены услуги в формате УСЛУГА | ЦЕНА | ПРОДОЛЖИТЕЛЬНОСТЬ</i>",
        reply_markup=markup,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, get_service)


def get_service(message):
    user_data[message.chat.id]["usluga"] = message.text
    days = database.get_available_days()
    if not days:
        bot.send_message(
            message.chat.id,
            "❌ Свободных дат пока нет.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(*days)  # Кнопки дней (Требование №1 исправлено)
    msg = bot.send_message(message.chat.id, "📅 Выберите день:", reply_markup=markup)
    bot.register_next_step_handler(msg, get_day)


def get_day(message):
    user_data[message.chat.id]["day"] = message.text
    times = database.get_free_slot(message.text)
    if not times:
        bot.send_message(message.chat.id, "❌ На этот день всё занято.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    markup.add(*times)  # Кнопки времени (Требование №1 исправлено)
    msg = bot.send_message(message.chat.id, "🕐 Выберите время:", reply_markup=markup)
    bot.register_next_step_handler(msg, finish)


def finish(message):
    chat_id = message.chat.id
    user_data[chat_id]["time"] = message.text
    d = user_data[chat_id]

    database.save_zayvka(
        chat_id, d["name"], d["phone"], d["usluga"], d["day"], d["time"]
    )
    database.book_slot(d["day"], d["time"])

    bot.send_message(
        chat_id,
        "✅ Вы успешно записаны!\n🚶Приходите по адресу Сочи, Тепличная улица, 71/6, квартира 29\n<i>Введите команду <b>my_record</b>, чтобы посмотреть свою запись и отменить (если нужно)</i>",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML",
    )
    bot.send_message(
        ADMIN_ID, f"🔔 Новая запись: {d['name']} на {d['day']} {d['time']}"
    )


# --- АДМИН: ДОБАВЛЕНИЕ СЛОТОВ ---
def add_slot_date(message):
    date_str = message.text.strip()
    try:
        # Проверка на прошедшую дату (Требование №2)
        current_year = datetime.now().year
        input_date = datetime.strptime(f"{date_str}.{current_year}", "%d.%m.%Y")
        if input_date.date() < datetime.now().date():
            bot.send_message(ADMIN_ID, "❌ Эта дата уже в прошлом!")
            return

        admin_temp[message.chat.id] = {"day": date_str}
        msg = bot.send_message(
            ADMIN_ID, "🕰 Введите время через запятую (напр. 10:00, 11:30):"
        )
        bot.register_next_step_handler(msg, add_slot_times)
    except:
        bot.send_message(ADMIN_ID, "❌ Неверный формат даты. Используй ДД.ММ")


def add_slot_times(message):
    day = admin_temp[message.chat.id]["day"]
    times = [t.strip() for t in message.text.split(",")]
    added, skipped = 0, 0

    for t in times:
        if database.add_slot(day, t):  # Требование №4 (проверка дублей в БД)
            added += 1
        else:
            skipped += 1

    bot.send_message(ADMIN_ID, f"✅ Добавлено: {added}\n⚠️ Дубликаты: {skipped}")
    admin_menu()


@bot.message_handler(commands=["my_record"])
def my_record(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Это команда для клиентов")
    else:
        record = database.get_active_zayvka(message.from_user.id)
        if record:
            day, time, usluga = record
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton(
                    "❌ Отменить запись", callback_data="cancel_my_visit"
                )
            )
            bot.send_message(
                message.chat.id,
                f"Вы записаны на {day} в {time}\nУслуга: {usluga}",
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
        # Уведомление барберу (вставь свой ID)
        bot.send_message(
            ADMIN_ID, f"⚠️ Клиент @{call.from_user.username} отменил запись!"
        )
    else:
        bot.answer_callback_query(call.id, "Запись не найдена или уже отменена.")


def reminders():
    clients = database.get_clients_for_reminder(datetime.now())
    for user_id, name, time in clients:
        try:
            bot.send_message(
                user_id,
                f"⏰ Напоминание! Вы записаны на {time}\n🚶Приходите по адресу Сочи, Тепличная улица, 71/6, квартира 29",
            )
        except:
            pass


def clear_old():
    database.clear_old_records()


scheduler = BackgroundScheduler()
scheduler.add_job(reminders, "interval", minutes=1)
scheduler.add_job(clear_old, "interval", minutes=10)
scheduler.start()


if __name__ == "__main__":
    print("🚀 Бот запущен!")
    bot.polling(non_stop=True)
