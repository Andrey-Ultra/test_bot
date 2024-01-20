import telebot
from telebot import types
import sqlite3
import cryptocompare

def get_crypto_price_in_rub(ticket):
    try:
        price = cryptocompare.get_price(ticket, currency='RUB')[ticket]['RUB']

        return price
    except Exception as e:
        return "???"

bot = telebot.TeleBot('6364713763:AAHpFmqk3pZLRoNkaoCL63miyIOP1CRTgT0')


conn = sqlite3.connect('currency_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_currencies (
        user_id INTEGER PRIMARY KEY,
        currencies TEXT
    )
''')
conn.commit()

keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_start.row("Добавить валюту", "Удалить валюту", "Текущая стоимость")


keyboard_add_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_add_currency.row("Вернуться назад", "Популярные валюты")
keyboard_add_currency.row("BTC", "ETH", "XRP", "LTC", "BCH")


keyboard_remove_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я твой бот для работы с валютами. Выбери команду:", reply_markup=keyboard_start)

@bot.message_handler(func=lambda message: message.text == "Добавить валюту")
def handle_add_currency(message):
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=keyboard_add_currency)

@bot.message_handler(func=lambda message: message.text == "Удалить валюту")
def handle_remove_currency(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    keyboard_remove_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_remove_currency.row("Вернуться назад")
    for currency in currencies:
        keyboard_remove_currency.row(currency)

    bot.send_message(message.chat.id, "Выбери валюту для удаления:", reply_markup=keyboard_remove_currency)

@bot.message_handler(func=lambda message: message.text == "Текущая стоимость")
def handle_current_price(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    currencies_message = "Выбранные валюты:\n"
    for i in currencies:
        currencies_message += i+': '+str(get_crypto_price_in_rub(i)) + ' ₽\n';
    bot.send_message(message.chat.id, currencies_message)

@bot.message_handler(func=lambda message: message.text == "Вернуться назад", content_types=['text'])
def handle_back(message):
    bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)

@bot.message_handler(func=lambda message: message.text == "Популярные валюты", content_types=['text'])
def handle_popular_currencies(message):

    bot.send_message(message.chat.id, "Список популярных валют: USD, EUR, GBP, JPY, CNY")


@bot.message_handler(func=lambda message: message.text not in ["Добавить валюту", "Удалить валюту", "Текущая стоимость", "Вернуться назад", "Популярные валюты", *get_user_currencies(message.from_user.id)])
def handle_custom_currency(message):
    user_id = message.from_user.id
    currency_name = message.text

    add_user_currency(user_id, currency_name)
    bot.send_message(message.chat.id, f"Валюта {currency_name} добавлена!")


@bot.message_handler(func=lambda message: message.text in get_user_currencies(message.from_user.id))
def handle_remove_currency_button(message):
    user_id = message.from_user.id
    currency_name = message.text

    remove_user_currency(user_id, currency_name)

    keyboard_remove_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_remove_currency.row("Вернуться назад")
    for currency in get_user_currencies(user_id):
        keyboard_remove_currency.row(currency)

    bot.send_message(message.chat.id, f"Валюта {currency_name} удалена!", reply_markup=keyboard_remove_currency)

def add_user_currency(user_id, currency_name):
    with conn:
        currencies = get_user_currencies(user_id)
        currencies.append(currency_name)

        cursor.execute('''
            INSERT OR REPLACE INTO user_currencies (user_id, currencies) VALUES (?, ?)
        ''', (user_id, ",".join(currencies)))

def remove_user_currency(user_id, currency_name):
    with conn:
        currencies = get_user_currencies(user_id)

        if currency_name in currencies:
            currencies.remove(currency_name)

            cursor.execute('''
                INSERT OR REPLACE INTO user_currencies (user_id, currencies) VALUES (?, ?)
            ''', (user_id, ",".join(currencies)))

def get_user_currencies(user_id):
    with conn:
        cursor.execute('''
            SELECT currencies FROM user_currencies WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()

        if result:
            return result[0].split(",") if result[0] else []
        else:
            return []

if __name__ == "__main__":
    bot.polling(none_stop=True)
