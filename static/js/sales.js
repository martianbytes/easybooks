// Highlight the active row on hover — handled by CSS.
// Future: add client-side search/sort here if needed.
(function () {
  // Animate rows in on page load
  const rows = document.querySelectorAll('.sales-row');
  rows.forEach(function (row, i) {
    row.style.opacity = '0';
    row.style.transform = 'translateY(8px)';
    setTimeout(function () {
      row.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
      row.style.opacity = '1';
      row.style.transform = 'translateY(0)';
    }, 40 * i);
  });
})();
