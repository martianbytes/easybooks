(function () {
  // Mark each message as read via POST when it scrolls into view
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1] || '';

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      const item = entry.target;
      if (item.dataset.alreadyRead) return;

      const url = item.dataset.readUrl;
      if (!url) return;

      fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
      }).then(function (res) {
        if (res.ok) {
          item.classList.remove('inbox-item--unread');
          const dot = item.querySelector('.inbox-unread-dot');
          if (dot) dot.remove();
          item.dataset.alreadyRead = '1';
          observer.unobserve(item);

          // Update the nav badge count
          const badge = document.querySelector('.pdb-nav-badge');
          const msgBadge = document.querySelector('.msg-badge');
          if (badge) {
            let n = parseInt(badge.textContent, 10) - 1;
            if (n <= 0) {
              badge.remove();
              if (msgBadge) msgBadge.remove();
            } else {
              badge.textContent = n;
              if (msgBadge) msgBadge.textContent = n;
            }
          }
        }
      });
    });
  }, { threshold: 0.6 });

  document.querySelectorAll('.inbox-item--unread').forEach(function (item) {
    observer.observe(item);
  });
})();
