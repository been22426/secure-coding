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
# Secure Coding - 중고거래 플랫폼 프로젝트

Flask 기반의 보안 중심 중고거래 웹 플랫폼입니다.  
채팅, 상품 거래, 유저 관리 등 핵심 기능을 구현하며, 보안 취약점을 예방하는 구조를 지향합니다.

---

## 구현된 주요 기능

### 회원 관리
- 회원가입 및 로그인
- `admin` 계정 로그인 시 관리자 대시보드로 자동 이동
- 정지된 계정 로그인 시 접근 차단 (`is_active = 0`)

### 마이페이지 기능

#### 1. 사용자 소개글 수정
- 사용자는 자신의 마이페이지에서 **소개글을 수정**할 수 있습니다.
- **비밀번호 변경**도 동일한 페이지에서 가능합니다.

#### 2. 비밀번호 변경
- 현재 비밀번호와 새로운 비밀번호를 입력하여 **비밀번호를 변경**할 수 있습니다.
- 비밀번호가 일치하지 않으면 변경이 거부됩니다.

#### 3. 다른 사용자의 프로필
- 다른 사용자의 프로필에서는 **소개글 수정**과 **비밀번호 변경** 기능이 보이지 않습니다.

### 상품 기능
- 상품 등록 (로그인 필요)
- 상품 목록 조회 (최신순)
- 상품 상세 조회
- 상품 검색 (추후 확장 가능)

### 실시간 채팅
- 전체 채팅: `/chat` 경로에서 모든 유저와 실시간 소통
- 1:1 채팅: `/chat/<상대유저>` 경로, Room 기반 소통

### 신고 기능
- **상품 신고**: 상세 페이지에서 신고 사유 입력 후 제출
- **유저 신고**: 판매자 대상 신고 가능 (사유 포함)

---

## 관리자 기능

> 관리자 계정: `admin`  
> 로그인 시 자동으로 `/admin/dashboard` 대시보드로 이동

### 관리자 페이지 요약

| 경로 | 기능 설명 |
|------|-----------|
| `/admin/dashboard` | 관리자 전용 진입 대시보드 |
| `/admin/products` | 상품 삭제 기능 포함 목록 |
| `/admin/users` | 유저 휴면 처리 (활성/정지 전환) |
| `/admin/reports` | 상품 신고 내역 조회 |
| `/admin/user-reports` | 유저 신고 내역 조회 |

---

## 보안 기능 요약
- 로그인된 사용자만 상품 등록, 채팅, 신고 가능
- 정지된 계정 자동 로그아웃
- 관리자 외 페이지 접근 시 `403 Forbidden` 처리
- (추후) 비밀번호 해시화, CSRF 토큰, 입력 검증 예정

---

## 실행 방법

```bash
git clone https://github.com/been22426/secure-coding.git
cd secure-coding
conda activate secure_coding
python app_whs.py

