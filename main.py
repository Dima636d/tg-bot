import os, telebot, random, json, time
from flask import Flask, render_template_string, request, session, redirect, url_for
from threading import Thread
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = os.environ.get('BOT_TOKEN') 
ADMIN_PASSWORD = "A131@Y&"  # Твой единственный пароль для входа
bot = telebot.TeleBot(TOKEN)
app = Flask('')
app.secret_key = 'final_support_version_v7'

DB_FILE = 'data.json'

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                return d.get("logs", []), list(set(d.get("users", [])))
        except: return [], []
    return [], []

def save_db(logs, users):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump({"logs": logs, "users": list(users)}, f, ensure_ascii=False, indent=4)

all_logs, users_list = load_db()

# --- HTML ШАБЛОН ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Createdet Admin Panel</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: #30363d; color: #c9d1d9; text-decoration: none; border-radius: 6px; font-size: 0.9em; }
        .tab-btn.active { background: #1f6feb; color: white; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .badge { color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; font-weight: bold; display: inline-block; margin-bottom: 10px; }
        .id-badge { background: #238636; }
        .teh-badge { background: #da3633; margin-left: 5px; }
        .msg-box { background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 4px; margin: 10px 0; color: #e6edf3; }
        .btn { border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; color: white; font-weight: bold; font-size: 0.85em; text-decoration: none; }
        .btn-send { background: #238636; width: 100%; }
        .btn-red { background: #da3633; }
        .stat-val { font-size: 2.5em; color: #58a6ff; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="color: #58a6ff; margin:0;">🛠 Admin Createdet</h2>
            <a href="/logout" class="tab-btn">Выход</a>
        </div>

        <div class="tabs">
            <a href="/admin?tab=all" class="tab-btn {% if current_tab == 'all' %}active{% endif %}">ЛОГИ</a>
            <a href="/admin?tab=support" class="tab-btn {% if current_tab == 'support' %}active{% endif %}">ПОДДЕРЖКА</a>
            <a href="/admin?tab=settings" class="tab-btn {% if current_tab == 'settings' %}active{% endif %}">⚙️ НАСТРОЙКИ</a>
        </div>

        {% if current_tab == 'settings' %}
            <div class="card" style="text-align:center;">
                <h3>Статистика пользователей</h3>
                <div class="stat-val">{{ user_count }}</div>
                <p>Всего уникальных пользователей в базе</p>
                <hr style="border: 0; border-top: 1px solid #30363d; margin: 20px 0;">
                <a href="/clear_all" class="btn btn-red" onclick="return confirm('Удалить все логи и пользователей?')">ОЧИСТИТЬ ВСЮ БАЗУ</a>
            </div>
        {% else %}
            {% for log in display_logs %}
            <div class="card">
                <div class="badge id-badge">ID: {{ log.user_id }}</div>
                {% if log.is_teh %}<div class="badge teh-badge">SUPPORT</div>{% endif %}
                <div style="font-weight: bold; color: #58a6ff;">👤 @{{ log.username }} <small style="color:#8b949e">{{ log.time }}</small></div>
                <div class="msg-box">{{ log.text }}</div>
                <form action="/reply" method="POST">
                    <input type="hidden" name="user_id" value="{{ log.user_id }}">
                    <input type="text" name="reply_text" placeholder="Введите ответ..." style="width:80%; background:#0d1117; border:1px solid #30363d; color:white; padding:8px; border-radius:5px;" required>
                    <button type="submit" class="btn btn-send" style="width:15%; margin-left:10px;">ОТВЕТИТЬ</button>
                </form>
            </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

# --- МАРШРУТЫ ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return '<body style="background:#0d1117;color:white;text-align:center;padding-top:100px;font-family:sans-serif;"><form method="POST"><h2>ВХОД В АДМИНКУ</h2><input type="password" name="password" placeholder="Пароль"><br><br><button type="submit" style="padding:10px 20px; background:#238636; color:white; border:none; border-radius:5px; cursor:pointer;">ВОЙТИ</button></form></body>'

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    tab = request.args.get('tab', 'all')
    filtered = [log for log in all_logs if log.get('is_teh')] if tab == 'support' else all_logs
    return render_template_string(ADMIN_HTML, display_logs=reversed(filtered), current_tab=tab, user_count=len(users_list))

@app.route('/reply', methods=['POST'])
def reply():
    if session.get('logged_in'):
        uid, txt = request.form.get('user_id'), request.form.get('reply_text')
        try: bot.send_message(uid, f"<b>📩 Ответ поддержки:</b>\n\n{txt}", parse_mode='HTML')
        except: pass
    return redirect(request.referrer)

@app.route('/clear_all')
def clear_all():
    if session.get('logged_in'):
        global all_logs, users_list
        all_logs, users_list = [], []
        save_db(all_logs, users_list)
    return redirect(url_for('admin', tab='settings'))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

# --- БОТ ---
@bot.message_handler(func=lambda m: True)
def track_msg(m):
    if m.chat.id not in users_list: users_list.append(m.chat.id)
    is_teh = m.text.startswith('/teh') if m.text else False
    text = m.text.replace('/teh','').strip() if is_teh else m.text
    
    all_logs.append({
        "id": random.randint(1000, 9999),
        "time": datetime.now().strftime("%H:%M"),
        "user_id": m.chat.id,
        "username": m.from_user.username or "N/A",
        "text": text or "[Медиа]",
        "is_teh": is_teh
    })
    save_db(all_logs, users_list)
    if is_teh: bot.reply_to(m, "✅ Сообщение отправлено в техподдержку!")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
