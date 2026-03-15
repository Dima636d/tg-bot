import os
import telebot
from flask import Flask
from threading import Thread

# 1. Настройка Flask (обманка для Render)
app = Flask('')

@app.route('/')
def home():
    return "Бот запущен и работает!"

def run():
    # Render сам подставит нужный порт в переменную PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Настройка бота через Environment
# Важно: на Render в Key напиши BOT_TOKEN, а в Value вставь сам токен
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ПРИВЕТ! Я живой и не сплю благодаря Flask! 🚀")

# 3. Запуск
if __name__ == "__main__":
    keep_alive()  # Запускаем сайт-затычку
    print("Бот погнал...")
    bot.infinity_polling() # Запускаем самого бота
