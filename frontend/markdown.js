/** Markdown rendering with syntax-highlighted code blocks. */

let markdownConfigured = false;

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

function configureMarkdown() {
  if (markdownConfigured || typeof marked === "undefined") return;
  markdownConfigured = true;

  marked.setOptions({
    gfm: true,
    breaks: true,
  });
}

function normalizeMarkdown(text) {
  if (!text) return "";

  let normalized = text.replace(/\r\n/g, "\n");
  normalized = normalized.replace(/^[ \t]+```/gm, "```");
  return normalized;
}

function renderMarkdown(text) {
  if (!text) return "";
  if (typeof marked === "undefined") {
    return `<p>${escapeHtml(text)}</p>`;
  }

  configureMarkdown();
  const raw = marked.parse(normalizeMarkdown(text));

  if (typeof DOMPurify !== "undefined") {
    return DOMPurify.sanitize(raw, {
      ADD_ATTR: ["class"],
      ADD_TAGS: ["span"],
    });
  }
  return raw;
}

function extractLanguage(codeEl) {
  for (const cls of codeEl.classList) {
    if (cls.startsWith("language-")) {
      return cls.slice("language-".length);
    }
  }
  return "code";
}

function enhanceCodeBlocks(root) {
  root.querySelectorAll(".markdown-body pre").forEach((pre) => {
    if (pre.closest(".code-block")) return;

    const code = pre.querySelector("code");
    if (!code) return;

    const lang = extractLanguage(code);

    if (typeof hljs !== "undefined") {
      if (lang !== "code" && hljs.getLanguage(lang)) {
        code.classList.add("language-" + lang);
      }
      hljs.highlightElement(code);
    }

    const wrapper = document.createElement("div");
    wrapper.className = "code-block";
    wrapper.innerHTML =
      `<div class="code-block-header">` +
      `<span class="code-lang">${escapeHtml(lang)}</span>` +
      `<button type="button" class="copy-code-btn">Copy</button>` +
      `</div>`;

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);
  });

  bindCopyButtons(root);
}

function copyTextToClipboard(text) {
  if (navigator.clipboard?.writeText && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }

  return new Promise((resolve, reject) => {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();

    try {
      const ok = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (ok) resolve();
      else reject(new Error("copy command failed"));
    } catch (err) {
      document.body.removeChild(textarea);
      reject(err);
    }
  });
}

function bindCopyButtons(container) {
  container.querySelectorAll(".copy-code-btn").forEach((btn) => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = "true";

    btn.addEventListener("click", async () => {
      const code = btn.closest(".code-block")?.querySelector("pre code")?.textContent || "";
      const prev = btn.textContent;
      try {
        await copyTextToClipboard(code);
        btn.textContent = "Copied!";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1500);
      } catch {
        btn.textContent = "Failed";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1500);
      }
    });
  });
}

function renderAssistantContent(answer) {
  return `<div class="markdown-body">${renderMarkdown(answer)}</div>`;
}

function finalizeAssistantMessage(container) {
  enhanceCodeBlocks(container);
  styleCitationRefs(container);
}

function styleCitationRefs(container) {
  const body = container.querySelector(".markdown-body");
  if (!body) return;

  const textNodes = [];
  const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    textNodes.push(walker.currentNode);
  }

  textNodes.forEach((node) => {
    if (node.parentElement?.closest("pre, code, .cite-ref")) return;

    const text = node.textContent;
    if (!/\[\d+\]/.test(text)) return;

    const fragment = document.createDocumentFragment();
    const re = /\[(\d+)\]/g;
    let lastIndex = 0;
    let match;

    while ((match = re.exec(text)) !== null) {
      if (match.index > lastIndex) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
      }

      const sup = document.createElement("sup");
      sup.className = "cite-ref";
      const link = document.createElement("a");
      link.href = `#cite-${match[1]}`;
      link.textContent = match[1];
      link.title = `Source ${match[1]}`;
      sup.appendChild(link);
      fragment.appendChild(sup);
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
    }

    node.replaceWith(fragment);
  });
}
