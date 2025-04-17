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
            password TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
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
    #상품 신고
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            reporter TEXT NOT NULL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    #유저 신고
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reported_user TEXT NOT NULL,
            reporter TEXT NOT NULL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
        row = c.fetchone()
        conn.close()

        if row and row[0] == password:
            session['username'] = username

            # ✅ admin 계정이면 관리자 대시보드로 이동
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))

            return redirect(url_for('products'))  # 일반 유저는 상품 목록으로
        else:
            return "로그인 실패"

    return render_template('login_whs.html')



#유저 목록
@app.route('/users')
def user_list():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, is_active FROM users WHERE username != 'admin'")
    users = c.fetchall()
    conn.close()
    return render_template('user_list_whs.html', users=users)


#프로필 페이지
@app.route('/user/<username>')
def user_profile(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    user_bio = row[0] if row else "소개글이 없습니다."

    return render_template('user_profile_whs.html', username=username, user_bio=user_bio)


#마이페이지
@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # 사용자 정보 가져오기 (현재 로그인한 사용자)
    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    bio = row[0] if row else ""

    if request.method == 'POST':
        new_bio = request.form['bio']
        c.execute("UPDATE users SET bio = ? WHERE username = ?", (new_bio, username))
        conn.commit()

    conn.close()

    return render_template('mypage_whs.html', user_bio=bio)



#비밀번호 변경
@app.route('/update_password', methods=['POST'])
def update_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    current_pw = request.form['current_pw']
    new_pw = request.form['new_pw']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()

    if row and row[0] == current_pw:
        c.execute("UPDATE users SET password = ? WHERE username = ?", (new_pw, username))
        conn.commit()
        message = "비밀번호가 변경되었습니다."
    else:
        message = "현재 비밀번호가 올바르지 않습니다."

    conn.close()
    return message




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








#신고 라우트 추가
@app.route('/report/product/<int:product_id>', methods=['POST'])
def report_product(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    reporter = session['username']
    reason = request.form.get('reason', '')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO product_reports (product_id, reporter, reason) VALUES (?, ?, ?)",
              (product_id, reporter, reason))
    conn.commit()
    conn.close()

    return redirect(url_for('product_detail', product_id=product_id))




#유저 신고
@app.route('/report/user/<username>', methods=['POST'])
def report_user(username):
    if 'username' not in session:
        return redirect(url_for('login'))

    reporter = session['username']
    reason = request.form.get('reason', '')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO user_reports (reported_user, reporter, reason) VALUES (?, ?, ?)",
              (username, reporter, reason))
    conn.commit()
    conn.close()

    return "신고가 접수되었습니다."




#관리자 계정
def is_admin():
    return session.get('username') == 'admin'

#관리자 페이지
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():
        return "권한 없음", 403
    return render_template('admin_dashboard_whs.html')


#관리자 상품 목록 라우트
@app.route('/admin/products')
def admin_products():
    if not is_admin():
        return "접근 권한이 없습니다.", 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, price, seller FROM products ORDER BY id DESC")
    items = c.fetchall()
    conn.close()

    return render_template('admin_products_whs.html', items=items)



#관리자 상품 삭제 라우트
@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_admin():
        return "권한 없음", 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_products'))




#관리자 확인용 라우트
@app.route('/admin/reports')
def view_reports():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT product_id, reporter, reason, timestamp FROM product_reports ORDER BY timestamp DESC")
    reports = c.fetchall()
    conn.close()
    return render_template('admin_reports_whs.html', reports=reports)


#관리자용 유저 목록
@app.route('/admin/users')
def admin_users():
    if not is_admin():
        return "권한 없음", 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, is_active FROM users WHERE username != 'admin'")
    users = c.fetchall()
    conn.close()

    return render_template('admin_users_whs.html', users=users)


# 유저 신고 내역 라우트
@app.route('/admin/user-reports')
def view_user_reports():
    if not is_admin():
        return "권한 없음", 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT reported_user, reporter, reason, timestamp FROM user_reports ORDER BY timestamp DESC")
    reports = c.fetchall()
    conn.close()

    return render_template('admin_user_reports_whs.html', reports=reports)




# 휴면 처리 라우트
@app.route('/admin/deactivate_user/<username>', methods=['POST'])
def deactivate_user(username):
    if not is_admin():
        return "권한 없음", 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_users'))

#정지된 계정 재활성화
@app.route('/admin/reactivate_user/<username>', methods=['POST'])
def reactivate_user(username):
    if not is_admin():
        return "권한 없음", 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_active = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_users'))



#자동 차단 기능
@app.before_request
def block_inactive_users():
    if 'username' in session:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT is_active FROM users WHERE username = ?", (session['username'],))
        row = c.fetchone()
        conn.close()

        if row and row[0] == 0:
            session.clear()
            return "정지된 계정입니다. 관리자에게 문의하세요.", 403





@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, debug=True)




