/**
 * messenger.js
 * Handles the Messenger-style inbox: conversation selection,
 * message loading (AJAX), sending, auto-grow textarea, and
 * unread badge updates.
 */

(function () {
  "use strict";

  const csrf        = window.MSNG_CSRF || "";
  const activeInit  = window.MSNG_ACTIVE || "";   // conv pk to open on load

  // DOM refs
  const convItems   = document.querySelectorAll(".msng-conv-item");
  const emptyPane   = document.getElementById("msng-empty");
  const innerPane   = document.getElementById("msng-inner");
  const bubblesEl   = document.getElementById("msng-bubbles");
  const loadingEl   = document.getElementById("msng-loading");
  const textarea    = document.getElementById("msng-textarea");
  const sendBtn     = document.getElementById("msng-send-btn");
  const headerAvatar = document.getElementById("msng-header-avatar");
  const headerName  = document.getElementById("msng-header-name");
  const headerBook  = document.getElementById("msng-header-book");
  const headerBookTitle = document.getElementById("msng-header-book-title");

  let activeConvId  = null;
  let activeSendUrl = null;
  let pollTimer     = null;

  // ── Helpers ────────────────────────────────────────────────

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function scrollToBottom() {
    bubblesEl.scrollTop = bubblesEl.scrollHeight;
  }

  function setActiveItem(convId) {
    convItems.forEach(el => {
      el.classList.toggle("is-active", el.dataset.convId === String(convId));
    });
  }

  // ── Active conversation book context ───────────────────────
  let activeBookTitle = "";
  let activeBookUrl   = "";

  // ── Render a single bubble row ──────────────────────────────

  function buildBubble(msg) {
    const row = document.createElement("div");
    row.className = "msng-bubble-row" + (msg.is_self ? " msng-bubble-row--self" : "");
    row.dataset.msgId = msg.id;

    const initial = msg.sender.charAt(0).toUpperCase();

    const avatarHtml = msg.is_self ? "" :
      `<div class="msng-bubble-mini-avatar">${escapeHtml(initial)}</div>`;

    row.innerHTML = `
      ${avatarHtml}
      <div class="msng-bubble ${msg.is_self ? "msng-bubble--sent" : "msng-bubble--received"}">
        ${escapeHtml(msg.body).replace(/\n/g, "<br>")}
        <span class="msng-bubble__time">${escapeHtml(msg.created_at)}</span>
      </div>
    `;
    return row;
  }

  // ── Render a book context pill ──────────────────────────────

  function buildBookPill(title, url) {
    const pill = document.createElement("div");
    pill.className = "msng-book-pill";
    const truncated = title.length > 40 ? title.slice(0, 38) + "…" : title;
    pill.innerHTML =
      `<svg class="msng-book-pill__icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>` +
      (url
        ? `<a href="${escapeHtml(url)}" target="_blank" title="${escapeHtml(title)}">${escapeHtml(truncated)}</a>`
        : `<span title="${escapeHtml(title)}">${escapeHtml(truncated)}</span>`);
    return pill;
  }

  // ── Load messages for a conversation ───────────────────────

  async function loadConversation(convItem) {
    const convId   = convItem.dataset.convId;
    const fetchUrl = convItem.dataset.fetchUrl;
    const sendUrl  = convItem.dataset.sendUrl;
    const other    = convItem.dataset.other || "User";
    const bookTitle = convItem.dataset.bookTitle || "";
    const bookUrl  = convItem.dataset.bookUrl   || "";

    // Stop previous poll
    if (pollTimer) clearInterval(pollTimer);

    activeConvId  = convId;
    activeSendUrl = sendUrl;

    setActiveItem(convId);

    // Show chat pane
    emptyPane.style.display = "none";
    innerPane.style.display = "flex";

    // Update header — name only; book context shown as pill in chat
    headerAvatar.textContent = other.charAt(0).toUpperCase();
    headerName.textContent   = other;
    headerBook.style.display = "none"; // pill replaces this

    // Enable input
    textarea.disabled = false;
    textarea.focus();

    // Show loading dots
    bubblesEl.innerHTML = "";
    if (loadingEl) {
      bubblesEl.appendChild(loadingEl);
      loadingEl.style.display = "flex";
    }

    await fetchMessages(fetchUrl, convId);

    // Clear unread badge for this conv
    const badge = document.getElementById("badge-" + convId);
    if (badge) badge.style.display = "none";

    // Poll every 5 s
    pollTimer = setInterval(() => fetchMessages(fetchUrl, convId, true), 5000);
  }

  async function fetchMessages(fetchUrl, convId, silent = false) {
    try {
      const res = await fetch(fetchUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } });
      if (!res.ok) return;
      const data = await res.json();
      if (!data.ok) return;

      // Only re-render if this conv is still active
      if (String(activeConvId) !== String(convId)) return;

      renderBubbles(data.messages, data.book_title, data.book_url);

      // Update preview in list
      const lastMsg = data.messages[data.messages.length - 1];
      if (lastMsg) {
        const preview = document.getElementById("preview-" + convId);
        if (preview) preview.textContent = lastMsg.body.slice(0, 50);
      }
    } catch (e) {
      // silently ignore network errors during polling
    }
  }

  function renderBubbles(messages, bookTitle, bookUrl) {
    // Preserve scroll position if user has scrolled up
    const atBottom = bubblesEl.scrollHeight - bubblesEl.clientHeight - bubblesEl.scrollTop < 60;

    bubblesEl.innerHTML = "";

    if (!messages || messages.length === 0) {
      bubblesEl.innerHTML = `<div style="text-align:center;color:var(--text-muted);font-size:.85rem;padding:32px 0;">No messages yet. Say hello!</div>`;
      return;
    }

    let lastDate = "";
    let lastBookTitle = null;

    messages.forEach(msg => {
      // Date separator
      const day = msg.created_at.split("·")[0].trim();
      if (day !== lastDate) {
        lastDate = day;
        const sep = document.createElement("div");
        sep.className = "msng-date-sep";
        sep.textContent = day;
        bubblesEl.appendChild(sep);
      }

      // Book context pill — only when book changes
      if (msg.book_title && msg.book_title !== lastBookTitle) {
        lastBookTitle = msg.book_title;
        bubblesEl.appendChild(buildBookPill(msg.book_title, msg.book_url));
      }

      bubblesEl.appendChild(buildBubble(msg));
    });

    if (atBottom) scrollToBottom();
  }

  // ── Send a message ──────────────────────────────────────────

  async function sendMessage() {
    const body = textarea.value.trim();
    if (!body || !activeSendUrl) return;

    // Optimistically disable send
    sendBtn.disabled = true;
    textarea.value   = "";
    textarea.style.height = "";

    const formData = new FormData();
    formData.append("body", body);
    formData.append("csrfmiddlewaretoken", csrf);

    try {
      const res = await fetch(activeSendUrl, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: formData,
      });

      const data = await res.json();

      if (data.ok) {
        // Book context pill if this message introduces a new book
        const bookPills = Array.from(bubblesEl.querySelectorAll(".msng-book-pill"));
        const lastPill = bookPills[bookPills.length - 1];
        const lastPillTitle = lastPill ? (lastPill.querySelector("a,span") || {}).textContent : null;
        if (data.book_title && data.book_title !== lastPillTitle) {
          bubblesEl.appendChild(buildBookPill(data.book_title, data.book_url));
        }

        // Append the new bubble
        const newDay = data.created_at.split("·")[0].trim();
        const dateSeps = Array.from(bubblesEl.querySelectorAll(".msng-date-sep"));
        const lastSep = dateSeps[dateSeps.length - 1];
        if (!lastSep || lastSep.textContent.trim() !== newDay) {
          const sep = document.createElement("div");
          sep.className = "msng-date-sep";
          sep.textContent = newDay;
          bubblesEl.appendChild(sep);
        }

        bubblesEl.appendChild(buildBubble(data));
        scrollToBottom();

        // Update preview
        const preview = document.getElementById("preview-" + activeConvId);
        if (preview) preview.textContent = data.body.slice(0, 50);
      }
    } catch (e) {
      // Restore text on failure
      textarea.value = body;
    }

    // Re-enable send if there's text
    sendBtn.disabled = textarea.value.trim() === "";
    textarea.focus();
  }

  // ── Auto-grow textarea ──────────────────────────────────────

  function autoGrow() {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
    sendBtn.disabled = textarea.value.trim() === "" || !activeConvId;
  }

  // ── Event listeners ─────────────────────────────────────────

  convItems.forEach(item => {
    item.addEventListener("click", () => loadConversation(item));
  });

  textarea.addEventListener("input", autoGrow);

  textarea.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  // ── Auto-open conversation if ?conv= param set ──────────────

  if (activeInit) {
    const target = document.querySelector(`.msng-conv-item[data-conv-id="${activeInit}"]`);
    if (target) {
      // Small delay so layout has rendered
      setTimeout(() => loadConversation(target), 80);
    }
  }

})();