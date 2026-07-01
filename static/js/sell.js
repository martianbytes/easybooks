function getCsrfToken() {
  return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
}

function getAuthorsField() {
  return document.querySelector('select[name="authors"]');
}

function addAuthorChip(id, name) {
  const tags = document.getElementById('author-tags');
  const authorsField = getAuthorsField();
  const input = document.getElementById('author-input');
  if (!tags || !authorsField || !input) return;

  let option = authorsField.querySelector(`option[value="${CSS.escape(String(id))}"]`);
  if (!option) {
    option = document.createElement('option');
    option.value = String(id);
    option.textContent = name;
    authorsField.appendChild(option);
  }
  option.selected = true;

  if (document.querySelector(`.author-tag[data-author-id="${CSS.escape(String(id))}"]`)) return;

  const chip = document.createElement('span');
  chip.className = 'author-tag';
  chip.dataset.authorId = String(id);
  chip.innerHTML = `${name} <button type="button" class="author-tag__remove" aria-label="Remove author">&times;</button>`;

  chip.querySelector('button')?.addEventListener('click', () => {
    option.selected = false;
    chip.remove();
  });

  tags.insertBefore(chip, input);
}

function showAuthorError(msg) {
  const input = document.getElementById('author-input');
  if (input) {
    input.style.outline = '2px solid red';
    setTimeout(() => { input.style.outline = ''; }, 3000);
  }
  let err = document.getElementById('author-input-error');
  if (!err) {
    err = document.createElement('div');
    err.id = 'author-input-error';
    err.style.cssText = 'color:#b91c1c; font-size:0.8rem; margin-top:4px; padding:4px 8px;';
    input?.insertAdjacentElement('afterend', err);
  }
  err.textContent = msg;
  setTimeout(() => { err.textContent = ''; }, 3000);
}

async function saveAuthorByName(name) {
  const trimmed = (name || '').trim();

  if (!trimmed) {
    showAuthorError('Author name cannot be empty or only spaces.');
    return null;
  }

  const authorCreateUrl = document.getElementById('sell-form').dataset.authorCreateUrl;
  const res = await fetch(authorCreateUrl, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({ new_author_name: trimmed }),
  });

  const data = await res.json();
  if (!data?.ok) {
    showAuthorError(data.error || 'Invalid author name.');
    return null;
  }

  addAuthorChip(data.id, data.name);
  return data;
}

(function bindAuthorSearch() {
  const input = document.getElementById('author-input');
  const dropdown = document.getElementById('author-dropdown');
  const all = window.EB_SELL_CONTEXT?.all_authors || [];

  if (!input || !dropdown) return;

  function renderDropdown(matches, typed) {
    dropdown.innerHTML = '';

    if (matches.length === 0 && typed) {
      const item = document.createElement('div');
      item.className = 'author-dropdown-item new-author';
      item.dataset.newAuthor = typed;
      item.textContent = `+ Add new author "${typed}"`;

      item.style.padding = '12px 14px';
      item.style.cursor = 'pointer';
      item.style.fontWeight = '600';
      item.style.color = '#2563eb';
      item.style.background = '#f8fbff';
      item.style.borderTop = '1px solid #e5eefc';

      item.addEventListener('mouseenter', () => { item.style.background = '#eef5ff'; });
      item.addEventListener('mouseleave', () => { item.style.background = '#f8fbff'; });

      dropdown.appendChild(item);
    } else {
      matches.forEach((a) => {
        const item = document.createElement('div');
        item.className = 'author-dropdown-item';
        item.dataset.authorId = String(a.id);
        item.textContent = a.name;
        dropdown.appendChild(item);
      });
    }

    dropdown.style.display = dropdown.children.length ? 'block' : 'none';
  }

  input.addEventListener('input', (e) => {
    const v = e.target.value.trim();
    if (!v) {
      dropdown.style.display = 'none';
      dropdown.innerHTML = '';
      return;
    }
    const q = v.toLowerCase();
    const matches = all.filter((a) => String(a.name || '').toLowerCase().includes(q));
    renderDropdown(matches, v);
  });

  dropdown.addEventListener('click', (e) => {
    const item = e.target.closest('.author-dropdown-item');
    if (!item) return;

    if (item.classList.contains('new-author')) {
      saveAuthorByName(item.dataset.newAuthor).then(() => {
        input.value = '';
        dropdown.style.display = 'none';
      });
      return;
    }

    const id = item.dataset.authorId;
    const name = item.textContent || '';
    addAuthorChip(id, name);
    input.value = '';
    dropdown.style.display = 'none';
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const first = dropdown.querySelector('.author-dropdown-item');
      if (first) {
        first.click();
      } else {
        saveAuthorByName(input.value).then(() => {
          input.value = '';
          dropdown.style.display = 'none';
        });
      }
    }
    if (e.key === 'Escape') {
      dropdown.style.display = 'none';
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('#author-tag-wrap')) {
      dropdown.style.display = 'none';
    }
  });
})();

function updatePricePreview() {
  const orig = document.getElementById('id_original_price');
  const ask = document.getElementById('id_asking_price');
  const preview = document.getElementById('price-preview');
  const ppOrig = document.getElementById('pp-orig');
  const ppAsk = document.getElementById('pp-ask');
  const ppDiscount = document.getElementById('pp-discount');

  if (!orig || !ask || !preview || !ppOrig || !ppAsk || !ppDiscount) return;

  const o = parseFloat(orig.value);
  const a = parseFloat(ask.value);

  if (!Number.isFinite(o) || !Number.isFinite(a) || o <= 0 || a <= 0) {
    preview.style.display = 'none';
    return;
  }

  ppOrig.textContent = `Rs. ${o.toLocaleString('en-PK')}`;
  ppAsk.textContent = `Rs. ${a.toLocaleString('en-PK')}`;

  const discount = ((o - a) / o) * 100;
  ppDiscount.textContent = discount > 0 ? `${discount.toFixed(0)}% off` : '';
  preview.style.display = 'block';
}

(function bindPricePreview() {
  const orig = document.getElementById('id_original_price');
  const ask = document.getElementById('id_asking_price');
  orig?.addEventListener('input', updatePricePreview);
  ask?.addEventListener('input', updatePricePreview);
  updatePricePreview();
})();

function triggerImagePicker(zoneEl) {
  const fileInput = zoneEl?.closest('.image-form-group')?.querySelector('input[type="file"]');
  if (fileInput) fileInput.click();
}

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

  // Mark deleted until a new real file is chosen.
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

    // IMPORTANT: picking a new file cancels the earlier delete.
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

(function restoreImagePreviews() {
  const dataUrls = window.EB_SELL_CONTEXT?.image_data_urls || {};
  Object.entries(dataUrls).forEach(([key, src]) => {
    if (!src) return;
    const match = key.match(/images-(\d+)-image_dataurl/);
    if (!match) return;
    const idx = match[1];

    const ta = document.getElementById(`dataurl-${idx}`);
    if (ta) ta.value = src;

    const preview = document.getElementById(`preview-${idx}`);
    const placeholder = document.getElementById(`placeholder-${idx}`);
    const removeBtn = document.getElementById(`remove-${idx}`);
    const zone = document.getElementById(`zone-${idx}`);
    const del = document.querySelector(
      `.image-form-group[data-index="${idx}"] input[type="checkbox"][name$="-DELETE"]`
    );

    if (preview) { preview.src = src; preview.style.display = 'block'; }
    if (placeholder) placeholder.style.display = 'none';
    if (removeBtn) removeBtn.style.display = 'inline-flex';
    zone?.classList.add('has-image');
    if (del) del.checked = false;
  });
})();

(function bindAddImageSlot() {
  const btn = document.getElementById('add-image-slot');
  const grid = document.getElementById('img-grid');
  const template = document.getElementById('empty-image-form-template');
  const totalFormsInput = document.querySelector('input[name="images-TOTAL_FORMS"]');

  if (!btn || !grid || !template || !totalFormsInput) return;

  btn.addEventListener('click', () => {
    const idx = parseInt(totalFormsInput.value, 10);
    const clone = template.content.cloneNode(true);

    clone.querySelectorAll('[id]').forEach(el => {
      el.id = el.id.replace('__prefix__', idx);
    });
    clone.querySelectorAll('[name]').forEach(el => {
      el.name = el.name.replace('__prefix__', idx);
    });
    clone.querySelectorAll('[for]').forEach(el => {
      el.htmlFor = el.htmlFor.replace('__prefix__', idx);
    });

    const slot = clone.querySelector('.image-form-group');
    if (slot) slot.dataset.index = idx;

    const zone = clone.querySelector('.img-zone');
    if (zone) zone.setAttribute('onclick', `triggerImagePicker(this)`);

    const removeBtn = clone.querySelector('.img-zone__clear');
    if (removeBtn) removeBtn.setAttribute('onclick', `clearImageSlot(event, ${idx})`);

    grid.insertBefore(clone, btn);
    totalFormsInput.value = idx + 1;

    if (idx + 1 >= 8) btn.style.display = 'none';
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

    // Cover validation must be done server-side.
  });
})();