from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import InputRequired, Length, NumberRange

class PasswordForm(FlaskForm):
    current_pw = PasswordField("현재 비밀번호", validators=[InputRequired(), Length(min=6)])
    new_pw = PasswordField("새 비밀번호", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("비밀번호 변경")

class BioForm(FlaskForm):
    bio = TextAreaField("소개글", validators=[Length(max=300)])
    submit = SubmitField("소개글 저장")

from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length

import re
import sqlite3
import datetime

def log_admin_action(action, actor, target):
    with open("admin_audit.log", "a", encoding="utf-8") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {actor} -> {action} : {target}\n")
import os
import time
from datetime import timedelta


app = Flask(__name__)



# Flask 비밀키 설정
app.config['SECRET_KEY'] = os.urandom(24) #안전한 랜덤 비밀키




# 쿠키 보안 설정
app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,  # HTTPS 환경에서만 사용
        SESSION_COOKIE_SAMESITE='Strict', # SameSite 설정 (Lax, Strict, None)
)




#세션 만료 시간 설정 (30분 후 세션 만료)
app.permanent_session_lifetime = timedelta(minutes=30)

csrf = CSRFProtect(app) # CSRF 보호 활성화
socketio = SocketIO(app)




# 회원가입 폼 정의
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])

# 로그인 폼 정의
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])

# 상품 업로드 폼 정의
class UploadProductForm(FlaskForm):
    title = StringField("상품명", validators=[InputRequired(), Length(min=1, max=100)])
    description = TextAreaField("설명", validators=[Length(max=500)])
    price = IntegerField("가격", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField("등록")


#admin 전용 폼
class UserActionForm(FlaskForm):
    submit = SubmitField("실행")

class ProductActionForm(FlaskForm):
    submit = SubmitField("삭제")


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
        bio TEXT DEFAULT '',
        balance INTEGER DEFAULT 10000,
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


#애플리케이션 시작 시 DB 초기화
init_db()




@app.route('/')
def index():
    if 'username' in session:
        return f"✅ 로그인됨: {session['username']}"
    return redirect(url_for('login'))




@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
            return '아이디는 4~20자의 영문/숫자/밑줄만 허용됩니다.', 400
        password = generate_password_hash(form.password.data)  # 비밀번호 해시화
        # DB에 사용자 추가
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))  # 회원가입 후 로그인 페이지로 리다이렉트
    return render_template('register_whs.html', form=form)




# 로그인 실패 횟수 추적용 딕셔너리
login_failures = {}

# 로그인 실패 횟수 추적용 딕셔너리
login_failures = {}

# 로그인 실패 횟수 + 타임스탬프 추적
login_failures = {}  # username: {"count": int, "last_fail": timestamp}

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT username, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user:
            fail_info = login_failures.get(username, {"count": 0, "last_fail": 0})
            now = time.time()
            # 실패 후 10분(600초) 경과 시 초기화
            if now - fail_info["last_fail"] > 600:
                fail_info = {"count": 0, "last_fail": 0}

            if fail_info["count"] >= 5:
                flash("로그인 5회 실패. 10분 후 다시 시도하세요.", "error")
                return "로그인 5회 실패. 10분 후 다시 시도하세요.", 403

            if check_password_hash(user[1], password):
                session['username'] = username
                login_failures[username] = {"count": 0, "last_fail": 0}
                if username == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('home'))
            else:
                fail_info["count"] += 1
                fail_info["last_fail"] = now
                login_failures[username] = fail_info
                flash("비밀번호가 틀렸습니다.", "error")
                return render_template("error_whs.html", error_message="로그인에 실패했습니다. 아이디 또는 비밀번호를 확인하세요.")
        else:
            flash("존재하지 않는 계정입니다.", "error")
            return render_template("error_whs.html", error_message="로그인에 실패했습니다. 아이디 또는 비밀번호를 확인하세요.")

    return render_template('login_whs.html', form=form)


#home화면
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('home_whs.html', username=session['username'])




#유저 목록
@app.route('/users')
def users():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, is_active FROM users WHERE username != 'admin'")
    users = c.fetchall()
    conn.close()

    return render_template('user_list_whs.html', users=users)

#프로필 페이지

@app.route('/user/<username>', methods=['GET', 'POST'])
def user_profile(username):
    form = BioForm()
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if request.method == 'POST' and form.validate_on_submit():
        new_bio = form.bio.data
        c.execute("UPDATE users SET bio = ? WHERE username = ?", (new_bio, username))
        conn.commit()
        flash("소개글이 저장되었습니다.", "success")
        return redirect(url_for('user_profile', username=username))

    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    user_bio = row[0] if row else "소개글이 없습니다."
    return render_template('user_profile_whs.html', username=username, user_bio=user_bio, form=form)



#마이페이지
@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # 사용자 소개글 불러오기
    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    bio = row[0] if row else ""

    # Form 객체 생성
    form = BioForm()
    pwform = PasswordForm()

    # 소개글 저장
    if form.validate_on_submit() and form.bio.data:
        new_bio = form.bio.data
        c.execute("UPDATE users SET bio = ? WHERE username = ?", (new_bio, username))
        conn.commit()
        flash("소개글이 저장되었습니다.", "success")
        return redirect(url_for("mypage"))

    # 비밀번호 변경 처리
    if pwform.validate_on_submit() and pwform.current_pw.data and pwform.new_pw.data:
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if row and check_password_hash(row[0], pwform.current_pw.data):
            new_hashed = generate_password_hash(pwform.new_pw.data)
            c.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed, username))
            conn.commit()
            flash("비밀번호가 변경되었습니다.", "success")
        else:
            flash("현재 비밀번호가 올바르지 않습니다.", "error")

    conn.close()

    return render_template('mypage_whs.html', user_bio=bio, form=form, pwform=pwform)


#비밀번호 변경
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    form = PasswordForm()
    if form.validate_on_submit():
        username = session['username']
        current_pw = form.current_pw.data
        new_pw = form.new_pw.data

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = c.fetchone()

        if row and check_password_hash(row[0], current_pw):
            c.execute("UPDATE users SET password = ? WHERE username = ?", (generate_password_hash(new_pw), username))
            conn.commit()
            flash("비밀번호가 변경되었습니다.", "success")
        else:
            flash("현재 비밀번호가 올바르지 않습니다.", "error")
        conn.close()
        return redirect(url_for("mypage"))

    return render_template("change_password_whs.html", form=form)





#상품 업로드
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    form = UploadProductForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        price = form.price.data
        seller = session['username']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (title, description, price, seller) VALUES (?, ?, ?, ?)",
                  (title, description, price, seller))
        conn.commit()
        conn.close()

        return redirect(url_for('products'))

    return render_template('upload_whs.html', form=form)



#유저 상품 삭제
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product_by_user(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # 관리자인지 일반 사용자인지 확인
    if username == 'admin':
        # 관리자라면 상품 삭제
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    else:
        # 일반 사용자라면 본인이 등록한 상품만 삭제
        c.execute("SELECT seller FROM products WHERE id = ?", (product_id,))
        product = c.fetchone()

        if product and product[0] == username:
            # 본인이 등록한 상품만 삭제 가능
            c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        else:
            return render_template("error_whs.html", error_message="삭제 권한이 없습니다."), 403

    conn.commit()
    conn.close()

    return redirect(url_for('products'))  # 상품 목록으로 리다이렉트


#상품 검색 및 목록
@app.route('/products_search', methods=['GET'])
def products_search():
    query = request.args.get('query')  # 검색어를 받아옴

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if query:
        # 상품명(title) 또는 상품 설명(description)을 기준으로 검색
        c.execute("SELECT id, title, price, seller FROM products WHERE title LIKE ? OR description LIKE ? ORDER BY id DESC", 
                  ('%' + query + '%', '%' + query + '%'))
    else:
        # 검색어가 없으면 모든 상품 출력
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
        return render_template("error_whs.html", error_message="상품을 찾을 수 없습니다."), 404

    return render_template('view_product_whs.html', product=product)



#송금 기능
@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        receiver = request.form['receiver']
        amount = int(request.form['amount'])

        sender = session['username']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        # 송금자 잔액 조회
        c.execute("SELECT balance FROM users WHERE username = ?", (sender,))
        row = c.fetchone()
        if row is None:
            conn.close()
            return render_template("error_whs.html", error_message="송금 실패 : 송금자 정보를 찾을 수 없습니다."), 400
        sender_balance = row[0]

        # 수신자 존재 확인
        c.execute("SELECT balance FROM users WHERE username = ?", (receiver,))
        row = c.fetchone()
        if row is None:
            conn.close()
            return render_template("error_whs.html", error_message="수신자 계정을 찾을 수 없습니다.")

        if sender_balance >= amount:
            # 잔액 처리
            c.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, sender))
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, receiver))
            c.execute("INSERT INTO transactions (sender, receiver, amount, date) VALUES (?, ?, ?, datetime('now'))",
                      (sender, receiver, amount))
            conn.commit()
            conn.close()
            return redirect(url_for('transactions'))
        else:
            conn.close()
            return render_template("error_whs.html", error_message="잔액이 부족합니다.")

    return render_template('transfer_whs.html')


#송금 내역 조회
@app.route('/transactions')
def transactions():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # 송금 내역을 가져옵니다.
    c.execute("SELECT * FROM transactions WHERE sender = ? OR receiver = ? ORDER BY date DESC", (username, username))
    transactions = c.fetchall()
    conn.close()

    return render_template('transactions_whs.html', transactions=transactions)



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


#상품 검색
@app.route('/products', methods=['GET'])
def products():
    query = request.args.get('query')  # 검색어를 받아옴

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if query:
        # 상품명(title) 또는 상품 설명(description)을 기준으로 검색
        c.execute("SELECT id, title, price, seller FROM products WHERE title LIKE ? OR description LIKE ? ORDER BY id DESC", 
                  ('%' + query + '%', '%' + query + '%'))
    else:
        # 검색어가 없다면 모든 상품 조회
        c.execute("SELECT id, title, price, seller FROM products ORDER BY id DESC")
    
    items = c.fetchall()
    conn.close()

    return render_template('products_whs.html', items=items)





#신고 라우트 추가
@app.route('/report/product/<int:product_id>', methods=['POST'])
def report_product(product_id):
    if 'username' not in session:
        return render_template("error_whs.html", error_message="로그인 필요"), 403
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
        return render_template("error_whs.html", error_message="로그인 필요"), 403
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
        return render_template("error_whs.html", error_message="권한 없음"), 403
    return render_template('admin_dashboard_whs.html')




#관리자 상품 목록 라우트
@app.route('/admin/products')
def admin_products():
    if not is_admin():
        return render_template("error_whs.html", error_message="권한 없음"), 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, price, seller FROM products ORDER BY id DESC")
    items = c.fetchall()
    conn.close()
    product_form = ProductActionForm()

    return render_template('admin_products_whs.html', items=items, product_form=product_form)



#관리자 상품 삭제 라우트
@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_admin():
        return render_template("error_whs.html", error_message="권한 없음"), 403

    form = ProductActionForm()
    if not form.validate_on_submit():
        return render_template("error_whs.html", error_message="잘못된 요청입니다."), 400

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
        return render_template("error_whs.html", error_message="권한 없음"), 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, is_active FROM users WHERE username != 'admin'")
    users = c.fetchall()
    conn.close()
    
    action_form = UserActionForm()

    return render_template('admin_users_whs.html', users=users, action_form=action_form)


# 유저 신고 내역 라우트
@app.route('/admin/user-reports')
def view_user_reports():
    if not is_admin():
        return render_template("error_whs.html", error_message="권한 없음"), 403

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT reported_user, reporter, reason, timestamp FROM user_reports ORDER BY timestamp DESC")
    reports = c.fetchall()
    conn.close()

    return render_template('admin_user_reports_whs.html', reports=reports)



#휴면 처리
@app.route('/admin/deactivate_user/<username>', methods=['POST'])
def deactivate_user(username):
    if not is_admin():
        return render_template("error_whs.html", error_message="권한 없음"), 403

    form = UserActionForm()
    if not form.validate_on_submit():
        return render_template("error_whs.html", error_message="잘못된 요청입니다."), 400

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
        return render_template("error_whs.html", error_message="권한 없음"), 403

    form = UserActionForm()
    if not form.validate_on_submit():
        return render_template("error_whs.html", error_message="잘못된 요청입니다."), 400

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
            return render_template("error_whs.html", error_message="정지된 계정입니다. 관리자에게 문의하세요."), 403



@app.route("/admin/audit_log")
def admin_audit_log():
    if not session.get("username") == "admin":
        return "접근 권한이 없습니다.", 403
    log_path = "admin_audit.log"
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.readlines()
    except FileNotFoundError:
        logs = []
    return render_template("admin_audit_log_whs.html", logs=logs[::-1])

@app.route('/forbidden')
def forbidden():
    return render_template('error_whs.html', error_message="권한이 없습니다.")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error_whs.html", error_message="페이지를 찾을 수 없습니다."), 404


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
