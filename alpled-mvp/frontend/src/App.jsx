import { useEffect, useState } from "react";
import { checkTsHealth, getTsDocxDownloadUrl, getTsJsonDownloadUrl, getTsResult, runTsAgent } from "./api";

export default function App() {
  const [health, setHealth] = useState(null);
  const [inputFile, setInputFile] = useState(null);
  const [uiFile, setUiFile] = useState(null);
  const [model, setModel] = useState("qwen3b");
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function refreshHealth() {
    try {
      setHealth(await checkTsHealth());
    } catch {
      setHealth(null);
    }
  }

  useEffect(() => {
    refreshHealth();
  }, []);

  async function handleRun() {
    if (!inputFile) {
      setMessage("요구사항 JSON 파일을 선택하세요.");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      const data = await runTsAgent({ inputFile, uiFile, model });
      setResult(data.data);
      setMessage("TS Agent 실행 완료");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadLatest() {
    setLoading(true);
    try {
      const data = await getTsResult();
      setResult(data.data);
      setMessage("최근 결과를 불러왔습니다.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  const scenarios = result?.scenarios || [];

  return (
    <div className="page">
      <aside className="sidebar">
        <div className="logo">A</div>
        <h2>ALPLED CORE</h2>
        <p>CBD D10 통합시험 시나리오 자동 생성 MVP</p>
        <button onClick={refreshHealth}>API 상태 확인</button>
        <div className={health ? "status ok" : "status bad"}>{health ? "TS API Online" : "TS API Offline"}</div>
      </aside>

      <main className="main">
        <section className="hero">
          <p className="eyebrow">Final Project MVP</p>
          <h1>요구사항 JSON 기반 통합시험 시나리오 생성</h1>
          <p>요구사항 정의서와 UI 설계서 JSON을 업로드하면 TS Agent가 D10 형식의 시나리오와 케이스를 생성합니다.</p>

          <div className="controls">
            <label>
              모델
              <select value={model} onChange={(e) => setModel(e.target.value)}>
                <option value="qwen3b">qwen3b</option>
                <option value="qwen">qwen</option>
                <option value="exaone2b">exaone2b</option>
                <option value="exaone">exaone</option>
              </select>
            </label>
            <label>
              요구사항 JSON
              <input type="file" accept=".json" onChange={(e) => setInputFile(e.target.files?.[0] || null)} />
            </label>
            <label>
              UI JSON 선택사항
              <input type="file" accept=".json" onChange={(e) => setUiFile(e.target.files?.[0] || null)} />
            </label>
          </div>

          <div className="actions">
            <button onClick={handleRun} disabled={loading}>{loading ? "실행 중..." : "TS Agent 실행"}</button>
            <button className="secondary" onClick={loadLatest} disabled={loading}>최근 결과</button>
            <a href={getTsJsonDownloadUrl()}>JSON 다운로드</a>
            <a href={getTsDocxDownloadUrl()}>DOCX 다운로드</a>
          </div>

          {message && <pre className="message">{message}</pre>}
        </section>

        <section className="grid">
          <div className="panel">
            <h2>생성 시나리오</h2>
            {scenarios.length === 0 ? <p className="empty">아직 결과가 없습니다.</p> : scenarios.map((s) => (
              <article className="card" key={s.scenario_id}>
                <span>{s.scenario_id}</span>
                <h3>{s.scenario_name}</h3>
                <p>{s.scenario_description}</p>
                {(s.test_cases || []).map((tc) => (
                  <div className="case" key={tc.test_case_id}>
                    <b>{tc.test_case_id}</b> {tc.test_case_description}
                  </div>
                ))}
              </article>
            ))}
          </div>
          <div className="panel">
            <h2>Raw JSON</h2>
            <pre className="json">{JSON.stringify(result || {}, null, 2)}</pre>
          </div>
        </section>
      </main>
    </div>
  );
}
