# 책마루 도서 대여 서비스

FastAPI와 Jinja2 서버 렌더링으로 도서 등록, 대여, 반납 및 사용자별 대여 이력을 관리하는 예제 서비스입니다. 사용자, 도서, 대여 데이터는 SQLAlchemy와 SQLite에 저장됩니다.

## 주요 기능과 사용자 흐름

1. 회원가입 또는 데모 계정으로 로그인합니다.
2. 도서를 조회하고 새 도서를 등록합니다.
3. 대여 가능한 도서를 대여한 뒤, 내 대여 내역에서 반납 완료 상태로 변경합니다.
4. 대여 화면은 대여자와 도서의 관계 데이터를 함께 보여줍니다.

비밀번호는 Python 표준 라이브러리의 PBKDF2-HMAC-SHA256으로 해시합니다. 로그인 정보는 Starlette `SessionMiddleware`의 서명된 쿠키에 사용자 ID로 저장하며, 별도 인증 서버나 토큰 발급 절차 없이 브라우저 SSR 요청에 일관되게 사용할 수 있습니다. 쿠키 변조는 서명으로 탐지하며 로그아웃 시 세션을 지웁니다. 이 방식은 서버 측 세션 저장소를 추가하지 않는 소규모 단일 서비스에 적합합니다.

`User -> Loan`과 `Book -> Loan`은 각각 1:N, 반대 방향은 N:1 관계입니다. 대여 레코드는 이력 보존을 위해 사용자나 도서 삭제 시 cascade 삭제하지 않고 외래 키 `RESTRICT` 정책을 사용합니다.

## 요구 사항 및 설치

- Python 3.10+
- FastAPI 0.115.12
- Uvicorn 0.34.0
- SQLAlchemy 2.0.40
- Jinja2 3.1.6
- python-multipart 0.0.20
- itsdangerous 2.2.0 (Starlette 서명 세션 쿠키)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

첫 실행 시 `library.db`와 데모 도서가 생성됩니다. 기본 계정은 아이디 `demo`, 비밀번호 `demo1234`입니다. 로그인 이후 비밀번호를 변경하는 기능은 없으므로 데모용으로만 사용하세요.

운영 환경에서는 반드시 충분히 무작위인 `SESSION_SECRET`을 설정하세요. 기본 키는 개발 편의용 공개 값이므로 실제 배포에 사용하면 안 됩니다. HTTPS 배포 시 `COOKIE_SECURE=true`도 설정합니다. `DATABASE_URL`로 데이터베이스 연결 문자열을 바꿀 수 있으며 기본값은 `sqlite:///./library.db`입니다.

```bash
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export COOKIE_SECURE=true  # HTTPS 배포에서만 활성화
```

## 경로

| 경로 | 공개 여부 | 설명 |
|---|---|---|
| `GET /` | 공개 | 서비스 소개 및 로그인 상태에 따른 진입 링크 |
| `GET, POST /login` | 공개 | 로그인 화면 및 인증 |
| `GET, POST /register` | 공개 | 회원가입 및 가입 후 로그인 |
| `POST /logout` | 공개 | 세션 종료 |
| `GET /library/books` | 보호 | 도서 목록과 등록 폼 |
| `POST /library/books` | 보호 | 도서 등록 |
| `POST /library/books/{book_id}/borrow` | 보호 | 도서 대여 |
| `GET /library/loans` | 보호 | 현재 사용자의 대여 이력 |
| `POST /library/loans/{loan_id}/return` | 보호 | 본인 대여 건을 반납 완료로 변경 |

인증되지 않은 보호 경로 요청은 `303 See Other`로 `/login`에 이동합니다. 모든 보호 경로는 `app/auth/dependencies.py`의 `require_user`를 `Depends`로 적용합니다. 인증(누구인지 확인)은 공통 의존성이 수행하고, 반납 시 본인 대여인지 확인하는 인가 검사는 서비스 계층에서 별도로 수행합니다.

## 테스트

```bash
python -m unittest discover -v
```

테스트는 비밀번호 해시 검증, 사용자-도서-대여 관계 조회, 대여/반납 상태 전환, 중복 대여 방지와 타인 대여 건 반납 차단을 확인합니다.
