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

  // ── Per-message inline reply toggle ───────────────────────────────
  document.querySelectorAll('.inbox-reply-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id      = btn.dataset.msgId;
      var form    = document.getElementById('reply-form-' + id);
      var thread  = document.getElementById('thread-' + id);
      if (!form) return;
      var opening = form.style.display === 'none';
      form.style.display  = opening ? 'block' : 'none';
      thread.style.display = 'block';
      if (opening) form.querySelector('.reply-textarea').focus();
    });
  });

  // ── Per-message cancel ────────────────────────────────────────────
  document.querySelectorAll('.reply-cancel-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id   = btn.dataset.msgId;
      var form = document.getElementById('reply-form-' + id);
      if (form) {
        form.style.display = 'none';
        form.querySelector('.reply-textarea').value = '';
      }
    });
  });

  // ── Per-message send ──────────────────────────────────────────────
  document.querySelectorAll('.reply-send-btn:not(#reply-bar-send)').forEach(function (btn) {
    btn.addEventListener('click', function () {
      sendReply(
        btn.dataset.msgId,
        document.getElementById('reply-form-' + btn.dataset.msgId).querySelector('.reply-textarea'),
        btn,
        function (id) {
          document.getElementById('reply-form-' + id).style.display = 'none';
        }
      );
    });
  });

  // ── Bottom new-message bar ─────────────────────────────────────────
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
    barTextarea.disabled     = false;
    barSend.disabled         = false;
    barTextarea.focus();
  }

  // Auto-activate first conversation so bar is ready immediately
  var firstBtn = document.querySelector('.inbox-reply-btn');
  if (firstBtn) {
    activateBar(
      firstBtn.dataset.msgId,
      firstBtn.dataset.replyUrl,
      firstBtn.dataset.sender,
      firstBtn.dataset.book
    );
  }

  // Clicking Reply on a different message also switches the bar context
  document.querySelectorAll('.inbox-reply-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      activateBar(btn.dataset.msgId, btn.dataset.replyUrl, btn.dataset.sender, btn.dataset.book);
    });
  });

  if (barClear) {
    barClear.addEventListener('click', function () {
      activeMsgId = activeReplyUrl = null;
      barContext.style.display = 'none';
      barTextarea.disabled = true;
      barSend.disabled     = true;
      barTextarea.value    = '';
    });
  }

  if (barSend) {
    barSend.addEventListener('click', function () {
      if (!activeMsgId || !activeReplyUrl) return;
      sendReply(activeMsgId, barTextarea, barSend, function () {
        barTextarea.value = '';
        barTextarea.focus();
      }, activeReplyUrl);
    });
  }

  // ── Auto-activate ?open=<pk> thread ───────────────────────────────
  var openParam = new URLSearchParams(window.location.search).get('open');
  if (openParam) {
    var triggerBtn = document.querySelector('.inbox-reply-btn[data-msg-id="' + openParam + '"]');
    if (triggerBtn) {
      activateBar(triggerBtn.dataset.msgId, triggerBtn.dataset.replyUrl, triggerBtn.dataset.sender, triggerBtn.dataset.book);
      setTimeout(function () {
        barTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    }
  }

  // ── Shared send helper ────────────────────────────────────────────
  function sendReply(msgId, textarea, btn, onSuccess, overrideUrl) {
    var body = textarea.value.trim();
    if (!body) { textarea.focus(); return; }
    var url = overrideUrl || textarea.dataset.replyUrl;
    btn.disabled    = true;
    btn.textContent = 'Sending…';

    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'body=' + encodeURIComponent(body),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) { alert(data.error || 'Failed to send.'); return; }
        var thread = document.getElementById('thread-' + msgId);
        var bubble = document.createElement('div');
        bubble.className = 'reply-bubble reply-bubble--self';
        bubble.innerHTML =
          '<span class="reply-bubble__sender">' + data.sender + '</span>' +
          '<p class="reply-bubble__text">' + escapeHtml(data.body) + '</p>' +
          '<span class="reply-bubble__time">' + data.created_at + '</span>';
        thread.appendChild(bubble);

        // Update reply count
        var replyBtn = document.querySelector('.inbox-reply-btn[data-msg-id="' + msgId + '"]');
        if (replyBtn) {
          var countSpan = replyBtn.querySelector('.reply-count');
          if (countSpan) {
            countSpan.textContent = '(' + (parseInt(countSpan.textContent.replace(/\D/g,''), 10) + 1) + ')';
          } else {
            var s = document.createElement('span');
            s.className = 'reply-count';
            s.textContent = '(1)';
            replyBtn.appendChild(s);
          }
        }
        onSuccess(msgId);
      })
      .finally(function () {
        btn.disabled = false;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send';
      });
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
})();
