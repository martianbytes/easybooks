document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('filter-form');
  if (!form) return;

  // Pills (radio buttons) — toggle active class visually
  form.querySelectorAll('.filter-pill input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const group = radio.closest('.filter-pill-group');
      group.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      radio.closest('.filter-pill').classList.add('active');
    });
  });

  // Checkboxes — toggle active class visually
  form.querySelectorAll('.filter-check-item input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      cb.closest('.filter-check-item').classList.toggle('checked', cb.checked);
    });
    // Set initial state
    if (cb.checked) cb.closest('.filter-check-item').classList.add('checked');
  });

  // Sort select — inject sort into filter form and submit
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      let sortInput = form.querySelector('input[name="sort"]');
      if (!sortInput) {
        sortInput = document.createElement('input');
        sortInput.type = 'hidden';
        sortInput.name = 'sort';
        form.appendChild(sortInput);
      }
      sortInput.value = sortSelect.value;
      form.submit();
    });
  }
});