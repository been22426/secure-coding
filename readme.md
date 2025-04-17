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

### 로그인('/login')
- 입력된 아이디/비밀번호 검증
- 세션을 통해 로그인 상태 유지
- 실패 시 에러 메시지 출력

### 로그아웃 ('/logout')
- 세션 초기화


