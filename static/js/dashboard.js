(function () {
  var trigger = document.getElementById('pdb-orders-trigger');
  var subnav  = document.getElementById('pdb-orders-subnav');
  if (!trigger || !subnav) return;

  // Auto-expand when a sub-link is the current page
  if (subnav.querySelector('.pdb-nav-active')) {
    trigger.classList.add('is-open');
    trigger.setAttribute('aria-expanded', 'true');
    subnav.classList.add('is-open');
  }

  trigger.addEventListener('click', function () {
    var open = this.classList.toggle('is-open');
    this.setAttribute('aria-expanded', open ? 'true' : 'false');
    subnav.classList.toggle('is-open', open);
  });
})();

(function () {
  var data = window.DASH_CHART_DATA;
  if (!data || !data.labels || data.labels.length === 0) return;

  var canvas = document.getElementById('dashChart');
  if (!canvas) return;

  var ctx = canvas.getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Sales (Rs)',
          data: data.sales,
          backgroundColor: 'rgba(34, 197, 94, 0.75)',
          borderColor: 'rgba(22, 163, 74, 1)',
          borderWidth: 1.5,
          borderRadius: 6,
        },
        {
          label: 'Purchases (Rs)',
          data: data.purchases,
          backgroundColor: 'rgba(99, 102, 241, 0.75)',
          borderColor: 'rgba(79, 70, 229, 1)',
          borderWidth: 1.5,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            font: { size: 12, family: 'Geist, system-ui, sans-serif' },
            usePointStyle: true,
            pointStyleWidth: 10,
          },
        },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return ' Rs ' + ctx.parsed.y.toLocaleString();
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 11 } },
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: {
            font: { size: 11 },
            callback: function (val) { return 'Rs ' + val.toLocaleString(); },
          },
        },
      },
    },
  });
})();
