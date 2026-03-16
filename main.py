import os, telebot, random, json
from flask import Flask, render_template_string, request, session, redirect, url_for
from threading import Thread
from datetime import datetime

# --- НАЛАШТУВАННЯ ---
TOKEN = os.environ.get('BOT_TOKEN') 
ADMIN_PASSWORD = "A131@Y&" 
bot = telebot.TeleBot(TOKEN)
app = Flask('')
app.secret_key = 'createdet_fix_v15'

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
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({"logs": logs, "users": list(set(users))}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка базы: {e}")

# --- HTML ШАБЛОН ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel Createdet</title>
    <style>
        body { font-family: sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .container { max-width: 850px; margin: 0 auto; }
        .header { background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: #30363d; color: #c9d1d9; text-decoration: none; border-radius: 6px; font-size: 0.9em; border: 1px solid transparent; }
        .tab-btn.active { background: #1f6feb; color: white; border-color: #58a6ff; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; position: relative; }
        .badge { padding: 2px 8px; border-radius: 10px; font-size: 0.7em; font-weight: bold; margin-bottom: 10px; display: inline-block; color: white; }
        .btn-red { background: #da3633; border:none; color:white; padding:5px 10px; border-radius:5px; cursor:pointer; }
        .msg-box { background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 4px; margin: 10px 0; }
        input, textarea { background: #0d1117; border: 1px solid #30363d; color: white; padding: 10px; border-radius: 5px; width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="color: #58a6ff; margin:0;">🛠 Createdet Admin</h2>
            <a href="/logout" class="tab-btn">Выход</a>
        </div>

        <div class="tabs">
            <a href="/admin?tab=all" class="tab-btn {% if current_tab == 'all' %}active{% endif %}">ВСЕ ЛОГИ</a>
            <a href="/admin?tab=pred" class="tab-btn {% if current_tab == 'pred' %}active{% endif %}">ПРЕДЛОЖЕНИЯ</a>
            <a href="/admin?tab=teh" class="tab-btn {% if current_tab == 'teh' %}active{% endif %}">ТЕХПОДДЕРЖКА</a>
            <a href="/admin?tab=news" class="tab-btn {% if current_tab == 'news' %}active{% endif %}">📢 НОВОСТИ</a>
        </div>

        {% if current_tab == 'news' %}
            <div class="card" style="text-align:center;">
                <h3>Рассылка ({{ user_count }} чел.)</h3>
                <form action="/broadcast" method="POST">
                    <textarea name="news_text" placeholder="Текст..." required></textarea>
                    <button type="submit" style="background:#238636; color:white; width:100%; margin-top:10px; padding:10px; border:none; border-radius:5px; cursor:pointer;">ОТПРАВИТЬ</button>
                </form>
            </div>
        {% else %}
            {% for log in logs %}
            <div class="card">
                <div class="badge" style="background: {% if log.type == 'pred' %}#da3633{% elif log.type == 'teh' %}#f1e05a{% else %}#238636{% endif %}; color: {% if log.type == 'teh' %}black{% else %}white{% endif %};">
                    {{ log.type | upper }}
                </div>
                <div style="font-weight: bold; color: #58a6ff;">ID: {{ log.user_id }} | @{{ log.username }} <small style="color:#8b949e">({{ log.time }})</small></div>
                <div class="msg-box">{{ log.text }}</div>
                <a href="/delete/{{ log.id }}?tab={{ current_tab }}" class="btn-red" style="position: absolute; top: 15px; right: 15px;">УДАЛИТЬ</a>
            </div>
            {% else %}
            <p style="text-align:center; color: #8b949e;">Сообщений нет</p>
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
    
    # Оновлюємо дані з файлу перед показом
    current_logs, current_users = load_db()
    
    if tab == 'all':
        filtered = current_logs # ТУТ ТЕПЕР БУДЕ ВСЕ
    elif tab == 'pred':
        filtered = [l for l in current_logs if l.get('type') == 'pred']
    elif tab == 'teh':
        filtered = [l for l in current_logs if l.get('type') == 'teh']
    else: filtered = []
        
    return render_template_string(ADMIN_HTML, logs=reversed(filtered), current_tab=tab, user_count=len(current_users))

@app.route('/delete/<int:log_id>')
def delete_one(log_id):
    if session.get('logged_in'):
        current_logs, current_users = load_db()
        new_logs = [l for l in current_logs if l['id'] != log_id]
        save_db(new_logs, current_users)
    return redirect(request.referrer)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    if session.get('logged_in'):
        current_logs, current_users = load_db()
        text = request.form.get('news_text')
        for u_id in current_users:
            try: bot.send_message(u_id, f"📢 <b>НОВОСТИ:</b>\n\n{text}", parse_mode='HTML')
            except: pass
    return redirect(url_for('admin', tab='news'))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

@bot.message_handler(func=lambda m: True)
def track(m):
    current_logs, current_users = load_db()
    if m.chat.id not in current_users: current_users.append(m.chat.id)
    
    msg_type = 'log'
    clean_text = m.text
    if m.text.startswith('/pred'):
        msg_type, clean_text = 'pred', m.text.replace('/pred', '').strip()
        bot.reply_to(m, "✅ Предложение отправлено!")
    elif m.text.startswith('/teh'):
        msg_type, clean_text = 'teh', m.text.replace('/teh', '').strip()
        bot.reply_to(m, "🆘 Техподдержка приняла!")

    current_logs.append({
        "id": random.randint(100000, 999999), "time": datetime.now().strftime("%H:%M"),
        "user_id": m.chat.id, "username": m.from_user.username or "N/A",
        "text": clean_text or "[Медиа]", "type": msg_type
    })
    save_db(current_logs, current_users)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
