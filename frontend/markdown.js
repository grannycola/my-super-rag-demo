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

    const rawCode = code.textContent || "";
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
    wrapper.dataset.code = rawCode;

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);
  });

  bindCopyButtons(root);
}

async function copyTextToClipboard(text) {
  if (!text) {
    throw new Error("empty code");
  }

  if (navigator.clipboard?.writeText && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // Fall back for browsers that expose clipboard API but reject the write.
    }
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  textarea.style.top = "0";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);

  textarea.focus();
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }

  document.body.removeChild(textarea);

  if (copied) {
    return;
  }

  throw new Error("copy failed");
}

function getCodeBlockText(block) {
  if (!block) return "";

  const stored = block.dataset.code;
  if (stored) {
    return stored;
  }

  return block.querySelector("pre code")?.textContent || "";
}

function bindCopyButtons(container) {
  container.querySelectorAll(".copy-code-btn").forEach((btn) => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = "true";

    btn.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();

      const block = btn.closest(".code-block");
      const code = getCodeBlockText(block);
      const prev = btn.textContent;

      try {
        await copyTextToClipboard(code);
        btn.textContent = "Copied!";
      } catch {
        btn.textContent = "Failed";
      }

      setTimeout(() => {
        btn.textContent = prev;
      }, 1500);
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
