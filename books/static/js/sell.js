function clearImageSlot(event, idx) {
  event.stopPropagation();

  const zone = document.getElementById(`zone-${idx}`);
  const preview = document.getElementById(`preview-${idx}`);
  const ph = document.getElementById(`placeholder-${idx}`);
  const btn = document.getElementById(`remove-${idx}`);
  const ta = document.getElementById(`dataurl-${idx}`);
  const fileInput = zone?.closest('.image-form-group')?.querySelector('input[type="file"]');
  const del = zone?.closest('.image-form-group')?.querySelector('input[type="checkbox"][name$="-DELETE"]');

  if (fileInput) fileInput.value = '';
  if (ta) ta.value = '';
  if (preview) { preview.src = ''; preview.style.display = 'none'; }
  if (ph) ph.style.display = 'flex';
  if (btn) btn.style.display = 'none';
  zone?.classList.remove('has-image');
  if (del) del.checked = true;
}

(function bindImagePicker() {
  const grid = document.getElementById('img-grid');
  if (!grid) return;

  grid.addEventListener('change', (e) => {
    const input = e.target;
    if (!(input instanceof HTMLInputElement) || input.type !== 'file') return;
    if (!input.files || !input.files[0]) return;

    const slot = input.closest('.image-form-group');
    if (!slot) return;

    const idx = slot.dataset.index;
    const preview = document.getElementById(`preview-${idx}`);
    const placeholder = document.getElementById(`placeholder-${idx}`);
    const removeBtn = document.getElementById(`remove-${idx}`);
    const zone = document.getElementById(`zone-${idx}`);
    const dataUrl = document.getElementById(`dataurl-${idx}`);
    const del = slot.querySelector('input[type="checkbox"][name$="-DELETE"]');

    if (del) del.checked = false;

    const reader = new FileReader();
    reader.onload = () => {
      const src = String(reader.result || '');
      if (preview) { preview.src = src; preview.style.display = 'block'; }
      if (placeholder) placeholder.style.display = 'none';
      if (removeBtn) removeBtn.style.display = 'inline-flex';
      zone?.classList.add('has-image');
      if (dataUrl) dataUrl.value = src;

      if (idx === '0') {
        document.getElementById('cover-error-msg')?.remove();
      }
    };
    reader.readAsDataURL(input.files[0]);
  });
})();

(function bindFormSubmitValidation() {
  const form = document.getElementById('sell-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    const authorsField = getAuthorsField();
    const selected = authorsField
      ? Array.from(authorsField.options).filter(o => o.selected)
      : [];

    if (selected.length === 0) {
      e.preventDefault();
      showAuthorError('Please add at least one author.');
      document.getElementById('author-input')?.focus();
      return;
    }

    // Cover validation is handled server-side to avoid duplicate/false errors.
  });
})();