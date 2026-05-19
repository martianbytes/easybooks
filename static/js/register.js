/* static/js/register.js
 * Live client-side validation for the EasyBooks registration form.
 * Mirrors the server-side rules in accounts/forms.py → UserRegistrationForm.
 */
(function () {
  /* ── helpers ──────────────────────────────────────────────────────── */
  function get(id) { return document.getElementById(id); }

  function setErr(el, msg) {
    if (!el) return;
    el.textContent = msg;
    el.style.display = msg ? 'block' : 'none';
  }

  function markInvalid(input, errEl, msg) {
    input.classList.add('input-invalid');
    input.classList.remove('input-valid');
    setErr(errEl, msg);
  }

  function markValid(input, errEl) {
    input.classList.remove('input-invalid');
    input.classList.add('input-valid');
    setErr(errEl, '');
  }

  /* ── field refs ───────────────────────────────────────────────────── */
  const usernameInput  = get('id_username');
  const emailInput     = get('id_email');
  const firstNameInput = get('id_first_name');
  const lastNameInput  = get('id_last_name');
  const pw1Input       = get('id_password1');
  const pw2Input       = get('id_password2');

  const errUsername  = get('err-username');
  const errEmail     = get('err-email');
  const errFirstName = get('err-first-name');
  const errLastName  = get('err-last-name');
  const errPw1       = get('err-password1');
  const errPw2       = get('err-password2');

  /* ── validators ───────────────────────────────────────────────────── */
  function validateUsername() {
    const v = (usernameInput.value || '').trim();
    if (!v)            { markInvalid(usernameInput, errUsername, 'Username is required.'); return false; }
    if (v.length < 3)  { markInvalid(usernameInput, errUsername, 'At least 3 characters required.'); return false; }
    if (v.length > 30) { markInvalid(usernameInput, errUsername, 'Cannot exceed 30 characters.'); return false; }
    if (!/^[a-zA-Z0-9_]+$/.test(v)) {
      markInvalid(usernameInput, errUsername, 'Letters, numbers, and underscores only — no spaces.');
      return false;
    }
    markValid(usernameInput, errUsername);
    return true;
  }

  function validateEmail() {
    const v = (emailInput.value || '').trim();
    if (!v) { markInvalid(emailInput, errEmail, 'Email is required.'); return false; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      markInvalid(emailInput, errEmail, 'Enter a valid email address.');
      return false;
    }
    markValid(emailInput, errEmail);
    return true;
  }

  function validateName(input, errEl, label) {
    const raw = input.value || '';
    // Reject whitespace-only input
    if (raw.trim() === '' && raw.length > 0) {
      markInvalid(input, errEl, label + ' cannot be only spaces.');
      return false;
    }
    // Catch leading/trailing spaces
    if (raw !== raw.trim()) {
      markInvalid(input, errEl, label + ' must not start or end with a space.');
      return false;
    }
    const v = raw.trim();
    if (!v) { markValid(input, errEl); return true; } // optional — truly empty is fine
    if (v.length < 2)  { markInvalid(input, errEl, label + ' must be at least 2 characters.'); return false; }
    if (v.length > 50) { markInvalid(input, errEl, label + ' cannot exceed 50 characters.'); return false; }
    if (!/^[a-zA-Z\s\-]+$/.test(v)) {
      markInvalid(input, errEl, 'Letters, spaces, and hyphens only.');
      return false;
    }
    if (!/[aeiouAEIOU]/.test(v)) {
      markInvalid(input, errEl, 'Please enter a real ' + label.toLowerCase() + '.');
      return false;
    }
    if (/(.)\1{3,}/.test(v)) {
      markInvalid(input, errEl, 'Please enter a real ' + label.toLowerCase() + '.');
      return false;
    }
    markValid(input, errEl);
    return true;
  }

  function validateFirstName() { return validateName(firstNameInput, errFirstName, 'First name'); }
  function validateLastName()  { return validateName(lastNameInput,  errLastName,  'Last name');  }

  /* ── password strength bar ────────────────────────────────────────── */
  const bar   = get('strength-bar');
  const fill  = get('strength-fill');
  const label = get('strength-label');

  function passwordStrength(pw) {
    let s = 0;
    if (pw.length >= 8)           s++;
    if (pw.length >= 12)          s++;
    if (/[A-Z]/.test(pw))         s++;
    if (/[0-9]/.test(pw))         s++;
    if (/[^a-zA-Z0-9]/.test(pw))  s++;
    return s; // 0–5
  }

  function updateStrengthBar(pw) {
    if (!pw) { bar.style.display = 'none'; label.textContent = ''; return; }
    bar.style.display = 'block';
    const s = passwordStrength(pw);
    fill.style.width = (s / 5 * 100) + '%';
    if (s <= 1) {
      fill.style.background = '#dc2626'; label.textContent = 'Weak';   label.style.color = '#dc2626';
    } else if (s <= 3) {
      fill.style.background = '#f59e0b'; label.textContent = 'Fair';   label.style.color = '#b45309';
    } else {
      fill.style.background = '#16a34a'; label.textContent = 'Strong'; label.style.color = '#16a34a';
    }
  }

  function validatePw1() {
    const v = pw1Input.value || '';
    if (!v)           { markInvalid(pw1Input, errPw1, 'Password is required.'); return false; }
    if (v.length < 8) { markInvalid(pw1Input, errPw1, 'Password must be at least 8 characters.'); return false; }
    if (/^\d+$/.test(v)) { markInvalid(pw1Input, errPw1, 'Password cannot be entirely numeric.'); return false; }
    markValid(pw1Input, errPw1);
    return true;
  }

  function validatePw2() {
    const v = pw2Input.value || '';
    if (!v)                   { markInvalid(pw2Input, errPw2, 'Please confirm your password.'); return false; }
    if (v !== pw1Input.value) { markInvalid(pw2Input, errPw2, 'Passwords do not match.'); return false; }
    markValid(pw2Input, errPw2);
    return true;
  }

  /* ── live listeners ───────────────────────────────────────────────── */
  usernameInput .addEventListener('blur',  validateUsername);
  usernameInput .addEventListener('input', validateUsername);
  emailInput    .addEventListener('blur',  validateEmail);
  emailInput    .addEventListener('input', validateEmail);
  firstNameInput.addEventListener('blur',  validateFirstName);
  firstNameInput.addEventListener('input', validateFirstName);
  lastNameInput .addEventListener('blur',  validateLastName);
  lastNameInput .addEventListener('input', validateLastName);

  pw1Input.addEventListener('input', function () {
    updateStrengthBar(this.value);
    validatePw1();
    if (pw2Input.value) validatePw2(); // re-check confirm if already typed
  });
  pw1Input.addEventListener('blur', validatePw1);
  pw2Input.addEventListener('blur',  validatePw2);
  pw2Input.addEventListener('input', validatePw2);

  /* ── submit guard ─────────────────────────────────────────────────── */
  get('register-form').addEventListener('submit', function (e) {
    const ok = [
      validateUsername(),
      validateEmail(),
      validateFirstName(),
      validateLastName(),
      validatePw1(),
      validatePw2(),
    ].every(Boolean);

    if (!ok) {
      e.preventDefault();
      // scroll to the first invalid field
      const first = document.querySelector('.input-invalid');
      if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
})();