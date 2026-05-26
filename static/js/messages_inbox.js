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
          // Update badges
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

  // ── Toggle reply form ──────────────────────────────────────────────
  document.querySelectorAll('[data-toggle-reply]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = this.dataset.toggleReply;
      var form = document.getElementById('reply-form-' + id);
      var thread = document.getElementById('thread-' + id);
      if (!form) return;
      var isHidden = form.style.display === 'none';
      form.style.display = isHidden ? 'block' : 'none';
      if (isHidden) {
        thread.style.display = 'block';
        form.querySelector('.reply-textarea').focus();
      }
    });
  });

  // ── Cancel reply ───────────────────────────────────────────────────
  document.querySelectorAll('.reply-cancel-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = this.dataset.msgId;
      var form = document.getElementById('reply-form-' + id);
      if (form) {
        form.style.display = 'none';
        form.querySelector('.reply-textarea').value = '';
      }
    });
  });

  // ── Send reply ─────────────────────────────────────────────────────
  document.querySelectorAll('.reply-send-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = this.dataset.msgId;
      var form = document.getElementById('reply-form-' + id);
      var textarea = form.querySelector('.reply-textarea');
      var body = textarea.value.trim();
      if (!body) { textarea.focus(); return; }

      var url = textarea.dataset.replyUrl;
      btn.disabled = true;
      btn.textContent = 'Sending…';

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'body=' + encodeURIComponent(body),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.ok) { alert(data.error || 'Failed to send.'); return; }

          // Append bubble
          var thread = document.getElementById('thread-' + id);
          var bubble = document.createElement('div');
          bubble.className = 'reply-bubble reply-bubble--self';
          bubble.innerHTML =
            '<span class="reply-bubble__sender">' + data.sender + '</span>' +
            '<p class="reply-bubble__text">' + escapeHtml(data.body) + '</p>' +
            '<span class="reply-bubble__time">' + data.created_at + '</span>';
          thread.insertBefore(bubble, form);

          // Update reply count on button
          var toggleBtn = document.querySelector('[data-toggle-reply="' + id + '"]');
          if (toggleBtn) {
            var countSpan = toggleBtn.querySelector('.reply-count');
            if (countSpan) {
              var n = parseInt(countSpan.textContent.replace(/\D/g, ''), 10) + 1;
              countSpan.textContent = '(' + n + ')';
            } else {
              var s = document.createElement('span');
              s.className = 'reply-count';
              s.textContent = '(1)';
              toggleBtn.appendChild(s);
            }
          }

          textarea.value = '';
          form.style.display = 'none';
        })
        .finally(function () {
          btn.disabled = false;
          btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send';
        });
    });
  });

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
})();
