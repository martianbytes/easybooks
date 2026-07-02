(function () {
  var toggle = document.getElementById('navbar-toggle');
  var menu = document.getElementById('navbar-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', function () {
    var isOpen = menu.classList.toggle('is-open');
    toggle.classList.toggle('is-active', isOpen);
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  document.addEventListener('click', function (e) {
    if (!menu.classList.contains('is-open')) return;
    if (menu.contains(e.target) || toggle.contains(e.target)) return;
    menu.classList.remove('is-open');
    toggle.classList.remove('is-active');
    toggle.setAttribute('aria-expanded', 'false');
  });
})();