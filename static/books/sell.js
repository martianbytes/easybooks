document.addEventListener('DOMContentLoaded', () => {
  const ctx = window.EB_SELL_CONTEXT || {};
  const ALL_AUTHORS = ctx.all_authors || [];
  const IMAGE_DATAURLS = ctx.image_data_urls || {};
  const PRESELECTED_AUTHOR_ID = ctx.preselected_author_id || 0;

  /* CONDITION PICKER */
  const condInput = document.getElementById('id_condition');
  if (condInput) {
    document.querySelectorAll('.condition-card').forEach(card => {
      if (card.dataset.value === condInput.value) card.classList.add('active');
      card.addEventListener('click', () => {
        document.querySelectorAll('.condition-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        condInput.value = card.dataset.value;
      });
    });
  }

  /* AUTHOR TAG WIDGET */
  const authorSelect   = document.getElementById('id_authors');
  const authorTagsBox  = document.getElementById('author-tags');
  const authorInput    = document.getElementById('author-input');
  const authorDropdown = document.getElementById('author-dropdown');
  let selectedAuthors = [];
  let kbdIdx = -1;

  if (authorSelect && authorTagsBox && authorInput && authorDropdown) {
    Array.from(authorSelect.selectedOptions).forEach(opt => {
      _addTag({ id: opt.value, name: opt.text });
    });

    if (PRESELECTED_AUTHOR_ID) {
      const found = ALL_AUTHORS.find(a => String(a.id) === String(PRESELECTED_AUTHOR_ID));
      if (found) {
        let opt = authorSelect.querySelector(`option[value="${PRESELECTED_AUTHOR_ID}"]`);
        if (!opt) { opt = new Option(found.name, found.id); authorSelect.appendChild(opt); }
        opt.selected = true;
        _addTag(found);
      }
    }
  }

  function _addTag(author) {
    if (selectedAuthors.find(a => String(a.id) === String(author.id))) return;
    selectedAuthors.push(author);
    _syncSelect();
    if (!authorTagsBox) return;
    const tag = document.createElement('div');
    tag.className  = 'author-tag';
    tag.dataset.id = author.id;
    tag.innerHTML  = `<span>${author.name}</span>
                      <span class="author-tag-remove" onclick="(function(){document.querySelector('.author-tag[data-id=\\'${author.id}\\']')?.remove();})()">✕</span>`;
    authorTagsBox.insertBefore(tag, authorInput);
  }

  window.removeAuthor = function(id) {
    selectedAuthors = selectedAuthors.filter(a => String(a.id) !== String(id));
    document.querySelector(`.author-tag[data-id="${id}"]`)?.remove();
    _syncSelect();
  };

  function _syncSelect() {
    if (!authorSelect) return;
    Array.from(authorSelect.options).forEach(opt => {
      opt.selected = selectedAuthors.some(a => String(a.id) === opt.value);
    });
  }

  if (authorInput) {
    authorInput.addEventListener('input',  _showDropdown);
    authorInput.addEventListener('focus',  _showDropdown);
    authorInput.addEventListener('blur',   () => setTimeout(_hideDropdown, 180));
    authorTagsBox?.addEventListener('click', () => authorInput.focus());

    authorInput.addEventListener('keydown', e => {
      const items = [...authorDropdown.querySelectorAll('.author-dropdown-item, .author-dropdown-create')];
      if      (e.key === 'ArrowDown')  { kbdIdx = Math.min(kbdIdx + 1, items.length - 1); _highlightKbd(items); e.preventDefault(); }
      else if (e.key === 'ArrowUp')    { kbdIdx = Math.max(kbdIdx - 1, 0); _highlightKbd(items); e.preventDefault(); }
      else if (e.key === 'Enter')      { e.preventDefault(); items[kbdIdx]?.click(); }
      else if (e.key === 'Escape')     { _hideDropdown(); }
    });
  }

  function _highlightKbd(items) { items.forEach((el, i) => el.classList.toggle('kbd-focus', i === kbdIdx)); }

  function _showDropdown() {
    const q = authorInput.value.toLowerCase().trim();
    const matches = ALL_AUTHORS.filter(a =>
      a.name.toLowerCase().includes(q) && !selectedAuthors.find(s => String(s.id) === String(a.id))
    );
    authorDropdown.innerHTML = '';
    kbdIdx = -1;

    matches.forEach(a => {
      const el = document.createElement('div');
      el.className   = 'author-dropdown-item';
      el.textContent = a.name;
      el.addEventListener('mousedown', () => { _addTag(a); authorInput.value = ''; _hideDropdown(); });
      authorDropdown.appendChild(el);
    });

    if (q) {
      const create = document.createElement('div');
      create.className   = 'author-dropdown-create';
      create.textContent = `+ Add new author "${authorInput.value}"`;
      create.addEventListener('mousedown', () => {
        const nameInput = document.querySelector('.add-author-inline-form input[name="new_author_name"]');
        if (nameInput) nameInput.value = authorInput.value;
        document.querySelector('.add-author-details').open = true;
        document.querySelector('.add-author-details').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        _hideDropdown();
      });
      authorDropdown.appendChild(create);
    }

    authorDropdown.style.display = (matches.length || q) ? 'block' : 'none';
  }
  function _hideDropdown() { authorDropdown.style.display = 'none'; }

  /* PRICE PREVIEW */
  const origInput = document.getElementById('id_original_price');
  const askInput  = document.getElementById('id_asking_price');
  const priceBox  = document.getElementById('price-preview');

  function _updatePrice() {
    const orig = parseFloat(origInput?.value);
    const ask  = parseFloat(askInput?.value);
    if (!isNaN(ask) && ask > 0) {
      document.getElementById('pp-ask').textContent = `Rs. ${ask.toFixed(0)}`;
      if (!isNaN(orig) && orig > 0 && orig > ask) {
        const pct = Math.round((orig - ask) / orig * 100);
        document.getElementById('pp-orig').textContent     = `Rs. ${orig.toFixed(0)}`;
        document.getElementById('pp-discount').textContent = `${pct}% OFF`;
        document.getElementById('pp-orig').style.display     = '';
        document.getElementById('pp-discount').style.display = '';
      } else {
        document.getElementById('pp-orig').style.display     = 'none';
        document.getElementById('pp-discount').style.display = 'none';
      }
      priceBox.style.display = 'block';
    } else {
      priceBox.style.display = 'none';
    }
  }
  origInput?.addEventListener('input', _updatePrice);
  askInput?.addEventListener('input',  _updatePrice);
  _updatePrice();

  /* IMAGE UPLOAD + PERSISTENCE */
  document.querySelectorAll('input[type=file][name$="-image"]').forEach(fileInput => {
    fileInput.addEventListener('change', function () {
      const idx  = this.closest('.image-form-group').dataset.index;
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = e => {
        const dataUrl = e.target.result;
        const ta = document.getElementById(`dataurl-${idx}`);
        if (ta) ta.value = dataUrl;
        _showPreview(idx, dataUrl);
      };
      reader.readAsDataURL(file);
    });
  });

  function _showPreview(idx, dataUrl) {
    const zone        = document.getElementById(`zone-${idx}`);
    const preview     = document.getElementById(`preview-${idx}`);
    const placeholder = document.getElementById(`placeholder-${idx}`);
    const removeBtn   = document.getElementById(`remove-${idx}`);
    if (!preview) return;
    preview.src               = dataUrl;
    preview.style.display     = 'block';
    if (placeholder) placeholder.style.display = 'none';
    if (removeBtn) removeBtn.style.display   = 'flex';
    if (zone) zone.classList.add('has-image');
  }

  window.clearImageSlot = function(event, idx) {
    event.stopPropagation();
    const zone        = document.getElementById(`zone-${idx}`);
    const preview     = document.getElementById(`preview-${idx}`);
    const placeholder = document.getElementById(`placeholder-${idx}`);
    const removeBtn   = document.getElementById(`remove-${idx}`);
    const dataUrlTA   = document.getElementById(`dataurl-${idx}`);
    const fileInput = zone?.closest('.image-form-group')?.querySelector('input[type=file]');
    if (fileInput) fileInput.value = '';
    if (dataUrlTA) dataUrlTA.value = '';
    if (preview) { preview.src = ''; preview.style.display = 'none'; }
    if (placeholder) placeholder.style.display = 'flex';
    if (removeBtn) removeBtn.style.display = 'none';
    zone?.classList.remove('has-image');
    const delBox = zone?.closest('.image-form-group')?.querySelector('input[type=checkbox][name$="-DELETE"]');
    if (delBox) delBox.checked = true;
  };

  (function restorePreviews() {
    for (const [key, dataUrl] of Object.entries(IMAGE_DATAURLS || {})) {
      if (!dataUrl?.startsWith('data:')) continue;
      const m = key.match(/images-(\d+)-image_dataurl/);
      if (!m) continue;
      const idx = m[1];
      const ta  = document.getElementById(`dataurl-${idx}`);
      if (ta) ta.value = dataUrl;
      _showPreview(idx, dataUrl);
    }
  })();

  /* STATUS default + submit spinner */
  const statusInput = document.getElementById('id_status');
  if (statusInput && !statusInput.value) statusInput.value = 'available';

  document.getElementById('sell-form')?.addEventListener('submit', () => {
    const sp = document.getElementById('submit-spinner');
    const btn = document.getElementById('submit-btn');
    if (sp) sp.style.display = 'inline-block';
    if (btn) btn.disabled = true;
  });

});