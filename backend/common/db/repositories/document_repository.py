from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.common.db.connection import db_connection


def list_documents(prj_sn: int = 1) -> list[dict[str, Any]]:
    sql = """
        SELECT
            f.file_sn AS id,
            f.file_nm AS name,
            f.file_cd AS type,
            COALESCE(u.employee_no, 'SYSTEM') AS user,
            DATE_FORMAT(f.crt_dt, '%%Y-%%m-%%d %%H:%%i') AS date,
            f.doc_state AS state,
            f.file_path AS path
        FROM tbl_file f
        LEFT JOIN tbl_user u
          ON f.creatr_sn = u.user_sn
        WHERE f.prj_sn = %s
          AND f.del_yn = 'N'
        ORDER BY f.file_sn DESC
    """
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (prj_sn,))
            return cursor.fetchall()


def get_document(document_id: int, prj_sn: int = 1) -> dict[str, Any] | None:
    sql = """
        SELECT
            file_sn AS id,
            file_nm AS name,
            file_cd AS type,
            file_path AS path,
            file_size,
            file_ext,
            doc_state AS state
        FROM tbl_file
        WHERE file_sn = %s
          AND prj_sn = %s
          AND del_yn = 'N'
        LIMIT 1
    """
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (document_id, prj_sn))
            return cursor.fetchone()


def insert_document(
    *,
    name: str,
    document_type: str,
    file_path: str,
    login_user_sn: int,
    prj_sn: int = 1,
) -> dict[str, Any]:
    path = Path(file_path)
    sql = """
        INSERT INTO tbl_file (
            prj_sn,
            file_cd,
            file_nm,
            file_path,
            file_size,
            file_ext,
            doc_state,
            del_yn,
            crt_dt,
            creatr_sn,
            mdfcn_dt,
            mdfr_sn
        )
        VALUES (%s, %s, %s, %s, %s, %s, '등록완료', 'N', NOW(), %s, NOW(), %s)
    """
    with db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        prj_sn,
                        document_type,
                        name or path.name,
                        str(path),
                        path.stat().st_size if path.exists() else 0,
                        path.suffix.lstrip(".").lower()[:20],
                        login_user_sn,
                        login_user_sn,
                    ),
                )
                document_id = int(cursor.lastrowid)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    document = get_document(document_id, prj_sn=prj_sn)
    if not document:
        raise FileNotFoundError(f"Inserted document was not found: {document_id}")
    return document


def delete_document(document_id: int, login_user_sn: int, prj_sn: int = 1) -> bool:
    sql = """
        UPDATE tbl_file
        SET del_yn = 'Y',
            mdfcn_dt = NOW(),
            mdfr_sn = %s
        WHERE file_sn = %s
          AND prj_sn = %s
          AND del_yn = 'N'
    """
    with db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (login_user_sn, document_id, prj_sn))
                changed = cursor.rowcount > 0
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return changed
