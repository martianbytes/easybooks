(function () {
  const overlay  = document.getElementById('pdb-delete-modal');
  const form     = document.getElementById('pdb-delete-form');
  const titleEl  = document.getElementById('pdb-delete-book-title');
  const cancelBtn = document.getElementById('pdb-delete-cancel');

  document.querySelectorAll('[data-delete-trigger]').forEach(btn => {
    btn.addEventListener('click', function () {
      titleEl.textContent = this.dataset.title;
      form.action = this.dataset.action;
      overlay.setAttribute('aria-hidden', 'false');
      overlay.classList.add('is-open');
    });
  });

  function closeModal() {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
  }

  cancelBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });
})();
