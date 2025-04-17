# Secure Coding

## Tiny Secondhand Shopping Platform.

You should add some functions and complete the security requirements.

## requirements

if you don't have a miniconda(or anaconda), you can install it on this url. - https://docs.anaconda.com/free/miniconda/index.html

```
git clone https://github.com/ugonfor/secure-coding
conda env create -f enviroments.yaml
```

## usage

run the server process.

```
python app.py
```

if you want to test on external machine, you can utilize the ngrok to forwarding the url.
```
# optional
sudo snap install ngrok
ngrok http 5000
```

## 로그인 및 회원가입 기능

### 목적
- 사용자 인증을 통한 접근제어
- 안전한 비밀번호 저장

### 기술 스택
- Flask
- SQLite
- bcrypt

### 구현 내용

#### 회원가입 ('/register')
- 아이디/비밀번호 입력
- 중복된 사용자 방지

#### 로그인('/login')
- 입력된 아이디/비밀번호 검증
- 세션을 통해 로그인 상태 유지
- 실패 시 에러 메시지 출력

#### 로그아웃 ('/logout')
- 세션 초기화


## 상품 등록 / 조회 기능
### 기능 설명
- 로그인한 사용자만 상품 등록 가능
- 등록한 상품은 전체 상품 목록에서 확인 가능

### 라우팅 경로
- '/upoad' : 상품 등록 폼
- '/products' : 상품 목록 확인

### 현재 데이터 저장 구조 (SQLite)
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    price INTEGER,
    seller TEXT
);
```

## 상품 상세 페이지 기능

### 경로
- '/product/<id>' : 선택한 상품의 상세 정보 확인 가능

### 기능 설명
- 상품 목록에서 제목을 클릭하면 상세 페이지로 이동
- 상세 페이지는 다음 정보가 표시됨.
  - 상품명
  - 가격
  - 상세 설명
  - 판매자 정보
- 목록으로 돌아가는 링크를 포함.

### 예시 흐름
1. 사용자가 상품을 '/upload'로 등록
2. 다른 사용자가 '/products'에서 해당 상품을 클릭
3. '/product/2' 등으로 이동하여 상세 정보 확인

# Secure Coding - 중고거래 플랫폼

이 프로젝트는 Flask 기반의 중고거래 웹 플랫폼입니다.  
보안 취약점 없이 핵심 기능을 안전하게 구현하는 것을 목표로 하며,  
채팅, 상품 등록, 회원 기능 등 필수 요소를 포함합니다.

---

##  주요 기능

###  회원가입 / 로그인
- 사용자는 아이디와 비밀번호로 회원가입 및 로그인 가능
- 현재는 평문 비밀번호 저장 (기능 테스트용), 추후 해시화 예정

---

###  상품 기능
- 상품 등록: 로그인한 사용자만 등록 가능 (`/upload`)
- 상품 목록: 전체 상품을 최신순으로 조회 (`/products`)
- 상품 상세: 개별 상품 상세 페이지 확인 (`/product/<id>`)

---

###  실시간 채팅 기능

#### 전체 채팅 (`/chat`)
- 모든 로그인된 사용자 간 실시간 메시지 송수신
- SocketIO 기반 브로드캐스트 사용

####  1:1 채팅 (`/chat/<상대아이디>`)
- 두 사용자가 하나의 고유한 room에 참여하여 대화
- 방 이름 구성 방식: `[내아이디, 상대아이디].toLowerCase().sort().join("_")`
- SocketIO room 기능 사용

---

## 📚 실행 방법

```bash
git clone https://github.com/been22426/secure-coding.git
cd secure-coding
conda activate secure_coding  # 가상환경 활성화
python app_whs.py             # SocketIO 서버 실행

