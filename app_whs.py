from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

# DB 초기화
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    #users 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    #products 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            price INTEGER,
            seller TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return f"✅ 로그인됨: {session['username']}"
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # 평문 저장

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "❌ 이미 존재하는 사용자입니다."
        finally:
            conn.close()

        return redirect(url_for('login'))
    return render_template('register_whs.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()

        if result and password == result[0]:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "❌ 로그인 실패"

    return render_template('login_whs.html')

#상품 등록
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        seller = session['username']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (title, description, price, seller) VALUES (?, ?, ?, ?)",
                  (title, description, price, seller))
        conn.commit()
        conn.close()

        return redirect(url_for('products'))

    return render_template('upload_whs.html')

#상품 목록 조회
@app.route('/products')
def products():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, price, seller FROM products ORDER BY id DESC")
    items = c.fetchall()
    conn.close()

    return render_template('products_whs.html', items=items)


#상품 상세 페이지 
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, description, price, seller FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()

    if not product:
        return "상품을 찾을 수 없습니다.", 404

    return render_template('view_product_whs.html', product=product)

#실시간 전체 채팅
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat_whs.html', username=session['username'])


#SocketIO 이벤트 처리
@socketio.on('send_message')
def handle_send_message(data):
    username = data['username']
    message = data['message']
    emit('receive_message', {'username': username, 'message': message}, broadcast=True)

# 1 대 1 채팅
@app.route('/chat/<target>')
def private_chat(target):
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('private_chat_whs.html', myname=session['username'], target=target)

#SocketIO 이벤트 추가
@socketio.on('join_room')
def handle_join(data):
    room = data['room']
    join_room(data['room'])


@socketio.on('private_message')
def handle_private_message(data):
    room = data['room']
    sender = data['sender']
    message = data['message']
    emit('receive_private', {'sender': sender, 'message': message}, to=room)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, debug=True)




