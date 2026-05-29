function togglePassword(fieldId, btn) {
    var input = document.getElementById(fieldId);
    var isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    btn.innerHTML = isHidden
        ? '<i data-lucide="eye-off" width="18" height="18"></i>'
        : '<i data-lucide="eye" width="18" height="18"></i>';
    lucide.createIcons();
}