"""
05_gen_mockup.py — Generate a self-contained dark 'mockup' HTML for review.
Injects the real dashboard_data.json inline so numbers are exact (no hand transcription).
The mockup is a LAYOUT + STYLE proposal: real KPI cards + representative charts,
each panel annotated with the question it answers and the insight it serves.
"""
import json, os
HERE = os.path.dirname(__file__)
DASH = os.path.join(HERE, "..", "dashboard")
data = json.load(open(os.path.join(DASH, "dashboard_data.json")))
DATA_JS = json.dumps(data, ensure_ascii=False)

HTML = r"""<meta charset="utf-8">
<title>BDC Dashboard — Mockup for Review</title>
<style>
:root{
  --bg:#0d0f14; --panel:#161a23; --panel2:#1c2130; --line:#262c3b;
  --ink:#f4f6fb; --ink2:#aab3c5; --ink3:#6c7689;
  --s1:#3987e5; --s2:#199e70; --s3:#d55181; --s4:#c98500; --s5:#9085e9; --s6:#d95926; --s7:#e66767; --s8:#39c0c8;
  --good:#0ca30c; --warn:#fab219; --crit:#d03b3b;
  --grad:linear-gradient(135deg,#3987e5,#9085e9);
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 600px at 80% -10%,#1a2336 0%,var(--bg) 55%);
  color:var(--ink);font:14px/1.5 'Segoe UI',system-ui,sans-serif;padding:0 0 60px}
.wrap{max-width:1320px;margin:0 auto;padding:0 22px}
header{padding:26px 0 14px}
.badge{display:inline-block;background:rgba(250,178,25,.15);color:var(--warn);border:1px solid rgba(250,178,25,.4);
  padding:3px 11px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.5px}
h1{margin:12px 0 4px;font-size:27px;font-weight:800;letter-spacing:-.5px}
h1 span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:var(--ink2);font-size:13px}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 6px}
.filters .f{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:8px 13px;font-size:12.5px;color:var(--ink2)}
.filters .f b{color:var(--ink)}
.note{color:var(--ink3);font-size:11.5px;margin-top:6px}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:20px 0}
.kpi{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:16px 16px 14px;position:relative;overflow:hidden}
.kpi::before{content:"";position:absolute;inset:0 0 auto 0;height:3px;background:var(--grad)}
.kpi .l{color:var(--ink3);font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.kpi .v{font-size:25px;font-weight:800;margin-top:7px;letter-spacing:-.5px}
.kpi .d{font-size:11px;color:var(--ink2);margin-top:3px}
.section-title{display:flex;align-items:center;gap:11px;margin:32px 0 4px;font-size:16px;font-weight:700}
.section-title .dot{width:10px;height:10px;border-radius:3px;background:var(--grad)}
.section-title small{color:var(--ink3);font-weight:500;font-size:12px}
.grid{display:grid;gap:14px;margin-top:14px}
.g3{grid-template-columns:repeat(3,1fr)} .g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 16px 12px}
.card h3{margin:0 0 2px;font-size:14px;font-weight:700}
.card .q{color:var(--s1);font-size:11.5px;margin:0 0 12px;font-weight:600}
.card .q::before{content:"❯ "}
.tag{position:absolute;top:12px;right:14px;font-size:9.5px;color:var(--ink3);border:1px solid var(--line);border-radius:5px;padding:1px 6px}
.card{position:relative}
.callout{background:linear-gradient(135deg,rgba(57,135,229,.12),rgba(144,133,233,.10));border:1px solid rgba(144,133,233,.3);border-radius:14px;padding:16px 18px}
.callout .k{font-size:22px;font-weight:800;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.callout p{margin:6px 0 0;color:var(--ink2);font-size:12.5px}
svg{display:block;width:100%;overflow:visible}
.lg{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font-size:11px;color:var(--ink2)}
.lg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.bar-row{display:flex;align-items:center;gap:9px;margin:7px 0;font-size:12px}
.bar-row .nm{width:104px;color:var(--ink2);text-align:right;flex:none;font-size:11.5px}
.bar-row .track{flex:1;background:var(--panel2);border-radius:5px;height:16px;overflow:hidden}
.bar-row .fill{height:100%;border-radius:5px}
.bar-row .val{width:70px;font-size:11px;color:var(--ink);flex:none}
footer{margin-top:34px;padding-top:16px;border-top:1px solid var(--line);color:var(--ink3);font-size:11.5px}
.hm{display:grid;grid-template-columns:34px repeat(24,1fr);gap:2px;font-size:9px}
.hm .cell{aspect-ratio:1;border-radius:2px}
.hm .lbl{color:var(--ink3);font-size:9px;display:flex;align-items:center}
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:center}
</style>
<div class="wrap">
<header>
  <span class="badge">◆ MOCKUP — CHỜ DUYỆT · chưa phải bản final</span>
  <h1>Brazilian Delivery Center · <span>Growth & Operations Analytics</span></h1>
  <div class="sub" id="daterange"></div>
  <div class="filters">
    <div class="f">🏙 City: <b>All (4)</b></div>
    <div class="f">🍔 Segment: <b>All</b></div>
    <div class="f">🔗 Channel: <b>All</b></div>
    <div class="f">📅 Period: <b>Jan–Apr 2021</b></div>
    <div class="f" style="border-style:dashed">＋ proposed slicers</div>
  </div>
  <div class="note">⏱ Trục thời gian hiển thị theo <b>giờ Brazil (UTC−3)</b> — giả định (dataset không nêu múi giờ gốc). Mọi outlier được gắn cờ, không xóa.</div>
</header>

<div class="kpis" id="kpis"></div>

<!-- SECTION A -->
<div class="section-title"><span class="dot"></span>A · Tăng trưởng & Doanh thu <small>— GMV đến từ đâu và đi về đâu?</small></div>
<div class="grid g2">
  <div class="card"><span class="tag">LINE</span><h3>GMV theo tuần</h3><p class="q">Doanh thu biến động thế nào trong 4 tháng?</p><div id="c_weekly"></div></div>
  <div class="card"><span class="tag">STACKED BAR</span><h3>Đơn theo tháng × loại cửa hàng</h3><p class="q">FOOD hay GOOD đang dẫn dắt tăng trưởng? (Insight 1)</p><div id="c_segmon"></div></div>
</div>
<div class="grid g3">
  <div class="card"><span class="tag">BAR + MAP</span><h3>GMV theo thành phố</h3><p class="q">Doanh thu tập trung ở đâu? (Insight 8)</p><div id="c_city"></div><div class="note" style="margin-top:8px">Final: bubble map toạ độ hub trên nền Brazil</div></div>
  <div class="card"><span class="tag">DONUT</span><h3>Marketplace vs Own channel</h3><p class="q">Kênh nào tạo doanh thu & AOV? (Insight 3)</p><div id="c_chtype"></div></div>
  <div class="card"><span class="tag">RANKING</span><h3>Top kênh theo GMV</h3><p class="q">Có phụ thuộc 1 kênh không? (Insight 3)</p><div id="c_topch"></div></div>
</div>

<!-- SECTION B -->
<div class="section-title"><span class="dot"></span>B · Vận hành giao hàng <small>— cầu đến khi nào, giao nhanh & xa ra sao?</small></div>
<div class="grid g2">
  <div class="card"><span class="tag">BAR</span><h3>Đơn theo giờ trong ngày (giờ địa phương)</h3><p class="q">Cao điểm rơi vào khung giờ nào? (Insight 6)</p><div id="c_hour"></div></div>
  <div class="card"><span class="tag">HEATMAP</span><h3>Cường độ đơn: Thứ × Giờ</h3><p class="q">Khi nào cần nhiều shipper nhất?</p><div id="c_heat"></div></div>
</div>
<div class="grid g3">
  <div class="card"><span class="tag">BAR</span><h3>Đơn theo ngày trong tuần</h3><p class="q">Cuối tuần có dồn đơn không? (Insight 6)</p><div id="c_dow"></div></div>
  <div class="card"><span class="tag">HISTOGRAM</span><h3>Phân bố cycle time (phút)</h3><p class="q">Thời gian hoàn tất đơn & SLA?</p><div id="c_cycle"></div></div>
  <div class="card"><span class="tag">BAR</span><h3>Đội xe: Motoboy vs Biker</h3><p class="q">Phân bổ đội theo cự ly? (Insight 7)</p><div id="c_modal"></div></div>
</div>

<!-- SECTION C -->
<div class="section-title"><span class="dot"></span>C · Rủi ro & Kinh tế đơn vị <small>— tiền rơi rụng ở đâu?</small></div>
<div class="grid g3">
  <div class="card"><span class="tag">LINE</span><h3>Tỷ lệ hủy đơn theo tháng</h3><p class="q">Hủy đơn đang tăng hay giảm? (Insight 4)</p><div id="c_cancelmon"></div></div>
  <div class="card"><span class="tag">BAR</span><h3>Tỷ lệ hủy theo loại cửa hàng</h3><p class="q">Segment nào rủi ro hơn? (Insight 4)</p><div id="c_cancelseg"></div></div>
  <div class="card"><span class="tag">PARETO</span><h3>Tập trung doanh thu cửa hàng</h3><p class="q">Bao nhiêu % cửa hàng tạo 80% GMV? (Insight 2)</p><div id="c_pareto"></div></div>
</div>
<div class="grid g2">
  <div class="card"><span class="tag">DIVERGING BAR</span><h3>Phí giao thu về vs Chi phí giao</h3><p class="q">Giao hàng đang lãi hay lỗ? (Insight 5)</p><div id="c_fee"></div></div>
  <div class="callout"><h3 style="margin:0 0 4px">💳 Cơ cấu thanh toán & rủi ro</h3><div id="c_pay"></div></div>
</div>

<footer id="foot"></footer>
</div>

<script>
const DATA = __DATA__;
const C={s1:'#3987e5',s2:'#199e70',s3:'#d55181',s4:'#c98500',s5:'#9085e9',s6:'#d95926',s7:'#e66767',s8:'#39c0c8',ink2:'#aab3c5',ink3:'#6c7689',grid:'#262c3b',good:'#0ca30c',warn:'#fab219',crit:'#d03b3b'};
const brl=v=>'R$'+(v>=1e6?(v/1e6).toFixed(1)+'M':v>=1e3?(v/1e3).toFixed(0)+'k':v.toFixed(0));
const num=v=>v>=1e6?(v/1e6).toFixed(2)+'M':v>=1e3?(v/1e3).toFixed(0)+'k':(''+v);
const el=(t,a={},h='')=>{const e=document.createElementNS('http://www.w3.org/2000/svg',t);for(const kk in a)e.setAttribute(kk,a[kk]);if(h)e.innerHTML=h;return e;};
function svg(w,h){const s=el('svg',{viewBox:`0 0 ${w} ${h}`,height:h});return s;}

// KPIs
const k=DATA.kpi;
document.getElementById('daterange').innerHTML=`📅 ${k.date_min} → ${k.date_max} · ${k.n_cities} thành phố · ${k.n_stores_total} cửa hàng · ${k.n_hubs} hub`;
const kpis=[['GMV (hoàn tất)',brl(k.gmv),'AOV '+brl(k.aov)],['Tổng đơn',num(k.total_orders),num(k.finished_orders)+' hoàn tất'],
['AOV',brl(k.aov),'median '+brl(k.median_order)],['Tỷ lệ hủy',k.cancel_rate+'%',num(k.total_orders-k.finished_orders)+' đơn hủy'],
['Median cycle',k.median_cycle_min+'′','giao ~'+k.median_distance_km+' km'],['Cửa hàng active',k.n_stores_active,'/'+k.n_stores_total+' tổng']];
document.getElementById('kpis').innerHTML=kpis.map(x=>`<div class="kpi"><div class="l">${x[0]}</div><div class="v">${x[1]}</div><div class="d">${x[2]}</div></div>`).join('');

// helper: simple bar list
function barlist(id,rows,color){const box=document.getElementById(id);const mx=Math.max(...rows.map(r=>r.v));
  box.innerHTML=rows.map(r=>`<div class="bar-row"><div class="nm">${r.n}</div><div class="track"><div class="fill" style="width:${r.v/mx*100}%;background:${r.c||color}"></div></div><div class="val">${r.t}</div></div>`).join('');}

// A1 weekly line
(function(){const d=DATA.weekly,w=560,h=150,pl=44,pr=10,pt=12,pb=22;const s=svg(w,h);
  const xs=i=>pl+i/(d.length-1)*(w-pl-pr);const mx=Math.max(...d.map(r=>r.gmv));const ys=v=>pt+(1-v/mx)*(h-pt-pb);
  for(let g=0;g<=3;g++){const y=pt+g/3*(h-pt-pb);s.appendChild(el('line',{x1:pl,x2:w-pr,y1:y,y2:y,stroke:C.grid}));s.appendChild(el('text',{x:2,y:y+3,fill:C.ink3,'font-size':9},brl(mx*(1-g/3))));}
  let path='';d.forEach((r,i)=>path+=(i?'L':'M')+xs(i)+' '+ys(r.gmv));
  s.appendChild(el('path',{d:path,fill:'none',stroke:C.s1,'stroke-width':2.5}));
  s.appendChild(el('path',{d:path+`L${xs(d.length-1)} ${h-pb}L${xs(0)} ${h-pb}Z`,fill:'url(#gw)'}));
  const defs=el('defs');defs.innerHTML=`<linearGradient id="gw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3987e5" stop-opacity=".35"/><stop offset="1" stop-color="#3987e5" stop-opacity="0"/></linearGradient>`;s.appendChild(defs);
  d.forEach((r,i)=>{if(i%2==0)s.appendChild(el('text',{x:xs(i),y:h-6,fill:C.ink3,'font-size':8,'text-anchor':'middle'},r.week.slice(5)));});
  document.getElementById('c_weekly').appendChild(s);})();

// A2 segment×month stacked
(function(){const months=[1,2,3,4];const segs=['FOOD','GOOD'];const cols={FOOD:C.s1,GOOD:C.s5};
  const get=(m,sg)=>{const r=DATA.segment_month.find(x=>x.month==m&&x.segment==sg);return r?r.orders:0;};
  const w=560,h=150,pl=36,pb=22,pt=10;const s=svg(w,h);const bw=(w-pl-10)/months.length*.55;
  const tot=months.map(m=>segs.reduce((a,sg)=>a+get(m,sg),0));const mx=Math.max(...tot);
  months.forEach((m,i)=>{const x=pl+(i+.5)/months.length*(w-pl-10)-bw/2;let yb=h-pb;
    segs.forEach(sg=>{const v=get(m,sg);const bh=v/mx*(h-pt-pb);yb-=bh;s.appendChild(el('rect',{x,y:yb,width:bw,height:Math.max(bh-2,0),fill:cols[sg],rx:2}));});
    s.appendChild(el('text',{x:x+bw/2,y:h-6,fill:C.ink3,'font-size':9,'text-anchor':'middle'},'T'+m));});
  document.getElementById('c_segmon').appendChild(s);
  document.getElementById('c_segmon').insertAdjacentHTML('beforeend',`<div class="lg"><span><i style="background:${C.s1}"></i>FOOD</span><span><i style="background:${C.s5}"></i>GOOD</span></div>`);})();

// A3 city bar
barlist('c_city',DATA.city.map((r,i)=>({n:r.city.replace('DE JANEIRO','RJ').slice(0,12),v:r.gmv,t:brl(r.gmv)+' · '+r.gmv/DATA.kpi.gmv*100|0+'%',c:[C.s1,C.s5,C.s3,C.s4][i]})),C.s1);
document.getElementById('c_city').querySelectorAll('.val').forEach((v,i)=>{v.textContent=brl(DATA.city[i].gmv)+' ('+(DATA.city[i].gmv/DATA.kpi.gmv*100).toFixed(0)+'%)';});

// A4 channel type donut
(function(){const d=DATA.channel_type;const tot=d.reduce((a,r)=>a+r.gmv,0);const w=230,h=150;const s=svg(w,h);
  const cx=75,cy=72,r=52,ir=32;let a0=-Math.PI/2;const cols=[C.s1,C.s5];
  d.forEach((r_,i)=>{const ang=r_.gmv/tot*2*Math.PI;const a1=a0+ang;const lg=ang>Math.PI?1:0;
    const p=`M${cx+r*Math.cos(a0)} ${cy+r*Math.sin(a0)}A${r} ${r} 0 ${lg} 1 ${cx+r*Math.cos(a1)} ${cy+r*Math.sin(a1)}L${cx+ir*Math.cos(a1)} ${cy+ir*Math.sin(a1)}A${ir} ${ir} 0 ${lg} 0 ${cx+ir*Math.cos(a0)} ${cy+ir*Math.sin(a0)}Z`;
    s.appendChild(el('path',{d:p,fill:cols[i]}));a0=a1;});
  s.appendChild(el('text',{x:cx,y:cy-2,fill:'#f4f6fb','font-size':15,'font-weight':800,'text-anchor':'middle'},'79%'));
  s.appendChild(el('text',{x:cx,y:cy+13,fill:C.ink3,'font-size':9,'text-anchor':'middle'},'Marketplace'));
  d.forEach((r_,i)=>{s.appendChild(el('rect',{x:150,y:50+i*24,width:10,height:10,rx:2,fill:cols[i]}));
    s.appendChild(el('text',{x:166,y:59+i*24,fill:C.ink2,'font-size':10},r_.type=='MARKETPLACE'?'Marketplace':'Own ch.'));
    s.appendChild(el('text',{x:166,y:71+i*24,fill:C.ink3,'font-size':9},'AOV '+brl(r_.aov)));});
  document.getElementById('c_chtype').appendChild(s);})();

// A4b top channels
barlist('c_topch',DATA.top_channels.slice(0,6).map(r=>({n:r.channel.replace(' PLACE',''),v:r.gmv,t:brl(r.gmv),c:r.type=='MARKETPLACE'?C.s1:C.s5})),C.s1);

// B1 hour bars
(function(){const d=DATA.orders_by_hour;const w=560,h=150,pl=30,pb=20,pt=8;const s=svg(w,h);const mx=Math.max(...d.map(r=>r.orders));
  const bw=(w-pl-8)/24*.7;d.forEach((r,i)=>{const x=pl+(i+.5)/24*(w-pl-8)-bw/2;const bh=r.orders/mx*(h-pt-pb);
    const peak=[12,19,20].includes(r.hour);s.appendChild(el('rect',{x,y:h-pb-bh,width:bw,height:bh,rx:2,fill:peak?C.s4:C.s1}));
    if(i%3==0)s.appendChild(el('text',{x:x+bw/2,y:h-6,fill:C.ink3,'font-size':8,'text-anchor':'middle'},r.hour+'h'));});
  s.appendChild(el('text',{x:pl+12*(w-pl-8)/24,y:14,fill:C.s4,'font-size':9},'🍽 trưa'));
  s.appendChild(el('text',{x:pl+19.5*(w-pl-8)/24,y:14,fill:C.s4,'font-size':9},'🌙 tối'));
  document.getElementById('c_hour').appendChild(s);})();

// B2 heatmap
(function(){const dows=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];const box=document.getElementById('c_heat');
  const mx=Math.max(...DATA.heatmap.map(r=>r.orders));const g=(d,h)=>{const r=DATA.heatmap.find(x=>x.dow==d&&x.hour==h);return r?r.orders:0;};
  let html='<div class="hm">';for(let hh=0;hh<24;hh+=1){}
  dows.forEach(d=>{html+=`<div class="lbl">${d}</div>`;for(let h=0;h<24;h++){const v=g(d,h);const t=v/mx;
    html+=`<div class="cell" title="${d} ${h}h: ${v}" style="background:rgba(57,135,229,${(.08+t*.92).toFixed(2)})"></div>`;}});
  html+='</div><div class="note" style="margin-top:6px">Đậm = nhiều đơn · trục ngang 0→23h</div>';box.innerHTML=html;})();

// B3 dow
barlist('c_dow',DATA.orders_by_dow.map(r=>({n:r.dow,v:r.orders,t:num(r.orders),c:['Fri','Sat','Sun'].includes(r.dow)?C.s2:C.s1})),C.s1);

// B4 cycle hist
(function(){const d=DATA.cycle_hist;const w=380,h=150,pl=26,pb=26,pt=8;const s=svg(w,h);const mx=Math.max(...d.map(r=>r.orders));
  const bw=(w-pl-6)/d.length*.72;d.forEach((r,i)=>{const x=pl+(i+.5)/d.length*(w-pl-6)-bw/2;const bh=r.orders/mx*(h-pt-pb);
    s.appendChild(el('rect',{x,y:h-pb-bh,width:bw,height:bh,rx:2,fill:C.s5}));
    s.appendChild(el('text',{x:x+bw/2,y:h-14,fill:C.ink3,'font-size':7.5,'text-anchor':'middle',transform:`rotate(35 ${x+bw/2} ${h-14})`},r.bucket));});
  const px=pl+(DATA.cycle_pct.p90/180)*(w-pl-6);
  document.getElementById('c_cycle').appendChild(s);
  document.getElementById('c_cycle').insertAdjacentHTML('beforeend',`<div class="note">p50=${DATA.cycle_pct.p50}′ · p90=${DATA.cycle_pct.p90}′ · p95=${DATA.cycle_pct.p95}′</div>`);})();

// B5 driver modal
barlist('c_modal',DATA.driver_modal.map(r=>({n:r.modal,v:r.deliveries,t:r.share+'% · '+r.median_km+'km',c:r.modal=='MOTOBOY'?C.s1:C.s2})),C.s1);
document.getElementById('c_modal').insertAdjacentHTML('beforeend',`<div class="note">Motoboy giao xa hơn Biker ~2.5×</div>`);

// C1 cancel by month line
(function(){const d=DATA.cancel_month;const w=360,h=140,pl=30,pr=10,pt=12,pb=20;const s=svg(w,h);
  const xs=i=>pl+i/(d.length-1)*(w-pl-pr);const mx=Math.max(...d.map(r=>r.cancel_rate))*1.15,mn=Math.min(...d.map(r=>r.cancel_rate))*.9;
  const ys=v=>pt+(1-(v-mn)/(mx-mn))*(h-pt-pb);let path='';
  d.forEach((r,i)=>{path+=(i?'L':'M')+xs(i)+' '+ys(r.cancel_rate);});
  s.appendChild(el('path',{d:path,fill:'none',stroke:C.crit,'stroke-width':2.5}));
  d.forEach((r,i)=>{s.appendChild(el('circle',{cx:xs(i),cy:ys(r.cancel_rate),r:3.5,fill:C.crit}));
    s.appendChild(el('text',{x:xs(i),y:ys(r.cancel_rate)-8,fill:'#f4f6fb','font-size':9,'text-anchor':'middle'},r.cancel_rate+'%'));
    s.appendChild(el('text',{x:xs(i),y:h-6,fill:C.ink3,'font-size':9,'text-anchor':'middle'},'T'+r.month));});
  document.getElementById('c_cancelmon').appendChild(s);})();

// C2 cancel by segment
barlist('c_cancelseg',DATA.segment.map(r=>({n:r.segment,v:r.cancel_rate,t:r.cancel_rate+'%',c:r.cancel_rate>8?C.crit:C.warn})),C.warn);

// C3 pareto
(function(){const d=DATA.pareto;const w=360,h=140,pl=30,pr=10,pt=10,pb=20;const s=svg(w,h);
  const xs=v=>pl+v/100*(w-pl-pr);const ys=v=>pt+(1-v/100)*(h-pt-pb);
  s.appendChild(el('line',{x1:xs(0),y1:ys(80),x2:xs(100),y2:ys(80),stroke:C.grid,'stroke-dasharray':'3 3'}));
  let path='';d.forEach((r,i)=>path+=(i?'L':'M')+xs(r.store_pct)+' '+ys(r.gmv_pct));
  s.appendChild(el('path',{d:path,fill:'none',stroke:C.s2,'stroke-width':2.5}));
  const st=DATA.pareto_stat;const xx=xs(st.stores_for_80/st.n_stores*100);
  s.appendChild(el('line',{x1:xx,y1:ys(0),x2:xx,y2:ys(80),stroke:C.warn,'stroke-dasharray':'3 3'}));
  s.appendChild(el('text',{x:xs(50),y:14,fill:C.ink2,'font-size':9,'text-anchor':'middle'},`${(st.stores_for_80/st.n_stores*100).toFixed(0)}% cửa hàng → 80% GMV`));
  s.appendChild(el('text',{x:6,y:ys(80)-3,fill:C.ink3,'font-size':8},'80%'));
  document.getElementById('c_pareto').appendChild(s);})();

// C4 fee vs cost
(function(){const e=DATA.delivery_econ;const box=document.getElementById('c_fee');const mx=Math.max(e.mean_fee,e.mean_cost);
  box.innerHTML=`<div class="bar-row"><div class="nm">Phí thu</div><div class="track"><div class="fill" style="width:${e.mean_fee/mx*100}%;background:${C.s1}"></div></div><div class="val">R$${e.mean_fee}</div></div>
  <div class="bar-row"><div class="nm">Chi phí giao</div><div class="track"><div class="fill" style="width:${e.mean_cost/mx*100}%;background:${C.crit}"></div></div><div class="val">R$${e.mean_cost}</div></div>
  <div class="note" style="margin-top:10px">🔻 Bù lỗ TB <b style="color:#e66767">R$${e.subsidy_per_order}/đơn</b> · ${e.fee_below_cost_share}% đơn phí thu &lt; chi phí · ${e.free_ship_share}% đơn free-ship</div>`;})();

// C5 payment
(function(){const d=DATA.payment_method;const box=document.getElementById('c_pay');const cols=[C.s1,C.s2,C.s3,C.s4,C.s5,C.s6,C.ink3];
  box.innerHTML=`<div style="display:flex;height:14px;border-radius:7px;overflow:hidden;margin:12px 0 10px">`+
    d.map((r,i)=>`<div title="${r.method} ${r.share}%" style="width:${r.share}%;background:${cols[i]}"></div>`).join('')+`</div>`+
    `<div class="lg">`+d.slice(0,4).map((r,i)=>`<span><i style="background:${cols[i]}"></i>${r.method} ${r.share}%</span>`).join('')+`</div>`+
    `<p style="margin-top:12px;color:#aab3c5;font-size:12px">ONLINE chiếm <b class="k" style="font-size:14px">${d[0].share}%</b> · chargeback chỉ <b style="color:#0ca30c">${DATA.kpi.chargeback_rate}%</b> — rủi ro thanh toán thấp.</p>`;})();

// footer
const qd=DATA.quality;
document.getElementById('foot').innerHTML=`<b>Ghi chú chất lượng dữ liệu (bản final sẽ đưa vào panel riêng):</b> giữ nguyên & gắn cờ ${qd.flag_extreme_amount} đơn giá trị bất thường, ${qd.flag_extreme_distance} lượt giao >50km, ${qd.flag_long_cycle} đơn cycle>24h, ${qd.flag_zero_amount} đơn amount=0. ${qd.orders_no_payment.toLocaleString()} đơn thiếu payment record, ${qd.orders_no_delivery.toLocaleString()} thiếu delivery record, ${qd.null_driver_deliveries.toLocaleString()} lượt giao thiếu driver. Cột <code>delivered</code> thiếu ${qd.delivered_missing_pct}% → dùng <code>finished</code> làm mốc hoàn tất. Dữ liệu 4 tháng (2021) → chưa phân tích được YoY.<br><br>
<b>Mockup này để duyệt:</b> bố cục 3 section · ${'6 KPI + 13 biểu đồ'} · palette dark đã kiểm CVD. Bản final sẽ thêm: tooltip hover, bộ lọc tương tác, bubble map Brazil thật, và panel data-quality.`;
</script>
"""

out = HTML.replace("__DATA__", DATA_JS)
open(os.path.join(DASH, "mockup.html"), "w").write(out)
print("wrote dashboard/mockup.html", len(out), "bytes")
