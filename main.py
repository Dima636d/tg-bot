import os, telebot, random, json
from flask import Flask, render_template_string, request, session, redirect, url_for
from threading import Thread
from datetime import datetime

# --- НАЛАШТУВАННЯ ---
TOKEN = os.environ.get('BOT_TOKEN') # Або встав свій токен прямо сюди
ADMIN_PASSWORD = "A131@Y&" 
bot = telebot.TeleBot(TOKEN)
app = Flask('')
app.secret_key = 'createdet_contact_v34'

DB_FILE = 'data.json'

# --- РОБОТА З БАЗОЮ (JSON) ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Повертаємо логи та словник юзерів {id: username}
                return data.get("logs", []), data.get("users", {})
        except: return [], {}
    return [], {}

def save_db(logs, users):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({"logs": logs, "users": users}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения БД: {e}")

# --- HTML ШАБЛОН ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Createdet v34</title>
    <style>
        body { font-family: sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .container { max-width: 850px; margin: 0 auto; }
        .header { background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: #30363d; color: #c9d1d9; text-decoration: none; border-radius: 6px; font-size: 0.9em; }
        .tab-btn.active { background: #1f6feb; color: white; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; position: relative; }
        .msg-box { background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 4px; margin: 10px 0; }
        input, textarea, select { background: #0d1117; border: 1px solid #30363d; color: white; padding: 10px; border-radius: 5px; width: 100%; box-sizing: border-box; }
        .btn { background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="color: #58a6ff; margin:0;">🛠 Createdet Admin</h2>
            <a href="/logout" class="tab-btn">Выход</a>
        </div>

        <div class="tabs">
            <a href="/admin?tab=all" class="tab-btn {% if current_tab == 'all' %}active{% endif %}">ЛОГИ</a>
            <a href="/admin?tab=personal" class="tab-btn {% if current_tab == 'personal' %}active{% endif %}">✉️ НАПИСАТЬ ЛИЧНО</a>
            <a href="/admin?tab=news" class="tab-btn {% if current_tab == 'news' %}active{% endif %}">📢 НОВОСТИ</a>
        </div>

        {% if current_tab == 'personal' %}
            <div class="card">
                <h3>Написать пользователю лично</h3>
                <form action="/send_private" method="POST">
                    <label>Выберите получателя:</label>
                    <select name="user_id" required style="margin-bottom:15px;">
                        {% for uid, uname in users.items() %}
                            <option value="{{ uid }}">ID: {{ uid }} (@{{ uname }})</option>
                        {% endfor %}
                    </select>
                    <textarea name="private_msg" placeholder="Текст сообщения..." required style="height:100px;"></textarea>
                    <button type="submit" class="btn" style="width:100%; margin-top:10px;">ОТПРАВИТЬ СООБЩЕНИЕ</button>
                </form>
            </div>
        {% elif current_tab == 'news' %}
            <div class="card" style="text-align:center;">
                <h3>Общая рассылка ({{ users|length }} чел.)</h3>
                <form action="/broadcast" method="POST">
                    <textarea name="news_text" placeholder="Текст рассылки для всех..." required style="height:100px;"></textarea>
                    <button type="submit" class="btn" style="width:100%; margin-top:10px;">ЗАПУСТИТЬ</button>
                </form>
            </div>
        {% else %}
            {% for log in logs %}
            <div class="card">
                <div style="font-weight: bold; color: #58a6ff;">ID: {{ log.user_id }} | @{{ log.username }} <small style="color:#8b949e">({{ log.time }})</small></div>
                <div class="msg-box">{{ log.text }}</div>
                <form action="/send_private" method="POST" style="display:flex; gap:5px;">
                    <input type="hidden" name="user_id" value="{{ log.user_id }}">
                    <input type="text" name="private_msg" placeholder="Быстрый ответ..." required>
                    <button type="submit" class="btn" style="background:#1f6feb;">➡️</button>
                </form>
            </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return '<body style="background:#0d1117;color:white;text-align:center;padding-top:100px;"><form method="POST"><h2>ADMIN PASS</h2><input type="password" name="password"><button type="submit">GO</button></form></body>'

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    tab = request.args.get('tab', 'all')
    logs, users = load_db()
    return render_template_string(ADMIN_HTML, logs=reversed(logs[-100:]), users=users, current_tab=tab)

@app.route('/send_private', methods=['POST'])
def send_private():
    if session.get('logged_in'):
        u_id = request.form.get('user_id')
        msg = request.form.get('private_msg')
        try:
            bot.send_message(u_id, f"💬 **Сообщение от администрации:**\n\n{msg}", parse_mode='Markdown')
        except: pass
    return redirect(request.referrer)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    if session.get('logged_in'):
        _, users = load_db()
        text = request.form.get('news_text')
        for u_id in users.keys():
            try: bot.send_message(u_id, f"📢 **НОВОСТИ:**\n\n{text}", parse_mode='Markdown')
            except: pass
    return redirect(url_for('admin', tab='news'))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

@bot.message_handler(func=lambda m: True)
def track(m):
    logs, users = load_db()
    
    # 1. Записуємо/оновлюємо юзера (чат ID та юзернейм)
    uid_str = str(m.chat.id)
    users[uid_str] = m.from_user.username or "NoUsername"
    
    # 2. Обробка команд
    if m.text and m.text.startswith('/start'):
        bot.send_message(m.chat.id, "Привет! Мы сохранили тебя в базу. Теперь можем общаться лично!")
        save_db(logs, users)
        return

    # 3. Логування повідомлення
    logs.append({
        "time": datetime.now().strftime("%H:%M"),
        "user_id": m.chat.id,
        "username": users[uid_str],
        "text": m.text or "[Медиа]"
    })
    
    # 4. Збереження
    save_db(logs, users)

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
