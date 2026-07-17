"""
05_gen_mockup.py — Generate multi-page Power BI-style HTML mockup for review.
The output is only for layout/UX validation before implementation in Power BI.
"""
import json
import os

HERE = os.path.dirname(__file__)
DASH = os.path.join(HERE, "..", "dashboard")
data = json.load(open(os.path.join(DASH, "dashboard_data.json")))
DATA_JS = json.dumps(data, ensure_ascii=False)

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brazilian Delivery Center — Power BI Mockup (Multi-page)</title>
<style>
:root{
  --bg:#0a0d14; --bg2:#0f1320; --panel:#141a28; --panel2:#1a2132; --line:#273146;
  --ink:#f3f6ff; --ink2:#aab4ca; --ink3:#6e7892;
  --blue:#3d8bff; --teal:#22b8a6; --violet:#8878ff; --amber:#f2a71b; --red:#df4f67; --green:#38c172;
  --grad:linear-gradient(135deg,#3d8bff,#8878ff);
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1400px 800px at 85% -20%,#1b2540 0%,var(--bg) 52%);color:var(--ink);font:14px/1.45 "Segoe UI",Inter,system-ui,sans-serif}
.app{display:grid;grid-template-columns:248px 1fr;min-height:100vh}
.side{background:linear-gradient(180deg,#0b101c,#0b0f18);border-right:1px solid var(--line);padding:16px 14px;position:sticky;top:0;height:100vh}
.brand{padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:rgba(61,139,255,.08)}
.brand h1{margin:0;font-size:14px;line-height:1.2}
.brand small{color:var(--ink2)}
.menu{margin-top:16px;display:grid;gap:8px}
.menu button{all:unset;cursor:pointer;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink2);font-size:12.5px}
.menu button.active{color:var(--ink);border-color:#44689f;background:linear-gradient(135deg,rgba(61,139,255,.25),rgba(136,120,255,.13))}
.menu .sec{margin:8px 0 2px;color:var(--ink3);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
.side .meta{margin-top:12px;font-size:11px;color:var(--ink3);border-top:1px dashed var(--line);padding-top:10px}
.main{padding:14px 18px 26px 18px}
.top{display:flex;align-items:center;gap:10px;justify-content:space-between;background:rgba(20,26,40,.85);border:1px solid var(--line);border-radius:14px;padding:10px 12px;position:sticky;top:10px;z-index:3;backdrop-filter:blur(4px)}
.title h2{margin:0;font-size:20px;letter-spacing:-.3px}
.title .sub{color:var(--ink2);font-size:12px}
.actions{display:flex;align-items:center;gap:8px}
.btn{all:unset;cursor:pointer;padding:7px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);font-size:12px;color:var(--ink2)}
.btn.primary{background:var(--grad);color:#fff;border:none}
.filters-summary{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0 2px}
.chip{padding:4px 8px;border-radius:999px;background:var(--panel);border:1px solid var(--line);font-size:11.5px;color:var(--ink2)}
.page{display:none;margin-top:12px}
.page.active{display:block}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.kpi{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:12px;padding:11px 12px;position:relative;overflow:hidden}
.kpi:before{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--grad)}
.kpi .l{font-size:10px;color:var(--ink3);text-transform:uppercase;letter-spacing:.6px}
.kpi .v{font-size:21px;font-weight:800;margin-top:4px}
.kpi .d{font-size:11px;color:var(--ink2);margin-top:2px}
.grid{display:grid;gap:10px;margin-top:10px}
.g2{grid-template-columns:1.5fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:11px 12px;position:relative;min-height:160px}
.card h3{margin:0 0 2px;font-size:13.5px}
.q{margin:0;color:#8fbaff;font-size:11px}
.tag{position:absolute;right:10px;top:10px;font-size:9px;color:var(--ink3);border:1px solid var(--line);padding:1px 6px;border-radius:5px}
.viz{height:96px;margin-top:10px;border-radius:8px;border:1px dashed #344362;background:linear-gradient(180deg,rgba(61,139,255,.08),rgba(61,139,255,.02))}
.mini-bars{display:grid;gap:6px;margin-top:10px}
.row{display:grid;grid-template-columns:82px 1fr 64px;gap:6px;align-items:center;font-size:11px}
.track{height:12px;background:#1b2335;border-radius:6px;overflow:hidden}.fill{height:100%;background:var(--blue)}
.callout{background:linear-gradient(135deg,rgba(61,139,255,.14),rgba(136,120,255,.12));border:1px solid #455892;border-radius:12px;padding:12px}
.callout b{font-size:20px}
.bullet{padding-left:16px;margin:6px 0 0 0;color:var(--ink2);font-size:12px}
.bullet li{margin:4px 0}
.status{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10.5px;font-weight:700}
.ok{background:rgba(56,193,114,.15);color:#5ee39a}.mid{background:rgba(242,167,27,.15);color:#ffd071}.risk{background:rgba(223,79,103,.15);color:#ff8ea4}
.drawer{position:fixed;right:16px;top:76px;width:290px;background:#101727;border:1px solid var(--line);border-radius:12px;padding:12px;z-index:5;display:none}
.drawer.open{display:block}
.drawer h4{margin:0 0 8px;font-size:13px}
.drawer .s{margin:8px 0}
.drawer label{display:block;font-size:11px;color:var(--ink2);margin-bottom:4px}
.drawer .box{height:28px;border:1px dashed #425371;border-radius:8px;padding:5px 8px;color:var(--ink3);font-size:11.5px;background:#0c1220}
.tooltip{position:fixed;pointer-events:none;background:#0f1523;border:1px solid #3b4a68;border-radius:8px;padding:7px 8px;max-width:220px;font-size:11px;color:var(--ink2);display:none;z-index:6}
.drill{cursor:pointer;border:1px dashed #4f638f;padding:5px 8px;border-radius:8px;font-size:11px;color:#9ab8ff;background:rgba(61,139,255,.1);display:inline-block;margin-top:9px}
.modal{position:fixed;inset:0;background:rgba(5,8,14,.7);display:none;align-items:center;justify-content:center;z-index:8}
.modal.open{display:flex}
.modal .panel{width:min(760px,92vw);background:#0f1524;border:1px solid var(--line);border-radius:12px;padding:14px}
.modal h3{margin:0 0 6px}
.modal p,.modal li{color:var(--ink2);font-size:12px}
.close{float:right}
.legend{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px}
.legend span{font-size:10.5px;color:var(--ink2)}
.dot{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:4px;vertical-align:-1px}
footer{margin-top:10px;padding-top:10px;border-top:1px dashed var(--line);color:var(--ink3);font-size:11px}
@media (max-width:1280px){.kpis{grid-template-columns:repeat(3,1fr)}.g3,.g4{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div class="app">
  <aside class="side">
    <div class="brand">
      <h1>Delivery Center<br>Analytics Showcase</h1>
      <small>Mockup only — waiting approval</small>
    </div>
    <div class="menu">
      <div class="sec">Pages</div>
      <button class="nav active" data-page="p1">1. Executive Overview</button>
      <button class="nav" data-page="p2">2. Order & Revenue</button>
      <button class="nav" data-page="p3">3. Delivery Performance</button>
      <button class="nav" data-page="p4">4. Hub & Geo</button>
      <button class="nav" data-page="p5">5. Store & Partner</button>
      <button class="nav" data-page="p6">6. Insight Lab</button>
    </div>
    <div class="meta">
      Canvas ratio: 16:9 · Dark logistics theme<br>
      Typography: Segoe UI + Inter<br>
      Color: blue/violet focus + semantic status
    </div>
  </aside>

  <main class="main">
    <div class="top">
      <div class="title">
        <h2 id="ttl">Page 1 — Executive Overview</h2>
        <div class="sub" id="sub"></div>
      </div>
      <div class="actions">
        <button class="btn" id="homeBtn">Home</button>
        <button class="btn" id="backBtn">Back</button>
        <button class="btn" id="resetBtn">Reset Filters</button>
        <button class="btn primary" id="toggleFilter">Filters</button>
      </div>
    </div>

    <div class="filters-summary" id="selectedFilters">
      <span class="chip">City: All (4)</span>
      <span class="chip">Segment: All</span>
      <span class="chip">Channel Type: All</span>
      <span class="chip">Period: Jan-Apr 2021</span>
    </div>

    <section class="page active" id="p1">
      <div class="kpis" id="kpis"></div>
      <div class="grid g2">
        <div class="card">
          <span class="tag">LINE</span><h3>GMV Trend by Week</h3><p class="q">Business scale is accelerating or flattening?</p>
          <div class="viz"></div>
          <div class="legend"><span><i class="dot" style="background:var(--blue)"></i>Weekly GMV</span><span><i class="dot" style="background:var(--amber)"></i>Anomaly marker</span></div>
        </div>
        <div class="callout">
          <div>Insight Callout</div>
          <b id="ins1"></b>
          <p style="margin:6px 0 0;color:var(--ink2);font-size:12px">GMV concentration risk is the top strategic issue for executive monitoring.</p>
          <div class="drill" data-drill="Executive drill-through: Channel concentration">Drill-through: Why concentration is high?</div>
        </div>
      </div>
      <div class="grid g3">
        <div class="card"><span class="tag">AREA</span><h3>Orders & Cancellation</h3><p class="q">Are we trading growth for quality?</p><div class="viz"></div></div>
        <div class="card"><span class="tag">MAP</span><h3>City Risk Heat</h3><p class="q">Where to intervene first?</p><div class="viz"></div></div>
        <div class="card"><span class="tag">RIBBON</span><h3>Segment Mix Shift</h3><p class="q">FOOD vs GOOD mix by month</p><div class="viz"></div></div>
      </div>
    </section>

    <section class="page" id="p2">
      <div class="grid g3">
        <div class="card"><span class="tag">LINE + SMALL MULTIPLES</span><h3>Orders by Day/Week/Month</h3><p class="q">Seasonality and growth cadence</p><div class="viz"></div></div>
        <div class="card"><span class="tag">Lollipop</span><h3>Top Channels by GMV</h3><p class="q">Over-dependence diagnosis</p><div class="mini-bars" id="topChannels"></div></div>
        <div class="card"><span class="tag">DONUT</span><h3>Payment Mix</h3><p class="q">Payment structure stability</p><div class="viz"></div></div>
      </div>
      <div class="grid g2">
        <div class="card"><span class="tag">HISTOGRAM</span><h3>Order Value Distribution</h3><p class="q">AOV strategy by segment</p><div class="viz"></div></div>
        <div class="card"><span class="tag">HEATMAP</span><h3>Peak-hour Analysis</h3><p class="q">When demand spikes and staffing needs</p><div class="viz"></div></div>
      </div>
      <div class="callout">
        <div class="status mid">Watch</div>
        <ul class="bullet">
          <li>Marketplace share ≈ 79% GMV, while OWN CHANNEL AOV is materially higher.</li>
          <li>Potential optimization: protect marketplace volume but selectively migrate high-value baskets.</li>
        </ul>
      </div>
    </section>

    <section class="page" id="p3">
      <div class="grid g4">
        <div class="card"><span class="tag">KPI</span><h3>Median Cycle</h3><p class="q">End-to-end speed</p><div class="v" id="cycleKpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
        <div class="card"><span class="tag">KPI</span><h3>P90 Cycle</h3><p class="q">Tail risk indicator</p><div class="v" id="p90Kpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
        <div class="card"><span class="tag">KPI</span><h3>Median Distance</h3><p class="q">Delivery footprint</p><div class="v" id="distKpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
        <div class="card"><span class="tag">KPI</span><h3>Cancel Rate</h3><p class="q">Service reliability</p><div class="v" id="cancelKpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
      </div>
      <div class="grid g2">
        <div class="card"><span class="tag">SCATTER</span><h3>Distance vs Delivery Time</h3><p class="q">Non-linear tail behavior detection</p><div class="viz"></div></div>
        <div class="card"><span class="tag">BOXPLOT</span><h3>Delivery Time by Driver Modal</h3><p class="q">Modal suitability under demand</p><div class="viz"></div></div>
      </div>
      <div class="grid g2">
        <div class="card"><span class="tag">BULLET</span><h3>SLA by Hour Slot</h3><p class="q">Performance against target</p><div class="viz"></div></div>
        <div class="card"><span class="tag">DRILL-THROUGH ENTRY</span><h3>Failed Delivery Cases</h3><p class="q">Investigate high-cycle or cancelled orders</p><div class="drill" data-drill="Delivery Case Detail: order timeline, distance, payment, hub">Open case drill-through</div></div>
      </div>
    </section>

    <section class="page" id="p4">
      <div class="grid g2">
        <div class="card"><span class="tag">AZURE MAPS</span><h3>Hub Map + Performance Bubble</h3><p class="q">Which geos are high-volume but underperforming?</p><div class="viz"></div></div>
        <div class="card"><span class="tag">DUMBBELL</span><h3>Hub Benchmark</h3><p class="q">Orders vs cycle vs cancel side-by-side</p><div class="viz"></div></div>
      </div>
      <div class="grid g3">
        <div class="card"><span class="tag">BAR</span><h3>GMV by City</h3><p class="q">Regional concentration</p><div class="mini-bars" id="cityBars"></div></div>
        <div class="card"><span class="tag">WATERFALL</span><h3>Delivery Margin by City</h3><p class="q">Fee-cost gap source</p><div class="viz"></div></div>
        <div class="card"><span class="tag">CALENDAR HEATMAP*</span><h3>Hub Load Calendar</h3><p class="q">Weekly stress mapping</p><div class="viz"></div><p style="margin:6px 0 0;color:var(--ink3);font-size:10px">*Custom visual optional.</p></div>
      </div>
    </section>

    <section class="page" id="p5">
      <div class="grid g3">
        <div class="card"><span class="tag">PARETO</span><h3>Store Revenue Concentration</h3><p class="q">Top stores dependency profile</p><div class="viz"></div></div>
        <div class="card"><span class="tag">MATRIX</span><h3>Partner Priority Matrix</h3><p class="q">Revenue contribution vs cancel risk</p><div class="viz"></div></div>
        <div class="card"><span class="tag">TABLE</span><h3>Top/Bottom Store List</h3><p class="q">Drill list for account manager</p><div class="viz"></div></div>
      </div>
      <div class="grid g2">
        <div class="card"><span class="tag">BUBBLE</span><h3>Store AOV vs Cancel Rate</h3><p class="q">Commercial quality segmentation</p><div class="viz"></div></div>
        <div class="card"><span class="tag">SANKEY*</span><h3>Channel → Store Segment Flow</h3><p class="q">Acquisition mix by partner type</p><div class="viz"></div><p style="margin:6px 0 0;color:var(--ink3);font-size:10px">*Custom visual only if default combo chart is not expressive enough.</p></div>
      </div>
      <div class="callout"><span class="status risk">Risk</span> GOOD segment has materially higher cancellation; partner playbook should be split by segment, not treated as one-size-fits-all.</div>
    </section>

    <section class="page" id="p6">
      <div class="grid g3">
        <div class="card"><span class="tag">DECOMPOSITION TREE</span><h3>What drives cancellation?</h3><p class="q">Slice by city, segment, channel, hour</p><div class="viz"></div></div>
        <div class="card"><span class="tag">KEY INFLUENCERS</span><h3>Likely cancellation factors</h3><p class="q">Explainability for stakeholders</p><div class="viz"></div></div>
        <div class="card"><span class="tag">WHAT-IF</span><h3>Free-shipping policy simulator</h3><p class="q">Margin impact sensitivity</p><div class="viz"></div></div>
      </div>
      <div class="grid g2">
        <div class="card"><span class="tag">OUTLIER TABLE</span><h3>Anomaly Register</h3><p class="q">Extreme amount / distance / cycle watchlist</p><div class="viz"></div><div class="drill" data-drill="Anomaly drill-through: raw transaction rows and data quality flags">Open anomaly drill-through</div></div>
        <div class="callout">
          <div class="status ok">Validated</div>
          <ul class="bullet" id="auditBullets"></ul>
        </div>
      </div>
    </section>

    <footer id="foot"></footer>
  </main>
</div>

<div class="drawer" id="drawer">
  <h4>Filter Panel (Bookmark Open/Close)</h4>
  <div class="s"><label>Date Range</label><div class="box">01 Jan 2021 → 30 Apr 2021</div></div>
  <div class="s"><label>City</label><div class="box">All</div></div>
  <div class="s"><label>Hub</label><div class="box">All</div></div>
  <div class="s"><label>Store Segment</label><div class="box">All</div></div>
  <div class="s"><label>Channel Type</label><div class="box">All</div></div>
  <div class="s"><label>Driver Modal</label><div class="box">All</div></div>
  <div class="s"><label>Delivery Status</label><div class="box">DELIVERED + CANCELED</div></div>
</div>

<div class="tooltip" id="tip"></div>

<div class="modal" id="modal">
  <div class="panel">
    <button class="btn close" id="closeModal">Close</button>
    <h3 id="modalTitle">Drill-through</h3>
    <p>This modal simulates Power BI drill-through destination pages.</p>
    <ul>
      <li>Order timeline checkpoints</li>
      <li>Driver/hub/store/channel context</li>
      <li>Cost-fee-payment diagnostics</li>
      <li>Data quality flags at row level</li>
    </ul>
  </div>
</div>

<script>
const DATA = __DATA__;
const pageNames = {
  p1:"Page 1 — Executive Overview",
  p2:"Page 2 — Order & Revenue Analysis",
  p3:"Page 3 — Delivery Performance",
  p4:"Page 4 — Hub & Geographic Performance",
  p5:"Page 5 — Store & Partner Performance",
  p6:"Page 6 — Deep-dive / Insight Lab"
};
const historyStack = ["p1"];
const byId = id => document.getElementById(id);
const brl = v => "R$" + (v >= 1e6 ? (v/1e6).toFixed(2)+"M" : v.toFixed(0));
const num = v => v >= 1e6 ? (v/1e6).toFixed(2)+"M" : v.toLocaleString();

function setPage(id, push=true){
  document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active", p.id===id));
  document.querySelectorAll(".nav").forEach(b=>b.classList.toggle("active", b.dataset.page===id));
  byId("ttl").textContent = pageNames[id];
  byId("sub").textContent = "Mockup canvas with navigation, tooltip, drill-through, and filter UX.";
  if(push && historyStack[historyStack.length-1] !== id) historyStack.push(id);
}
document.querySelectorAll(".nav").forEach(btn => btn.addEventListener("click",()=>setPage(btn.dataset.page)));
byId("homeBtn").addEventListener("click",()=>setPage("p1"));
byId("backBtn").addEventListener("click",()=>{
  if(historyStack.length>1){ historyStack.pop(); setPage(historyStack[historyStack.length-1], false); }
});
byId("toggleFilter").addEventListener("click",()=>byId("drawer").classList.toggle("open"));
byId("resetBtn").addEventListener("click",()=>{
  byId("selectedFilters").innerHTML = '<span class="chip">City: All (4)</span><span class="chip">Segment: All</span><span class="chip">Channel Type: All</span><span class="chip">Period: Jan-Apr 2021</span>';
});

// KPIs on page 1
const k = DATA.kpi;
const kpiRows = [
  ["GMV (Finished)", brl(k.gmv), "AOV "+brl(k.aov)],
  ["Total Orders", num(k.total_orders), num(k.finished_orders)+" finished"],
  ["Cancellation", k.cancel_rate+"%", "Monitor monthly trend"],
  ["Median Cycle", k.median_cycle_min+" min", "P90 "+DATA.cycle_pct.p90+" min"],
  ["Median Distance", k.median_distance_km+" km", "Delivered only"],
  ["Active Stores", k.n_stores_active, "/"+k.n_stores_total]
];
byId("kpis").innerHTML = kpiRows.map(r=>`<div class="kpi"><div class="l">${r[0]}</div><div class="v">${r[1]}</div><div class="d">${r[2]}</div></div>`).join("");
byId("ins1").textContent = `${(DATA.top_channels[0].gmv / k.gmv * 100).toFixed(1)}% GMV from one channel`;

// Populate sample ranking cards
const topChannels = DATA.top_channels.slice(0,5);
const maxCh = Math.max(...topChannels.map(x=>x.gmv));
byId("topChannels").innerHTML = topChannels.map(x=>`
  <div class="row"><div>${x.channel.replace(" PLACE","")}</div>
  <div class="track"><div class="fill" style="width:${(x.gmv/maxCh*100).toFixed(1)}%;background:${x.type==="MARKETPLACE"?"var(--blue)":"var(--violet)"}"></div></div>
  <div>${brl(x.gmv)}</div></div>`).join("");

const city = DATA.city;
const maxCity = Math.max(...city.map(x=>x.gmv));
byId("cityBars").innerHTML = city.map(x=>`
  <div class="row"><div>${x.city.replace(" DE JANEIRO","")}</div>
  <div class="track"><div class="fill" style="width:${(x.gmv/maxCity*100).toFixed(1)}%;background:var(--teal)"></div></div>
  <div>${(x.gmv/k.gmv*100).toFixed(1)}%</div></div>`).join("");

// Page 3 KPI cards
byId("cycleKpi").textContent = DATA.cycle_pct.p50+"m";
byId("p90Kpi").textContent = DATA.cycle_pct.p90+"m";
byId("distKpi").textContent = k.median_distance_km+"km";
byId("cancelKpi").textContent = k.cancel_rate+"%";

// Audit bullets on page 6
const q = DATA.quality;
const audit = [
  `No PK duplicates and no FK orphans in core joins.`,
  `${q.flag_extreme_amount} extreme-order amounts and ${q.flag_extreme_distance} extreme distances are flagged (not deleted).`,
  `${q.flag_long_cycle} long-cycle orders (>24h) can distort SLA if not trimmed.`,
  `${q.orders_no_payment.toLocaleString()} orders have no payment records and ${q.orders_no_delivery.toLocaleString()} have no delivery records.`,
  `order_moment_delivered missing ~${q.delivered_missing_pct}% -> use finished timestamp as completion proxy.`
];
byId("auditBullets").innerHTML = audit.map(x=>`<li>${x}</li>`).join("");

// Tooltip behavior
const tip = byId("tip");
document.querySelectorAll(".q,.tag,.status").forEach(node=>{
  node.setAttribute("data-tip", node.textContent.trim());
  node.addEventListener("mousemove",(e)=>{
    tip.style.display="block";
    tip.style.left=(e.clientX+12)+"px";
    tip.style.top=(e.clientY+12)+"px";
    tip.textContent=node.getAttribute("data-tip");
  });
  node.addEventListener("mouseleave",()=>tip.style.display="none");
});

// Drill-through modal
document.querySelectorAll(".drill").forEach(d=>{
  d.addEventListener("click",()=>{
    byId("modalTitle").textContent = d.dataset.drill;
    byId("modal").classList.add("open");
  });
});
byId("closeModal").addEventListener("click",()=>byId("modal").classList.remove("open"));
byId("modal").addEventListener("click",(e)=>{ if(e.target.id==="modal") byId("modal").classList.remove("open"); });

// Footer
byId("foot").innerHTML = `<b>Design concept:</b> Neo-Logistics Dark (Brazil urban night) · semantic color for status (green/amber/red) · dynamic title + navigation + filter drawer bookmark + selected-filter summary + tooltip + drill-through.
<br><b>Custom visual policy:</b> Sankey / Calendar Heatmap only if default visuals cannot express flow/load clearly; fallback: stacked bar + matrix.`;
</script>
</body>
</html>
"""

out = HTML.replace("__DATA__", DATA_JS)
open(os.path.join(DASH, "mockup.html"), "w").write(out)
print("wrote dashboard/mockup.html", len(out), "bytes")
