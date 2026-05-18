// Browse page — AJAX filter update
async function performAjaxUpdate(url) {
  try {
    const response = await fetch(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    document.getElementById('book-grid-container').innerHTML =
      doc.getElementById('book-grid-container').innerHTML;
    document.getElementById('filter-sidebar-container').innerHTML =
      doc.getElementById('filter-sidebar-container').innerHTML;

    window.history.pushState({}, '', url);
    attachAjaxListeners();
  } catch (err) {
    window.location.href = url;
  }
}

function attachAjaxListeners() {
  document.querySelectorAll('.ajax-link').forEach(link => {
    link.onclick = (e) => {
      e.preventDefault();
      performAjaxUpdate(link.href);
    };
  });
}

document.addEventListener('DOMContentLoaded', attachAjaxListeners);