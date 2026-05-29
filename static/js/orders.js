(function () {
  // Toggle "Complete via Other Method" form visibility
  document.querySelectorAll('[data-toggle-other-form]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.getAttribute('data-toggle-other-form');
      var form = document.getElementById(targetId);
      if (form) {
        form.classList.toggle('order-other-form--visible');
      }
    });
  });
})();
