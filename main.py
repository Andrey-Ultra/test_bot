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


def get_history_prices_5min(ticker):
    currencies_message = ""  # а есть какие более разумные интервалы limit = ?
    eternalsin = cryptocompare.get_historical_price_minute(ticker, currency='USD', limit=4)
    # high low . open close yf[eq не нужны здесь
    currencies_message += ticker + ':\n\n'
    for j in eternalsin:
        dicct = j
        currencies_message += 'Max:  ' + str(
            dicct.get('high')) + ' USD\n' '\n'  # + 'Min:  ' + str(dicct.get('low')) + ' USD\n\n'
    return currencies_message


def get_history_prices_3hour(ticker):
    currencies_message = ""
    eternalsin = cryptocompare.get_historical_price_hour(ticker, currency='USD', limit=2)
    currencies_message += ticker + ':\n\n'
    for j in eternalsin:
        dicct = j
        # currencies_message += 'Max:  ' + str(dicct.get('high')) + ' USD\n' + 'Min:  ' + str(dicct.get('low')) + ' USD\n' + 'Откр: ' + str(dicct.get('open')) + ' USD\n'
        currencies_message += str(dicct.get('close')) + 'USD\n\n'
    return currencies_message


def get_history_prices_2day(ticker):
    currencies_message = ""
    eternalsin = cryptocompare.get_historical_price_minute(ticker, currency='USD', limit=1)
    currencies_message += ticker + ':\n\n'
    for j in eternalsin:
        dicct = j
        currencies_message += 'Max:  ' + str(dicct.get('high')) + ' USD\n' + 'Min:  ' + str(
            dicct.get('low')) + ' USD\n' + 'Откр: ' + str(dicct.get('open')) + ' USD\n' + 'Закр: ' + str(
            dicct.get('close')) + ' USD\n\n'
    return currencies_message


def get_history_prices_week(ticker):
    currencies_message = ""
    eternalsin = cryptocompare.get_historical_price_day(ticker, currency='USD', limit=6)
    currencies_message += ticker + ':\n\n'
    for j in eternalsin:
        dicct = j
        # currencies_message+= 'Max:  ' + str(dicct.get('high')) + ' USD\n' + 'Min:  ' + str(dicct.get('low')) + ' USD\n' + 'Откр: ' + str(dicct.get('open')) + ' USD\n' + 'Закр: ' + str(dicct.get('close')) + ' USD\n\n'
        currencies_message += str(dicct.get('close')) + ' USD\n\n'
    return currencies_message

bot = telebot.TeleBot('6457686610:AAHLoxn3SS7iAQ8j_XkuYF8xl8AlITjmLmo')


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
keyboard_start.row("Добавить валюту", "Удалить валюту")
keyboard_start.row("Текущая стоимость", "Изменения за период")
keyboard_start.row("Что такое тикер???")


keyboard_other = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_other.row("Вернуться назад", "5 минут",  "3 часа", "2 дня", "неделя")


keyboard_add_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_add_currency.row("Вернуться назад")
keyboard_add_currency.row("BTC", "ETH", "XRP", "LTC", "BCH")

keyboard_remove_currency = types.ReplyKeyboardMarkup(resize_keyboard=True)


known_tickers = cryptocompare.get_coin_list(format=True)

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я твой бот для работы с криптовалютами. Выбери команду:", reply_markup=keyboard_start)

@bot.message_handler(func=lambda message: message.text == "Добавить валюту")
def handle_add_currency(message):
    bot.send_message(message.chat.id, "Введите название тикер криптовалюты или выберете из популярных для добавления:", reply_markup=keyboard_add_currency)
    bot.register_next_step_handler(message, process_add_currency)

def process_add_currency(message):
    user_id = message.from_user.id
    currency_to_add = message.text.strip()

    if currency_to_add == "Вернуться назад":
        bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)
        return

    if currency_to_add not in known_tickers:
        bot.send_message(user_id, "Неверный тикер криптовалюты.")
        bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)
        return

    if not currency_to_add:
        bot.send_message(user_id, "Вы ввели пустое название криптовалюты. Попробуйте еще раз.")
        bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)
        return

    currencies = get_user_currencies(user_id)

    if currency_to_add in currencies:
        bot.send_message(user_id, "Эта криптовалюта уже есть в вашем списке.")
        bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)
        return

    add_user_currency(user_id, currency_to_add)
    bot.send_message(user_id, f"Криптовалюта {currency_to_add} добавлена!")
    bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)

# Удаляем валюту
@bot.message_handler(func=lambda message: message.text == "Удалить валюту")
def handle_remove_currency(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    keyboard_remove_currency = types.InlineKeyboardMarkup()
    for currency in currencies:
        keyboard_remove_currency.add(types.InlineKeyboardButton(text=currency, callback_data=f'remove_{currency}'))

    bot.send_message(message.chat.id, "Выберите валюту для удаления:", reply_markup=keyboard_remove_currency)

# Обрабатываем inline-кнопки для удаления валюты
@bot.callback_query_handler(func=lambda call: call.data.startswith('remove'))
def handle_remove_callback(call):
    user_id = call.from_user.id
    currency_to_remove = call.data.split('_')[1]

    currencies = get_user_currencies(user_id)

    if currency_to_remove not in currencies:
        bot.send_message(user_id, "Элемента нет в вашем списке.")
        return

    remove_user_currency(user_id, currency_to_remove)
    bot.send_message(user_id, f"Валюта {currency_to_remove} удалена!")

    # Обновляем inline-кнопки после удаления
    currencies = get_user_currencies(user_id)
    keyboard_remove_currency = types.InlineKeyboardMarkup()
    for currency in currencies:
        keyboard_remove_currency.add(types.InlineKeyboardButton(text=currency, callback_data=f'remove_{currency}'))

    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                          text="Выберите валюту для удаления:", reply_markup=keyboard_remove_currency)

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

#new
@bot.message_handler(func=lambda message: message.text == "Изменения за период")
def handle_other(message):
    bot.send_message(message.chat.id, "За какой период?", reply_markup=keyboard_other)


@bot.message_handler(func=lambda message: message.text == "5 минут")
def handle_other_5min(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    currencies_message = "История торгов за последние 5 минут:\n"
    for i in currencies:
        currencies_message += get_history_prices_5min(i) + '\n';
    bot.send_message(message.chat.id, currencies_message)

@bot.message_handler(func=lambda message: message.text == "3 часа")
def handle_other_3hour(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    currencies_message = "История торгов за последние 3 часa:\n"
    for i in currencies:
        currencies_message += get_history_prices_3hour(i) + '\n';
    bot.send_message(message.chat.id, currencies_message)


@bot.message_handler(func=lambda message: message.text == "2 дня")
def handle_other_2d(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    currencies_message = "История торгов за вчера и сегодня\n"
    for i in currencies:
        currencies_message += get_history_prices_2day(i) + '\n';
    bot.send_message(message.chat.id, currencies_message)


@bot.message_handler(func=lambda message: message.text == "неделя")
def handle_other_week(message):
    user_id = message.from_user.id
    currencies = get_user_currencies(user_id)

    if not currencies:
        bot.send_message(message.chat.id, "Список валют пуст.")
        return

    currencies_message = "История торгов за последнюю неделю:\n"
    for i in currencies:
        currencies_message += get_history_prices_week(i) + '\n';
    bot.send_message(message.chat.id, currencies_message)



@bot.message_handler(func=lambda message: message.text == "Вернуться назад", content_types=['text'])
def handle_back(message):
    bot.send_message(message.chat.id, "Выбери команду:", reply_markup=keyboard_start)

@bot.message_handler(func=lambda message: message.text == "Что такое тикер???", content_types=['text'])
def handle_popular_currencies(message):

    bot.send_message(message.chat.id, "Тикер криптовалюты — это короткий символьный код, обозначающий данную криптовалюту. Например, тикер для Биткоина — BTC, для Эфириума — ETH.")



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
