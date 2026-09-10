const runBtn = document.getElementById("runBtn");
const downloadBtn = document.getElementById("downloadBtn");
const browseFolderBtn = document.getElementById("browseFolderBtn");
const statusEl = document.getElementById("status");
const table = document.getElementById("resultsTable");
const tbody = document.getElementById("resultsBody");
const progressWrap = document.getElementById("progressWrap");
const progressFill = document.getElementById("progressFill");
const progressLabel = document.getElementById("progressLabel");

let pollTimer = null;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function renderResults(results) {
  tbody.innerHTML = "";
  for (const r of results) {
    const tr = document.createElement("tr");
    tr.className = `status-${r.status}`;
    tr.innerHTML = `
      <td>${escapeHtml(r.filename)}</td>
      <td>${escapeHtml(r.status)}</td>
      <td>${escapeHtml(r.name)}</td>
      <td>${escapeHtml(r.phone)}</td>
      <td>${escapeHtml(r.subject)}</td>
      <td>${escapeHtml(r.urgency)}</td>
      <td>${escapeHtml(r.error)}</td>
    `;
    tbody.appendChild(tr);
  }
  table.hidden = results.length === 0;
}

function setProgress(done, total) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  progressFill.style.width = pct + "%";
  progressLabel.textContent = `${done} / ${total}`;
}

async function poll() {
  try {
    const resp = await fetch("/api/progress");
    const data = await resp.json();

    setProgress(data.done, data.total);
    renderResults(data.results);

    if (!data.running) {
      clearInterval(pollTimer);
      pollTimer = null;
      runBtn.disabled = false;

      if (data.summary) {
        const s = data.summary;
        statusEl.className = "";
        statusEl.textContent = `Found ${s.total_found}, processed ${s.processed}, errors ${s.errors}.`;
      }
      downloadBtn.hidden = !data.download_ready;
    }
  } catch (err) {
    clearInterval(pollTimer);
    pollTimer = null;
    runBtn.disabled = false;
    statusEl.className = "error";
    statusEl.textContent = "Lost connection while polling progress: " + err.message;
  }
}

browseFolderBtn.addEventListener("click", async () => {
  browseFolderBtn.disabled = true;
  try {
    const resp = await fetch("/api/browse-folder");
    const data = await resp.json();
    if (data.path) {
      document.getElementById("folderPath").value = data.path;
    }
  } catch (err) {
    statusEl.className = "error";
    statusEl.textContent = "Browse failed: " + err.message;
  } finally {
    browseFolderBtn.disabled = false;
  }
});

runBtn.addEventListener("click", async () => {
  const folder_path = document.getElementById("folderPath").value.trim();

  statusEl.className = "";
  statusEl.textContent = "Starting...";
  downloadBtn.hidden = true;
  runBtn.disabled = true;
  progressWrap.hidden = false;
  setProgress(0, 0);
  renderResults([]);

  try {
    const resp = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder_path }),
    });
    const data = await resp.json();

    if (!resp.ok) {
      statusEl.className = "error";
      statusEl.textContent = data.error || "Request failed.";
      runBtn.disabled = false;
      return;
    }

    setProgress(0, data.total);
    statusEl.textContent = `Processing ${data.total} email(s)...`;
    pollTimer = setInterval(poll, 500);
  } catch (err) {
    statusEl.className = "error";
    statusEl.textContent = "Request failed: " + err.message;
    runBtn.disabled = false;
  }
});

downloadBtn.addEventListener("click", () => {
  window.location = "/api/download";
});
