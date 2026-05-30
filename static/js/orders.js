(function () {
  document.querySelectorAll('[data-toggle-other-form]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.getAttribute('data-toggle-other-form');
      var panel = document.getElementById(targetId);
      if (!panel) return;
      var isVisible = panel.style.display !== 'none';
      panel.style.display = isVisible ? 'none' : 'block';
      // Toggle active state visually
      if (isVisible) {
        btn.classList.remove('obtn--primary');
        btn.classList.add('obtn--outline');
      } else {
        btn.classList.remove('obtn--outline');
        btn.classList.add('obtn--primary');
      }
    });
  });
})();
