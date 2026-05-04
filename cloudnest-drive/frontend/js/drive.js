"use strict";

// ── State variables ──
let allFiles    = [];   // all files from server
let deleteKey   = null; // s3 key of file to delete
let deleteName  = null; // name of file to delete

// ── Called when Firebase confirms user is logged in ──
function initDrive(user) {
  // Show user's name in topbar
  const stored = JSON.parse(
    sessionStorage.getItem("cloudnest_user") || "{}"
  );
  document.getElementById("user-name").textContent =
    stored.name || user.email;

  // Load their files
  loadFiles();
}

// ── Make API calls with auth token ──
async function apiRequest(path, options = {}) {
  const token = window._idToken;
  if (!token) throw new Error("Not logged in.");

  const response = await fetch(`${window._apiBase}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(options.headers || {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

// ── Load all files from backend ──
async function loadFiles() {
  // Show loading, hide everything else
  document.getElementById("loading").style.display      = "block";
  document.getElementById("error-state").style.display  = "none";
  document.getElementById("empty-state").style.display  = "none";
  document.getElementById("files-grid").style.display   = "none";

  try {
    const data = await apiRequest("/api/files/list");
    allFiles = data.files || [];
    renderFiles(allFiles);
  } catch (err) {
    console.error("Load error:", err);
    document.getElementById("loading").style.display     = "none";
    document.getElementById("error-state").style.display = "flex";
  }
}

// ── Render file cards on screen ──
function renderFiles(files) {
  document.getElementById("loading").style.display = "none";

  if (files.length === 0) {
    document.getElementById("empty-state").style.display = "flex";
    document.getElementById("files-grid").style.display  = "none";
    return;
  }

  document.getElementById("empty-state").style.display = "none";
  document.getElementById("files-grid").style.display  = "grid";

  const grid = document.getElementById("files-grid");
  grid.innerHTML = files.map(file => buildCard(file)).join("");
}

// ── Build HTML for one file card ──
function buildCard(file) {
  const icon    = getIcon(file.filename);
  const size    = formatSize(file.size);
  const safeKey = encodeURIComponent(file.s3_key);
  const safeName = escapeHtml(file.filename);

  return `
    <div class="file-card">
      <div class="file-icon">${icon}</div>
      <div class="file-name" title="${safeName}">${safeName}</div>
      <div class="file-size">${size}</div>
      <div class="file-actions">
        <button class="btn-download"
          onclick="downloadFile('${safeKey}')">
          ⬇ Download
        </button>
        <button class="btn-delete"
          onclick="askDelete('${safeKey}', '${safeName}')">
          🗑 Delete
        </button>
      </div>
    </div>
  `;
}

// ── Handle file selection from input ──
function handleFileSelect(event) {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;
  uploadFiles(files);
  event.target.value = ""; // reset so same file can be uploaded again
}

// ── Upload files one by one ──
async function uploadFiles(files) {
  const box    = document.getElementById("upload-box");
  const status = document.getElementById("upload-status");
  const fill   = document.getElementById("progress-fill");

  box.style.display = "flex";

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    status.textContent = `Uploading ${i + 1}/${files.length}: ${file.name}`;
    fill.style.width   = "30%";

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${window._apiBase}/api/files/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${window._idToken}` },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Upload failed.");
      }

      fill.style.width = "100%";
      status.textContent = `✅ ${file.name} uploaded!`;

    } catch (err) {
      status.textContent = `❌ ${file.name} failed: ${err.message}`;
    }

    // Short pause between files
    await new Promise(r => setTimeout(r, 600));
  }

  // Done — reload file list
  fill.style.width = "100%";
  setTimeout(() => {
    box.style.display = "none";
    fill.style.width  = "0%";
    loadFiles();
  }, 1000);
}

// ── Download a file ──
async function downloadFile(encodedKey) {
  const s3Key = decodeURIComponent(encodedKey);
  try {
    const data = await apiRequest(
      `/api/files/download?key=${encodeURIComponent(s3Key)}`
    );
    // Open the presigned URL in a new tab
    window.open(data.download_url, "_blank");
  } catch (err) {
    alert("Download failed: " + err.message);
  }
}

// ── Show delete confirmation modal ──
function askDelete(encodedKey, name) {
  deleteKey  = decodeURIComponent(encodedKey);
  deleteName = name;
  document.getElementById("delete-name").textContent = name;
  document.getElementById("delete-modal").style.display = "flex";
}

// ── Close modal without deleting ──
function closeModal() {
  document.getElementById("delete-modal").style.display = "none";
  deleteKey  = null;
  deleteName = null;
}

// ── Actually delete the file ──
async function confirmDelete() {
  if (!deleteKey) return;

  const btn = document.getElementById("confirm-delete-btn");
  btn.disabled    = true;
  btn.textContent = "Deleting…";

  try {
    await apiRequest(
      `/api/files/delete?key=${encodeURIComponent(deleteKey)}`,
      { method: "DELETE" }
    );

    closeModal();
    loadFiles(); // refresh the list

  } catch (err) {
    alert("Delete failed: " + err.message);
    btn.disabled    = false;
    btn.textContent = "Delete";
  }
}

// ── Search / filter files by name ──
function filterFiles(query) {
  const q = query.toLowerCase().trim();
  if (!q) {
    renderFiles(allFiles);
    return;
  }
  const filtered = allFiles.filter(f =>
    f.filename.toLowerCase().includes(q)
  );
  renderFiles(filtered);
}

// ── Logout ──
async function handleLogout() {
  try {
    await window._signOut(window._auth);
  } catch (err) {
    console.error(err);
  }
  sessionStorage.clear();
  window.location.href = "index.html";
}

// ── Helper: pick emoji icon based on file extension ──
function getIcon(filename) {
  const ext = filename.split(".").pop().toLowerCase();
  const icons = {
    pdf:  "📄", doc: "📝", docx: "📝",
    xls:  "📊", xlsx: "📊", csv: "📊",
    ppt:  "📑", pptx: "📑",
    jpg:  "🖼️", jpeg: "🖼️", png: "🖼️",
    gif:  "🖼️", webp: "🖼️", svg: "🖼️",
    mp4:  "🎬", mov: "🎬", avi: "🎬",
    mp3:  "🎵", wav: "🎵", flac: "🎵",
    zip:  "🗜️", rar: "🗜️", gz: "🗜️",
    txt:  "📃", md: "📃",
    js:   "💻", py: "💻", html: "💻",
  };
  return icons[ext] || "📁";
}

// ── Helper: format bytes into readable size ──
function formatSize(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(1)} ${units[i]}`;
}

// ── Helper: prevent XSS in filenames ──
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}