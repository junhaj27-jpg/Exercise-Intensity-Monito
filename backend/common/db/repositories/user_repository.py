from __future__ import annotations

from typing import Any

from backend.auth_users import DEMO_USERS
from backend.common.db.connection import db_connection
from backend.common.db.security import hash_password, verify_password


def seed_demo_users() -> None:
    sql = """
        INSERT INTO tbl_user (
            employee_no,
            name,
            role,
            password_hash,
            first_login,
            is_active,
            crt_dt,
            mdfcn_dt
        )
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            role = VALUES(role),
            is_active = VALUES(is_active),
            mdfcn_dt = NOW()
    """
    with db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                for user in DEMO_USERS:
                    cursor.execute(
                        sql,
                        (
                            user["employee_no"],
                            user["name"],
                            user["role"],
                            hash_password(user["temp_password"]),
                            bool(user["first_login"]),
                            bool(user["is_active"]),
                        ),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def get_user_by_employee_no(employee_no: str) -> dict[str, Any] | None:
    sql = """
        SELECT
            user_sn,
            employee_no,
            name,
            role,
            password_hash,
            first_login,
            is_active
        FROM tbl_user
        WHERE employee_no = %s
        LIMIT 1
    """
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (employee_no,))
            return cursor.fetchone()


def list_users() -> list[dict[str, Any]]:
    sql = """
        SELECT
            user_sn,
            employee_no,
            name,
            role,
            first_login,
            is_active
        FROM tbl_user
        ORDER BY user_sn
    """
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


def authenticate_user(employee_no: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_employee_no(employee_no)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


def update_password(employee_no: str, new_password: str) -> None:
    sql = """
        UPDATE tbl_user
        SET password_hash = %s,
            first_login = 0,
            mdfcn_dt = NOW()
        WHERE employee_no = %s
    """
    with db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hash_password(new_password), employee_no))
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def get_system_user_sn() -> int:
    user = get_user_by_employee_no("ALPLED-ROOT-01")
    return int(user["user_sn"]) if user else 1
