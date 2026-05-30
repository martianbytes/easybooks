(function () {
  document.querySelectorAll('[data-toggle-other-form]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.getAttribute('data-toggle-other-form');
      var panel = document.getElementById(targetId);
      if (!panel) return;
      var isVisible = panel.style.display !== 'none';
      panel.style.display = isVisible ? 'none' : 'block';
      btn.classList.toggle('obtn--outline', !isVisible);
    });
  });
})();