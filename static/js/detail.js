// Book detail page — delete confirmation modal
(function () {
  var trigger = document.getElementById('delete-trigger');
  var modal   = document.getElementById('delete-modal');
  var cancel  = document.getElementById('delete-cancel');

  if (trigger && modal && cancel) {
    trigger.addEventListener('click', function () {
      modal.setAttribute('aria-hidden', 'false');
      modal.classList.add('is-open');
    });

    cancel.addEventListener('click', function () {
      modal.setAttribute('aria-hidden', 'true');
      modal.classList.remove('is-open');
    });

    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        modal.setAttribute('aria-hidden', 'true');
        modal.classList.remove('is-open');
      }
    });
  }
})();