from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

LAST_JSON = OUTPUT_DIR / "latest_ts_result.json"
LAST_DOCX = OUTPUT_DIR / "latest_ts_result.docx"

app = FastAPI(title="ALPLED TS Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def save_upload(file: UploadFile, prefix: str) -> Path:
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="JSON 파일만 업로드할 수 있습니다.")
    path = UPLOAD_DIR / f"{prefix}_{uuid.uuid4().hex}_{Path(file.filename).name}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return path


def read_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_latest(patterns: list[str]) -> Path | None:
    files = []
    for pattern in patterns:
        files += list(BASE_DIR.glob(pattern))
        files += list(UPLOAD_DIR.glob(pattern))
    files = [p for p in files if p.exists()]
    if not files:
        return None
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[0]


@app.get("/api/ts/health")
def health():
    return {
        "backend": "ok",
        "mode": "TS_agent API",
        "ts_agent_exists": (BASE_DIR / "TS_agent.py").exists(),
        "ts_prompt_exists": (BASE_DIR / "TS_prompt.py").exists(),
    }


@app.post("/api/ts/generate")
async def generate_ts(
    input_file: UploadFile = File(...),
    ui_file: UploadFile | None = File(None),
    model: str = Form("qwen3b"),
):
    agent = BASE_DIR / "TS_agent.py"
    prompt = BASE_DIR / "TS_prompt.py"
    if not agent.exists():
        raise HTTPException(status_code=500, detail="TS_agent.py가 없습니다.")
    if not prompt.exists():
        raise HTTPException(status_code=500, detail="TS_prompt.py가 없습니다.")

    input_path = save_upload(input_file, "input")
    ui_path = save_upload(ui_file, "ui") if ui_file else None

    output_path = OUTPUT_DIR / f"{input_path.stem}_output.json"
    cmd = [sys.executable, str(agent), "--model", model, "--input", str(input_path), "--output", str(output_path)]
    if ui_path:
        cmd.extend(["--ui", str(ui_path)])

    try:
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="TS_agent 실행 시간이 초과되었습니다.")

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "TS_agent 실행 실패",
                "stdout": result.stdout[-3000:],
                "stderr": result.stderr[-3000:],
                "cmd": cmd,
            },
        )

    output_json = output_path if output_path.exists() else find_latest(["*output*.json", "*result*.json"])
    output_docx = output_json.with_suffix(".docx") if output_json else None

    if not output_json or not output_json.exists():
        raise HTTPException(status_code=500, detail="실행은 됐지만 결과 JSON을 찾지 못했습니다.")

    shutil.copyfile(output_json, LAST_JSON)
    if output_docx and output_docx.exists():
        shutil.copyfile(output_docx, LAST_DOCX)

    return {
        "backend": "ok",
        "message": "TS_agent 실행 완료",
        "data": read_json(LAST_JSON),
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


@app.get("/api/ts/result")
def result():
    return {"backend": "ok", "data": read_json(LAST_JSON)}


@app.get("/api/ts/download-json")
def download_json():
    if not LAST_JSON.exists():
        raise HTTPException(status_code=404, detail="결과 JSON이 없습니다.")
    return FileResponse(LAST_JSON, filename="ts_result.json", media_type="application/json")


@app.get("/api/ts/download-docx")
def download_docx():
    if not LAST_DOCX.exists():
        raise HTTPException(status_code=404, detail="결과 DOCX가 없습니다.")
    return FileResponse(
        LAST_DOCX,
        filename="ts_result.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
