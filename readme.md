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

### 회원가입 ('/register')
- 아이디/비밀번호 입력
- 중복된 사용자 방지

### 로그인('/login')
- 입력된 아이디/비밀번호 검증
- 세션을 통해 로그인 상태 유지
- 실패 시 에러 메시지 출력

### 로그아웃 ('/logout')
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


