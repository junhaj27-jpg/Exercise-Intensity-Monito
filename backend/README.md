# ALPLED Web Backend

FastAPI 기반 웹 백엔드입니다. `frontend/` 정적 화면을 서빙하고, 로그인/사용자/문서 관리 API를 MySQL DB와 연결합니다.

## 실행

```bash
pip install -r backend/requirements.txt
copy .env.example .env
uvicorn backend.main_api:app --host 0.0.0.0 --port 8000 --reload
```

프론트는 기본 목업 모드로 열립니다. 실제 API를 확인하려면 다음 주소를 사용합니다.

```text
http://localhost:8000/?mock=false&api=http://localhost:8000
```

## DB 설정

`.env`에 MySQL 접속 정보를 입력합니다.

```env
DB_ENABLED=true
DB_REQUIRED=false
DB_HOST=localhost
DB_PORT=3306
DB_NAME=alpled_db
DB_USER=alpled
DB_PASSWORD=alpled
```

서버 시작 시 `backend/db/schema.sql` 기준으로 DB와 테이블을 자동 생성하고, `backend/auth_users.py`의 데모 계정을 시드합니다.

`DB_REQUIRED=false`이면 DB 연결이 실패해도 JSON fallback으로 개발 서버가 뜹니다. DB 연결 실패를 배포 오류로 처리하려면 `DB_REQUIRED=true`로 바꾸세요.

## API

- `POST /api/login`
- `POST /api/auth/login`
- `POST /api/auth/change-password`
- `GET /api/users`
- `GET /api/documents`
- `POST /api/documents`
- `DELETE /api/documents/{document_id}`
- `GET /api/documents/{document_id}/download`
- `GET /api/db/status`
