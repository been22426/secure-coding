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
- 상품 삭제 (본인이 등록한 상품에 한함)

### 실시간 채팅
- 전체 채팅: `/chat` 경로에서 모든 유저와 실시간 소통
- 1:1 채팅: `/chat/<상대유저>` 경로, Room 기반 소통

### 신고 기능
- **상품 신고**: 상세 페이지에서 신고 사유 입력 후 제출
- **유저 신고**: 판매자 대상 신고 가능 (사유 포함)

## 상품 검색 기능

### 기능 설명
- 사용자는 **상품명**과 **상품 설명**을 기준으로 상품을 검색할 수 있습니다.
- **부분 일치 검색**이 가능하며, 상품명과 상품 설명에 포함된 키워드로 검색을 수행할 수 있습니다.
- 검색어를 입력하면, **상품명** 또는 **상품 설명**에 해당 검색어가 포함된 상품들이 **최신순**으로 표시됩니다.

### 시스템 분석

#### 1. 요구 사항
- 사용자는 **상품명**(title)과 **상품 설명**(description)을 기준으로 상품을 검색할 수 있어야 합니다.
- 사용자가 입력한 검색어는 **부분 일치**로 상품명 또는 상품 설명에서 검색됩니다.
- **검색어가 없을 경우**: 검색어를 입력하지 않으면 모든 상품이 표시됩니다.
- **결과 출력**: 검색 결과는 **최신순**으로 정렬되어 출력됩니다.

#### 2. 기술 분석
- **백엔드**:
  - **Flask** 웹 프레임워크를 사용하여 서버를 구현하고 있습니다.
  - **SQLite** 데이터베이스에서 **상품명(title)**과 **상품 설명(description)**을 기준으로 검색합니다.
  - SQL 쿼리에서는 `LIKE` 연산자를 사용하여 **부분 일치 검색**을 구현합니다.

  예시 쿼리:
  ```sql
  SELECT * FROM products WHERE title LIKE '%search_term%' OR description LIKE '%search_term%'
  ```
### 6. 유저 간 송금 기능
- 사용자는 다른 사용자에게 **포인트 송금** 기능을 사용할 수 있습니다.
- 송금 시 **송금액**과 **수수료** 등을 입력받고, **계좌 간 거래**가 이루어집니다.
- 송금 내역은 **`transactions`** 테이블에 기록되고, 사용자는 **송금 내역 페이지**에서 확인할 수 있습니다.

#### 송금 흐름
1. **사용자 입력**: 사용자가 송금 페이지에서 **받는 사람**과 **송금액**을 입력합니다.
2. **서버 처리**: 서버에서는 송금자의 **잔액**을 차감하고, **받는 사람**의 잔액을 추가합니다.
3. **결과 출력**: 송금 내역은 **`transactions`** 테이블에 기록되며, 사용자는 송금 내역을 확인할 수 있습니다.

#### 송금 기능 구현
1. **송금 처리**:
   - **송금자**의 잔액을 차감하고, **수신자**의 잔액을 추가하는 방식입니다.
   - 송금 내역은 **`transactions`** 테이블에 저장됩니다.
2. **송금 내역 조회**:
   - 사용자는 **자신의 송금 내역**을 확인할 수 있습니다.
   - 송금 기록은 **`sender`**, **`receiver`**, **`amount`** 등을 포함합니다.

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

