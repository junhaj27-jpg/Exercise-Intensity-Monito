# ALPLED MVP

CBD 산출물 기준의 통합시험 시나리오 자동 생성 MVP입니다.

이 폴더는 기존 프로젝트를 망가뜨리지 않도록 `alpled-mvp/` 하위에 독립 실행 구조로 정리했습니다.

## 구조

```text
alpled-mvp/
  backend/
    TS_agent.py          # Ollama 기반 통합시험 시나리오 생성 CLI
    TS_prompt.py         # D10 통합시험 시나리오 프롬프트
    ts_api.py            # FastAPI 브릿지 API
    requirements.txt
  data/
    sample_requirements.json
    sample_ui.json
    training_examples.jsonl
  frontend/
    package.json
    index.html
    src/
  huggingface/
    README.md            # Hugging Face Space용 README 예시
```

## 1. 로컬/RunPod 백엔드 실행

```bash
cd alpled-mvp/backend
pip install -r requirements.txt
```

Ollama 설치 후 서버 실행:

```bash
ollama serve
```

작은 모델 테스트:

```bash
ollama pull qwen2.5:3b
ollama pull exaone3.5:2.4b
```

API 서버 실행:

```bash
uvicorn ts_api:app --host 0.0.0.0 --port 8001
```

확인:

```text
http://localhost:8001/api/ts/health
```

## 2. CLI로 직접 실행

```bash
cd alpled-mvp/backend
python TS_agent.py --model qwen3b --input ../data/sample_requirements.json --ui ../data/sample_ui.json
```

실행 결과:

```text
sample_requirements_output.json
sample_requirements_output.docx
```

## 3. 프론트 실행

```bash
cd alpled-mvp/frontend
npm install
cp .env.example .env
npm run dev
```

접속:

```text
http://localhost:5173
```

## 4. Hugging Face에 올릴 때

`frontend/` 안의 파일을 Hugging Face Static Space 루트에 올리고, `README.md`는 `huggingface/README.md` 내용을 사용하세요.

`.env` 예시:

```env
VITE_TS_API_BASE_URL=https://YOUR_BACKEND_URL
```

PC 원격 실행은 Cloudflare Tunnel을 사용하면 됩니다.

```bash
cloudflared tunnel --url http://localhost:8001
```

생성된 `https://xxxx.trycloudflare.com` 주소를 Hugging Face `.env`의 `VITE_TS_API_BASE_URL`에 넣으면 됩니다.

## 5. 학습용 데이터

`data/training_examples.jsonl`은 요구사항/UI 입력과 통합시험 시나리오 출력 예시를 담은 JSONL입니다. 모델 파인튜닝용 원천이라기보다는 프롬프트 평가/샘플 학습/데모 테스트용 데이터입니다.
