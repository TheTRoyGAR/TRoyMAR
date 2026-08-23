const API = "https://api.troymaritime.com";
const API_KEY = "TRoyMAR-2b29c5ce8d3f52cc29a5c2dd634a94d3";

const headers = {
  "Content-Type": "application/json",
  Authorization: `Bearer ${API_KEY}`,
};

// Task IDs currently expanded to show their output — preserved across the
// 30s auto-refresh so an open task doesn't snap shut while you're reading it.
const expandedTaskIds = new Set();

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

async function checkStatus() {
  const dot = document.getElementById("status-dot");
  const label = document.getElementById("status-label");
  try {
    const res = await fetch(`${API}/api/health`, { headers });
    if (res.ok) {
      dot.classList.add("online");
      dot.classList.remove("offline");
      if (label) label.textContent = "Online";
    } else {
      dot.classList.add("offline");
      dot.classList.remove("online");
      if (label) label.textContent = "Offline";
    }
  } catch {
    dot.classList.add("offline");
    dot.classList.remove("online");
    if (label) label.textContent = "Offline";
  }
}

function renderTaskItems(tasks) {
  return tasks
    .map((t) => {
      const expanded = expandedTaskIds.has(t.id);
      const hasDetail = Boolean(t.input || t.output);
      return `
    <div class="task-item ${hasDetail ? "clickable" : ""}" data-id="${escapeHtml(t.id)}">
      <span class="task-toggle">${hasDetail ? (expanded ? "▾" : "▸") : ""}</span>
      <span class="task-dept">${escapeHtml(t.department)}</span>
      <span class="task-name">${escapeHtml(t.task)}</span>
      <span class="task-status ${escapeHtml(t.status)}">${escapeHtml(t.status)}</span>
      <span class="task-time">${formatTime(t.created_at)}</span>
    </div>
    ${hasDetail ? `
    <div class="task-detail ${expanded ? "open" : ""}" data-detail-id="${escapeHtml(t.id)}">
      ${t.input ? `<div class="task-detail-label">Input</div><pre>${escapeHtml(t.input)}</pre>` : ""}
      <div class="task-detail-label">Output</div>
      <pre>${t.output ? escapeHtml(t.output) : "(no output yet)"}</pre>
    </div>` : ""}`;
    })
    .join("");
}

async function loadTasks() {
  try {
    const res = await fetch(`${API}/api/tasks`, { headers });
    if (!res.ok) return;
    const data = await res.json();
    const tasks = data.tasks || [];

    document.getElementById("tasks-count").textContent = tasks.length;

    const list = document.getElementById("task-list");
    if (tasks.length === 0) {
      list.innerHTML = '<p class="empty-state">No tasks yet. Run an agent from any department page.</p>';
    } else {
      list.innerHTML = renderTaskItems(tasks.slice(0, 20));
    }

    // Per-department filtered lists, one per department page.
    document.querySelectorAll("[id^='dept-task-list-']").forEach((container) => {
      const dept = container.id.replace("dept-task-list-", "");
      const deptTasks = tasks.filter((t) => t.department === dept).slice(0, 20);
      container.innerHTML = deptTasks.length
        ? renderTaskItems(deptTasks)
        : '<p class="empty-state">No tasks run yet.</p>';
    });
  } catch {}
}

// Delegated click handler — attached once to <main>, which survives every
// innerHTML rebuild in every task-list container (overview + all per-dept
// pages), so it keeps working across every refresh and every page.
document.querySelector("main").addEventListener("click", (e) => {
  const item = e.target.closest(".task-item.clickable[data-id]");
  if (!item) return;
  const id = item.dataset.id;
  // A task can appear twice (Overview's all-tasks list + its own department
  // page's filtered list) — toggle every instance of both the item and its
  // detail block together so state stays consistent wherever you click it.
  const expand = !expandedTaskIds.has(id);
  if (expand) expandedTaskIds.add(id); else expandedTaskIds.delete(id);

  document.querySelectorAll(`.task-item[data-id="${CSS.escape(id)}"]`).forEach((el) => {
    const toggle = el.querySelector(".task-toggle");
    if (toggle) toggle.textContent = expand ? "▾" : "▸";
  });
  document.querySelectorAll(`.task-detail[data-detail-id="${CSS.escape(id)}"]`).forEach((el) => {
    el.classList.toggle("open", expand);
  });
});

// Memory record IDs currently expanded to show full content — same
// preserved-across-refresh pattern as expandedTaskIds above.
const expandedMemoryIds = new Set();

async function loadMemory() {
  try {
    const res = await fetch(`${API}/api/memory`, { headers });
    if (!res.ok) return;
    const data = await res.json();
    const records = data.records || [];

    document.getElementById("memory-count").textContent =
      records.length > 0 ? `— ${records.length} learnings saved` : "";

    const list = document.getElementById("memory-list");
    if (records.length === 0) {
      list.innerHTML = '<p class="empty-state">Nothing saved yet. Learnings appear here as agents complete tasks.</p>';
      return;
    }

    list.innerHTML = records
      .slice(0, 30)
      .map((r) => {
        const expanded = expandedMemoryIds.has(r.id);
        const preview = (r.content || "").slice(0, 90);
        return `
      <div class="task-item clickable" data-memory-id="${escapeHtml(r.id)}">
        <span class="task-toggle">${expanded ? "▾" : "▸"}</span>
        <span class="task-dept">${escapeHtml(r.scope || "")}</span>
        <span class="task-name">${escapeHtml(preview)}${(r.content || "").length > 90 ? "…" : ""}</span>
        <span class="task-time">${formatTime(r.created_at)}</span>
      </div>
      <div class="task-detail ${expanded ? "open" : ""}" data-memory-detail-id="${escapeHtml(r.id)}">
        <div class="task-detail-label">Categories</div><pre>${escapeHtml((r.categories || []).join(", ") || "—")}</pre>
        <div class="task-detail-label">Full Content</div><pre>${escapeHtml(r.content)}</pre>
      </div>`;
      })
      .join("");
  } catch {}
}

document.getElementById("memory-list").addEventListener("click", (e) => {
  const item = e.target.closest(".task-item.clickable[data-memory-id]");
  if (!item) return;
  const id = item.dataset.memoryId;
  const detail = document.querySelector(`.task-detail[data-memory-detail-id="${CSS.escape(id)}"]`);
  if (!detail) return;

  if (expandedMemoryIds.has(id)) {
    expandedMemoryIds.delete(id);
    detail.classList.remove("open");
    item.querySelector(".task-toggle").textContent = "▸";
  } else {
    expandedMemoryIds.add(id);
    detail.classList.add("open");
    item.querySelector(".task-toggle").textContent = "▾";
  }
});

async function queueTask(dept, task, input = "") {
  try {
    const res = await fetch(`${API}/api/tasks`, {
      method: "POST",
      headers,
      body: JSON.stringify({ department: dept, task, input }),
    });
    if (res.ok) {
      await loadTasks();
    }
  } catch {}
}

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso + "Z");
  return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

// Orchestrator brief button
const briefBtn = document.getElementById("brief-btn");
const briefInput = document.getElementById("brief-input");

briefBtn.addEventListener("click", async () => {
  const input = briefInput.value.trim();
  if (!input) {
    briefInput.focus();
    return;
  }
  briefBtn.textContent = "Queued...";
  briefBtn.disabled = true;
  await queueTask("orchestrator", "intake_brief", input);
  briefInput.value = "";
  setTimeout(() => {
    briefBtn.textContent = "Run Brief";
    briefBtn.disabled = false;
  }, 2000);
});

briefInput.addEventListener("keydown", (e) => {
  // Plain Enter inserts a newline (it's a multi-line textarea now) —
  // Ctrl/Cmd+Enter submits, same convention as most chat/compose boxes.
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) briefBtn.click();
});

// Sales — Find Opportunities (needs a real target description, not a bare click)
const opportunityBtn = document.getElementById("opportunity-btn");
const opportunityInput = document.getElementById("opportunity-input");
if (opportunityBtn) {
  opportunityBtn.addEventListener("click", async () => {
    const input = opportunityInput.value.trim();
    if (!input) {
      opportunityInput.focus();
      return;
    }
    opportunityBtn.textContent = "Researching...";
    opportunityBtn.disabled = true;
    await queueTask("sales", "find_opportunities", input);
    setTimeout(() => {
      opportunityBtn.textContent = "Find Opportunities (research + report only, never sends)";
      opportunityBtn.disabled = false;
    }, 2000);
  });
}

// Department run buttons
document.querySelectorAll(".run-btn:not(#brief-btn)").forEach((btn) => {
  btn.dataset.label = btn.textContent.trim();

  btn.addEventListener("click", () => {
    const dept = btn.dataset.dept;
    const task = btn.dataset.task;
    btn.textContent = "Queued...";
    btn.disabled = true;
    queueTask(dept, task).finally(() => {
      setTimeout(() => {
        btn.textContent = btn.dataset.label;
        btn.disabled = false;
      }, 2000);
    });
  });
});

// Page router — hash-based, e.g. #/marketing
const PAGE_TITLES = {
  overview: "Overview",
  management: "Management",
  marketing: "Marketing",
  sales: "Sales",
  finance: "Finance",
  shipping: "Shipping",
};
const VALID_PAGES = Object.keys(PAGE_TITLES);

function showPage(page) {
  if (!VALID_PAGES.includes(page)) page = "overview";
  document.querySelectorAll(".page").forEach((p) => {
    p.style.display = p.id === `page-${page}` ? "block" : "none";
  });
  document.querySelectorAll(".nav-item").forEach((a) => {
    a.classList.toggle("active", a.dataset.page === page);
  });
  const title = document.getElementById("page-title");
  if (title) title.textContent = PAGE_TITLES[page];
}

function routeFromHash() {
  const page = (location.hash || "#/overview").replace(/^#\//, "");
  showPage(page);
}

window.addEventListener("hashchange", routeFromHash);
routeFromHash();

// Collapsible sidebar
const collapseBtn = document.getElementById("sidebar-collapse-btn");
if (collapseBtn) {
  collapseBtn.addEventListener("click", () => {
    document.querySelector(".app-shell").classList.toggle("collapsed");
  });
}

checkStatus();
loadTasks();
loadMemory();
setInterval(loadTasks, 30000);
setInterval(loadMemory, 30000);
setInterval(checkStatus, 60000);
