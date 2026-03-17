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
app.secret_key = 'server_final_fix_v32'

# Підключення до MongoDB
client = None
try:
    if MONGO_URL:
        client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        db = client['bot_database']
        logs_col = db['logs']
        users_col = db['users']
        bans_col = db['bans']
        client.admin.command('ping')
        print("✅ MongoDB підключено!")
except Exception as e:
    print(f"❌ Помилка бази: {e}")

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
                    <button type="submit" class="btn btn-green" style="width:100%; margin-top:10px; padding:12px;">ОТПРАВИТЬ ВСЕМ</button>
                </form>
            </div>
        {% elif current_tab == 'bans' %}
            {% for user in users_list %}
                <div class="card">
                    <div style="font-weight:bold; color:#58a6ff;">ID: {{ user.user_id }} | @{{ user.username }}</div>
                    <div style="margin:10px 0;">Варны: {{ user.warns or 0 }} | Статус: {% if user.is_banned %}🚫 ЗАБАНЕН{% else %}✅ ОК{% endif %}</div>
                    <form action="/moderate" method="POST" style="display:flex; gap:10px;">
                        <input type="hidden" name="user_id" value="{{ user.user_id }}">
                        <input type="number" name="mins" placeholder="Мин" style="width:70px;">
                        <button name="act" value="ban" class="btn btn-red">БАН</button>
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
                <div style="font-weight: bold; color: #58a6ff;">ID: {{ log.user_id }} | @{{ log.username }}</div>
                <div class="msg-box">{{ log.text }}</div>
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
    return '<form method="POST" style="text-align:center;padding-top:100px;"><input type="password" name="password"><button>GO</button></form>'

@app.route('/admin')
def admin():
    if not session.get('logged_in') or not client: return redirect(url_for('login'))
    tab = request.args.get('tab', 'all')
    logs = list(logs_col.find().sort('_id', -1).limit(50))
    u_count = users_col.count_documents({})
    
    users_list = []
    if tab == 'bans':
        for u in list(users_col.find().limit(20)):
            ban = bans_col.find_one({"user_id": u['user_id']})
            u['is_banned'] = True if (ban and datetime.now() < ban['until']) else False
            users_list.append(u)

    if tab == 'pred': filtered = [l for l in logs if l.get('type') == 'pred']
    elif tab == 'teh': filtered = [l for l in logs if l.get('type') == 'teh']
    else: filtered = logs

    return render_template_string(ADMIN_HTML, logs=filtered, current_tab=tab, user_count=u_count, users_list=users_list)

@app.route('/moderate', methods=['POST'])
def moderate():
    uid = int(request.form.get('user_id'))
    act = request.form.get('act')
    if act == "ban":
        mins = int(request.form.get('mins') or 60)
        bans_col.update_one({"user_id": uid}, {"$set": {"until": datetime.now() + timedelta(minutes=mins)}}, upsert=True)
    elif act == "unban":
        bans_col.delete_one({"user_id": uid})
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
    logs_col.delete_one({"id": log_id})
    return redirect(request.referrer)

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

# --- BOT LOGIC ---
@bot.message_handler(func=lambda m: True)
def track(m):
    try:
        if not client: return
        
        # Перевірка бану
        ban = bans_col.find_one({"user_id": m.chat.id})
        if ban and datetime.now() < ban['until']:
            bot.send_message(m.chat.id, "❌ Вы заблокированы.")
            return

        # РЕЄСТРАЦІЯ (ОБОВ'ЯЗКОВО)
        users_col.update_one(
            {"user_id": m.chat.id}, 
            {"$set": {"username": m.from_user.username or "N/A"}}, 
            upsert=True
        )

        if m.text and m.text.startswith('/start'):
            bot.send_message(m.chat.id, "Привет! Я бот каналов **Dimoon** и **Createdet**. 🤝\nИспользуй /help для команд.", parse_mode='Markdown')
            return
        
        if m.text and m.text.startswith('/help'):
            bot.send_message(m.chat.id, "🚀 **Команды:**\n/pred [текст] - идея\n/teh [текст] - помощь", parse_mode='Markdown')
            return

        m_type, txt = 'log', m.text or "[Медиа]"
        if m.text:
            if m.text.startswith('/pred'): 
                m_type, txt = 'pred', m.text.replace('/pred','').strip()
                bot.reply_to(m, "✅ Принято!")
            elif m.text.startswith('/teh'): 
                m_type, txt = 'teh', m.text.replace('/teh','').strip()
                bot.reply_to(m, "🆘 Ожидайте!")

        # ЗАПИС В БАЗУ
        logs_col.insert_one({
            "id": random.randint(100000, 999999), 
            "time": datetime.now().strftime("%H:%M"),
            "user_id": m.chat.id, 
            "username": m.from_user.username or "N/A",
            "text": txt, 
            "type": m_type
        })
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
