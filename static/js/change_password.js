(function () {
  // ── Show / hide password toggles ─────────────────────────────────────
  document.querySelectorAll('.pdb-pw-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = document.getElementById(this.dataset.target);
      if (!input) return;
      var isText = input.type === 'text';
      input.type = isText ? 'password' : 'text';
      this.querySelector('.eye-show').style.display = isText ? '' : 'none';
      this.querySelector('.eye-hide').style.display = isText ? 'none' : '';
    });
  });

  // ── Password strength meter ───────────────────────────────────────────
  var newPwInput = document.getElementById('id_new_password1');
  var strengthWrap = document.getElementById('pwStrength');
  var strengthFill = document.getElementById('pwStrengthFill');
  var strengthLabel = document.getElementById('pwStrengthLabel');

  if (newPwInput && strengthWrap) {
    newPwInput.addEventListener('input', function () {
      var val = this.value;
      if (!val) { strengthWrap.style.display = 'none'; return; }
      strengthWrap.style.display = 'flex';

      var score = 0;
      if (val.length >= 8)  score++;
      if (val.length >= 12) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      var levels = [
        { label: 'Very weak', color: '#ef4444', width: '20%' },
        { label: 'Weak',      color: '#f97316', width: '40%' },
        { label: 'Fair',      color: '#eab308', width: '60%' },
        { label: 'Strong',    color: '#22c55e', width: '80%' },
        { label: 'Very strong', color: '#16a34a', width: '100%' },
      ];
      var level = levels[Math.min(score, 4)];
      strengthFill.style.width = level.width;
      strengthFill.style.background = level.color;
      strengthLabel.textContent = level.label;
      strengthLabel.style.color = level.color;
    });
  }
})();
