from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from chat_GD import ChatGDGraph
from mysql_db import User, get_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 初始化问答系统
chat_bot = ChatGDGraph()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(user_data['id'], user_data['username'])
    finally:
        conn.close()
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', username=current_user.username)

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.json
    question = data.get('message', '')
    
    if not question.strip():
        return jsonify({'reply': '请输入您的问题'})
    
    # 调用问答系统回答问题
    answer = chat_bot.chat_main(question)
    
    # 保存对话历史到数据库（可选）
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_history (user_id, question, answer) VALUES (%s, %s, %s)",
                (current_user.id, question, answer)
            )
        conn.commit()
    finally:
        conn.close()
    
    return jsonify({'reply': answer})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    user_obj = User(user['id'], user['username'])
                    login_user(user_obj)
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('chat'))
                else:
                    flash('用户名或密码错误')
        finally:
            conn.close()
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # 检查用户名是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('用户名已存在')
                    return render_template('register.html')
                
                # 检查邮箱是否已存在
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('邮箱已被注册')
                    return render_template('register.html')
                
                # 创建新用户
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
                conn.commit()
                
                # 获取新用户ID
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_id = cursor.fetchone()['id']
                
                # 自动登录
                user_obj = User(user_id, username)
                login_user(user_obj)
                
                return redirect(url_for('chat'))
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/history')
@login_required
def history():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT question, answer, created_at FROM chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
                (current_user.id,)
            )
            history = cursor.fetchall()
    finally:
        conn.close()
    
    return render_template('history.html', history=history)

# 初始化聊天历史表
def init_chat_history_table():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    # 初始化聊天历史表
    init_chat_history_table()
    # 启动Flask应用
    app.run(debug=True) 