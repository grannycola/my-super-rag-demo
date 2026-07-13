const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const questionInput = document.getElementById("question");
const submitBtn = document.getElementById("submit-btn");
const btnLabel = submitBtn.querySelector(".btn-label");
const btnSpinner = submitBtn.querySelector(".btn-spinner");
const statusEl = document.getElementById("status");
const statusText = document.getElementById("status-text");
const logsEl = document.getElementById("logs");
const logsPanel = document.getElementById("logs-panel");
const logsBackdrop = document.getElementById("logs-backdrop");
const logsDrawerHandle = document.getElementById("logs-drawer-handle");
const logsEdgeSwipe = document.getElementById("logs-edge-swipe");
const progressPanel = document.getElementById("progress-panel");
const progressDrawerHandle = document.getElementById("progress-drawer-handle");
const progressEdgeSwipe = document.getElementById("progress-edge-swipe");
const closeProgressBtn = document.getElementById("close-progress");
const closeLogsBtn = document.getElementById("close-logs");
const clearLogsBtn = document.getElementById("clear-logs");
const progressBadge = document.getElementById("progress-badge");
const progressBar = document.getElementById("progress-bar");
const progressSteps = document.querySelectorAll(".step");

const PIPELINE_STEPS = ["embed", "search", "rerank", "context", "llm", "citations"];
const RETRIEVE_STEPS = ["embed", "search", "rerank"];
const GENERATE_STEPS = ["context", "llm", "citations"];

let progressTimer = null;

function nowTime() {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function addLog(type, message, html = null) {
  const line = document.createElement("div");
  line.className = `log-line log-${type}`;
  line.innerHTML = `
    <span class="log-time">${nowTime()}</span>
    <span class="log-msg">${html || escapeHtml(message)}</span>
  `;
  logsEl.appendChild(line);
  logsEl.scrollTop = logsEl.scrollHeight;
}

function logChunk(chunk) {
  const score = chunk.rerank_score != null
    ? `rerank ${chunk.rerank_score.toFixed(3)}`
    : chunk.score != null
      ? `score ${chunk.score.toFixed(3)}`
      : "";

  const summaryText = `#${chunk.rank} chunk found${score ? ` · ${score}` : ""}`;

  const html = `
    <details class="log-chunk-spoiler">
      <summary>
        <span class="chunk-arrow" aria-hidden="true">▶</span>
        <span class="chunk-summary-text">${escapeHtml(summaryText)}</span>
      </summary>
      <div class="log-chunk-card">
        <div class="chunk-title">${escapeHtml(chunk.title || "Untitled")}</div>
        <div class="chunk-meta">${escapeHtml(chunk.section || "")} · ${escapeHtml(chunk.source_url)}</div>
        <div class="chunk-snippet">${escapeHtml(chunk.snippet)}</div>
      </div>
    </details>
  `;

  const line = document.createElement("div");
  line.className = "log-line log-chunk";
  line.innerHTML = `
    <span class="log-time">${nowTime()}</span>
    <span class="log-msg">${html}</span>
  `;
  logsEl.appendChild(line);
  logsEl.scrollTop = logsEl.scrollHeight;
}

function resetProgress() {
  clearInterval(progressTimer);
  progressSteps.forEach((step) => {
    step.classList.remove("active", "done");
  });
  progressBar.classList.remove("indeterminate");
  progressBar.style.setProperty("--progress", "0%");
  progressBadge.className = "progress-badge idle";
  progressBadge.textContent = "Idle";
}

function setProgressState(state, label) {
  progressBadge.className = `progress-badge ${state}`;
  progressBadge.textContent = label;
}

function setStepActive(stepId) {
  const idx = PIPELINE_STEPS.indexOf(stepId);
  progressSteps.forEach((el) => {
    const id = el.dataset.step;
    const stepIdx = PIPELINE_STEPS.indexOf(id);
    el.classList.remove("active");
    if (stepIdx < idx) el.classList.add("done");
  });
  const active = document.querySelector(`.step[data-step="${stepId}"]`);
  if (active) active.classList.add("active");

  const pct = Math.round(((idx + 0.5) / PIPELINE_STEPS.length) * 100);
  progressBar.style.setProperty("--progress", `${pct}%`);
}

function completeThrough(stepId) {
  const idx = PIPELINE_STEPS.indexOf(stepId);
  progressSteps.forEach((el) => {
    const stepIdx = PIPELINE_STEPS.indexOf(el.dataset.step);
    el.classList.remove("active");
    if (stepIdx <= idx) el.classList.add("done");
  });
  const pct = Math.round(((idx + 1) / PIPELINE_STEPS.length) * 100);
  progressBar.style.setProperty("--progress", `${pct}%`);
}

function finishProgress(success) {
  progressBar.classList.remove("indeterminate");
  if (success) {
    progressSteps.forEach((el) => {
      el.classList.remove("active");
      el.classList.add("done");
    });
    progressBar.style.setProperty("--progress", "100%");
    setProgressState("done", "Complete");
  } else {
    setProgressState("error", "Failed");
  }
}

function animateRetrieveSteps() {
  let i = 0;
  setStepActive(RETRIEVE_STEPS[0]);
  progressBar.classList.add("indeterminate");

  progressTimer = setInterval(() => {
    if (i < RETRIEVE_STEPS.length - 1) {
      completeThrough(RETRIEVE_STEPS[i]);
      i += 1;
      setStepActive(RETRIEVE_STEPS[i]);
    }
  }, 900);
}

function scrollChatToBottom() {
  const scroll = () => {
    chatLog.scrollTop = chatLog.scrollHeight;
  };

  scroll();
  requestAnimationFrame(scroll);
  setTimeout(scroll, 0);
  setTimeout(scroll, 150);
}

function appendMessage(role, html, options = {}) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = html;
  if (options.markdown) {
    finalizeAssistantMessage(div);
  }
  chatLog.appendChild(div);
  scrollChatToBottom();
  return div;
}

function appendLoadingMessage(text) {
  return appendMessage(
    "assistant loading",
    `<p>${escapeHtml(text)} <span class="typing-dots"><span></span><span></span><span></span></span></p>`
  );
}

function formatCitations(citations) {
  if (!citations?.length) return "";
  const items = citations
    .map((c) => {
      const id = c.citation_id.replace(/\[|\]/g, "");
      return `<li id="cite-${id}"><span class="cite-badge">${c.citation_id}</span> <a href="${c.source_url}" target="_blank" rel="noopener">${escapeHtml(c.title || c.source_url)}</a></li>`;
    })
    .join("");
  return `<div class="citations"><h4>Sources</h4><ul>${items}</ul></div>`;
}

function setHitRate(hitRate) {
  if (typeof hitRate !== "number" || Number.isNaN(hitRate)) return;
  document.getElementById("stat-hit-rate").textContent = `${(hitRate * 100).toFixed(0)}%`;
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    document.getElementById("stat-chunks").textContent = data.indexed_chunks.toLocaleString();
    setHitRate(data.retrieval_hit_rate);
    statusEl.classList.add("ok");
    statusText.textContent = "Online";
  } catch {
    statusEl.classList.add("error");
    statusText.textContent = "Offline";
  }
}

async function loadMetrics() {
  try {
    const res = await fetch(`/metrics.json?v=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    setHitRate(data.hit_rate);
  } catch {
    // optional fallback
  }
}

clearLogsBtn.addEventListener("click", () => {
  logsEl.innerHTML = "";
  addLog("info", "Logs cleared.");
});

const MOBILE_DRAWER_MQ = window.matchMedia("(max-width: 1100px)");
const LOGS_OPEN_THRESHOLD = 72;
const PROGRESS_OPEN_THRESHOLD = 72;

let logsDrawerOpen = false;
let progressDrawerOpen = false;
let logsTouchStartX = 0;
let logsTouchStartY = 0;
let logsTouchMode = null;
let progressTouchStartY = 0;
let progressTouchStartX = 0;
let progressTouchMode = null;

function isMobileDrawer() {
  return MOBILE_DRAWER_MQ.matches;
}

function updateAppHeaderHeight() {
  const header = document.querySelector(".header");
  if (!header) return;
  document.documentElement.style.setProperty("--app-header-height", `${header.offsetHeight}px`);
}

function syncDrawerBackdrop() {
  const open = logsDrawerOpen || progressDrawerOpen;
  logsBackdrop.classList.toggle("is-visible", open);
  logsBackdrop.setAttribute("aria-hidden", open ? "false" : "true");
  document.body.classList.toggle("drawer-open", open);
}

function setLogsDragOffset(px) {
  document.documentElement.style.setProperty("--logs-drag-offset", `${px}px`);
}

function clearLogsDragOffset() {
  document.documentElement.style.removeProperty("--logs-drag-offset");
}

function setProgressDragOffset(px) {
  document.documentElement.style.setProperty("--progress-drag-offset", `${px}px`);
}

function clearProgressDragOffset() {
  document.documentElement.style.removeProperty("--progress-drag-offset");
}

function setLogsDrawerOpen(open, options = {}) {
  const { syncOther = true } = options;
  if (!isMobileDrawer()) return;

  if (open && syncOther && progressDrawerOpen) {
    setProgressDrawerOpen(false, { syncOther: false });
  }

  logsDrawerOpen = open;
  logsPanel.classList.toggle("is-open", open);
  logsDrawerHandle.setAttribute("aria-expanded", open ? "true" : "false");
  document.body.classList.toggle("logs-drawer-open", open);
  clearLogsDragOffset();
  syncDrawerBackdrop();
}

function setProgressDrawerOpen(open, options = {}) {
  const { syncOther = true } = options;
  if (!isMobileDrawer()) return;

  if (open && syncOther && logsDrawerOpen) {
    setLogsDrawerOpen(false, { syncOther: false });
  }

  progressDrawerOpen = open;
  progressPanel.classList.toggle("is-open", open);
  progressDrawerHandle.setAttribute("aria-expanded", open ? "true" : "false");
  document.body.classList.toggle("progress-drawer-open", open);
  clearProgressDragOffset();
  syncDrawerBackdrop();
}

function openLogsDrawer() {
  setLogsDrawerOpen(true);
}

function closeLogsDrawer() {
  setLogsDrawerOpen(false);
}

function openProgressDrawer() {
  setProgressDrawerOpen(true);
}

function closeProgressDrawer() {
  setProgressDrawerOpen(false);
}

function toggleProgressDrawer() {
  setProgressDrawerOpen(!progressDrawerOpen);
}

function toggleLogsDrawer() {
  setLogsDrawerOpen(!logsDrawerOpen);
}

function handleLogsTouchStart(event) {
  if (!isMobileDrawer()) return;

  const touch = event.touches[0];
  logsTouchStartX = touch.clientX;
  logsTouchStartY = touch.clientY;
  logsTouchMode = event.currentTarget === logsPanel ? "close" : "open";

  if (logsTouchMode === "open" && logsDrawerOpen) {
    logsTouchMode = null;
    return;
  }

  if (logsTouchMode === "close" && !logsDrawerOpen) {
    logsTouchMode = null;
    return;
  }

  logsPanel.classList.add("is-dragging");
}

function handleLogsTouchMove(event) {
  if (!isMobileDrawer() || !logsTouchMode) return;

  const touch = event.touches[0];
  const deltaX = touch.clientX - logsTouchStartX;
  const deltaY = touch.clientY - logsTouchStartY;

  if (Math.abs(deltaY) > Math.abs(deltaX) * 1.2) {
    logsTouchMode = null;
    logsPanel.classList.remove("is-dragging");
    clearLogsDragOffset();
    return;
  }

  if (logsTouchMode === "open" && deltaX > 0) {
    event.preventDefault();
    setLogsDragOffset(Math.min(deltaX, logsPanel.offsetWidth));
    return;
  }

  if (logsTouchMode === "close" && deltaX < 0) {
    event.preventDefault();
    if (logsDrawerOpen) {
      logsPanel.classList.remove("is-open");
      document.body.classList.remove("logs-drawer-open");
      logsDrawerOpen = false;
      syncDrawerBackdrop();
    }
    setLogsDragOffset(Math.max(logsPanel.offsetWidth + deltaX, 0));
  }
}

function handleProgressTouchStart(event) {
  if (!isMobileDrawer()) return;

  const touch = event.touches[0];
  progressTouchStartY = touch.clientY;
  progressTouchStartX = touch.clientX;
  progressTouchMode = event.currentTarget === progressPanel ? "close" : "open";

  if (progressTouchMode === "open" && progressDrawerOpen) {
    progressTouchMode = null;
    return;
  }

  if (progressTouchMode === "close" && !progressDrawerOpen) {
    progressTouchMode = null;
    return;
  }

  progressPanel.classList.add("is-dragging");
}

function handleProgressTouchMove(event) {
  if (!isMobileDrawer() || !progressTouchMode) return;

  const touch = event.touches[0];
  const deltaY = touch.clientY - progressTouchStartY;
  const deltaX = touch.clientX - progressTouchStartX;

  if (Math.abs(deltaX) > Math.abs(deltaY) * 1.2) {
    progressTouchMode = null;
    progressPanel.classList.remove("is-dragging");
    clearProgressDragOffset();
    return;
  }

  if (progressTouchMode === "open" && deltaY < 0) {
    event.preventDefault();
    setProgressDragOffset(Math.min(-deltaY, progressPanel.offsetHeight));
    return;
  }

  if (progressTouchMode === "close" && deltaY > 0) {
    event.preventDefault();
    if (progressDrawerOpen) {
      progressPanel.classList.remove("is-open");
      document.body.classList.remove("progress-drawer-open");
      progressDrawerOpen = false;
      syncDrawerBackdrop();
    }
    setProgressDragOffset(Math.max(progressPanel.offsetHeight - deltaY, 0));
  }
}

function handleProgressTouchEnd(event) {
  if (!isMobileDrawer() || !progressTouchMode) return;

  progressPanel.classList.remove("is-dragging");
  const touch = event.changedTouches[0];
  const deltaY = touch.clientY - progressTouchStartY;

  if (progressTouchMode === "open") {
    setProgressDrawerOpen(-deltaY >= PROGRESS_OPEN_THRESHOLD);
  } else if (progressTouchMode === "close") {
    setProgressDrawerOpen(deltaY < PROGRESS_OPEN_THRESHOLD);
  }

  clearProgressDragOffset();
  progressTouchMode = null;
}

function handleLogsTouchEnd(event) {
  if (!isMobileDrawer() || !logsTouchMode) return;

  logsPanel.classList.remove("is-dragging");
  const touch = event.changedTouches[0];
  const deltaX = touch.clientX - logsTouchStartX;

  if (logsTouchMode === "open") {
    setLogsDrawerOpen(deltaX >= LOGS_OPEN_THRESHOLD);
  } else if (logsTouchMode === "close") {
    setLogsDrawerOpen(deltaX > -LOGS_OPEN_THRESHOLD);
  }

  clearLogsDragOffset();
  logsTouchMode = null;
}

logsDrawerHandle.addEventListener("click", openLogsDrawer);
closeLogsBtn.addEventListener("click", closeLogsDrawer);
closeProgressBtn.addEventListener("click", closeProgressDrawer);
logsBackdrop.addEventListener("click", () => {
  closeLogsDrawer();
  closeProgressDrawer();
});
progressDrawerHandle.addEventListener("click", openProgressDrawer);

if (logsEdgeSwipe) {
  logsEdgeSwipe.addEventListener("touchstart", handleLogsTouchStart, { passive: true });
  logsEdgeSwipe.addEventListener("touchmove", handleLogsTouchMove, { passive: false });
  logsEdgeSwipe.addEventListener("touchend", handleLogsTouchEnd, { passive: true });
}

logsPanel.addEventListener("touchstart", handleLogsTouchStart, { passive: true });
logsPanel.addEventListener("touchmove", handleLogsTouchMove, { passive: false });
logsPanel.addEventListener("touchend", handleLogsTouchEnd, { passive: true });

if (progressEdgeSwipe) {
  progressEdgeSwipe.addEventListener("touchstart", handleProgressTouchStart, { passive: true });
  progressEdgeSwipe.addEventListener("touchmove", handleProgressTouchMove, { passive: false });
  progressEdgeSwipe.addEventListener("touchend", handleProgressTouchEnd, { passive: true });
}

progressPanel.addEventListener("touchstart", handleProgressTouchStart, { passive: true });
progressPanel.addEventListener("touchmove", handleProgressTouchMove, { passive: false });
progressPanel.addEventListener("touchend", handleProgressTouchEnd, { passive: true });

MOBILE_DRAWER_MQ.addEventListener("change", () => {
  updateAppHeaderHeight();
  if (!isMobileDrawer()) {
    setLogsDrawerOpen(false);
    setProgressDrawerOpen(false);
    logsPanel.classList.remove("is-dragging");
    progressPanel.classList.remove("is-dragging");
  }
});

window.addEventListener("resize", updateAppHeaderHeight);
updateAppHeaderHeight();

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = questionInput.value.trim();
  if (!question) return;

  appendMessage("user", `<p>${escapeHtml(question)}</p>`);
  questionInput.value = "";
  submitBtn.disabled = true;
  btnLabel.classList.add("hidden");
  btnSpinner.classList.remove("hidden");

  resetProgress();
  setProgressState("running", "Running");
  addLog("info", `Query: "${question}"`);

  const loadingEl = appendLoadingMessage("Running RAG pipeline");

  try {
    animateRetrieveSteps();
    addLog("info", "Embedding query (bge-small)…");

    const retrieveRes = await fetch("/api/retrieve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, rerank: true }),
    });

    clearInterval(progressTimer);
    progressBar.classList.remove("indeterminate");

    if (!retrieveRes.ok) {
      const err = await retrieveRes.json().catch(() => ({}));
      throw new Error(err.detail || `Retrieve failed: HTTP ${retrieveRes.status}`);
    }

    const retrieveData = await retrieveRes.json();
    completeThrough("rerank");

    addLog("success", `Retrieved ${retrieveData.total} chunks after rerank.`);
    retrieveData.chunks.forEach((chunk) => logChunk(chunk));

    if (retrieveData.total === 0) {
      addLog("error", "No chunks found — check index.");
      loadingEl.remove();
      appendMessage("assistant", "<p>No relevant documentation found in the index.</p>");
      finishProgress(false);
      return;
    }

    GENERATE_STEPS.forEach((step, i) => {
      setTimeout(() => setStepActive(step), i * 400);
    });
    addLog("info", "Assembling context and calling Groq LLM…");
    loadingEl.querySelector("p").firstChild.textContent = "Generating answer… ";

    const generateRes = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        chunks: retrieveData.chunks,
      }),
    });

    if (!generateRes.ok) {
      const err = await generateRes.json().catch(() => ({}));
      throw new Error(err.detail || `Generate failed: HTTP ${generateRes.status}`);
    }

    const data = await generateRes.json();
    loadingEl.remove();

    completeThrough("citations");
    addLog("success", `Answer ready · ${data.citations.length} citation(s) · ${data.chunks_used} chunks used.`);

    appendMessage(
      "assistant",
      `${renderAssistantContent(data.answer)}${formatCitations(data.citations)}`,
      { markdown: true }
    );
    scrollChatToBottom();
    finishProgress(true);
  } catch (err) {
    clearInterval(progressTimer);
    loadingEl.remove();
    addLog("error", err.message);
    appendMessage("error", `<p>Error: ${escapeHtml(err.message)}</p>`);
    finishProgress(false);
  } finally {
    submitBtn.disabled = false;
    btnLabel.classList.remove("hidden");
    btnSpinner.classList.add("hidden");
    questionInput.focus();
  }
});

loadHealth();
loadMetrics();
