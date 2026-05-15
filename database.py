import sqlite3
from datetime import datetime

DB_NAME = "user.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients(
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            usluga TEXT,
            day TEXT,
            time TEXT,
            status TEXT DEFAULT 'active'
        )
        """)
        # UNIQUE(day, time) — это твоя броня от дублей (Требование №4)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            time TEXT,
            is_free INTEGER DEFAULT 1,
            UNIQUE(day, time)
        )
        """)
        conn.commit()


def add_slot(day, time):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO slots(day, time, is_free) VALUES (?, ?, 1)", (day, time)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_available_days():
    """Показывает только те дни, где есть хотя бы одно свободное окно (Требование №3)"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT day FROM slots WHERE is_free=1 ORDER BY day ASC"
        )
        return [row[0] for row in cursor.fetchall()]


def get_free_slot(day):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT time FROM slots WHERE day=? AND is_free=1 ORDER BY time ASC", (day,)
        )
        return [row[0] for row in cursor.fetchall()]


def save_zayvka(user_id, name, phone, usluga, day, time):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO clients VALUES (?, ?, ?, ?, ?, ?, 'active')",
            (user_id, name, phone, usluga, day, time),
        )
        conn.commit()


def book_slot(day, time):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE slots SET is_free=0 WHERE day=? AND time=?", (day, time))
        conn.commit()


def free_slot(day, time):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE slots SET is_free=1 WHERE day=? AND time=?", (day, time))
        conn.commit()


def cancel_zayvka(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Сначала узнаем, какой день и время были у клиента, чтобы освободить слот
        cursor.execute(
            "SELECT day, time FROM clients WHERE user_id=? AND status='active'",
            (user_id,),
        )
        record = cursor.fetchone()

        if record:
            day, time = record
            # 1. Помечаем заявку как отмененную
            cursor.execute(
                "UPDATE clients SET status='cancelled' WHERE user_id=?", (user_id,)
            )
            # 2. Освобождаем слот в таблице slots
            cursor.execute(
                "UPDATE slots SET is_free=1 WHERE day=? AND time=?", (day, time)
            )
            conn.commit()
            return True
        return False


def get_active_zayvka(user_id):
    """Специально для кнопки 'Моя запись'"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT day, time, usluga FROM clients WHERE user_id=? AND status='active'",
            (user_id,),
        )
        return cursor.fetchone()


def get_all_zayvki():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, phone, usluga, day, time, status FROM clients"
        )
        return cursor.fetchall()


def get_zayvka(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, phone, usluga, day, time, status FROM clients WHERE user_id=?",
            (user_id,),
        )
        return cursor.fetchone()


# ====================== НАПОМИНАНИЯ И ОЧИСТКА ======================
def get_clients_for_reminder(target_time):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, day, time 
            FROM clients 
            WHERE status='active'
        """)
        rows = cursor.fetchall()

    result = []
    now = datetime.now()

    for user_id, name, day, time in rows:
        try:
            dt = datetime.strptime(f"{day} {time}", "%d.%m %H:%M")
            if 0 <= (dt - now).total_seconds() <= 7200:  # 2 часа
                result.append((user_id, name, time))
        except:
            pass
    return result


def clear_old_records():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Получаем активные записи
        cursor.execute("SELECT user_id, day, time FROM clients WHERE status='active'")
        rows = cursor.fetchall()
        now = datetime.now()
        for user_id, day, time in rows:
            try:
                dt = datetime.strptime(f"{day} {time}", "%d.%m %H:%M")
                if dt < now:
                    cursor.execute(
                        "UPDATE clients SET status='completed' WHERE user_id=?",
                        (user_id,),
                    )
            except:
                pass

        conn.commit()
        print("✅ Старые записи обработаны")


init_db()  # Инициализация при запуске
