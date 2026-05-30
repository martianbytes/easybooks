(function () {
  var csrfToken = document.cookie
    .split('; ')
    .find(function (r) { return r.startsWith('csrftoken='); });
  csrfToken = csrfToken ? csrfToken.split('=')[1] : '';

  // ── Mark as read via IntersectionObserver ─────────────────────────
  var readObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var item = entry.target;
      if (item.dataset.alreadyRead) return;
      var url = item.dataset.readUrl;
      if (!url) return;
      fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken } })
        .then(function (res) {
          if (!res.ok) return;
          item.classList.remove('inbox-item--unread');
          var dot = item.querySelector('.inbox-unread-dot');
          if (dot) dot.remove();
          item.dataset.alreadyRead = '1';
          readObserver.unobserve(item);
          ['pdb-nav-badge', 'msg-badge'].forEach(function (cls) {
            var badge = document.querySelector('.' + cls);
            if (!badge) return;
            var n = parseInt(badge.textContent, 10) - 1;
            n <= 0 ? badge.remove() : (badge.textContent = n);
          });
        });
    });
  }, { threshold: 0.6 });

  document.querySelectorAll('.inbox-item--unread').forEach(function (item) {
    readObserver.observe(item);
  });

  // ── Bottom message bar state ───────────────────────────────────────
  var barTextarea = document.getElementById('reply-bar-textarea');
  var barSend     = document.getElementById('reply-bar-send');
  var barContext  = document.getElementById('reply-bar-context');
  var barLabel    = document.getElementById('reply-bar-label');
  var barClear    = document.getElementById('reply-bar-clear');

  var activeMsgId    = null;
  var activeReplyUrl = null;

  function activateBar(msgId, replyUrl, sender, book) {
    activeMsgId    = msgId;
    activeReplyUrl = replyUrl;
    barLabel.textContent     = sender + ' · ' + book;
    barContext.style.display = 'flex';
    barTextarea.focus();
  }

  // Seed bar with the first conversation on load
  var firstBtn = document.querySelector('.inbox-reply-btn');
  if (firstBtn) {
    activeMsgId    = firstBtn.dataset.msgId;
    activeReplyUrl = firstBtn.dataset.replyUrl;
  }

  // Clicking Reply on any message switches the active conversation
  document.querySelectorAll('.inbox-reply-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      activateBar(btn.dataset.msgId, btn.dataset.replyUrl, btn.dataset.sender, btn.dataset.book);
      // Scroll the bar into view
      barTextarea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  // Clear resets back to first conversation (never disables the bar)
  if (barClear) {
    barClear.addEventListener('click', function () {
      barTextarea.value = '';
      if (firstBtn) {
        activateBar(firstBtn.dataset.msgId, firstBtn.dataset.replyUrl, firstBtn.dataset.sender, firstBtn.dataset.book);
      }
    });
  }

  // Send via button
  if (barSend) {
    barSend.addEventListener('click', function () {
      doSend();
    });
  }

  // Send via Enter (Shift+Enter = newline)
  if (barTextarea) {
    barTextarea.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        doSend();
      }
    });
  }

  function doSend() {
    if (!activeMsgId || !activeReplyUrl) return;
    var body = barTextarea.value.trim();
    if (!body) { barTextarea.focus(); return; }

    barSend.disabled    = true;
    barSend.textContent = 'Sending…';

    fetch(activeReplyUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'body=' + encodeURIComponent(body),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) { alert(data.error || 'Failed to send.'); return; }

        // Append the new bubble to the flat chat thread
        var thread = document.getElementById('thread-' + activeMsgId);
        var bubble = document.createElement('div');
        bubble.className = 'reply-bubble reply-bubble--self';
        bubble.innerHTML =
          '<span class="reply-bubble__sender">' + escapeHtml(data.sender) + '</span>' +
          '<p class="reply-bubble__text">' + escapeHtml(data.body) + '</p>' +
          '<span class="reply-bubble__time">' + data.created_at + '</span>';
        thread.appendChild(bubble);

        // Scroll the new bubble into view
        bubble.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Update reply count on the Reply button
        var replyBtn = document.querySelector('.inbox-reply-btn[data-msg-id="' + activeMsgId + '"]');
        if (replyBtn) {
          var countSpan = replyBtn.querySelector('.reply-count');
          if (countSpan) {
            countSpan.textContent = '(' + (parseInt(countSpan.textContent.replace(/\D/g, ''), 10) + 1) + ')';
          } else {
            var s = document.createElement('span');
            s.className = 'reply-count';
            s.textContent = '(1)';
            replyBtn.appendChild(s);
          }
        }

        barTextarea.value = '';
        barTextarea.focus();
      })
      .finally(function () {
        barSend.disabled = false;
        barSend.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send';
      });
  }

  // ── Auto-activate ?open=<pk> thread ───────────────────────────────
  var openParam = new URLSearchParams(window.location.search).get('open');
  if (openParam) {
    var triggerBtn = document.querySelector('.inbox-reply-btn[data-msg-id="' + openParam + '"]');
    if (triggerBtn) {
      activateBar(triggerBtn.dataset.msgId, triggerBtn.dataset.replyUrl, triggerBtn.dataset.sender, triggerBtn.dataset.book);
      setTimeout(function () {
        document.getElementById('inbox-item-' + openParam)
          .scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
})();