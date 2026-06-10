const params = new URLSearchParams(window.location.search);

const isHttpPage = window.location.protocol === "http:" || window.location.protocol === "https:";
const defaultApiBaseUrl = isHttpPage ? window.location.origin : "http://localhost:8000";

// FastAPI에서 서빙하면 기본으로 같은 origin의 백엔드 API를 사용합니다.
// 목업 모드는 http://localhost:8000?mock=true 처럼 명시한 경우에만 켜집니다.
const MOCK_MODE = params.get("mock") === "true";
const API_BASE_URL = params.get("api") || defaultApiBaseUrl;

const sampleDocs = [
  { id: 1, name: "요구사항 정의서 20260520.pdf", type: "RFP", user: "USER001", date: "2026-05-20 14:24", state: "등록완료" },
  { id: 2, name: "RFP 20260520.pdf", type: "RFP", user: "USER001", date: "2026-05-20 14:24", state: "등록완료" },
  { id: 3, name: "회의록 20260520.docx", type: "회의록", user: "USER001", date: "2026-05-20 14:24", state: "등록완료" },
  { id: 4, name: "추가사항20260520.pdf", type: "회의록", user: "USER001", date: "2026-05-20 14:24", state: "등록완료" },
  { id: 5, name: "SR_20260520.hwp", type: "산출물", user: "USER001", date: "2026-05-20 14:24", state: "생성완료" }
];

let docs = [];
let checked = [];
let selectedRole = "user";

const themeNames = {
  ice: "아이스 블루 + 네이비",
  cyan: "화이트 + 딥블루 + 시안",
  mint: "화이트 + 민트 블루",
  charcoal: "차콜 + 전기 블루",
  purple: "라이트 그레이 + 퍼플 블루"
};

const loginScreen = document.getElementById("loginScreen");
const workspaceScreen = document.getElementById("workspaceScreen");
const adminScreen = document.getElementById("adminScreen");
const loginMessage = document.getElementById("loginMessage");
const rows = document.getElementById("rows");
const modal = document.getElementById("modal");

function displayOnly(screen) {
  [loginScreen, workspaceScreen, adminScreen].forEach(section => {
    section.classList.add("hidden");
  });
  screen.classList.remove("hidden");
}

function showPage(id) {
  workspaceScreen.querySelectorAll(".page").forEach(page => {
    page.classList.remove("active");
  });

  const target = workspaceScreen.querySelector(`#${id}`);
  if (target) target.classList.add("active");

  workspaceScreen.querySelectorAll(".nav").forEach(nav => {
    nav.classList.toggle("active", nav.dataset.page === id);
  });
}

function applyTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem("alpledTheme", theme);

  const label = document.getElementById("activeThemeLabel");
  const select = document.getElementById("themeSelect");

  if (label) label.textContent = themeNames[theme] || themeNames.cyan;
  if (select) select.value = theme;
}

function toast(text) {
  const element = document.getElementById("toast");
  if (!element) return;

  element.textContent = text;
  element.classList.add("show");

  setTimeout(() => {
    element.classList.remove("show");
  }, 2200);
}

async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status}`);
  }

  return response.json();
}

async function loadDocs() {
  checked = [];

  if (MOCK_MODE) {
    docs = [...sampleDocs];
    render();
    return;
  }

  try {
    const result = await requestJSON(`${API_BASE_URL}/api/documents`);
    docs = Array.isArray(result) ? result : result.documents || [];
    render();
  } catch (error) {
    console.error(error);
    docs = [];
    render();
    toast("백엔드 연결 실패: 문서 목록을 불러오지 못했습니다.");
  }
}

async function loginWithApi(id, password, role) {
  const result = await requestJSON(`${API_BASE_URL}/api/login`, {
    method: "POST",
    body: JSON.stringify({ id, password, role })
  });

  return result;
}

function handleMockLogin(id, password) {
  if (selectedRole === "user" && id === "user" && password === "1234") {
    loginMessage.textContent = "";
    showPage("dashboard");
    displayOnly(workspaceScreen);
    return true;
  }

  if (selectedRole === "admin" && id === "admin" && password === "1234") {
    loginMessage.textContent = "";
    displayOnly(adminScreen);
    return true;
  }

  return false;
}

async function handleLogin(event) {
  event.preventDefault();

  const id = document.getElementById("loginId").value.trim();
  const password = document.getElementById("loginPassword").value.trim();

  if (MOCK_MODE) {
    const ok = handleMockLogin(id, password);
    if (!ok) {
      loginMessage.textContent = "선택한 권한 또는 로그인 정보가 올바르지 않습니다.";
    }
    return;
  }

  try {
    const result = await loginWithApi(id, password, selectedRole);

    if (!result.success) {
      loginMessage.textContent = result.message || "로그인 정보가 올바르지 않습니다.";
      return;
    }

    loginMessage.textContent = "";

    if (selectedRole === "admin") {
      displayOnly(adminScreen);
    } else {
      showPage("dashboard");
      displayOnly(workspaceScreen);
    }
  } catch (error) {
    console.error(error);
    loginMessage.textContent = "백엔드 로그인 API 연결에 실패했습니다.";
  }
}

function logout() {
  document.getElementById("loginForm").reset();

  selectedRole = "user";

  document.querySelectorAll(".role-tab").forEach((item, index) => {
    item.classList.toggle("active", index === 0);
  });

  document.getElementById("selectedRole").value = "user";
  loginMessage.textContent = "";

  displayOnly(loginScreen);
}

function getFiltered() {
  const category = document.getElementById("category").value;
  const q = document.getElementById("query").value.trim().toLowerCase();

  return docs.filter(doc =>
    (category === "전체 구분" || doc.type === category) &&
    (!q || doc.name.toLowerCase().includes(q))
  );
}

function render() {
  if (!rows) return;

  const list = getFiltered();

  rows.innerHTML = list.length
    ? list.map(doc => `
      <tr>
        <td>
          <input class="row" type="checkbox" value="${doc.id}" ${checked.includes(doc.id) ? "checked" : ""}>
        </td>
        <td>${doc.id}</td>
        <td>${doc.name}</td>
        <td>${doc.type}</td>
        <td>${doc.user}</td>
        <td>${doc.date}</td>
        <td>
          <i class="${doc.state === "생성완료" ? "wait" : "done"}">${doc.state}</i>
        </td>
      </tr>
    `).join("")
    : `<tr><td colspan="7">조회된 문서가 없습니다.</td></tr>`;

  const totalDocs = document.getElementById("totalDocs");
  if (totalDocs) totalDocs.textContent = `전체 ${list.length}건`;

  document.querySelectorAll(".row").forEach(box => {
    box.addEventListener("change", () => {
      const id = Number(box.value);

      checked = box.checked
        ? [...new Set([...checked, id])]
        : checked.filter(value => value !== id);
    });
  });
}

async function deleteSelectedDocs() {
  if (!checked.length) {
    toast("삭제할 문서를 선택해주세요.");
    return;
  }

  if (MOCK_MODE) {
    checked.forEach(id => {
      const index = docs.findIndex(doc => doc.id === id);
      if (index > -1) docs.splice(index, 1);
    });

    checked = [];
    render();
    toast("문서가 삭제되었습니다.");
    return;
  }

  try {
    await Promise.all(
      checked.map(id =>
        requestJSON(`${API_BASE_URL}/api/documents/${id}`, {
          method: "DELETE"
        })
      )
    );

    checked = [];
    await loadDocs();
    toast("문서가 삭제되었습니다.");
  } catch (error) {
    console.error(error);
    toast("문서 삭제 중 오류가 발생했습니다.");
  }
}

function downloadSelectedDocs() {
  if (!checked.length) {
    toast("다운로드할 문서를 선택해주세요.");
    return;
  }

  if (MOCK_MODE) {
    toast(`${checked.length}개 문서 다운로드를 요청했습니다.`);
    return;
  }

  checked.forEach(id => {
    window.open(`${API_BASE_URL}/api/documents/${id}/download`, "_blank");
  });
}

async function submitDocument() {
  const name = document.getElementById("newName").value.trim();
  const type = document.getElementById("newType").value;
  const fileInput = document.getElementById("fileInput");

  if (!name) {
    toast("문서명을 입력해주세요.");
    return;
  }

  if (MOCK_MODE) {
    docs.push({
      id: docs.length ? Math.max(...docs.map(doc => doc.id)) + 1 : 1,
      name,
      type,
      user: "USER001",
      date: getNowText(),
      state: "등록완료"
    });

    modal.classList.remove("show");
    render();
    showPage("documents");
    toast("문서가 등록되었습니다.");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("name", name);
    formData.append("type", type);

    if (fileInput.files[0]) {
      formData.append("file", fileInput.files[0]);
    }

    const response = await fetch(`${API_BASE_URL}/api/documents`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`문서 등록 실패: ${response.status}`);
    }

    modal.classList.remove("show");
    await loadDocs();
    showPage("documents");
    toast("문서가 등록되었습니다.");
  } catch (error) {
    console.error(error);
    toast("문서 등록 중 오류가 발생했습니다.");
  }
}

function getNowText() {
  const now = new Date();

  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const mi = String(now.getMinutes()).padStart(2, "0");

  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(localStorage.getItem("alpledTheme") || "cyan");
  displayOnly(loginScreen);
  loadDocs();

  if (!MOCK_MODE) {
    toast("실제 API 모드로 실행 중입니다.");
  }
});

document.querySelectorAll(".role-tab").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".role-tab").forEach(item => {
      item.classList.remove("active");
    });

    button.classList.add("active");
    selectedRole = button.dataset.role;

    document.getElementById("selectedRole").value = selectedRole;
    loginMessage.textContent = "";
  });
});

document.getElementById("loginForm").addEventListener("submit", handleLogin);

document.getElementById("themeSelect").addEventListener("change", event => {
  applyTheme(event.target.value);
  toast(`테마가 ${themeNames[event.target.value]}(으)로 변경되었습니다.`);
});

document.getElementById("userLogoutBtn").addEventListener("click", logout);
document.getElementById("adminLogoutBtn").addEventListener("click", logout);

workspaceScreen.querySelectorAll(".nav").forEach(nav => {
  nav.addEventListener("click", () => showPage(nav.dataset.page));
});

const goDocumentsButton = workspaceScreen.querySelector(".go-documents");
if (goDocumentsButton) {
  goDocumentsButton.addEventListener("click", () => showPage("documents"));
}

document.getElementById("searchBtn").addEventListener("click", render);

document.getElementById("category").addEventListener("change", render);

document.getElementById("query").addEventListener("keydown", event => {
  if (event.key === "Enter") render();
});

document.getElementById("selectAll").addEventListener("change", event => {
  checked = event.target.checked ? getFiltered().map(doc => doc.id) : [];
  render();
});

document.getElementById("deleteBtn").addEventListener("click", deleteSelectedDocs);

document.getElementById("downloadBtn").addEventListener("click", downloadSelectedDocs);

document.querySelectorAll(".open-modal").forEach(button => {
  button.addEventListener("click", () => modal.classList.add("show"));
});

document.getElementById("modalClose").addEventListener("click", () => {
  modal.classList.remove("show");
});

document.getElementById("modalCancel").addEventListener("click", () => {
  modal.classList.remove("show");
});

document.getElementById("fileInput").addEventListener("change", event => {
  if (event.target.files[0]) {
    document.getElementById("filename").textContent = event.target.files[0].name;
  }
});

document.getElementById("submit").addEventListener("click", submitDocument);
