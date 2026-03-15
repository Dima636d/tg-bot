import os
import requests
import random
from flask import Flask, request

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_URL = f"https://api.telegram.org{BOT_TOKEN}/"

app = Flask('')

# 1. Главная страница (просто чтобы Render не ругался)
@app.route('/')
def home():
    return "API Бот верификации Createdet запущен!"

# 2. ТОТ САМЫЙ ПУТЬ ДЛЯ ТВОЕГО САЙТА
# Когда твой сайт обратится по адресу: ://xn----btbb2aydwg.onrender.com
@app.route('/send_code')
def send_code():
    chat_id = request.args.get('chat_id')
    if not chat_id:
        return {"status": "error", "message": "No chat_id provided"}, 400

    # Генерируем код
    code = random.randint(100000, 999999)
    
    # Текст сообщения
    text = (
        "<b>Привет! Это официальный бот Createdet</b>\n\n"
        f"Ваш код для входа/верификации на сайте: <code>{code}</code>\n"
        "Никому не сообщайте этот код!"
    )
    
    # Отправка в Telegram
    url = API_URL + "sendMessage"
    res = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
    
    if res.status_code == 200:
        return {"status": "success", "code": code} # Возвращаем код твоему сайту
    else:
        return {"status": "error", "telegram_error": res.text}, 500

# Запуск
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
