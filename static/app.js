const runBtn = document.getElementById("runBtn");
const downloadBtn = document.getElementById("downloadBtn");
const fileInput = document.getElementById("emailFiles");
const statusEl = document.getElementById("status");
const table = document.getElementById("resultsTable");
const tbody = document.getElementById("resultsBody");
const progressWrap = document.getElementById("progressWrap");
const progressFill = document.getElementById("progressFill");
const progressLabel = document.getElementById("progressLabel");

let downloadUrl = null;

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

async function parseOne(file) {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await fetch("/api/parse-one", { method: "POST", body: formData });
  const data = await resp.json();
  if (!resp.ok) {
    return { filename: file.name, status: "error", error: data.error || "Request failed." };
  }
  return data;
}

runBtn.addEventListener("click", async () => {
  const files = Array.from(fileInput.files || []);
  if (files.length === 0) {
    statusEl.className = "error";
    statusEl.textContent = "Select at least one .eml/.msg file first.";
    return;
  }

  if (downloadUrl) {
    URL.revokeObjectURL(downloadUrl);
    downloadUrl = null;
  }

  statusEl.className = "";
  statusEl.textContent = `Processing ${files.length} email(s)...`;
  downloadBtn.hidden = true;
  runBtn.disabled = true;
  progressWrap.hidden = false;
  setProgress(0, files.length);
  renderResults([]);

  const results = [];
  for (const file of files) {
    const result = await parseOne(file);
    results.push(result);
    renderResults(results);
    setProgress(results.length, files.length);
  }

  const processed = results.filter((r) => r.status === "processed");
  const errors = results.length - processed.length;
  statusEl.textContent = `Found ${results.length}, processed ${processed.length}, errors ${errors}.`;
  runBtn.disabled = false;

  if (processed.length > 0) {
    try {
      const resp = await fetch("/api/generate-excel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows: processed }),
      });
      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.error || "Failed to generate Excel file.");
      }
      const blob = await resp.blob();
      downloadUrl = URL.createObjectURL(blob);
      downloadBtn.hidden = false;
    } catch (err) {
      statusEl.className = "error";
      statusEl.textContent = "Excel generation failed: " + err.message;
    }
  }
});

downloadBtn.addEventListener("click", () => {
  if (!downloadUrl) return;
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = "parsed_emails.xlsx";
  document.body.appendChild(a);
  a.click();
  a.remove();
});
