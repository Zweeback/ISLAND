let catalog = [];

const terminal = () => document.getElementById("agent-terminal");
const text = (value) => document.createTextNode(String(value ?? ""));

function addTerminalLog(level, message) {
  const line = document.createElement("div");
  line.className = `log-line ${level}`;
  const timestamp = new Date().toISOString().slice(11, 19);
  line.appendChild(text(`[${timestamp}] [${level.toUpperCase()}] ${message}`));
  terminal().appendChild(line);
  terminal().scrollTop = terminal().scrollHeight;
}

async function fetchStatus() {
  try {
    const response = await fetch("/api/status");
    const status = await response.json();
    catalog = [];
    for (const source of Object.keys(status)) {
      updateBadgeUI(source, status[source].status || "idle");
      for (const item of status[source].files || []) {
        catalog.push({ ...item, scan_source: source });
      }
    }
    renderCatalog();
  } catch (error) {
    addTerminalLog("error", "Dashboard API is not reachable.");
  }
}

async function triggerScan(source) {
  updateBadgeUI(source, "scanning");
  addTerminalLog("info", `Requesting ${source} scan.`);
  try {
    const response = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "scan failed");
    addTerminalLog("success", `${source} scan indexed ${data.file_count} entries.`);
    await fetchStatus();
  } catch (error) {
    updateBadgeUI(source, "error");
    addTerminalLog("error", `${source} scan failed: ${error.message}`);
  }
}

async function createTemplate(event) {
  event.preventDefault();
  const type = document.getElementById("template-type").value;
  const name = document.getElementById("template-name").value;
  addTerminalLog("info", `Generating ${type} template: ${name}`);
  try {
    const response = await fetch("/api/template", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, name }),
    });
    if (!response.ok) throw new Error("template request failed");
    const blob = await response.blob();
    const header = response.headers.get("Content-Disposition") || "";
    const match = /filename="([^"]+)"/.exec(header);
    const filename = match ? match[1] : "template.txt";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    addTerminalLog("success", `Saved template to ingest/${filename}.`);
  } catch (error) {
    addTerminalLog("error", error.message);
  }
}

function updateBadgeUI(source, status) {
  const card = document.getElementById(`scan-${source}`);
  if (!card) return;
  const badge = card.querySelector(".status-badge");
  badge.className = `status-badge status-${status}`;
  badge.textContent = String(status || "idle").toUpperCase();
}

function renderCatalog() {
  const body = document.getElementById("catalog-body");
  const query = document.getElementById("search-input").value.toLowerCase();
  const rows = catalog.filter((item) => `${item.name} ${item.path} ${item.source}`.toLowerCase().includes(query));
  body.innerHTML = "";
  if (!rows.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.textContent = "No catalog entries yet.";
    row.appendChild(cell);
    body.appendChild(row);
    return;
  }
  for (const item of rows) {
    const row = document.createElement("tr");
    for (const value of [item.name, item.source || item.scan_source, item.type, formatBytes(item.size_bytes), item.path]) {
      const cell = document.createElement("td");
      if (String(value || "").startsWith("https://")) {
        const link = document.createElement("a");
        link.href = value;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = value;
        cell.appendChild(link);
      } else {
        cell.textContent = value || "";
      }
      row.appendChild(cell);
    }
    body.appendChild(row);
  }
}

function formatBytes(bytes) {
  const n = Number(bytes || 0);
  if (!n) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(n) / Math.log(1024)), units.length - 1);
  return `${(n / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

document.addEventListener("DOMContentLoaded", () => {
  addTerminalLog("system", "ISLAND Scanner Dashboard ready. Autonomy is manual-gated.");
  fetchStatus();
});
