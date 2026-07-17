"""
08_gen_pbi_mockup.py — Build the full 6-page Power BI-style mockup.
Preserves the hand-authored scaffold's design system (CSS variables, shell, nav,
filter drawer, tooltip, drill modal, JS interactions) and fills every visual with a
real SVG chart rendered from dashboard/page_data.json.
Output: dashboard/mockup.html (self-contained, artifact-ready).
"""
import json, os
HERE = os.path.dirname(__file__); DASH = os.path.join(HERE, "..", "dashboard")
PD = json.load(open(os.path.join(DASH, "page_data.json")))
PD_JS = json.dumps(PD, ensure_ascii=False)

# ---- Theme tokens (:root per theme) ----
ROOT_DARK = """:root{
  --bg:#0a0d14;--radial:radial-gradient(1400px 800px at 85% -20%,#1b2540 0%,#0a0d14 52%);
  --panel:#141a28;--panel2:#1a2132;--line:#273146;--ink:#f3f6ff;--ink2:#aab4ca;--ink3:#6e7892;
  --blue:#3d8bff;--teal:#22b8a6;--violet:#8878ff;--amber:#f2a71b;--red:#df4f67;--green:#38c172;
  --grad:linear-gradient(135deg,#3d8bff,#8878ff);--qink:#8fbaff;
  --sidebg:linear-gradient(180deg,#0b101c,#0b0f18);--topbg:rgba(20,26,40,.85);--drawerbg:#101727;
  --tipbg:#0f1523;--tipink:#f3f6ff;--track:#1b2335;--boxbg:#0c1220;
  --calbg:linear-gradient(135deg,rgba(61,139,255,.14),rgba(136,120,255,.12));--calborder:#455892;
  --menuact:linear-gradient(135deg,rgba(61,139,255,.25),rgba(136,120,255,.13));--menuactbd:#44689f;--brandbg:rgba(61,139,255,.08);
  --drillink:#9ab8ff;--drillbd:#4f638f;--drillbg:rgba(61,139,255,.1);
  --okbg:rgba(56,193,114,.15);--okink:#5ee39a;--midbg:rgba(242,167,27,.15);--midink:#ffd071;--riskbg:rgba(223,79,103,.15);--riskink:#ff8ea4;
}"""
ROOT_LIGHT = """:root{
  --bg:#eaeefb;--radial:radial-gradient(1200px 720px at 85% -10%,#dbe6ff 0%,#eef2fc 55%);
  --panel:#ffffff;--panel2:#f4f7ff;--line:#e2e8f5;--ink:#0f1a30;--ink2:#4c587a;--ink3:#8b95ad;
  --blue:#2f6bff;--teal:#0d9488;--violet:#7a3bf5;--amber:#d97706;--red:#e11d48;--green:#0f9d58;
  --grad:linear-gradient(135deg,#2f6bff,#7a3bf5);--qink:#2f6bff;
  --sidebg:linear-gradient(180deg,#f4f7ff,#e9eefb);--topbg:rgba(255,255,255,.92);--drawerbg:#ffffff;
  --tipbg:#0f1a30;--tipink:#ffffff;--track:#e9eef8;--boxbg:#f4f7ff;
  --calbg:linear-gradient(135deg,rgba(47,107,255,.10),rgba(122,59,245,.08));--calborder:#cdd7f2;
  --menuact:linear-gradient(135deg,rgba(47,107,255,.15),rgba(122,59,245,.10));--menuactbd:#b7c5ee;--brandbg:rgba(47,107,255,.08);
  --drillink:#2f6bff;--drillbd:#b7c5ee;--drillbg:rgba(47,107,255,.09);
  --okbg:rgba(15,157,88,.13);--okink:#0b7a44;--midbg:rgba(217,119,6,.15);--midink:#a85d05;--riskbg:rgba(225,29,72,.12);--riskink:#c11340;
}"""

# JS chart palette per theme
C_DARK = {"blue":"#3d8bff","teal":"#22b8a6","violet":"#8878ff","amber":"#f2a71b","red":"#df4f67","green":"#38c172",
          "ink2":"#aab4ca","ink3":"#6e7892","grid":"#243049","lab":"#c7cee0","markOn":"#ffffff","strong":"#ffffff",
          "total":"#ffffff","areaGrad":"#3d8bff","heat":"61,139,255","cal":"56,193,114"}
C_LIGHT = {"blue":"#2f6bff","teal":"#0d9488","violet":"#7a3bf5","amber":"#d97706","red":"#e11d48","green":"#0f9d58",
           "ink2":"#4c587a","ink3":"#8b95ad","grid":"#e7ebf6","lab":"#3f4a66","markOn":"#ffffff","strong":"#0f1a30",
           "total":"#0f1a30","areaGrad":"#2f6bff","heat":"47,107,255","cal":"15,157,88"}

# ---- CSS body (theme-agnostic; every color via var()) ----
CSS_STATIC = r"""
*{box-sizing:border-box}
body{margin:0;background:var(--radial);color:var(--ink);font:14px/1.45 "Segoe UI",Inter,system-ui,sans-serif}
.app{display:grid;grid-template-columns:248px 1fr;min-height:100vh}
.side{background:var(--sidebg);border-right:1px solid var(--line);padding:16px 14px;position:sticky;top:0;height:100vh}
.brand{padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--brandbg)}
.brand h1{margin:0;font-size:14px;line-height:1.2}
.brand small{color:var(--ink2)}
.menu{margin-top:16px;display:grid;gap:8px}
.menu button{all:unset;cursor:pointer;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink2);font-size:12.5px}
.menu button.active{color:var(--ink);border-color:var(--menuactbd);background:var(--menuact)}
.menu .sec{margin:8px 0 2px;color:var(--ink3);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
.side .meta{margin-top:12px;font-size:11px;color:var(--ink3);border-top:1px dashed var(--line);padding-top:10px}
.main{padding:14px 18px 26px 18px}
.top{display:flex;align-items:center;gap:10px;justify-content:space-between;background:var(--topbg);border:1px solid var(--line);border-radius:14px;padding:10px 12px;position:sticky;top:10px;z-index:3;backdrop-filter:blur(6px)}
.title h2{margin:0;font-size:20px;letter-spacing:-.3px}
.title .sub{color:var(--ink2);font-size:12px}
.actions{display:flex;align-items:center;gap:8px}
.btn{all:unset;cursor:pointer;padding:7px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);font-size:12px;color:var(--ink2)}
.btn.primary{background:var(--grad);color:#fff;border:none}
.btn:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.filters-summary{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0 2px}
.chip{padding:4px 8px;border-radius:999px;background:var(--panel);border:1px solid var(--line);font-size:11.5px;color:var(--ink2)}
.page{display:none;margin-top:12px}
.page.active{display:block}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.kpi{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:12px;padding:11px 12px;position:relative;overflow:hidden;box-shadow:0 1px 2px rgba(20,30,60,.04)}
.kpi:before{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--grad)}
.kpi .l{font-size:10px;color:var(--ink3);text-transform:uppercase;letter-spacing:.6px}
.kpi .v{font-size:21px;font-weight:800;margin-top:4px}
.kpi .d{font-size:11px;color:var(--ink2);margin-top:2px}
.grid{display:grid;gap:10px;margin-top:10px}
.g2{grid-template-columns:1.5fr 1fr}.g2e{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:11px 12px;position:relative;min-height:160px;box-shadow:0 1px 2px rgba(20,30,60,.04)}
.card h3{margin:0 0 2px;font-size:13.5px}
.q{margin:0;color:var(--qink);font-size:11px}
.tag{position:absolute;right:10px;top:10px;font-size:9px;color:var(--ink3);border:1px solid var(--line);padding:1px 6px;border-radius:5px}
.chart{margin-top:9px}
.chart svg{display:block;width:100%;overflow:visible}
.mini-bars{display:grid;gap:6px;margin-top:10px}
.row{display:grid;grid-template-columns:82px 1fr 64px;gap:6px;align-items:center;font-size:11px}
.track{height:12px;background:var(--track);border-radius:6px;overflow:hidden}.fill{height:100%;background:var(--blue)}
.callout{background:var(--calbg);border:1px solid var(--calborder);border-radius:12px;padding:12px}
.callout b{font-size:20px}
.bullet{padding-left:16px;margin:6px 0 0 0;color:var(--ink2);font-size:12px}
.bullet li{margin:4px 0}
.status{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10.5px;font-weight:700}
.ok{background:var(--okbg);color:var(--okink)}.mid{background:var(--midbg);color:var(--midink)}.risk{background:var(--riskbg);color:var(--riskink)}
.drawer{position:fixed;right:16px;top:76px;width:290px;background:var(--drawerbg);border:1px solid var(--line);border-radius:12px;padding:12px;z-index:5;display:none;box-shadow:0 12px 40px rgba(10,20,50,.25)}
.drawer.open{display:block}
.drawer h4{margin:0 0 8px;font-size:13px}
.drawer .s{margin:8px 0}
.drawer label{display:block;font-size:11px;color:var(--ink2);margin-bottom:4px}
.drawer .box{border:1px dashed var(--line);border-radius:8px;padding:6px 8px;color:var(--ink2);font-size:11.5px;background:var(--boxbg);cursor:pointer;margin-bottom:5px}
.drawer .box.sel{border-style:solid;border-color:var(--menuactbd);color:var(--ink);background:var(--drillbg)}
.tooltip{position:fixed;pointer-events:none;background:var(--tipbg);border:1px solid var(--line);border-radius:8px;padding:7px 8px;max-width:230px;font-size:11px;color:var(--tipink);display:none;z-index:9;box-shadow:0 6px 20px rgba(10,20,50,.3)}
.drill{cursor:pointer;border:1px dashed var(--drillbd);padding:5px 8px;border-radius:8px;font-size:11px;color:var(--drillink);background:var(--drillbg);display:inline-block;margin-top:9px}
.modal{position:fixed;inset:0;background:rgba(5,8,14,.55);display:none;align-items:center;justify-content:center;z-index:8}
.modal.open{display:flex}
.modal .panel{width:min(820px,92vw);max-height:86vh;overflow:auto;background:var(--drawerbg);border:1px solid var(--line);border-radius:12px;padding:14px}
.modal h3{margin:0 0 6px}
.modal p,.modal li{color:var(--ink2);font-size:12px}
.close{float:right}
.legend{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
.legend span{font-size:10.5px;color:var(--ink2)}
.dot{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.dtbl{width:100%;border-collapse:collapse;font-size:11px;margin-top:8px}
.dtbl th{color:var(--ink3);text-align:left;font-weight:600;padding:4px 6px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--panel)}
.dtbl td{padding:4px 6px;border-bottom:1px solid var(--line);color:var(--ink2)}
.dtbl td.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--ink)}
input[type=range]{width:100%;accent-color:var(--blue)}
.reco-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}
.reco-hero{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:12px;padding:14px 16px;position:relative;overflow:hidden}
.reco-hero:before{content:"";position:absolute;inset:0 0 auto 0;height:3px;background:var(--grad)}
.reco-hero .n{font-size:26px;font-weight:800;letter-spacing:-.5px}
.reco-hero .l{font-size:11px;color:var(--ink3);text-transform:uppercase;letter-spacing:.5px}
.reco-hero .s{font-size:11.5px;color:var(--ink2);margin-top:3px}
.reco-list{display:grid;gap:10px}
.reco-card{display:grid;grid-template-columns:40px 1fr 168px;gap:14px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;position:relative;overflow:hidden}
.reco-card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px}
.reco-card.p1c:before{background:var(--red)}.reco-card.p2c:before{background:var(--amber)}.reco-card.p3c:before{background:var(--blue)}.reco-card.p4c:before{background:var(--violet)}.reco-card.p5c:before{background:var(--teal)}
.reco-num{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:17px;color:#fff;background:var(--grad)}
.reco-main h4{margin:0 0 3px;font-size:14px}
.reco-main .ev{color:var(--ink2);font-size:12px;margin:2px 0}
.reco-main .ev b{color:var(--ink)}
.reco-main .ac{color:var(--qink);font-size:12px;margin-top:3px}
.reco-main .ac:before{content:"→ "}
.reco-side{text-align:right}
.reco-side .big{font-size:18px;font-weight:800;letter-spacing:-.3px}
.reco-side .cap{font-size:10px;color:var(--ink3)}
.pill{display:inline-block;font-size:9.5px;font-weight:700;padding:2px 7px;border-radius:999px;margin-top:6px}
.pill.pv{background:var(--okbg);color:var(--okink)}.pill.hy{background:var(--midbg);color:var(--midink)}
footer{margin-top:10px;padding-top:10px;border-top:1px dashed var(--line);color:var(--ink3);font-size:11px}
@media (max-width:1280px){.kpis{grid-template-columns:repeat(3,1fr)}.g3,.g4{grid-template-columns:repeat(2,1fr)}.g2,.g2e{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

# ---- page bodies: each card's visual is a real chart container ----
PAGES = r"""
<section class="page active" id="p1">
  <div class="kpis" id="kpis"></div>
  <div class="grid g2">
    <div class="card"><span class="tag">LINE + AREA</span><h3>GMV Trend by Week</h3><p class="q">Business scale is accelerating or flattening?</p>
      <div class="chart" id="c_gmvweek"></div>
      <div class="legend"><span><i class="dot" style="background:var(--blue)"></i>Weekly GMV</span><span><i class="dot" style="background:var(--amber)"></i>Peak week (29 Mar)</span></div></div>
    <div class="callout">
      <div class="status mid">Strategic watch</div>
      <b id="ins1"></b>
      <p style="margin:6px 0 0;color:var(--ink2);font-size:12px">Doanh thu phụ thuộc một kênh duy nhất — rủi ro tập trung là vấn đề chiến lược hàng đầu cần theo dõi ở cấp điều hành.</p>
      <div class="drill" data-drill="Executive drill-through — Vì sao GMV tập trung: bóc tách theo kênh, segment, cửa hàng top">Drill-through: Vì sao tập trung cao?</div></div>
  </div>
  <div class="grid g3">
    <div class="card"><span class="tag">SMALL MULTIPLES</span><h3>Orders & Cancellation</h3><p class="q">Có đánh đổi tăng trưởng lấy chất lượng?</p><div class="chart" id="c_ordcancel"></div></div>
    <div class="card"><span class="tag">BUBBLE MAP</span><h3>City Risk Heat</h3><p class="q">Nên can thiệp ở đâu trước?</p><div class="chart" id="c_cityrisk"></div></div>
    <div class="card"><span class="tag">RIBBON / STACKED AREA</span><h3>Segment Mix Shift</h3><p class="q">FOOD vs GOOD dịch chuyển theo tháng?</p><div class="chart" id="c_segmix"></div></div>
  </div>
</section>

<section class="page" id="p2">
  <div class="grid g3">
    <div class="card"><span class="tag">LINE</span><h3>Orders Trend by Week</h3><p class="q">Nhịp tăng trưởng & mùa vụ ngắn hạn</p><div class="chart" id="c_ordtrend"></div></div>
    <div class="card"><span class="tag">LOLLIPOP</span><h3>Top Channels by GMV</h3><p class="q">Chẩn đoán phụ thuộc kênh</p><div class="chart" id="c_channels"></div></div>
    <div class="card"><span class="tag">DONUT</span><h3>Payment Mix</h3><p class="q">Cơ cấu & ổn định thanh toán</p><div class="chart" id="c_payment"></div></div>
  </div>
  <div class="grid g2e">
    <div class="card"><span class="tag">HISTOGRAM</span><h3>Order Value Distribution</h3><p class="q">Chiến lược AOV — phần lớn đơn nằm ở đâu?</p><div class="chart" id="c_aov"></div></div>
    <div class="card"><span class="tag">HEATMAP</span><h3>Peak-hour Analysis (Day × Hour, giờ địa phương)</h3><p class="q">Cầu bùng nổ khi nào → bố trí shipper</p><div class="chart" id="c_heat"></div></div>
  </div>
  <div class="callout" style="margin-top:10px">
    <div class="status mid">Watch</div>
    <ul class="bullet">
      <li>Marketplace ≈ <b>79% GMV</b> nhưng AOV kênh riêng cao hơn hẳn (R$218 vs R$88) → dư địa "kéo" giỏ hàng giá trị cao về kênh riêng.</li>
      <li>Cầu lưỡng đỉnh <b>12h &amp; 19–20h</b>, dồn Thứ 6–CN → lịch shipper nên theo daypart, không đồng đều.</li>
    </ul>
  </div>
</section>

<section class="page" id="p3">
  <div class="grid g4">
    <div class="card"><span class="tag">KPI</span><h3>Median Cycle</h3><p class="q">Tốc độ end-to-end</p><div class="v" id="cycleKpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
    <div class="card"><span class="tag">KPI</span><h3>P90 Cycle</h3><p class="q">Rủi ro đuôi (tail)</p><div class="v" id="p90Kpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
    <div class="card"><span class="tag">KPI</span><h3>Median Distance</h3><p class="q">Bán kính giao</p><div class="v" id="distKpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
    <div class="card"><span class="tag">KPI</span><h3>Delivery Success</h3><p class="q">Độ tin cậy dịch vụ</p><div class="v" id="succKpi" style="font-size:30px;font-weight:800;margin-top:16px"></div></div>
  </div>
  <div class="grid g2e">
    <div class="card"><span class="tag">SCATTER</span><h3>Distance vs Delivery Time</h3><p class="q">Quãng đường có quyết định thời gian giao?</p><div class="chart" id="c_scatter"></div>
      <p style="margin:7px 0 0;color:var(--ink2);font-size:11px" id="scatterNote"></p></div>
    <div class="card"><span class="tag">BOXPLOT</span><h3>Cycle Time by Driver Modal</h3><p class="q">Motoboy vs Biker chịu tải thế nào?</p><div class="chart" id="c_box"></div></div>
  </div>
  <div class="grid g2e">
    <div class="card"><span class="tag">FUNNEL / BAR</span><h3>Thời gian nằm ở khâu nào?</h3><p class="q">Chuẩn bị vs Di chuyển — nút thắt thật sự</p><div class="chart" id="c_funnel"></div></div>
    <div class="card"><span class="tag">DRILL-THROUGH ENTRY</span><h3>Failed / Slow Delivery Cases</h3><p class="q">Điều tra đơn hủy hoặc cycle cao bất thường</p>
      <div class="chart" id="c_modalsplit"></div>
      <div class="drill" data-drill="Delivery Case Detail — dòng thời gian đơn, cự ly, hub, tài xế, cờ chất lượng dữ liệu">Mở case drill-through</div></div>
  </div>
</section>

<section class="page" id="p4">
  <div class="grid g2e">
    <div class="card"><span class="tag">MAP (Azure Maps)</span><h3>Hub Map + Performance Bubble</h3><p class="q">Khu vực nào khối lượng cao nhưng hiệu suất thấp?</p><div class="chart" id="c_hubmap"></div>
      <div class="legend"><span><i class="dot" style="background:var(--green)"></i>Hủy thấp</span><span><i class="dot" style="background:var(--amber)"></i>Trung bình</span><span><i class="dot" style="background:var(--red)"></i>Hủy cao</span><span style="color:var(--ink3)">· cỡ bubble = số đơn</span></div></div>
    <div class="card"><span class="tag">RANKED BAR</span><h3>Hub Cancellation Benchmark</h3><p class="q">Hub nào lệch chuẩn về tỷ lệ hủy? (≥500 đơn)</p><div class="chart" id="c_hubcancel"></div></div>
  </div>
  <div class="grid g3">
    <div class="card"><span class="tag">BAR</span><h3>GMV by City</h3><p class="q">Tập trung theo vùng</p><div class="chart" id="c_citybars"></div></div>
    <div class="card"><span class="tag">SCATTER · QUADRANT</span><h3>Hub: Volume vs Cancel Rate</h3><p class="q">Hub nào khối lượng cao NHƯNG hủy cao? (ô đỏ = ưu tiên xử lý)</p><div class="chart" id="c_hubquad"></div></div>
    <div class="card"><span class="tag">CALENDAR HEATMAP*</span><h3>Daily Load Calendar</h3><p class="q">Ngày nào hệ thống chịu tải cao</p><div class="chart" id="c_calendar"></div><p style="margin:6px 0 0;color:var(--ink3);font-size:10px">*Custom visual (Calendar) — mặc định thay bằng matrix tuần×thứ.</p></div>
  </div>
</section>

<section class="page" id="p5">
  <div class="grid g3">
    <div class="card"><span class="tag">PARETO</span><h3>Store Revenue Concentration</h3><p class="q">Bao nhiêu % cửa hàng tạo 80% GMV?</p><div class="chart" id="c_pareto"></div></div>
    <div class="card"><span class="tag">MATRIX 2×2</span><h3>Partner Priority Matrix</h3><p class="q">Đóng góp doanh thu vs rủi ro hủy</p><div class="chart" id="c_matrix"></div></div>
    <div class="card"><span class="tag">TABLE</span><h3>Top Stores (GMV, ≥100 đơn)</h3><p class="q">Danh sách drill cho account manager</p><div class="chart" id="c_storetable"></div></div>
  </div>
  <div class="grid g2e">
    <div class="card"><span class="tag">BUBBLE</span><h3>Store AOV vs Cancel Rate</h3><p class="q">Phân khúc chất lượng thương mại</p><div class="chart" id="c_storebubble"></div></div>
    <div class="card"><span class="tag">100% STACKED BAR</span><h3>Segment mix by Channel Type</h3><p class="q">Marketplace vs Own channel bán FOOD hay GOOD?</p><div class="chart" id="c_chanseg"></div></div>
  </div>
  <div class="callout" style="margin-top:10px"><span class="status risk">Risk</span> GOOD bị hủy <b>12.7%</b> vs FOOD <b>3.4%</b> → playbook đối tác phải tách theo segment, không "một cỡ cho tất cả".</div>
</section>

<section class="page" id="p6">
  <div class="grid g3">
    <div class="card"><span class="tag">DECOMPOSITION TREE</span><h3>What drives cancellation?</h3><p class="q">Bóc tách theo segment → loại kênh</p><div class="chart" id="c_decomp"></div></div>
    <div class="card"><span class="tag">KEY INFLUENCERS</span><h3>Yếu tố làm tăng tỷ lệ hủy</h3><p class="q">Giải thích cho stakeholder</p><div class="chart" id="c_infl"></div></div>
    <div class="card"><span class="tag">WHAT-IF</span><h3>Free-shipping policy simulator</h3><p class="q">Tác động biên tới chi phí bù giao</p>
      <div style="margin-top:12px"><label style="font-size:11px;color:var(--ink2)">% đơn được free-ship: <b id="wiVal">35.6%</b></label>
      <input type="range" id="wiSlider" min="0" max="100" value="36"></div>
      <div class="chart" id="c_whatif"></div></div>
  </div>
  <div class="grid g2e">
    <div class="card"><span class="tag">OUTLIER TABLE</span><h3>Anomaly Register</h3><p class="q">Watchlist: amount / distance / cycle bất thường</p><div class="chart" id="c_anomaly"></div>
      <div class="drill" data-drill="Anomaly drill-through — các dòng giao dịch thô + cờ chất lượng dữ liệu ở cấp bản ghi">Mở anomaly drill-through</div></div>
    <div class="callout"><div class="status ok">Validated by data</div><ul class="bullet" id="auditBullets"></ul></div>
  </div>
</section>
"""

SHELL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brazilian Delivery Center — Power BI Mockup (Multi-page)</title><style>__CSS__</style></head><body>
<div class="app">
  <aside class="side">
    <div class="brand"><h1>Delivery Center<br>Analytics Showcase</h1><small>Mockup — chờ duyệt · Concept C</small></div>
    <div class="menu">
      <div class="sec">Pages</div>
      <button class="nav active" data-page="p1">1 · Executive Overview</button>
      <button class="nav" data-page="p2">2 · Order &amp; Revenue</button>
      <button class="nav" data-page="p3">3 · Delivery Performance</button>
      <button class="nav" data-page="p4">4 · Hub &amp; Geographic</button>
      <button class="nav" data-page="p5">5 · Store &amp; Partner</button>
      <button class="nav" data-page="p6">6 · Insight Lab</button>
      <button class="nav" data-page="p7">7 · Khuyến nghị &amp; Hành động</button>
    </div>
    <div class="meta">Canvas 16:9 · __THEME_LABEL__ theme<br>Type: Segoe UI / Inter<br>Blue–violet focus + semantic status<br>TZ: UTC−3 (assumed) · min-vol ranking</div>
  </aside>
  <main class="main">
    <div class="top">
      <div class="title"><h2 id="ttl">Page 1 — Executive Overview</h2><div class="sub" id="sub"></div></div>
      <div class="actions">
        <button class="btn" id="homeBtn">⌂ Home</button>
        <button class="btn" id="backBtn">← Back</button>
        <button class="btn" id="resetBtn">Reset Filters</button>
        <button class="btn primary" id="toggleFilter">⚙ Filters</button>
      </div>
    </div>
    <div class="filters-summary" id="selectedFilters"></div>
    """ + PAGES + """
    <section class="page" id="p7">
      <div class="reco-strip" id="recoStrip"></div>
      <div class="reco-list" id="recoList"></div>
      <div class="callout" style="margin-top:12px"><span class="status mid">Giới hạn</span> Chưa khẳng định được (thiếu dữ liệu): nguyên nhân hủy (không có cancel reason) · thiệt hại phụ thuộc kênh (không có hoa hồng) · giữ chân/LTV (không có customer_id) · YoY (chỉ 4 tháng) · múi giờ là giả định UTC−3.</div>
    </section>

    <footer id="foot"></footer>
  </main>
</div>
<div class="drawer" id="drawer">
  <h4>Filter Panel <span style="color:var(--ink3);font-weight:400">(bookmark open/close)</span></h4>
  <div class="s"><label>Date Range</label><div class="box">01 Jan 2021 → 30 Apr 2021</div></div>
  <div class="s"><label>City</label><div class="box" data-f="City" data-v="São Paulo">São Paulo</div><div class="box" data-f="City" data-v="Rio de Janeiro">Rio de Janeiro</div><div class="box" data-f="City" data-v="Porto Alegre">Porto Alegre</div><div class="box" data-f="City" data-v="Curitiba">Curitiba</div></div>
  <div class="s"><label>Store Segment</label><div class="box" data-f="Segment" data-v="FOOD">FOOD</div><div class="box" data-f="Segment" data-v="GOOD">GOOD</div></div>
  <div class="s"><label>Channel Type</label><div class="box" data-f="Channel" data-v="Marketplace">Marketplace</div><div class="box" data-f="Channel" data-v="Own">Own channel</div></div>
  <p style="color:var(--ink3);font-size:10.5px;margin:8px 0 0">Mockup: filter là minh hoạ tương tác (bookmark). Bản Power BI sẽ wire slicer thật vào toàn bộ visual.</p>
</div>
<div class="tooltip" id="tip"></div>
<div class="modal" id="modal"><div class="panel"><button class="btn close" id="closeModal">Close</button><h3 id="modalTitle">Drill-through</h3>
  <p>Mô phỏng trang đích drill-through của Power BI — trang chi tiết được lọc theo ngữ cảnh điểm được chọn.</p>
  <ul><li>Dòng thời gian checkpoint của đơn (created → accepted → ready → collected → delivering → finished)</li>
  <li>Ngữ cảnh tài xế / hub / cửa hàng / kênh</li><li>Chẩn đoán phí – chi phí – thanh toán</li>
  <li>Cờ chất lượng dữ liệu ở cấp bản ghi (extreme amount/distance/cycle)</li></ul></div></div>
<script>
const PD = __PD__;
""" + r"""
const byId=id=>document.getElementById(id);
const NS="http://www.w3.org/2000/svg";
const C = __C__;
const brl=v=>"R$"+(Math.abs(v)>=1e6?(v/1e6).toFixed(2)+"M":Math.abs(v)>=1e3?(v/1e3).toFixed(0)+"k":(+v).toFixed(0));
const nk=v=>v>=1e6?(v/1e6).toFixed(2)+"M":v>=1e3?(v/1e3).toFixed(0)+"k":(""+v);
const E=(t,a={},kids=[])=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);(Array.isArray(kids)?kids:[kids]).forEach(c=>c&&e.appendChild(c));return e;};
const T=(x,y,s,o={})=>E("text",{x,y,fill:o.fill||C.ink3,"font-size":o.fs||9,"text-anchor":o.anc||"start","font-weight":o.fw||400},[document.createTextNode(s)]);
function mk(id,w,h){const box=byId(id);if(!box)return null;const s=E("svg",{viewBox:`0 0 ${w} ${h}`,height:h});box.appendChild(s);return s;}
// shared hover tooltip
const tip=byId("tip");
function hov(node,html){node.style.cursor="default";node.addEventListener("mousemove",e=>{tip.style.display="block";tip.innerHTML=html;tip.style.left=(e.clientX+13)+"px";tip.style.top=(e.clientY+13)+"px";});node.addEventListener("mouseleave",()=>tip.style.display="none");}

/* ---------- P1 ---------- */
const k=PD.exec_kpi;
byId("kpis").innerHTML=[
 ["GMV (Finished)",brl(k.gmv),"AOV "+brl(k.aov)],
 ["Total Orders",nk(k.orders),nk(k.finished)+" finished"],
 ["Cancellation",k.cancel_rate+"%","Fulfillment "+k.fulfill_rate+"%"],
 ["Median Cycle",k.median_cycle+"′","P90 "+PD.cycle_pct.p90+"′"],
 ["Median Distance",k.median_km+" km","delivered only"],
 ["Active Stores",k.active_stores,"/"+ (PD.pareto_stat.n) +" · "+k.hubs+" hubs"]
].map(r=>`<div class="kpi"><div class="l">${r[0]}</div><div class="v">${r[1]}</div><div class="d">${r[2]}</div></div>`).join("");
byId("ins1").textContent=`${(PD.top_channels[0].gmv/k.gmv*100).toFixed(0)}% GMV từ 1 kênh (FOOD PLACE)`;

// GMV weekly line+area with peak marker
(function(){const d=PD.weekly,w=560,h=150,pl=42,pr=12,pt=12,pb=22;const s=mk("c_gmvweek",w,h);if(!s)return;
 const mx=Math.max(...d.map(r=>r.gmv)),xs=i=>pl+i/(d.length-1)*(w-pl-pr),ys=v=>pt+(1-v/mx)*(h-pt-pb);
 for(let g=0;g<=3;g++){const y=pt+g/3*(h-pt-pb);s.appendChild(E("line",{x1:pl,x2:w-pr,y1:y,y2:y,stroke:C.grid}));s.appendChild(T(2,y+3,brl(mx*(1-g/3)),{fs:8}));}
 let p="";d.forEach((r,i)=>p+=(i?"L":"M")+xs(i)+" "+ys(r.gmv));
 const def=E("defs");def.innerHTML=`<linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${C.areaGrad}" stop-opacity=".4"/><stop offset="1" stop-color="${C.areaGrad}" stop-opacity="0"/></linearGradient>`;s.appendChild(def);
 s.appendChild(E("path",{d:p+`L${xs(d.length-1)} ${h-pb}L${xs(0)} ${h-pb}Z`,fill:"url(#gA)"}));
 s.appendChild(E("path",{d:p,fill:"none",stroke:C.blue,"stroke-width":2.5}));
 const pk=d.reduce((a,r,i)=>r.gmv>d[a].gmv?i:a,0);
 const c=E("circle",{cx:xs(pk),cy:ys(d[pk].gmv),r:4,fill:C.amber});s.appendChild(c);hov(c,`<b>Tuần ${d[pk].week}</b><br>GMV ${brl(d[pk].gmv)} · ${nk(d[pk].orders)} đơn<br>Đỉnh trước khi giảm cuối T4`);
 d.forEach((r,i)=>{if(i%3==0)s.appendChild(T(xs(i),h-7,r.week.slice(5),{fs:7.5,anc:"middle"}));
   const hit=E("rect",{x:xs(i)-8,y:pt,width:16,height:h-pt-pb,fill:"transparent"});hov(hit,`<b>${r.week}</b><br>GMV ${brl(r.gmv)}<br>${nk(r.orders)} đơn`);s.appendChild(hit);});})();

// Orders & cancellation small multiples (top: weekly orders area; bottom: monthly cancel line)
(function(){const d=PD.weekly,w=330,h=150,pl=8,pr=8;const s=mk("c_ordcancel",w,h);if(!s)return;
 const topH=78,botY=92;const mx=Math.max(...d.map(r=>r.orders)),xs=i=>pl+i/(d.length-1)*(w-pl-pr),ys=v=>10+(1-v/mx)*(topH-14);
 let p="";d.forEach((r,i)=>p+=(i?"L":"M")+xs(i)+" "+ys(r.orders));
 s.appendChild(E("path",{d:p+`L${xs(d.length-1)} ${topH}L${xs(0)} ${topH}Z`,fill:"rgba(34,184,166,.18)"}));
 s.appendChild(E("path",{d:p,fill:"none",stroke:C.teal,"stroke-width":2}));
 s.appendChild(T(pl,9,"Orders / tuần",{fs:8.5,fill:C.ink2}));
 const cm=PD.cancel_by.month,mxc=Math.max(...cm.map(r=>r.v)),mnc=Math.min(...cm.map(r=>r.v));
 const cx=i=>pl+i/(cm.length-1)*(w-pl-pr),cy=v=>botY+ (1-(v-mnc*.98)/((mxc-mnc)*1.3+.01))*(h-botY-16);
 s.appendChild(T(pl,botY-2,"Cancel rate / tháng",{fs:8.5,fill:C.ink2}));
 let cp="";cm.forEach((r,i)=>cp+=(i?"L":"M")+cx(i)+" "+cy(r.v));
 s.appendChild(E("path",{d:cp,fill:"none",stroke:C.red,"stroke-width":2}));
 cm.forEach((r,i)=>{const c=E("circle",{cx:cx(i),cy:cy(r.v),r:3,fill:C.red});s.appendChild(c);s.appendChild(T(cx(i),cy(r.v)-6,r.v+"%",{fs:8,anc:"middle",fill:C.ink2}));s.appendChild(T(cx(i),h-4,r.k,{fs:8,anc:"middle"}));});})();

// City risk bubble (lat/lng schematic) sized orders, colored cancel
(function(){const d=PD.city,w=330,h=150;const s=mk("c_cityrisk",w,h);if(!s)return;
 const lats=d.map(c=>c.lat),lngs=d.map(c=>c.lng);const la0=Math.min(...lats),la1=Math.max(...lats),lo0=Math.min(...lngs),lo1=Math.max(...lngs);
 const X=lo=>30+(lo-lo0)/((lo1-lo0)||1)*(w-70),Y=la=>24+(la1-la)/((la1-la0)||1)*(h-54);
 const mxo=Math.max(...d.map(c=>c.orders));const col=c=>c.cancel_rate>=6?C.red:c.cancel_rate>=4?C.amber:C.green;
 d.forEach(c=>{const r=8+Math.sqrt(c.orders/mxo)*22;const cc=E("circle",{cx:X(c.lng),cy:Y(c.lat),r,fill:col(c),"fill-opacity":.45,stroke:col(c),"stroke-width":1.5});s.appendChild(cc);
   hov(cc,`<b>${c.city} (${c.state})</b><br>${nk(c.orders)} đơn · GMV ${brl(c.gmv)}<br>AOV ${brl(c.aov)} · hủy ${c.cancel_rate}%`);
   s.appendChild(T(X(c.lng),Y(c.lat)+3,c.state,{fs:9,anc:"middle",fill:C.lab,fw:700}));});})();

// Segment mix ribbon (stacked area share by month)
(function(){const w=330,h=150,pl=8,pr=8,pt=14;const pb2=18;const s=mk("c_segmix",w,h);if(!s)return;
 const months=[1,2,3,4];const get=(m,sg)=>{const r=PD.seg_month.find(x=>x.month==m&&x.segment==sg);return r?r.orders:0;};
 const xs=i=>pl+i/(months.length-1)*(w-pl-pr);const yb=h-pb2;
 // GOOD share area (violet) on top of FOOD (blue) — 100% stacked
 const goodShare=months.map(m=>{const g=get(m,"GOOD"),f=get(m,"FOOD");return g/(g+f);});
 const yGood=sh=>pt+sh*(yb-pt); // from top
 s.appendChild(E("rect",{x:pl,y:pt,width:w-pl-pr,height:yb-pt,fill:"rgba(61,139,255,.16)"}));
 let gp="M"+pl+" "+pt;months.forEach((m,i)=>gp+="L"+xs(i)+" "+yGood(goodShare[i]));gp+="L"+xs(months.length-1)+" "+pt+"Z";
 s.appendChild(E("path",{d:gp,fill:"rgba(136,120,255,.55)"}));
 let ln="";months.forEach((m,i)=>ln+=(i?"L":"M")+xs(i)+" "+yGood(goodShare[i]));
 s.appendChild(E("path",{d:ln,fill:"none",stroke:C.violet,"stroke-width":2}));
 months.forEach((m,i)=>{s.appendChild(T(xs(i),h-4,"T"+m,{fs:8.5,anc:"middle"}));
   const hit=E("rect",{x:xs(i)-10,y:pt,width:20,height:yb-pt,fill:"transparent"});hov(hit,`<b>Tháng ${m}</b><br>GOOD ${(goodShare[i]*100).toFixed(1)}% đơn<br>FOOD ${((1-goodShare[i])*100).toFixed(1)}%`);s.appendChild(hit);});
 s.appendChild(T(pl,10,"GOOD ↑ từ 5%→14% share đơn",{fs:8.5,fill:C.violet}));})();

/* ---------- P2 ---------- */
(function(){const d=PD.weekly,w=330,h=150,pl=34,pr=10,pt=12,pb=20;const s=mk("c_ordtrend",w,h);if(!s)return;
 const mx=Math.max(...d.map(r=>r.orders)),xs=i=>pl+i/(d.length-1)*(w-pl-pr),ys=v=>pt+(1-v/mx)*(h-pt-pb);
 for(let g=0;g<=2;g++){const y=pt+g/2*(h-pt-pb);s.appendChild(E("line",{x1:pl,x2:w-pr,y1:y,y2:y,stroke:C.grid}));s.appendChild(T(2,y+3,nk(mx*(1-g/2)),{fs:8}));}
 let p="";d.forEach((r,i)=>p+=(i?"L":"M")+xs(i)+" "+ys(r.orders));
 s.appendChild(E("path",{d:p,fill:"none",stroke:C.blue,"stroke-width":2.2}));
 d.forEach((r,i)=>{if(i%3==0)s.appendChild(T(xs(i),h-6,r.week.slice(5),{fs:7.5,anc:"middle"}));});})();

// lollipop top channels
(function(){const d=PD.top_channels.slice(0,7),w=330,rowh=17,h=d.length*rowh+16,pl=88,pr=44;const s=mk("c_channels",w,h);if(!s)return;
 const mx=Math.max(...d.map(x=>x.gmv));
 d.forEach((x,i)=>{const y=12+i*rowh,xv=pl+(x.gmv/mx)*(w-pl-pr),col=x.type=="MARKETPLACE"?C.blue:C.violet;
  s.appendChild(T(pl-6,y+3,x.channel.replace(" PLACE",""),{fs:9.5,anc:"end",fill:C.ink2}));
  s.appendChild(E("line",{x1:pl,y1:y,x2:xv,y2:y,stroke:col,"stroke-width":2}));
  const c=E("circle",{cx:xv,cy:y,r:4.5,fill:col});s.appendChild(c);hov(c,`<b>${x.channel}</b> (${x.type})<br>GMV ${brl(x.gmv)} · ${nk(x.orders)} đơn`);
  s.appendChild(T(xv+7,y+3,brl(x.gmv),{fs:8.5,fill:C.ink2}));});})();

// payment donut
(function(){const d=PD.payment,w=330,h=150;const s=mk("c_payment",w,h);if(!s)return;
 const tot=d.reduce((a,r)=>a+r.orders,0),cx=72,cy=74,r=50,ir=30;let a0=-Math.PI/2;
 const cols=[C.blue,C.teal,C.violet,C.amber,C.green,C.red,C.ink3];
 d.forEach((r_,i)=>{const ang=r_.orders/tot*2*Math.PI,a1=a0+ang,lg=ang>Math.PI?1:0;
  const p=`M${cx+r*Math.cos(a0)} ${cy+r*Math.sin(a0)}A${r} ${r} 0 ${lg} 1 ${cx+r*Math.cos(a1)} ${cy+r*Math.sin(a1)}L${cx+ir*Math.cos(a1)} ${cy+ir*Math.sin(a1)}A${ir} ${ir} 0 ${lg} 0 ${cx+ir*Math.cos(a0)} ${cy+ir*Math.sin(a0)}Z`;
  const path=E("path",{d:p,fill:cols[i]});s.appendChild(path);hov(path,`<b>${r_.method}</b><br>${r_.share}% · ${nk(r_.orders)} đơn`);a0=a1;});
 s.appendChild(T(cx,cy-1,d[0].share+"%",{fs:15,anc:"middle",fill:C.markOn,fw:800}));s.appendChild(T(cx,cy+13,"ONLINE",{fs:9,anc:"middle"}));
 d.slice(0,5).forEach((r_,i)=>{s.appendChild(E("rect",{x:150,y:34+i*20,width:9,height:9,rx:2,fill:cols[i]}));s.appendChild(T(164,42+i*20,r_.method+" "+r_.share+"%",{fs:9.5,fill:C.ink2}));});})();

// AOV histogram
(function(){const d=PD.aov_hist,w=560,h=150,pl=30,pr=8,pt=10,pb=26;const s=mk("c_aov",w,h);if(!s)return;
 const mx=Math.max(...d.map(r=>r.orders)),bw=(w-pl-pr)/d.length*.74;
 d.forEach((r,i)=>{const x=pl+(i+.5)/d.length*(w-pl-pr)-bw/2,bh=r.orders/mx*(h-pt-pb);
  const rc=E("rect",{x,y:h-pb-bh,width:bw,height:bh,rx:3,fill:C.blue});s.appendChild(rc);hov(rc,`<b>R$${r.bucket}</b><br>${nk(r.orders)} đơn`);
  s.appendChild(T(x+bw/2,h-14,r.bucket,{fs:8,anc:"middle",fill:C.ink3}));});
 s.appendChild(T(pl,h-2,"Giá trị đơn (R$) — median R$"+PD.exec_kpi.aov,{fs:8.5,fill:C.ink3}));})();

// heatmap dow x hour
(function(){const box=byId("c_heat");if(!box)return;const dows=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
 const mx=Math.max(...PD.heatmap.map(r=>r.orders)),g=(d,h)=>{const r=PD.heatmap.find(x=>x.dow==d&&x.hour==h);return r?r.orders:0;};
 let html='<div style="display:grid;grid-template-columns:30px repeat(24,1fr);gap:2px">';
 dows.forEach(d=>{html+=`<div style="font-size:9px;color:var(--ink3);display:flex;align-items:center">${d}</div>`;
   for(let h=0;h<24;h++){const v=g(d,h),t=v/mx;html+=`<div title="${d} ${h}h — ${v} đơn" style="aspect-ratio:1;border-radius:2px;background:rgba(${C.heat},${(.06+t*.94).toFixed(2)})"></div>`;}});
 html+='</div><div style="font-size:9.5px;color:var(--ink3);margin-top:5px">Đậm = nhiều đơn · trục ngang 0→23h · đỉnh 12h &amp; 19–20h</div>';box.innerHTML=html;})();

/* ---------- P3 ---------- */
byId("cycleKpi").textContent=PD.cycle_pct.p50+"′";
byId("p90Kpi").textContent=PD.cycle_pct.p90+"′";
byId("distKpi").textContent=PD.exec_kpi.median_km+"km";
byId("succKpi").textContent=PD.delivery_success.delivery_level+"%";

// scatter distance vs cycle
(function(){const d=PD.scatter,w=560,h=170,pl=34,pr=10,pt=10,pb=26;const s=mk("c_scatter",w,h);if(!s)return;
 const xmax=Math.max(...d.map(p=>p.dist)),ymax=Math.max(...d.map(p=>p.cycle));
 const X=v=>pl+v/xmax*(w-pl-pr),Y=v=>pt+(1-v/ymax)*(h-pt-pb);
 for(let g=0;g<=3;g++){const y=pt+g/3*(h-pt-pb);s.appendChild(E("line",{x1:pl,x2:w-pr,y1:y,y2:y,stroke:C.grid}));s.appendChild(T(2,y+3,Math.round(ymax*(1-g/3))+"′",{fs:8}));}
 d.forEach(p=>{s.appendChild(E("circle",{cx:X(p.dist),cy:Y(p.cycle),r:2.4,fill:p.seg=="GOOD"?C.violet:C.blue,"fill-opacity":.5}));});
 // trend hint: weak
 s.appendChild(T(w-pr,h-14,"Khoảng cách (km) →",{fs:8.5,anc:"end",fill:C.ink3}));
 byId("scatterNote").innerHTML=`Tương quan cự ly ↔ thời gian giao chỉ <b style="color:#8fbaff">r=${PD.corr.dist_cycle}</b> → quãng đường giải thích &lt;8% biến thiên. <b>Nút thắt là thời gian chuẩn bị, không phải khoảng cách.</b>`;})();

// boxplot cycle by modal
(function(){const d=PD.cycle_box_modal,w=330,h=170,pl=54,pr=14,pt=12,pb=20;const s=mk("c_box",w,h);if(!s)return;
 const all=d.flatMap(b=>[b.min,b.p95]);const mx=Math.max(...d.map(b=>b.p95)),mn=0;
 const Y=v=>pt+(1-(v-mn)/(mx-mn))*(h-pt-pb);const bw=40;
 d.forEach((b,i)=>{const x=pl+(i+.5)/d.length*(w-pl-pr),col=i==0?C.blue:C.teal;
  s.appendChild(E("line",{x1:x,y1:Y(b.min),x2:x,y2:Y(b.p95),stroke:col,"stroke-width":1.5}));
  s.appendChild(E("line",{x1:x-8,y1:Y(b.min),x2:x+8,y2:Y(b.min),stroke:col}));
  s.appendChild(E("line",{x1:x-8,y1:Y(b.p95),x2:x+8,y2:Y(b.p95),stroke:col}));
  const rc=E("rect",{x:x-bw/2,y:Y(b.q3),width:bw,height:Y(b.q1)-Y(b.q3),rx:3,fill:col,"fill-opacity":.28,stroke:col});s.appendChild(rc);
  s.appendChild(E("line",{x1:x-bw/2,y1:Y(b.med),x2:x+bw/2,y2:Y(b.med),stroke:C.strong,"stroke-width":2}));
  hov(rc,`<b>${b.modal}</b><br>median ${b.med}′ · Q1 ${b.q1}′ · Q3 ${b.q3}′<br>p95 ${b.p95}′`);
  s.appendChild(T(x,h-5,b.modal,{fs:9,anc:"middle",fill:C.ink2}));
  s.appendChild(T(x+bw/2+4,Y(b.med)+3,b.med+"′",{fs:8,fill:C.lab}));});
 for(let g=0;g<=3;g++){const v=mx*g/3;s.appendChild(T(2,Y(v)+3,Math.round(v)+"′",{fs:8}));}})();

// funnel stage bar
(function(){const d=PD.funnel_stage,w=330,h=120,pl=110,pr=44;const s=mk("c_funnel",w,h);if(!s)return;
 const mx=Math.max(...d.map(r=>r.median_min));const rowh=30;
 d.forEach((r,i)=>{const y=24+i*rowh,bw=(r.median_min/mx)*(w-pl-pr);
  s.appendChild(T(pl-6,y+4,r.stage,{fs:9.5,anc:"end",fill:C.ink2}));
  const rc=E("rect",{x:pl,y:y-8,width:bw,height:16,rx:4,fill:i==0?C.amber:C.teal});s.appendChild(rc);hov(rc,`<b>${r.stage}</b><br>median ${r.median_min}′`);
  s.appendChild(T(pl+bw+6,y+4,r.median_min+"′",{fs:9,fill:C.lab}));});
 s.appendChild(T(pl,h-6,"Median cycle tổng "+PD.cycle_pct.p50+"′ — phần còn lại là hàng chờ/queue",{fs:8.5,fill:C.ink3}));})();

// modal split donut small
(function(){const d=PD.driver_modal,w=330,h=90;const s=mk("c_modalsplit",w,h);if(!s)return;
 let x=10;const tot=d.reduce((a,r)=>a+r.deliveries,0);
 d.forEach((r,i)=>{const bw=(r.deliveries/tot)*(w-20);const rc=E("rect",{x,y:20,width:bw-2,height:20,rx:4,fill:i==0?C.teal:C.blue});s.appendChild(rc);
  hov(rc,`<b>${r.modal}</b><br>${r.share}% lượt · median ${r.median_km}km`);
  s.appendChild(T(x+3,34,r.modal+" "+r.share+"%",{fs:9,fill:C.markOn}));x+=bw;});
 s.appendChild(T(10,58,"Motoboy giao xa hơn Biker ~2.5× (2.62 vs 1.03 km)",{fs:9,fill:C.ink2}));
 s.appendChild(T(10,74,PD.driver_prod.active+" tài xế active · median "+PD.driver_prod.median+" đơn/tài xế",{fs:9,fill:C.ink3}));})();

/* ---------- P4 ---------- */
// hub bubble map
(function(){const d=PD.hub,w=560,h=210,pl=8;const s=mk("c_hubmap",w,h);if(!s)return;
 const lats=d.map(c=>c.lat),lngs=d.map(c=>c.lng),la0=Math.min(...lats),la1=Math.max(...lats),lo0=Math.min(...lngs),lo1=Math.max(...lngs);
 const X=lo=>34+(lo-lo0)/((lo1-lo0)||1)*(w-70),Y=la=>20+(la1-la)/((la1-la0)||1)*(h-46);
 const mxo=Math.max(...d.map(c=>c.orders));const col=c=>c.cancel_rate>=8?C.red:c.cancel_rate>=4.6?C.amber:C.green;
 d.forEach(c=>{const r=5+Math.sqrt(c.orders/mxo)*20;const cc=E("circle",{cx:X(c.lng),cy:Y(c.lat),r,fill:col(c),"fill-opacity":.4,stroke:col(c),"stroke-width":1.3});s.appendChild(cc);
   hov(cc,`<b>${c.hub} — ${c.city}</b><br>${nk(c.orders)} đơn · GMV ${brl(c.gmv)}<br>hủy ${c.cancel_rate}% · cycle ${c.cycle_med}′`);});
 // label 4 city clusters
 const cities={};d.forEach(c=>{cities[c.city]=cities[c.city]||[];cities[c.city].push(c);});
 Object.keys(cities).forEach(cn=>{const g=cities[cn];const mlo=g.reduce((a,c)=>a+c.lng,0)/g.length,mla=g.reduce((a,c)=>a+c.lat,0)/g.length;s.appendChild(T(X(mlo),Y(mla)-24,cn.replace(" DE JANEIRO"," RJ"),{fs:8.5,anc:"middle",fill:C.ink2,fw:700}));});})();

// hub cancel ranked bar (top 10)
(function(){const d=[...PD.hub].sort((a,b)=>b.cancel_rate-a.cancel_rate).slice(0,10),w=330,rowh=16,h=d.length*rowh+22,pl=74,pr=38;const s=mk("c_hubcancel",w,h);if(!s)return;
 const mx=Math.max(...d.map(x=>x.cancel_rate));const med=PD.exec_kpi.cancel_rate;
 d.forEach((x,i)=>{const y=10+i*rowh,bw=(x.cancel_rate/mx)*(w-pl-pr),col=x.cancel_rate>=8?C.red:x.cancel_rate>=5?C.amber:C.teal;
  s.appendChild(T(pl-5,y+4,x.hub.slice(0,10),{fs:9,anc:"end",fill:C.ink2}));
  const rc=E("rect",{x:pl,y:y-1,width:bw,height:10,rx:3,fill:col});s.appendChild(rc);hov(rc,`<b>${x.hub} (${x.city})</b><br>hủy ${x.cancel_rate}% · ${nk(x.orders)} đơn`);
  s.appendChild(T(pl+bw+5,y+4,x.cancel_rate+"%",{fs:8.5,fill:C.lab}));});
 const mx2=Math.max(...d.map(x=>x.cancel_rate));const xm=pl+(med/mx2)*(w-pl-pr);
 s.appendChild(E("line",{x1:xm,y1:6,x2:xm,y2:h-14,stroke:C.ink3,"stroke-dasharray":"3 3"}));
 s.appendChild(T(pl,h-3,"Đường đứt = TB toàn hệ thống "+med+"% · ELIXIR gấp ~6.7×",{fs:8,fill:C.ink3}));})();

// city bars
(function(){const d=PD.city,w=330,rowh=26,h=d.length*rowh+10,pl=88,pr=52;const s=mk("c_citybars",w,h);if(!s)return;
 const mx=Math.max(...d.map(x=>x.gmv)),tot=d.reduce((a,x)=>a+x.gmv,0);
 d.forEach((x,i)=>{const y=10+i*rowh,bw=(x.gmv/mx)*(w-pl-pr);
  s.appendChild(T(pl-5,y+4,x.city.replace(" DE JANEIRO"," RJ").slice(0,11),{fs:9.5,anc:"end",fill:C.ink2}));
  const rc=E("rect",{x:pl,y:y-6,width:bw,height:14,rx:4,fill:C.teal});s.appendChild(rc);hov(rc,`<b>${x.city}</b><br>GMV ${brl(x.gmv)} (${(x.gmv/tot*100).toFixed(0)}%)<br>${nk(x.orders)} đơn · AOV ${brl(x.aov)}`);
  s.appendChild(T(pl+bw+5,y+4,(x.gmv/tot*100).toFixed(0)+"%",{fs:9,fill:C.lab}));});})();

// hub quadrant scatter: orders (x) vs cancel_rate (y), size=gmv, color band
(function(){const d=PD.hub,w=330,h=150,pl=34,pr=12,pt=12,pb=24;const s=mk("c_hubquad",w,h);if(!s)return;
 const omax=Math.max(...d.map(x=>x.orders)),cmax=Math.max(...d.map(x=>x.cancel_rate))*1.1,gmax=Math.max(...d.map(x=>x.gmv));
 const omed=[...d.map(x=>x.orders)].sort((a,b)=>a-b)[Math.floor(d.length/2)];const csys=PD.exec_kpi.cancel_rate;
 const X=v=>pl+v/omax*(w-pl-pr),Y=v=>pt+(1-v/cmax)*(h-pt-pb);
 // quadrant guides
 s.appendChild(E("line",{x1:X(omed),y1:pt,x2:X(omed),y2:h-pb,stroke:C.grid,"stroke-dasharray":"3 3"}));
 s.appendChild(E("line",{x1:pl,y1:Y(csys),x2:w-pr,y2:Y(csys),stroke:C.grid,"stroke-dasharray":"3 3"}));
 for(let g=0;g<=2;g++){const v=cmax*g/2;s.appendChild(T(2,Y(v)+3,v.toFixed(0)+"%",{fs:8}));}
 d.forEach(x=>{const r=4+Math.sqrt(x.gmv/gmax)*14;const danger=x.orders>=omed&&x.cancel_rate>csys;
  const col=x.cancel_rate>=8?C.red:x.cancel_rate>=csys?C.amber:C.green;
  const c=E("circle",{cx:X(x.orders),cy:Y(x.cancel_rate),r,fill:col,"fill-opacity":danger?.7:.4,stroke:col,"stroke-width":danger?1.6:1});s.appendChild(c);
  hov(c,`<b>${x.hub} — ${x.city}</b><br>${nk(x.orders)} đơn · GMV ${brl(x.gmv)}<br>hủy ${x.cancel_rate}% · cycle ${x.cycle_med}′`);});
 s.appendChild(T(w-pr,h-12,"số đơn →",{fs:8,anc:"end",fill:C.ink3}));
 s.appendChild(T(X(omed)+3,pt+8,"vol cao + hủy cao",{fs:7.5,fill:C.riskink||C.red}));})();

// calendar heatmap (daily)
(function(){const box=byId("c_calendar");if(!box)return;const d=PD.calendar;
 const mx=Math.max(...d.map(x=>x.orders));const map={};d.forEach(x=>map[x.date]=x.orders);
 const start=new Date("2021-01-01"),end=new Date("2021-04-30");
 // build weeks columns
 let html='<div style="display:flex;gap:2px;overflow-x:auto">';let cur=new Date(start);
 // align to Monday
 const wd=(cur.getDay()+6)%7;cur.setDate(cur.getDate()-wd);
 while(cur<=end){html+='<div style="display:grid;grid-template-rows:repeat(7,1fr);gap:2px">';
   for(let r=0;r<7;r++){const ds=cur.toISOString().slice(0,10);const v=map[ds]||0;const inr=cur>=start&&cur<=end;
     const t=v/mx;html+=`<div title="${ds} — ${v} đơn" style="width:9px;height:9px;border-radius:2px;background:${inr?`rgba(${C.cal},${(.08+t*.92).toFixed(2)})`:"transparent"}"></div>`;
     cur.setDate(cur.getDate()+1);}
   html+='</div>';}
 html+='</div><div style="font-size:9.5px;color:var(--ink3);margin-top:5px">Mỗi ô = 1 ngày (cột = tuần) · đậm = tải cao · đỉnh cuối T3</div>';box.innerHTML=html;})();

/* ---------- P5 ---------- */
// pareto
(function(){const d=PD.pareto,w=330,h=150,pl=30,pr=10,pt=10,pb=22;const s=mk("c_pareto",w,h);if(!s)return;
 const X=v=>pl+v/100*(w-pl-pr),Y=v=>pt+(1-v/100)*(h-pt-pb);
 s.appendChild(E("line",{x1:X(0),y1:Y(80),x2:X(100),y2:Y(80),stroke:C.grid,"stroke-dasharray":"3 3"}));
 let p="";d.forEach((r,i)=>p+=(i?"L":"M")+X(r.store_pct)+" "+Y(r.gmv_pct));
 s.appendChild(E("path",{d:p,fill:"none",stroke:C.blue,"stroke-width":2.5}));
 const st=PD.pareto_stat,xx=X(st.stores_80/st.n*100);
 s.appendChild(E("line",{x1:xx,y1:Y(0),x2:xx,y2:Y(80),stroke:C.amber,"stroke-dasharray":"3 3"}));
 s.appendChild(T(X(48),Y(20),`${(st.stores_80/st.n*100).toFixed(0)}% cửa hàng → 80% GMV`,{fs:9,anc:"middle",fill:C.ink2}));
 s.appendChild(T(4,Y(80)-2,"80%",{fs:8}));s.appendChild(T(X(50),h-5,"% cửa hàng (xếp theo GMV) →",{fs:8,anc:"middle",fill:C.ink3}));})();

// matrix 2x2 partner priority
(function(){const d=PD.store_quadrant,w=330,h=170,pl=40,pr=12,pt=12,pb=26;const s=mk("c_matrix",w,h);if(!s)return;
 const mg=PD.store_med_gmv,mc=PD.store_med_cancel;const gmax=Math.max(...d.map(x=>x.gmv)),cmax=Math.max(...d.map(x=>x.cancel_rate));
 const X=v=>pl+Math.min(v/gmax,1)*(w-pl-pr),Y=v=>pt+(1-Math.min(v/cmax,1))*(h-pt-pb);
 // quadrant lines
 s.appendChild(E("line",{x1:X(mg),y1:pt,x2:X(mg),y2:h-pb,stroke:C.grid}));s.appendChild(E("line",{x1:pl,y1:Y(mc),x2:w-pr,y2:Y(mc),stroke:C.grid}));
 d.forEach(x=>{const good=x.cancel_rate<=mc;const c=E("circle",{cx:X(x.gmv),cy:Y(x.cancel_rate),r:3+Math.sqrt(x.orders)/22,fill:x.gmv>=mg&&x.cancel_rate>mc?C.red:(x.gmv>=mg?C.green:C.ink3),"fill-opacity":.5});s.appendChild(c);
   hov(c,`<b>${x.store}</b> (${x.seg})<br>GMV ${brl(x.gmv)} · hủy ${x.cancel_rate}% · ${nk(x.orders)} đơn`);});
 s.appendChild(T(w-pr,Y(mc)-4,"↑ hủy cao + GMV cao = ƯU TIÊN SỬA",{fs:8,anc:"end",fill:"#ff8ea4"}));
 s.appendChild(T(pl,h-4,"GMV cửa hàng →",{fs:8,fill:C.ink3}));s.appendChild(T(4,pt+6,"hủy%",{fs:8}));})();

// store table
(function(){const box=byId("c_storetable");if(!box)return;const d=PD.store_top.slice(0,8);
 let h='<table class="dtbl"><thead><tr><th>Store</th><th>Seg</th><th class="num">GMV</th><th class="num">Đơn</th><th class="num">Hủy%</th></tr></thead><tbody>';
 d.forEach(x=>{h+=`<tr><td>${x.store.slice(0,16)}</td><td>${x.seg}</td><td class="num">${brl(x.gmv)}</td><td class="num">${nk(x.orders)}</td><td class="num" style="color:${x.cancel_rate>8?'#ff8ea4':'var(--ink)'}">${x.cancel_rate}</td></tr>`;});
 h+='</tbody></table>';box.innerHTML=h;})();

// store bubble aov vs cancel
(function(){const d=PD.store_quadrant,w=560,h=180,pl=40,pr=12,pt=10,pb=26;const s=mk("c_storebubble",w,h);if(!s)return;
 const ax=d.map(x=>x.aov),cx=d.map(x=>x.cancel_rate);const amax=Math.min(Math.max(...ax),600),cmax=Math.min(Math.max(...cx),40);
 const X=v=>pl+Math.min(v,amax)/amax*(w-pl-pr),Y=v=>pt+(1-Math.min(v,cmax)/cmax)*(h-pt-pb);
 for(let g=0;g<=3;g++){const y=pt+g/3*(h-pt-pb);s.appendChild(E("line",{x1:pl,x2:w-pr,y1:y,y2:y,stroke:C.grid}));s.appendChild(T(2,y+3,Math.round(cmax*(1-g/3))+"%",{fs:8}));}
 d.forEach(x=>{const c=E("circle",{cx:X(x.aov),cy:Y(x.cancel_rate),r:3+Math.sqrt(x.orders)/24,fill:x.seg=="GOOD"?C.violet:C.blue,"fill-opacity":.45});s.appendChild(c);
   hov(c,`<b>${x.store}</b> (${x.seg})<br>AOV ${brl(x.aov)} · hủy ${x.cancel_rate}%`);});
 s.appendChild(T(w-pr,h-12,"AOV (R$) →",{fs:8.5,anc:"end",fill:C.ink3}));s.appendChild(T(4,pt+4,"hủy%",{fs:8}));
 s.appendChild(T(pl+6,pt+10,"● FOOD  ● GOOD",{fs:9,fill:C.ink2}));})();

// 100% stacked bar: segment mix by channel_type
(function(){const d=PD.chan_seg_flow,w=560,h=150,pl=96,pr=54,pt=16,pb=16;const s=mk("c_chanseg",w,h);if(!s)return;
 const froms=["MARKETPLACE","OWN CHANNEL"];const tc={FOOD:C.teal,GOOD:C.amber};const rowh=40;
 froms.forEach((f,i)=>{const rows=d.filter(x=>x.from==f);const tot=rows.reduce((a,x)=>a+x.orders,0);
  const y=pt+i*(rowh+18);let x=pl;
  s.appendChild(T(pl-6,y+rowh/2+3,f.replace(" CHANNEL",""),{fs:10,anc:"end",fill:C.ink2,fw:600}));
  ["FOOD","GOOD"].forEach(sg=>{const r=rows.find(z=>z.to==sg);const v=r?r.orders:0;const bw=v/tot*(w-pl-pr);
    const rc=E("rect",{x,y,width:Math.max(bw-2,0),height:rowh,rx:4,fill:tc[sg]});s.appendChild(rc);
    hov(rc,`<b>${f} · ${sg}</b><br>${nk(v)} đơn (${(v/tot*100).toFixed(1)}%)`);
    if(bw>34)s.appendChild(T(x+bw/2,y+rowh/2+4,(v/tot*100).toFixed(0)+"%",{fs:11,anc:"middle",fill:C.markOn,fw:700}));
    x+=bw;});
  s.appendChild(T(w-pr+6,y+rowh/2+3,nk(tot)+" đơn",{fs:9,fill:C.ink3}));});
 s.appendChild(T(pl,h-2,"● FOOD",{fs:9.5,fill:C.teal}));s.appendChild(T(pl+58,h-2,"● GOOD",{fs:9.5,fill:C.amber}));
 s.appendChild(T(pl+130,h-2,"Own channel nghiêng GOOD hơn Marketplace",{fs:8.5,fill:C.ink3}));})();

/* ---------- P6 ---------- */
// decomposition tree (static): total -> segment -> channel_type
(function(){const box=byId("c_decomp");if(!box)return;const base=PD.exec_kpi.cancel_rate;
 const seg=PD.cancel_by.segment,ch=PD.cancel_by.channel_type;
 let h=`<div style="font-size:11px;margin-top:6px"><div style="display:flex;align-items:center;gap:8px">
   <div style="background:var(--calbg);border:1px solid var(--calborder);border-radius:8px;padding:6px 9px"><div style="color:var(--ink3);font-size:9px">Cancel rate</div><b style="font-size:15px">${base}%</b></div>
   <div style="color:var(--ink3)">▸ theo Segment</div>
   <div style="display:grid;gap:4px">`;
 seg.forEach(sg=>{const col=sg.v>8?'#ff8ea4':'#8fbaff';h+=`<div style="border:1px solid var(--line);border-radius:7px;padding:3px 8px;background:var(--panel2)"><span style="color:var(--ink2)">${sg.k}</span> <b style="color:${col}">${sg.v}%</b></div>`;});
 h+=`</div><div style="color:var(--ink3)">▸ theo Kênh</div><div style="display:grid;gap:4px">`;
 ch.forEach(c=>{h+=`<div style="border:1px solid var(--line);border-radius:7px;padding:3px 8px;background:var(--panel2)"><span style="color:var(--ink2)">${c.k=="MARKETPLACE"?"Marketplace":"Own"}</span> <b>${c.v}%</b></div>`;});
 h+=`</div></div><div style="color:var(--ink3);font-size:10px;margin-top:8px">GOOD segment là nhánh đóng góp hủy lớn nhất (${seg.find(x=>x.k=='GOOD').v}%).</div>`;box.innerHTML=h;})();

// key influencers (bars of cancel rate by factor)
(function(){const box=byId("c_infl");if(!box)return;const base=PD.exec_kpi.cancel_rate;
 const items=[["Segment = GOOD",PD.cancel_by.segment.find(x=>x.k=="GOOD").v],
   ["Tháng 4 (T4)",PD.cancel_by.month.find(x=>x.k=="T4").v],
   ["Own channel",PD.cancel_by.channel_type.find(x=>x.k=="OWN CHANNEL").v],
   ["Marketplace",PD.cancel_by.channel_type.find(x=>x.k=="MARKETPLACE").v],
   ["Segment = FOOD",PD.cancel_by.segment.find(x=>x.k=="FOOD").v]].sort((a,b)=>b[1]-a[1]);
 const w=330,rowh=22,h=items.length*rowh+8,pl=118,pr=34;const s=mk("c_infl",w,h);
 const mx=Math.max(...items.map(x=>x[1]));
 items.forEach((x,i)=>{const y=10+i*rowh,bw=(x[1]/mx)*(w-pl-pr),col=x[1]>base*1.3?C.red:x[1]<base*.9?C.green:C.amber;
   s.appendChild(T(pl-5,y+4,x[0],{fs:9,anc:"end",fill:C.ink2}));
   const rc=E("rect",{x:pl,y:y-2,width:bw,height:12,rx:3,fill:col});s.appendChild(rc);hov(rc,`<b>${x[0]}</b><br>cancel ${x[1]}% (TB ${base}%)`);
   s.appendChild(T(pl+bw+5,y+4,x[1]+"%",{fs:9,fill:C.lab}));});
 const xm=pl+(base/mx)*(w-pl-pr);s.appendChild(E("line",{x1:xm,y1:4,x2:xm,y2:h-4,stroke:C.ink3,"stroke-dasharray":"3 3"}));})();

// what-if simulator
function renderWhatIf(pct){const e=PD.delivery_econ;const box=byId("c_whatif");if(!box)return;
 const ordersFin=PD.exec_kpi.finished;const subsidyFull=e.mean_cost-0; // if free, fee=0 => subsidy=full cost
 const currentFree=e.free_ship/100; // baseline
 // model: monthly subsidy = orders * (freePct * cost + (1-freePct)*max(cost-fee,0))
 const p=pct/100;const est=ordersFin*(p*e.mean_cost+(1-p)*Math.max(e.mean_cost-e.mean_fee,0));
 const baseEst=ordersFin*(currentFree*e.mean_cost+(1-currentFree)*Math.max(e.mean_cost-e.mean_fee,0));
 const w=330,h=70;box.innerHTML="";const s=mk("c_whatif",w,h);
 s.appendChild(T(8,20,"Ước tính chi phí bù giao (4 tháng):",{fs:9.5,fill:C.ink2}));
 s.appendChild(T(8,44,brl(est),{fs:20,fill:C.strong,fw:800}));
 const delta=est-baseEst;s.appendChild(T(150,44,(delta>=0?"+":"")+brl(delta)+" vs hiện tại",{fs:10,fill:delta>0?"#ff8ea4":"#5ee39a"}));
 s.appendChild(T(8,62,"Giả định: free→bù đủ chi phí R$"+e.mean_cost+"; có phí→bù R$"+(e.mean_cost-e.mean_fee).toFixed(2),{fs:8.5,fill:C.ink3}));}
byId("wiSlider").addEventListener("input",e=>{byId("wiVal").textContent=e.target.value+"%";renderWhatIf(+e.target.value);});
renderWhatIf(36);

// anomaly register table
(function(){const box=byId("c_anomaly");if(!box)return;const q=PD.quality;
 const rows=[["Extreme order amount (>p99.9)",q.flag_extreme_amount,"amount tối đa R$1.79M"],
   ["Extreme distance (>50km)",q.flag_extreme_distance,"tối đa 7,251 km"],
   ["Long cycle (>24h)",q.flag_long_cycle,"tối đa ~107 ngày"],
   ["Zero amount",q.flag_zero_amount,"đơn R$0"],
   ["No payment record",q.orders_no_payment,"coverage gap"],
   ["No delivery record",q.orders_no_delivery,"coverage gap"],
   ["Delivery thiếu driver",q.null_driver,"4.2% lượt giao"]];
 let h='<table class="dtbl"><thead><tr><th>Loại bất thường</th><th class="num">Số dòng</th><th>Ghi chú</th></tr></thead><tbody>';
 rows.forEach(r=>{h+=`<tr><td>${r[0]}</td><td class="num">${nk(r[1])}</td><td style="color:var(--ink3)">${r[2]}</td></tr>`;});
 h+='</tbody></table>';box.innerHTML=h;})();

byId("auditBullets").innerHTML=[
 `0 trùng khóa chính, 0 FK mồ côi ở các join lõi.`,
 `${PD.quality.flag_extreme_amount} đơn amount + ${PD.quality.flag_extreme_distance} lượt distance bất thường được <b>gắn cờ, không xóa</b>.`,
 `Doanh thu = SUM(order_amount) lọc FINISHED — KHÔNG dùng payments (tránh double-count R$37.3M).`,
 `Ranking hub/store áp ngưỡng min-volume (hub≥${PD.meta.min_vol_hub}, store≥${PD.meta.min_vol_store} đơn).`,
 `Giới hạn: không có customer_id (❌ retention/LTV) · chỉ 4 tháng (❌ YoY) · giờ UTC−3 là giả định.`
].map(x=>`<li>${x}</li>`).join("");

/* ---------- P7 Recommendations ---------- */
(function(){const r=PD.reco;
 byId("recoStrip").innerHTML=[
  ["GMV có thể cứu",brl(r.good_recoverable_gmv),"nếu kéo hủy GOOD về mức FOOD (4 tháng)"],
  ["Đang bù lỗ giao",brl(r.subsidy_total),`${r.free_ship_pct}% đơn free-ship · R$1.36/đơn`],
  ["Phụ thuộc 1 kênh",r.top_channel_share+"%","GMV từ FOOD PLACE"]
 ].map(x=>`<div class="reco-hero"><div class="l">${x[0]}</div><div class="n">${x[1]}</div><div class="s">${x[2]}</div></div>`).join("");
 const recos=[
  {p:1,t:"Giảm hủy đơn GOOD trước khi mở rộng",ev:`GOOD hủy <b>${r.good_cr}%</b> vs FOOD ${r.food_cr}% → <b>${brl(r.good_cancel_gmv)}</b> GMV bị hủy (${nk(r.good_cancel_orders)} đơn)`,ac:"Điều tra nguyên nhân hủy GOOD (tồn kho / thời gian giao) rồi mới scale",big:brl(r.good_recoverable_gmv),cap:"GMV cứu được",tag:"hy",tagt:"Nguyên nhân: giả thuyết"},
  {p:2,t:"Đặt ngưỡng free-ship theo AOV & khoảng cách",ev:`Bù lỗ <b>${brl(r.subsidy_total)}</b>/4 tháng · ${r.free_ship_pct}% đơn free-ship · 53% đơn phí < chi phí`,ac:"Dùng what-if (P6) mô phỏng ngưỡng thay vì free-ship đại trà",big:brl(r.subsidy_total),cap:"chi phí/4 tháng",tag:"pv",tagt:"Chứng minh"},
  {p:3,t:"Giảm phụ thuộc kênh & kéo giỏ giá trị cao về kênh riêng",ev:`1 kênh = <b>${r.top_channel_share}%</b> GMV · kênh riêng AOV <b>R$${r.own_aov}</b> vs marketplace R$${r.mkt_aov}`,ac:"Giữ volume marketplace, migrate đơn giá trị cao sang kênh riêng",big:"R$"+r.own_aov,cap:"AOV kênh riêng",tag:"hy",tagt:"Thiệt hại: cần data hoa hồng"},
  {p:4,t:`Audit vận hành 3 hub lệch chuẩn (dẫn đầu ${r.elixir_hub})`,ev:`${r.elixir_hub} hủy <b>${r.elixir_cr}%</b> = gấp ~${(r.elixir_cr/r.sys_cr).toFixed(1)}× TB hệ thống (${r.sys_cr}%), dù ≥500 đơn`,ac:"Audit khu trú theo hub (shipper/đối tác), không dùng chính sách toàn hệ thống",big:r.elixir_cr+"%",cap:r.elixir_hub+" cancel",tag:"pv",tagt:"Chứng minh"},
  {p:5,t:"Rút ngắn giao hàng nhắm khâu CHUẨN BỊ, không phải quãng đường",ev:`Cự ly↔thời gian chỉ <b>r=${r.corr}</b> · production ${r.prod_min}′ nhưng cycle tổng ${r.cycle_med}′ (phần lớn là hàng chờ)`,ac:"Cải thiện dự báo & gán shipper sớm; đừng đầu tư tối ưu tuyến đường",big:"r="+r.corr,cap:"cự ly↔cycle",tag:"pv",tagt:"Chứng minh (phản trực giác)"}
 ];
 byId("recoList").innerHTML=recos.map(x=>`<div class="reco-card p${x.p}c">
   <div class="reco-num">${x.p}</div>
   <div class="reco-main"><h4>${x.t}</h4><div class="ev">${x.ev}</div><div class="ac">${x.ac}</div></div>
   <div class="reco-side"><div class="big">${x.big}</div><div class="cap">${x.cap}</div><span class="pill ${x.tag}">${x.tagt}</span></div>
 </div>`).join("");})();

/* ---------- shell interactions ---------- */
const pageNames={p1:"Page 1 — Executive Overview",p2:"Page 2 — Order & Revenue Analysis",p3:"Page 3 — Delivery Performance",p4:"Page 4 — Hub & Geographic Performance",p5:"Page 5 — Store & Partner Performance",p6:"Page 6 — Insight Lab (deep-dive)",p7:"Page 7 — Khuyến nghị & Hành động"};
const subNames={p1:"Ban điều hành · sức khỏe GMV & rủi ro tập trung",p2:"Xu hướng đơn – doanh thu – kênh – thanh toán – cao điểm",p3:"SLA giao hàng · cự ly · đội xe · nút thắt thời gian",p4:"Hub Manager · bản đồ & benchmark hiệu suất vùng",p5:"Store/Partner Manager · đóng góp & rủi ro đối tác",p6:"Deep-dive · decomposition · what-if · anomaly",p7:"5 khuyến nghị ưu tiên · số liệu chứng minh · phân biệt proven vs giả thuyết"};
const stack=["p1"];
function setPage(id,push=true){document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));
 document.querySelectorAll(".nav").forEach(b=>b.classList.toggle("active",b.dataset.page===id));
 byId("ttl").textContent=pageNames[id];byId("sub").textContent=subNames[id];
 if(push&&stack[stack.length-1]!==id)stack.push(id);window.scrollTo({top:0,behavior:"instant"});}
document.querySelectorAll(".nav").forEach(b=>b.addEventListener("click",()=>setPage(b.dataset.page)));
byId("homeBtn").addEventListener("click",()=>setPage("p1"));
byId("backBtn").addEventListener("click",()=>{if(stack.length>1){stack.pop();setPage(stack[stack.length-1],false);}});
byId("toggleFilter").addEventListener("click",()=>byId("drawer").classList.toggle("open"));
const baseChips='<span class="chip">City: All (4)</span><span class="chip">Segment: All</span><span class="chip">Channel: All</span><span class="chip">Period: 01 Jan–30 Apr 2021</span><span class="chip">TZ: UTC−3 (assumed)</span>';
byId("selectedFilters").innerHTML=baseChips;
const sel={City:new Set(),Segment:new Set(),Channel:new Set()};
function refreshChips(){let c=`<span class="chip">City: ${sel.City.size?[...sel.City].join(", "):"All (4)"}</span><span class="chip">Segment: ${sel.Segment.size?[...sel.Segment].join(", "):"All"}</span><span class="chip">Channel: ${sel.Channel.size?[...sel.Channel].join(", "):"All"}</span><span class="chip">Period: 01 Jan–30 Apr 2021</span><span class="chip">TZ: UTC−3</span>`;byId("selectedFilters").innerHTML=c;}
document.querySelectorAll(".drawer .box[data-f]").forEach(b=>b.addEventListener("click",()=>{const f=b.dataset.f,v=b.dataset.v;if(sel[f].has(v)){sel[f].delete(v);b.classList.remove("sel");}else{sel[f].add(v);b.classList.add("sel");}refreshChips();}));
byId("resetBtn").addEventListener("click",()=>{Object.values(sel).forEach(s=>s.clear());document.querySelectorAll(".drawer .box.sel").forEach(b=>b.classList.remove("sel"));byId("selectedFilters").innerHTML=baseChips;});
document.querySelectorAll(".q,.tag,.status").forEach(n=>{n.setAttribute("data-tip",n.textContent.trim());n.addEventListener("mousemove",e=>{tip.style.display="block";tip.style.left=(e.clientX+12)+"px";tip.style.top=(e.clientY+12)+"px";tip.textContent=n.getAttribute("data-tip");});n.addEventListener("mouseleave",()=>tip.style.display="none");});
document.querySelectorAll(".drill").forEach(d=>d.addEventListener("click",()=>{byId("modalTitle").textContent=d.dataset.drill;byId("modal").classList.add("open");}));
byId("closeModal").addEventListener("click",()=>byId("modal").classList.remove("open"));
byId("modal").addEventListener("click",e=>{if(e.target.id==="modal")byId("modal").classList.remove("open");});
const _h=(location.hash||"").replace("#","");setPage(pageNames[_h]?_h:"p1",false);
byId("foot").innerHTML=`<b>Design concept:</b> Neo-Logistics __THEME_LABEL__ (đô thị Brazil) · màu ngữ nghĩa cho trạng thái (green/amber/red) · dynamic title + nav + filter drawer bookmark + selected-filter summary + tooltip + drill-through + what-if. <b>Custom visual:</b> chỉ giữ 1 optional (Calendar Heatmap, P4) — Sankey đã thay bằng 100% stacked bar (native); fallback Calendar = matrix tuần×thứ.`;
</script></body></html>"""

def build(theme_root, c_palette, out_name, theme_label):
    css = theme_root + "\n" + CSS_STATIC
    out = SHELL.replace("__CSS__", css).replace("__PD__", PD_JS).replace("__C__", json.dumps(c_palette)).replace("__THEME_LABEL__", theme_label)
    open(os.path.join(DASH, out_name), "w").write(out)
    print(f"wrote dashboard/{out_name} ({len(out)} bytes)")

build(ROOT_DARK, C_DARK, "mockup.html", "Dark")
build(ROOT_LIGHT, C_LIGHT, "mockup_light.html", "Light")
