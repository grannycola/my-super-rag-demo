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
  setTimeout(scroll, 400);
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
const LOGS_EDGE_SWIPE = 28;
const LOGS_OPEN_THRESHOLD = 72;

let logsDrawerOpen = false;
let logsTouchStartX = 0;
let logsTouchStartY = 0;
let logsTouchMode = null;

function isMobileDrawer() {
  return MOBILE_DRAWER_MQ.matches;
}

function updateAppHeaderHeight() {
  const header = document.querySelector(".header");
  if (!header) return;
  document.documentElement.style.setProperty("--app-header-height", `${header.offsetHeight}px`);
}

function setLogsDragOffset(px) {
  document.documentElement.style.setProperty("--logs-drag-offset", `${px}px`);
}

function clearLogsDragOffset() {
  document.documentElement.style.removeProperty("--logs-drag-offset");
}

function setLogsDrawerOpen(open) {
  if (!isMobileDrawer()) return;

  logsDrawerOpen = open;
  logsPanel.classList.toggle("is-open", open);
  logsBackdrop.classList.toggle("is-visible", open);
  logsBackdrop.setAttribute("aria-hidden", open ? "false" : "true");
  logsDrawerHandle.setAttribute("aria-expanded", open ? "true" : "false");
  document.body.classList.toggle("logs-drawer-open", open);
  clearLogsDragOffset();
}

function openLogsDrawer() {
  setLogsDrawerOpen(true);
}

function closeLogsDrawer() {
  setLogsDrawerOpen(false);
}

function toggleLogsDrawer() {
  setLogsDrawerOpen(!logsDrawerOpen);
}

function handleLogsTouchStart(event) {
  if (!isMobileDrawer()) return;

  const touch = event.touches[0];
  const inChat = event.target.closest("#chat-log");

  if (inChat && touch.clientX > LOGS_EDGE_SWIPE && !logsDrawerOpen) {
    return;
  }

  logsTouchStartX = touch.clientX;
  logsTouchStartY = touch.clientY;
  logsTouchMode = null;

  if (!logsDrawerOpen && touch.clientX <= LOGS_EDGE_SWIPE) {
    logsTouchMode = "open";
    logsPanel.classList.add("is-dragging");
  } else if (logsDrawerOpen && touch.clientX <= logsPanel.offsetWidth + 12) {
    logsTouchMode = "close";
    logsPanel.classList.add("is-dragging");
  }
}

function handleLogsTouchMove(event) {
  if (!isMobileDrawer() || !logsTouchMode) return;

  const touch = event.touches[0];
  const deltaX = touch.clientX - logsTouchStartX;
  const deltaY = touch.clientY - logsTouchStartY;

  if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaX) < 12) {
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
      logsBackdrop.classList.remove("is-visible");
      document.body.classList.remove("logs-drawer-open");
      logsDrawerOpen = false;
    }
    setLogsDragOffset(Math.max(logsPanel.offsetWidth + deltaX, 0));
  }
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
logsBackdrop.addEventListener("click", closeLogsDrawer);

document.addEventListener("touchstart", handleLogsTouchStart, { passive: true });
document.addEventListener("touchmove", handleLogsTouchMove, { passive: false });
document.addEventListener("touchend", handleLogsTouchEnd, { passive: true });

MOBILE_DRAWER_MQ.addEventListener("change", () => {
  updateAppHeaderHeight();
  if (!isMobileDrawer()) {
    setLogsDrawerOpen(false);
    logsPanel.classList.remove("is-dragging");
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
