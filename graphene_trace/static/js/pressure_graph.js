(function(){
  var chart;
  function initChart(){
    var ctx = document.getElementById('pressureChart').getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Pressure (mmHg)',
          data: [],
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239,68,68,0.08)',
          fill: true,
          tension: 0.2,
        }]
      },
      options: {
        animation: false,
        responsive: true,
        scales: {
          x: { display: true, title: { display: false } },
          y: { beginAtZero: true }
        }
      }
    });
  }

  function updateChart(data){
    if(!chart) initChart();
    var labels = data.map(function(d){ return new Date(d.timestamp).toLocaleTimeString(); });
    var values = data.map(function(d){ return d.value; });
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
  }

  function fetchAndUpdate(){
    if(!window.LIVE_GRAPH_URL) return;
    fetch(window.LIVE_GRAPH_URL, { credentials: 'same-origin' })
      .then(function(r){ if(!r.ok) throw new Error('Network'); return r.json(); })
      .then(function(j){ if(j.data) updateChart(j.data); })
      .catch(function(e){ console.warn('graph fetch failed', e); });
  }

  window.addEventListener('load', function(){
    // lazy init chart element exists
    if(document.getElementById('pressureChart')){
      initChart();
      fetchAndUpdate();
      setInterval(fetchAndUpdate, 2000);
    }
  });
})();
