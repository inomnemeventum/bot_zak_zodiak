import logging
import telebot # Импортируем telebot
from my_secrets_ import secrets
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes
from datetime import datetime

# Настройки бота
token = secrets.get('BOT_API_TOKEN')
application = ApplicationBuilder().token(token).build()
bot = telebot.TeleBot(token)

# Файл для хранения пользователей
USERS_FILE = 'bot_users.txt'

def load_user_count():
    """Загружает количество уникальных пользователей из файла"""
    try:
        with open(USERS_FILE, 'r') as f:
            users = set(line.strip() for line in f if line.strip().isdigit())
        return len(users), users
    except FileNotFoundError:
        return 0, set()

def save_user(user_id):
    """Сохраняет пользователя в файл, если его ещё нет"""
    count, users = load_user_count()
    if str(user_id) not in users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
        return True  # Пользователь новый
    return False  # Уже был



# Обработчик кнопки "Расчёт"
@bot.message_handler(func=lambda message: message.text == "Расчитай ключ к счастливым отношениям")
def handle_calculate_button(message):
    sent_msg = bot.send_message(
        chat_id=message.chat.id,
        text="Введите вашу дату рождения в формате ДД.ММ.ГГГГ:"
    )
    bot.register_next_step_handler(sent_msg, process_birth_date)
    
@bot.message_handler(commands=['admin_stats'])
def admin_stats(message):
    admin_id = secrets.get('ADMIN_ID')
    
    # Проверяем, является ли пользователь админом
    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    
    total_users, _ = load_user_count()
    bot.send_message(
        chat_id=message.chat.id,
        text=f"📊 Статистика бота:\n\n"
             f"Всего пользователей: {total_users}"
    )    

# Обработчик первого сообщения пользователя
@bot.message_handler(func=lambda message: True)
def handle_first_message(message):
    user_id = message.from_user.id
    is_new = save_user(user_id)
    
    # Отправляем приветствие с именем пользователя или никнеймом
    if message.from_user.first_name:
        name = message.from_user.first_name
    else:
        name = message.from_user.username or "Пользователь"
        
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Привет {name}!",
        reply_markup=get_keyboard()
    )

# Функция возвращает клавиатуру с кнопкой "Расчёт"
def get_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = telebot.types.KeyboardButton("Расчитай ключ к счастливым отношениям")
    markup.add(button)
    return markup

from datetime import datetime

def digital_root(n):
    """Вычисляет цифровой корень числа (суммирует цифры, пока не останется одна цифра)"""
    while n >= 10:
        n = sum(int(digit) for digit in str(n))
    return n

def process_birth_date(message):
    text = message.text.strip()
    
    # Проверяем формат даты
    try:
        datetime.strptime(text, '%d.%m.%Y')
    except ValueError:
        sent_msg = bot.send_message(message.chat.id, "Введина некорректная дата, расчет не был выполнен.")
        return

    # Убираем точки и суммируем все цифры
    digits_str = text.replace('.', '')
    total_sum = sum(int(d) for d in digits_str)

    # Получаем однозначное число
    result = digital_root(total_sum)

    bot.send_message(
        chat_id=message.chat.id,
        text=f"Ваше число: {result}"
    )
    
    # Читаем и отправляем содержимое соответствующего HTML-файла
    if 1 <= result <= 9:
        filename = f"RED{result}.html"
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                bot.send_message(
                    chat_id=message.chat.id,
                    text=content,
                    parse_mode='HTML'  # Поддержка HTML-разметки (если есть)
                )
        except FileNotFoundError:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Информация для числа {result} временно недоступна."
            )
        except Exception as e:
            bot.send_message(
                chat_id=message.chat.id,
                text="Произошла ошибка при чтении файла."
            )
            print(f"Ошибка при чтении файла {filename}: {e}")


# --- Запуск бота ---
if __name__ == "__main__":
    print("Запускаю бот...")
    total, _ = load_user_count()
    print(f"Текущее количество пользователей: {total}")
    try:
        bot.infinity_polling(logger_level=logging.INFO)
        break
    except ReadTimeout as timeoutError:
            print(f"Ошибка при работе бота: {timeoutError}")
    except Exception as e:
            print(f"Ошибка при работе бота: {e}")
        