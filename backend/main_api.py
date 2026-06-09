from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.auth_users import DEMO_USERS
from backend.common.db.connection import DatabaseUnavailable, ensure_database
from backend.common.db.repositories import document_repository, user_repository

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STATE_DIR = BACKEND_DIR / "json_temp"
UPLOAD_DIR = BACKEND_DIR / "uploads"
USER_STATE_PATH = STATE_DIR / "user_state.json"
DOCUMENT_STATE_PATH = STATE_DIR / "documents.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_READY = False
DB_ERROR: str | None = None

app = FastAPI(title="ALPLED API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    id: str | None = None
    employee_no: str | None = None
    password: str
    role: str | None = "user"


class AuthLoginRequest(BaseModel):
    employee_no: str
    password: str


class ChangePasswordRequest(BaseModel):
    employee_no: str
    current_password: str
    new_password: str


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() not in {"0", "false", "no", "off"}


def _db_enabled() -> bool:
    return _flag("DB_ENABLED", True)


def _db_required() -> bool:
    return _flag("DB_REQUIRED", False)


def _role_allowed(user_role: str, requested_role: str | None) -> bool:
    normalized = (requested_role or "user").upper()
    if normalized == "ADMIN":
        return user_role in {"ADMIN", "SUPER_ADMIN"}
    return True


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "employee_no": user["employee_no"],
        "name": user["name"],
        "role": user["role"],
        "first_login": bool(user["first_login"]),
        "is_active": bool(user["is_active"]),
    }


def _load_json(path: Path, default: Any) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_json_users() -> dict[str, dict[str, Any]]:
    users = {
        user["employee_no"]: {
            "employee_no": user["employee_no"],
            "name": user["name"],
            "role": user["role"],
            "password": user["temp_password"],
            "first_login": user["first_login"],
            "is_active": user["is_active"],
        }
        for user in DEMO_USERS
    }
    return _load_json(USER_STATE_PATH, users)


def _json_documents() -> list[dict[str, Any]]:
    return _load_json(DOCUMENT_STATE_PATH, [])


def _save_json_documents(documents: list[dict[str, Any]]) -> None:
    _save_json(DOCUMENT_STATE_PATH, documents)


@app.on_event("startup")
def startup() -> None:
    global DB_READY, DB_ERROR

    if not _db_enabled():
        DB_READY = False
        DB_ERROR = "DB_ENABLED=false"
        _seed_json_users()
        return

    try:
        ensure_database()
        user_repository.seed_demo_users()
        DB_READY = True
        DB_ERROR = None
    except DatabaseUnavailable as exc:
        DB_READY = False
        DB_ERROR = str(exc)
        if _db_required():
            raise
        _seed_json_users()


def _login_with_db(employee_no: str, password: str, requested_role: str | None) -> dict[str, Any]:
    user = user_repository.authenticate_user(employee_no, password)
    if not user:
        raise HTTPException(status_code=401, detail="사원번호 또는 비밀번호가 올바르지 않습니다.")
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    if not _role_allowed(user["role"], requested_role):
        raise HTTPException(status_code=403, detail="선택한 권한으로 로그인할 수 없습니다.")
    return user


def _login_with_json(employee_no: str, password: str, requested_role: str | None) -> dict[str, Any]:
    users = _seed_json_users()
    user = users.get(employee_no)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="사원번호 또는 비밀번호가 올바르지 않습니다.")
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    if not _role_allowed(user["role"], requested_role):
        raise HTTPException(status_code=403, detail="선택한 권한으로 로그인할 수 없습니다.")
    return user


def _login(employee_no: str, password: str, requested_role: str | None) -> dict[str, Any]:
    user = (
        _login_with_db(employee_no, password, requested_role)
        if DB_READY
        else _login_with_json(employee_no, password, requested_role)
    )
    return {
        "success": True,
        **_public_user(user),
        "db_mode": DB_READY,
    }


@app.post("/api/login")
def login(req: LoginRequest):
    employee_no = (req.employee_no or req.id or "").strip()
    if not employee_no:
        raise HTTPException(status_code=400, detail="사원번호를 입력해주세요.")
    return _login(employee_no, req.password, req.role)


@app.post("/api/auth/login")
def auth_login(req: AuthLoginRequest):
    return _login(req.employee_no, req.password, None)


@app.post("/api/auth/change-password")
def change_password(req: ChangePasswordRequest):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="새 비밀번호는 8자리 이상이어야 합니다.")

    if DB_READY:
        _login_with_db(req.employee_no, req.current_password, None)
        user_repository.update_password(req.employee_no, req.new_password)
        user = user_repository.get_user_by_employee_no(req.employee_no)
    else:
        users = _seed_json_users()
        user = users.get(req.employee_no)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        if user["password"] != req.current_password:
            raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
        user["password"] = req.new_password
        user["first_login"] = False
        users[req.employee_no] = user
        _save_json(USER_STATE_PATH, users)

    return {
        "success": True,
        "message": "비밀번호가 변경되었습니다.",
        **_public_user(user),
        "db_mode": DB_READY,
    }


@app.get("/api/users")
def get_users():
    users = user_repository.list_users() if DB_READY else list(_seed_json_users().values())
    return {
        "success": True,
        "db_mode": DB_READY,
        "users": [_public_user(user) for user in users],
    }


def _save_upload(file: UploadFile | None) -> Path | None:
    if file is None or not file.filename:
        return None

    safe_name = Path(file.filename).name
    today = datetime.now().strftime("%Y%m%d")
    target_dir = UPLOAD_DIR / today
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex}_{safe_name}"

    with target.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)
    return target


def _document_response(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(document["id"]),
        "name": document["name"],
        "type": document["type"],
        "user": document.get("user", "SYSTEM"),
        "date": document.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "state": document.get("state", "등록완료"),
    }


@app.get("/api/documents")
def list_documents():
    documents = document_repository.list_documents() if DB_READY else _json_documents()
    return {
        "success": True,
        "db_mode": DB_READY,
        "documents": [_document_response(document) for document in documents],
    }


@app.post("/api/documents")
def create_document(
    name: str = Form(...),
    type: str = Form(...),
    file: UploadFile | None = File(None),
):
    path = _save_upload(file)
    stored_path = str(path) if path else ""
    display_name = name or (path.name if path else "새 문서")

    if DB_READY:
        document = document_repository.insert_document(
            name=display_name,
            document_type=type,
            file_path=stored_path,
            login_user_sn=user_repository.get_system_user_sn(),
        )
    else:
        documents = _json_documents()
        document = {
            "id": max([doc["id"] for doc in documents], default=0) + 1,
            "name": display_name,
            "type": type,
            "user": "SYSTEM",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "state": "등록완료",
            "path": stored_path,
        }
        documents.insert(0, document)
        _save_json_documents(documents)

    return {
        "success": True,
        "db_mode": DB_READY,
        "document": _document_response(document),
    }


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int):
    if DB_READY:
        deleted = document_repository.delete_document(
            document_id,
            login_user_sn=user_repository.get_system_user_sn(),
        )
    else:
        documents = _json_documents()
        remaining = [doc for doc in documents if int(doc["id"]) != document_id]
        deleted = len(remaining) != len(documents)
        _save_json_documents(remaining)

    if not deleted:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    return {"success": True, "db_mode": DB_READY}


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: int):
    document = document_repository.get_document(document_id) if DB_READY else None
    if not DB_READY:
        document = next((doc for doc in _json_documents() if int(doc["id"]) == document_id), None)

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    path = Path(document.get("path") or "")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="다운로드할 파일이 없습니다.")

    return FileResponse(path, filename=document.get("name") or path.name)


@app.get("/api/db/status")
def db_status():
    return {
        "db_enabled": _db_enabled(),
        "db_required": _db_required(),
        "db_ready": DB_READY,
        "error": DB_ERROR,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ALPLED",
        "db_ready": DB_READY,
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
