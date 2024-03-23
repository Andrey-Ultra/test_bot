from urllib.parse import urlparse
import telebot
from telebot import types

bot = telebot.TeleBot('5992928516:AAG2KqhhF-n21dqPssb4NtdcgCKo0h2t8sU')
hrefflag = 0

def is_url(s): #интегрировать парсер
    try:
        result = urlparse(s)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_start.row("Отправить ссылку на товар")
keyboard_start.row("Для чего нужен этот бот")


@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот для отслеживания цен на различные товары. Можно просто отправить ссылку на нужный товар. Выбери команду:", reply_markup=keyboard_start)

@bot.message_handler(func=lambda message: message.text == "Отправить ссылку на товар", content_types=['text'])
def handle_back(message):
    bot.send_message(message.chat.id, "Жду ссылку", reply_markup=keyboard_start)
    hrefflag = 1

@bot.message_handler(content_types=['text'])
def handle_href(message):
    if hrefflag != 1: # ф зачем
        exit()
    nigger = is_url(message.text)
    if nigger == True:
        bot.send_message(message.chat.id, "Сссылка добавлена", reply_markup=keyboard_start) #мб другая клава
    if nigger == False:
        bot.send_message(message.chat.id, "Сссылка некорректна", reply_markup=keyboard_start)
    hrefflag = 0


if __name__ == "__main__":
    bot.polling(none_stop=True)
