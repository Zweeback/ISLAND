const fallbackTasks = [
  { task_id: "JULES-P0-001", title: "Review and resolve ISLAND security PR #55 command injection", priority: "P0", agent_target: "jules", status: "queued" },
  { task_id: "JULES-P0-002", title: "Review and resolve ISLAND security PR #53 SSRF/path traversal", priority: "P0", agent_target: "jules", status: "queued" },
  { task_id: "ANTI-P0-001", title: "Build ISLAND multi-agent operating model", priority: "P0", agent_target: "antigravity", status: "queued" },
  { task_id: "ANTI-P1-002", title: "Map AI Studio and Drive inventory signals to APPS candidates", priority: "P1", agent_target: "antigravity", status: "queued" },
  { task_id: "CODEX-P0-001", title: "Classify Drive inventory CSV into registry proposal", priority: "P0", agent_target: "codex_subagent", status: "queued" }
];

const feed = [
  { source: "GitHub", title: "Control Plane merged", detail: "PR #62 landed registry schemas and task queue." },
  { source: "Drive", title: "Inventory CSV is the source material", detail: "Classify it into registries, do not blindly sync." },
  { source: "AI Studio", title: "Projects need export status", detail: "metadata_only, export_needed, exported_code, imported_to_apps." },
  { source: "Alice", title: "3D asset slot ready", detail: "Load local alice_full.glb on the machine that has the asset." },
  { source: "Agents", title: "Routing model fixed", detail: "Jules for GitHub PRs, Antigravity for workbench flow, Codex local." }
];

const projects = [
  { name: "alice", status: "3D persona", pct: 42 },
  { name: "gta-dortmund", status: "simulation target", pct: 24 },
  { name: "grimm", status: "lore graph", pct: 28 },
  { name: "feednoodle", status: "livefeed browser", pct: 36 },
  { name: "promptdex", status: "prompt hub", pct: 31 },
  { name: "RAG source", status: "knowledge base", pct: 38 }
];

const agents = [
  { name: "Codex", role: "local coordinator", state: "active" },
  { name: "Jules", role: "GitHub PR worker", state: "task queue seeded" },
  { name: "Antigravity", role: "multi-agent workbench", state: "task packet ready" },
  { name: "AI Studio", role: "prototype source", state: "export required" }
];

function parseJsonl(text) {
  return text.split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => JSON.parse(line));
}

async function loadTasks() {
  try {
    const response = await fetch("../../03_MANIFESTE_INVENTAR/task_queue.jsonl", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    document.getElementById("taskSource").textContent = "repo task_queue.jsonl";
    return parseJsonl(await response.text());
  } catch (error) {
    document.getElementById("taskSource").textContent = "fallback task data";
    return fallbackTasks;
  }
}

function renderFeed() {
  document.getElementById("feedList").innerHTML = feed.map(item => `
    <article class="feed-item">
      <span class="tag">${item.source}</span>
      <div>
        <strong>${item.title}</strong>
        <span class="small">${item.detail}</span>
      </div>
      <span class="small">now</span>
    </article>
  `).join("");
}

function renderProjects() {
  document.getElementById("projectGrid").innerHTML = projects.map(project => `
    <article class="project-card">
      <strong>${project.name}</strong>
      <span class="small">${project.status}</span>
      <div class="progress"><span style="width:${project.pct}%"></span></div>
    </article>
  `).join("");
}

function renderAgents() {
  document.getElementById("agentList").innerHTML = agents.map(agent => `
    <article class="agent-card">
      <strong>${agent.name}</strong>
      <span class="small">${agent.role}</span>
      <div class="small">${agent.state}</div>
    </article>
  `).join("");
}

function renderTasks(tasks) {
  document.getElementById("taskList").innerHTML = tasks.map(task => `
    <article class="task-card ${(task.priority || "P2").toLowerCase()}">
      <span class="tag">${task.priority || "P2"} / ${task.agent_target || "agent"}</span>
      <strong>${task.title}</strong>
      <span class="small">${task.task_id || "untracked"} - ${task.status || "unknown"}</span>
    </article>
  `).join("");
}

function wireAliceLoader() {
  const input = document.getElementById("aliceFile");
  const viewer = document.getElementById("aliceViewer");
  const empty = document.getElementById("aliceEmpty");
  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    viewer.src = url;
    empty.style.display = "none";
  });
}

async function init() {
  renderFeed();
  renderProjects();
  renderAgents();
  renderTasks(await loadTasks());
  wireAliceLoader();
}

init();
