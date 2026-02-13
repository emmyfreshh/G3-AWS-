(function(){
  function $(s){return document.querySelector(s)}
  function $all(s){return document.querySelectorAll(s)}

  var heatmapInstance;
  function initHeatmap(){
    var container = document.getElementById('heatmapContainer');
    var config = {
      container: container,
      maxOpacity: 0.9,
      radius: Math.max(8, Math.floor(container.offsetWidth/40)),
      blur: 0.85,
      backgroundColor: 'rgba(250,250,250,0)'
    };
    heatmapInstance = h337.create(config);
  }

  function resizeHeatmap(){
    if(!heatmapInstance) return;
    var container = document.getElementById('heatmapContainer');
    heatmapInstance._renderer.setDimensions(container.offsetWidth, container.offsetHeight);
  }

  function gridToPoints(cells){
    // cells: [{r,c,value},...]
    if(cells.length===0) return [];
    var maxR=0,maxC=0;
    cells.forEach(function(p){ if(p.r!=null){ maxR=Math.max(maxR,p.r); maxC=Math.max(maxC,p.c);} });
    var rows = maxR+1 || 1, cols = maxC+1 || 1;
    var container = document.getElementById('heatmapContainer');
    var w = container.offsetWidth, h = container.offsetHeight;
    var cellW = w/cols, cellH = h/rows;
    var points = [];
    cells.forEach(function(p){
      if(p.r==null || p.c==null) return;
      var x = Math.floor((p.c + 0.5) * cellW);
      var y = Math.floor((p.r + 0.5) * cellH);
      points.push({ x: x, y: y, value: Number(p.value) || 0, r: p.r, c: p.c });
    });
    return points;
  }

  function updateHeatmap(data){
    if(!heatmapInstance) initHeatmap();
    var points = gridToPoints(data.cells || []);
    var maxVal = points.reduce(function(m,p){ return Math.max(m,p.value); }, 0);
    heatmapInstance.setData({ max: Math.max(100, Math.ceil(maxVal)), min: 0, data: points });
    var last = document.getElementById('last-update');
    if(last) last.textContent = new Date(data.timestamp || Date.now()).toLocaleString();

    // show reposition suggestion if present
    if(data.reposition){
      var sug = document.getElementById('reposition-suggestion');
      if(sug){
        sug.textContent = data.reposition.reason + (data.reposition.confidence? (' (confidence: '+Math.round(data.reposition.confidence*100)+'%)') : '');
        if(data.reposition.action && (data.reposition.action === 'roll_left' || data.reposition.action === 'roll_right')){
          sug.className = 'alert alert-warning';
        } else {
          sug.className = 'alert';
        }
      }
    }

    // update recent list
    var recent = document.getElementById('recent-list');
    if(recent){
      recent.innerHTML = '';
      if(points.length===0){
        var msg = document.createElement('div'); msg.className='small-muted'; msg.textContent='No live data'; recent.appendChild(msg);
      } else {
        // show top 20 values descending
        var sorted = points.slice().sort(function(a,b){return b.value - a.value}).slice(0,20);
        sorted.forEach(function(p){
          var div = document.createElement('div');
          div.style.display = 'flex'; div.style.justifyContent='space-between'; div.style.padding='6px 0'; div.style.borderBottom='1px solid #f1f5f9';
          var label = document.createElement('div'); label.textContent = 'r'+p.r+'_c'+p.c;
          var val = document.createElement('div'); val.textContent = Math.round(p.value) + ' mmHg';
          if(p.value>100) val.className = 'text-danger';
          div.appendChild(label); div.appendChild(val);
          recent.appendChild(div);
        });
      }
    }
  }

  function fetchAndUpdate(){
    fetch(window.LIVE_GRID_URL, { credentials: 'same-origin' })
      .then(function(r){ if(!r.ok) throw new Error('Network error'); return r.json(); })
      .then(function(data){ updateHeatmap(data); })
      .catch(function(e){ console.warn('heatmap fetch failed', e); });
  }

  window.addEventListener('load', function(){
    initHeatmap();
    fetchAndUpdate();
    setInterval(fetchAndUpdate, 2000);
    window.addEventListener('resize', function(){ setTimeout(resizeHeatmap,120); });
  });
})();
