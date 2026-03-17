import os, telebot, random, pymongo
from flask import Flask, render_template_string, request, session, redirect, url_for
from threading import Thread
from datetime import datetime, timedelta

# --- НАЛАШТУВАННЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
MONGO_URL = os.environ.get('MONGO_URL') 
ADMIN_PASSWORD = "A131@Y&"
bot = telebot.TeleBot(TOKEN)
app = Flask('')
app.secret_key = 'server_bans_global_v31'

# Підключення до MongoDB
try:
    client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client['bot_database']
    logs_col = db['logs']
    users_col = db['users'] # Тут: {user_id, username, warns}
    bans_col = db['bans']   # Тут: {user_id, until}
    client.admin.command('ping')
    print("✅ MongoDB підключено успішно!")
except Exception as e:
    print(f"❌ Помилка бази: {e}")
    client = None

# --- HTML ШАБЛОН ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel Createdet</title>
    <style>
        body { font-family: sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: #30363d; color: #c9d1d9; text-decoration: none; border-radius: 6px; font-size: 0.9em; border: 1px solid transparent; }
        .tab-btn.active { background: #1f6feb; color: white; border-color: #58a6ff; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; position: relative; }
        .badge { padding: 2px 8px; border-radius: 10px; font-size: 0.7em; font-weight: bold; margin-bottom: 10px; display: inline-block; color: white; }
        .btn { padding: 6px 12px; border:none; border-radius:5px; cursor:pointer; color:white; text-decoration:none; font-size:0.8em; font-weight:bold; }
        .btn-red { background: #da3633; }
        .btn-green { background: #238636; }
        .btn-warn { background: #f1e05a; color: black; }
        .msg-box { background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 4px; margin: 10px 0; white-space: pre-wrap; }
        input, textarea { background: #0d1117; border: 1px solid #30363d; color: white; padding: 10px; border-radius: 5px; width: 100%; box-sizing: border-box; }
        .status-banned { color: #f85149; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="color: #58a6ff; margin:0;">🛠 Global Admin</h2>
            <a href="/logout" class="tab-btn">Выход</a>
        </div>

        <div class="tabs">
            <a href="/admin?tab=all" class="tab-btn {% if current_tab == 'all' %}active{% endif %}">ВСЕ ЛОГИ</a>
            <a href="/admin?tab=pred" class="tab-btn {% if current_tab == 'pred' %}active{% endif %}">ПРЕДЛОЖЕНИЯ</a>
            <a href="/admin?tab=teh" class="tab-btn {% if current_tab == 'teh' %}active{% endif %}">ТЕХПОДДЕРЖКА</a>
            <a href="/admin?tab=bans" class="tab-btn {% if current_tab == 'bans' %}active{% endif %}">🚫 БАНЫ</a>
            <a href="/admin?tab=news" class="tab-btn {% if current_tab == 'news' %}active{% endif %}">📢 НОВОСТИ</a>
        </div>

        {% if current_tab == 'news' %}
            <div class="card" style="text-align:center;">
                <h3>Рассылка ({{ user_count }} чел.)</h3>
                <form action="/broadcast" method="POST">
                    <textarea name="news_text" placeholder="Текст..." required></textarea>
                    <button type="submit" class="btn btn-green" style="width:100%; margin-top:10px; padding:12px;">ОТПРАВИТЬ</button>
                </form>
            </div>
        {% elif current_tab == 'bans' %}
            <form action="/admin" method="GET" style="display:flex; gap:10px; margin-bottom:20px;">
                <input type="hidden" name="tab" value="bans">
                <input type="text" name="search" placeholder="Поиск по ID..." style="flex-grow:1;">
                <button type="submit" class="btn" style="background:#30363d;">Найти</button>
            </form>
            {% for user in users_list %}
                <div class="card">
                    <div style="font-weight:bold; color:#58a6ff;">ID: {{ user.user_id }} | @{{ user.username }}</div>
                    <div style="margin:10px 0;">
                        Варны: <b>{{ user.warns or 0 }} / 3</b> | 
                        Статус: 
                        {% if user.is_banned %}
                            <span class="status-banned">ЗАБАНЕН до {{ user.ban_until }}</span>
                        {% else %}
                            <span style="color:#3fb950;">Активен</span>
                        {% endif %}
                    </div>
                    <form action="/moderate" method="POST" style="display:flex; gap:10px; align-items:center;">
                        <input type="hidden" name="user_id" value="{{ user.user_id }}">
                        <input type="number" name="mins" placeholder="Мин" style="width:70px;">
                        <button name="act" value="ban" class="btn btn-red">БАН</button>
                        <button name="act" value="warn" class="btn btn-warn">ВАРН</button>
                        <button name="act" value="unban" class="btn btn-green">РАЗБАН</button>
                    </form>
                </div>
            {% endfor %}
        {% else %}
            {% for log in logs %}
            <div class="card">
                <div class="badge" style="background: {% if log.type == 'pred' %}#da3633{% elif log.type == 'teh' %}#f1e05a{% else %}#238636{% endif %}; color: {% if log.type == 'teh' %}black{% else %}white{% endif %};">
                    {{ (log.type or 'LOG') | upper }}
                </div>
                <div style="font-weight: bold; color: #58a6ff;">ID: {{ log.user_id }} | @{{ log.username }} <small style="color:#8b949e">({{ log.time }})</small></div>
                <div class="msg-box">{{ log.text }}</div>
                <form action="/reply" method="POST" style="display: flex; gap: 10px; margin-top:10px;">
                    <input type="hidden" name="user_id" value="{{ log.user_id }}">
                    <input type="text" name="reply_text" placeholder="Ответить..." required style="flex-grow:1;">
                    <button type="submit" class="btn" style="background:#1f6feb;">ОТВЕТИТЬ</button>
                </form>
                <a href="/delete/{{ log.id }}?tab={{ current_tab }}" class="btn btn-red" style="position: absolute; top: 15px; right: 15px;">УДАЛИТЬ</a>
            </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return '<body style="background:#0d1117;color:white;text-align:center;padding-top:100px;"><form method="POST"><h2>LOGIN</h2><input type="password" name="password"><button type="submit">GO</button></form></body>'

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    tab = request.args.get('tab', 'all')
    search = request.args.get('search', '')
    
    logs = list(logs_col.find().sort('_id', -1).limit(100))
    user_count = users_col.count_documents({})
    
    users_list = []
    if tab == 'bans':
        query = {"user_id": int(search)} if search.isdigit() else {}
        raw_users = list(users_col.find(query).limit(50))
        for u in raw_users:
            ban = bans_col.find_one({"user_id": u['user_id']})
            is_b = False
            until_str = ""
            if ban and datetime.now() < ban['until']:
                is_b = True
                until_str = ban['until'].strftime("%H:%M %d.%m")
            u['is_banned'] = is_b
            u['ban_until'] = until_str
            users_list.append(u)

    if tab == 'pred': filtered = [l for l in logs if l.get('type') == 'pred']
    elif tab == 'teh': filtered = [l for l in logs if l.get('type') == 'teh']
    else: filtered = logs

    return render_template_string(ADMIN_HTML, logs=filtered, current_tab=tab, user_count=user_count, users_list=users_list)

@app.route('/moderate', methods=['POST'])
def moderate():
    if not session.get('logged_in'): return redirect(url_for('login'))
    uid = int(request.form.get('user_id'))
    act = request.form.get('act')
    if act == "ban":
        mins = int(request.form.get('mins') or 60)
        bans_col.update_one({"user_id": uid}, {"$set": {"until": datetime.now() + timedelta(minutes=mins)}}, upsert=True)
    elif act == "unban":
        bans_col.delete_one({"user_id": uid})
    elif act == "warn":
        users_col.update_one({"user_id": uid}, {"$inc": {"warns": 1}}, upsert=True)
        u = users_col.find_one({"user_id": uid})
        if u.get('warns', 0) >= 3:
            bans_col.update_one({"user_id": uid}, {"$set": {"until": datetime.now() + timedelta(days=1)}}, upsert=True)
            users_col.update_one({"user_id": uid}, {"$set": {"warns": 0}})
    return redirect(request.referrer)

@app.route('/reply', methods=['POST'])
def reply():
    if session.get('logged_in'):
        u_id, text = request.form.get('user_id'), request.form.get('reply_text')
        try: bot.send_message(u_id, f"✉️ **Ответ администрации:**\n\n{text}", parse_mode='Markdown')
        except: pass
    return redirect(request.referrer)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    if session.get('logged_in'):
        text = request.form.get('news_text')
        for u in users_col.find():
            try: bot.send_message(u['user_id'], f"📢 **НОВОСТИ:**\n\n{text}", parse_mode='Markdown')
            except: pass
    return redirect(url_for('admin', tab='news'))

@app.route('/delete/<int:log_id>')
def delete_one(log_id):
    if session.get('logged_in'): logs_col.delete_one({"id": log_id})
    return redirect(request.referrer)

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

# --- BOT LOGIC ---
@bot.message_handler(func=lambda m: True)
def track(m):
    try:
        # Check Ban
        ban = bans_col.find_one({"user_id": m.chat.id})
        if ban and datetime.now() < ban['until']:
            bot.send_message(m.chat.id, f"❌ Вы заблокированы до {ban['until'].strftime('%H:%M %d.%m')}")
            return

        # Register User
        users_col.update_one(
            {"user_id": m.chat.id}, 
            {"$set": {"username": m.from_user.username or "N/A"}}, 
            upsert=True
        )

        if m.text and m.text.startswith('/start'):
            bot.send_message(m.chat.id, "Привет! Используй /help для команд.")
            return
        
        m_type, txt = 'log', m.text or "[Медиа]"
        if m.text:
            if m.text.startswith('/pred'): m_type, txt = 'pred', m.text.replace('/pred','').strip()
            elif m.text.startswith('/teh'): m_type, txt = 'teh', m.text.replace('/teh','').strip()

        logs_col.insert_one({
            "id": random.randint(100000, 999999), "time": datetime.now().strftime("%H:%M"),
            "user_id": m.chat.id, "username": m.from_user.username or "N/A",
            "text": txt, "type": m_type
        })
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
