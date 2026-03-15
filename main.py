import os, telebot, random, json, time
from flask import Flask, render_template_string, request, session, redirect, url_for
from threading import Thread
from datetime import datetime

# --- НАЛАШТУВАННЯ ---
TOKEN = os.environ.get('BOT_TOKEN') 
ADMIN_PASSWORD = "A131@Y&" 
bot = telebot.TeleBot(TOKEN)
app = Flask('')
app.secret_key = 'createdet_ultimate_v10_final'

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

# --- HTML ШАБЛОН (DARK MODE) ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Createdet Ultimate</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: #30363d; color: #c9d1d9; text-decoration: none; border-radius: 6px; font-size: 0.9em; border: 1px solid transparent; }
        .tab-btn.active { background: #1f6feb; color: white; border-color: #58a6ff; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; position: relative; }
        .badge { color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; font-weight: bold; display: inline-block; margin-bottom: 10px; }
        .id-badge { background: #238636; }
        .teh-badge { background: #da3633; margin-left: 5px; }
        .msg-box { background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 4px; margin: 10px 0; color: #e6edf3; }
        .btn { border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; color: white; font-weight: bold; font-size: 0.85em; text-decoration: none; }
        .btn-send { background: #238636; }
        .btn-red { background: #da3633; }
        .btn-del { background: #da3633; position: absolute; top: 15px; right: 15px; padding: 4px 8px; font-size: 0.7em; }
        input, textarea { background: #0d1117; border: 1px solid #30363d; color: white; padding: 10px; border-radius: 5px; width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="color: #58a6ff; margin:0;">🛠 Admin Createdet</h2>
            <div>
                {% if current_tab == 'all' or current_tab == 'support' %}
                <a href="/clear_tab?tab={{ current_tab }}" class="btn btn-red" onclick="return confirm('Очистить эту вкладку?')">УДАЛИТЬ ВСЕ</a>
                {% endif %}
                <a href="/logout" class="tab-btn" style="margin-left:10px;">Выход</a>
            </div>
        </div>

        <div class="tabs">
            <a href="/admin?tab=all" class="tab-btn {% if current_tab == 'all' %}active{% endif %}">ЛОГИ</a>
            <a href="/admin?tab=support" class="tab-btn {% if current_tab == 'support' %}active{% endif %}">ПОДДЕРЖКА</a>
            <a href="/admin?tab=news" class="tab-btn {% if current_tab == 'news' %}active{% endif %}">НОВОСТИ</a>
            <a href="/admin?tab=settings" class="tab-btn {% if current_tab == 'settings' %}active{% endif %}">⚙️ НАСТРОЙКИ</a>
        </div>

        {% if current_tab == 'settings' %}
            <div class="card" style="text-align:center; padding: 40px;">
                <h3>Статистика пользователей</h3>
                <div style="font-size: 3em; color: #58a6ff; font-weight: bold;">{{ user_count }}</div>
                <p>Всего уникальных пользователей в базе</p>
                <hr style="border:0; border-top:1px solid #30363d; margin: 30px 0;">
                <a href="/clear_database" class="btn btn-red" style="width: 100%; display: block;" onclick="return confirm('УДАЛИТЬ ВООБЩЕ ВСЁ?')">ПОЛНАЯ ОЧИСТКА БАЗЫ</a>
            </div>
        {% elif current_tab == 'news' %}
            <div class="card">
                <h3>📢 Создать рассылку для всех</h3>
                <form action="/broadcast" method="POST">
                    <textarea name="news_text" placeholder="Введите текст новости..." required></textarea>
                    <button type="submit" class="btn btn-send" style="width: 100%; margin-top: 15px;">ОТПРАВИТЬ ВСЕМ</button>
                </form>
            </div>
        {% else %}
            {% for log in display_logs %}
            <div class="card">
                <a href="/delete/{{ log.id }}?tab={{ current_tab }}" class="btn btn-del">❌ УДАЛИТЬ</a>
                <div class="badge id-badge">ID: {{ log.user_id }}</div>
                {% if log.is_teh %}<div class="badge teh-badge">SUPPORT</div>{% endif %}
                <div style="font-weight: bold; color: #58a6ff;">👤 @{{ log.username }} <small style="color:#8b949e">{{ log.time }}</small></div>
                <div class="msg-box">{{ log.text }}</div>
                <form action="/reply" method="POST" style="display: flex; gap: 10px;">
                    <input type="hidden" name="user_id" value="{{ log.user_id }}">
                    <input type="text" name="reply_text" placeholder="Ответ..." required style="flex-grow: 1; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 5px; padding: 8px;">
                    <button type="submit" class="btn btn-send">ОТВЕТИТЬ</button>
                </form>
            </div>
            {% else %}
            <p style="text-align:center; color: #8b949e;">Сообщений нет</p>
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
    return '<body style="background:#0d1117;color:white;text-align:center;padding-top:100px;"><form method="POST"><h2>ADMIN PASS</h2><input type="password" name="password"><button type="submit">ENTER</button></form></body>'

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
        try: bot.send_message(uid, f"<b>📩 Ответ:</b>\n\n{txt}", parse_mode='HTML')
        except: pass
    return redirect(request.referrer)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    if session.get('logged_in'):
        text = request.form.get('news_text')
        for u_id in users_list:
            try: bot.send_message(u_id, f"📢 <b>НОВОСТИ:</b>\n\n{text}", parse_mode='HTML')
            except: pass
    return redirect(url_for('admin', tab='news'))

@app.route('/delete/<int:log_id>')
def delete_one(log_id):
    if session.get('logged_in'):
        global all_logs
        all_logs = [l for l in all_logs if l['id'] != log_id]
        save_db(all_logs, users_list)
    return redirect(request.referrer)

@app.route('/clear_tab')
def clear_tab():
    if session.get('logged_in'):
        tab = request.args.get('tab', 'all')
        global all_logs
        if tab == 'support':
            all_logs = [l for l in all_logs if not l.get('is_teh')]
        else: all_logs = []
        save_db(all_logs, users_list)
    return redirect(url_for('admin', tab=tab))

@app.route('/clear_database')
def clear_db():
    if session.get('logged_in'):
        global all_logs, users_list
        all_logs, users_list = [], []
        save_db(all_logs, users_list)
    return redirect(url_for('admin', tab='settings'))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

# --- ЛОГИКА БОТА ---
@bot.message_handler(func=lambda m: True)
def track(m):
    if m.chat.id not in users_list: users_list.append(m.chat.id)
    is_teh = m.text.startswith('/teh') if m.text else False
    text = m.text.replace('/teh','').strip() if is_teh else m.text
    
    all_logs.append({
        "id": random.randint(100000, 999999),
        "time": datetime.now().strftime("%H:%M"),
        "user_id": m.chat.id,
        "username": m.from_user.username or "N/A",
        "text": text or "[Media]",
        "is_teh": is_teh
    })
    save_db(all_logs, users_list)
    if is_teh: bot.reply_to(m, "✅ Сообщение отправлено в поддержку!")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
