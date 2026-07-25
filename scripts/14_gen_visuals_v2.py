"""
14_gen_visuals_v2.py — Rebuild the Power BI report (PBIR) as 8 user-story pages.

Replaces the 7 generic pages authored by 11_gen_visuals.py. Each page = one user story from
reports/07_user_stories_insights.md: title states the story, KPI cards answer it, charts prove it,
and a textbox carries the finding + action + limitation so the page is self-explanatory offline.

Design rules applied:
  * min-volume ranking via measure guards ([Cancellation Rate (min 500 orders)]) — never raw ranking
  * Top-N via RANKX guard measures (empty categories auto-hide) — no fragile visual-level filters
  * SLA split FOOD vs GOOD (blended cycle-time KPI is invalid: P90 64.6' vs 947')
  * money-at-risk uses the outlier-safe measure (1 canceled order of R$1.79M = 51% of the raw figure)
  * every page carries the same 4 slicers (Date / City / Segment / Channel type) — turn on
    "Sync slicers" in Desktop to link them across pages
Run AFTER 13_extend_model.py. Idempotent: wipes definition/pages and rewrites it.
"""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(HERE, "..", "powerbi", "BrazilianDeliveryCenter.Report")
PAGES = os.path.join(RP, "definition", "pages")
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
PAGES_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"

W, H = 1280, 800
INK, MUT, MUT2 = "#0f1a30", "#4c587a", "#8b95ad"
RISK, GOOD = "#c11340", "#0b7a44"

# ------------------------------------------------------------------ model map
HOME = {}
for m in ["Total Orders", "Finished Orders", "Canceled Orders", "GMV", "AOV", "Median Order Value",
          "Cancellation Rate", "Fulfillment Rate", "Active Stores", "Median Cycle (min)", "P90 Cycle (min)",
          "P95 Cycle (min)", "Median Prep (min)", "Median Transit (min)", "Orders with valid cycle",
          "SLA Breach % (over 60min)", "Median Cycle FOOD (min)", "Median Cycle GOOD (min)",
          "P90 Cycle FOOD (min)", "P90 Cycle GOOD (min)", "Mean Delivery Fee", "Mean Delivery Cost",
          "Delivery Subsidy / Order", "Free-ship Order %", "GMV Concentration Top1 Channel %",
          "Canceled GMV (at risk)", "Canceled GMV % of GMV", "Canceled GMV (raw, incl. outliers)",
          "Delivery Fee (total)", "Delivery Cost (total)", "Delivery Margin", "Delivery Margin / Order",
          "Free-ship Margin", "Paid-ship Margin", "Free-ship Orders",
          "Cancellation Rate (min 500 orders)", "Cancellation Rate (min 100 orders)",
          "Median Prep (min 200 orders)", "GMV (Top 12 Brands)", "GMV (Top 10 Channels)",
          "GMV (Top 15 Stores)", "GMV Concentration Top1 Brand %", "GMV Share %", "Active Brands"]:
    HOME[m] = "fact_orders"
for m in ["Deliveries", "Delivered", "Delivery Success Rate", "Median Distance (km)", "Active Drivers",
          "P90 Distance (km)", "Deliveries per Driver (median)", "Failed Deliveries"]:
    HOME[m] = "fact_deliveries"
for m in ["Payments", "Chargeback Orders", "Chargeback Rate"]:
    HOME[m] = "fact_payments"


def M(prop):
    e = HOME[prop]
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": prop}},
            "queryRef": f"{e}.{prop}", "nativeQueryRef": prop}


def C(entity, prop, active=False):
    d = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
         "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if active:
        d["active"] = True
    return d


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def write(pid, name, obj):
    d = os.path.join(PAGES, pid, "visuals", name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "visual.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


Z = [3000]
LABELLED = {"barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart", "lineChart", "donutChart"}
MULTICOLOR = {"barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart"}


def viz(pid, name, vtype, x, y, w, h, roles, title=None, labels=None, legend=None):
    Z[0] += 10
    v = {"visualType": vtype,
         "query": {"queryState": {r: {"projections": p} for r, p in roles.items()}},
         "drillFilterOtherVisuals": True}
    if title is not None:
        v["visualContainerObjects"] = {"title": [{"properties": {"show": lit("true"), "text": lit(f"'{title}'")}}]}
    objects = {}
    if labels if labels is not None else (vtype in LABELLED):
        objects["labels"] = [{"properties": {"show": lit("true")}}]
    if vtype in MULTICOLOR and "Series" not in roles and len(roles.get("Y", [])) == 1:
        objects["dataPoint"] = [{"properties": {"showAllDataPoints": lit("true")}}]
    if legend is False:
        objects["legend"] = [{"properties": {"show": lit("false")}}]
    if objects:
        v["objects"] = objects
    write(pid, name, {"$schema": VC, "name": name,
                      "position": {"x": x, "y": y, "z": Z[0], "height": h, "width": w, "tabOrder": Z[0]},
                      "visual": v})


def card(pid, name, x, y, w, measure, label, h=86):
    viz(pid, name, "card", x, y, w, h, {"Values": [M(measure)]}, title=label)


def kpi_row(pid, items, y=168, x0=24, gap=8, w=None):
    n = len(items)
    w = w or int((1232 - gap * (n - 1)) / n)
    for i, (name, measure, label) in enumerate(items):
        card(pid, name, x0 + i * (w + gap), y, w, measure, label)


def textbox(pid, name, x, y, w, h, paragraphs, title=None):
    Z[0] += 10
    paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{sz}pt",
                                                      "fontWeight": "bold" if b else "normal", "color": c}}
                           for (t, sz, b, c) in runs]} for runs in paragraphs]
    v = {"visualType": "textbox",
         "objects": {"general": [{"properties": {"paragraphs": paras}}]},
         "visualContainerObjects": {"title": [{"properties": {"show": lit("true" if title else "false"),
                                                              **({"text": lit(f"'{title}'")} if title else {})}}]},
         "drillFilterOtherVisuals": True}
    write(pid, name, {"$schema": VC, "name": name,
                      "position": {"x": x, "y": y, "z": Z[0], "height": h, "width": w, "tabOrder": Z[0]},
                      "visual": v})


def slicer(pid, name, x, y, w, h, field):
    Z[0] += 10
    write(pid, name, {"$schema": VC, "name": name,
                      "position": {"x": x, "y": y, "z": Z[0], "height": h, "width": w, "tabOrder": Z[0]},
                      "visual": {"visualType": "slicer",
                                 "query": {"queryState": {"Values": {"projections": [field]}}},
                                 "drillFilterOtherVisuals": True}})


def page(pid, display, story, sub):
    """Page shell: navigator + title/user-story + the 4 shared slicers."""
    os.makedirs(os.path.join(PAGES, pid, "visuals"), exist_ok=True)
    with open(os.path.join(PAGES, pid, "page.json"), "w", encoding="utf-8") as f:
        json.dump({"$schema": PAGE_SCHEMA, "name": pid, "displayName": display,
                   "displayOption": "FitToPage", "height": H, "width": W}, f, indent=2, ensure_ascii=False)
    Z[0] += 10
    write(pid, "pageNav", {"$schema": VC, "name": "pageNav",
                           "position": {"x": 24, "y": 8, "z": 6000, "height": 34, "width": 1232, "tabOrder": -1000},
                           "visual": {"visualType": "pageNavigator", "drillFilterOtherVisuals": True}})
    textbox(pid, "title", 24, 42, 1232, 60,
            [[(display + "  —  ", 16, True, INK), (story, 11, False, MUT)], [(sub, 10, False, MUT2)]])
    slicer(pid, "slDate", 24, 106, 320, 52, C("dim_date", "Date"))
    slicer(pid, "slCity", 352, 106, 260, 52, C("dim_hub", "hub_city"))
    slicer(pid, "slSeg", 620, 106, 250, 52, C("dim_store", "store_segment"))
    slicer(pid, "slChan", 878, 106, 378, 52, C("dim_channel", "channel_type"))


# ======================================================================== reset
if os.path.isdir(PAGES):
    shutil.rmtree(PAGES)
os.makedirs(PAGES)

# ============================================================ P1 · US-1 Executive
page("p1", "1 · Executive Overview",
     "US-1: là ban điều hành, tôi cần thấy doanh thu phụ thuộc vào ai để biết rủi ro nào có thể đánh sập P&L.",
     "GMV = SUM(order_amount) trên đơn FINISHED · 01/01–30/04/2021 · giờ UTC−3 (giả định)")
kpi_row("p1", [("cGMV", "GMV", "GMV (Finished)"), ("cOrd", "Finished Orders", "Đơn hoàn tất"),
               ("cAOV", "AOV", "AOV"), ("cCanc", "Cancellation Rate", "Tỷ lệ hủy"),
               ("cRisk", "Canceled GMV % of GMV", "GMV rủi ro (đã lọc outlier)"),
               ("cBrand", "GMV Concentration Top1 Brand %", "Top-1 brand / GMV")])
viz("p1", "lineGMV", "lineChart", 24, 266, 620, 250,
    {"Category": [C("dim_date", "Date", True)], "Y": [M("GMV")]},
    "GMV theo ngày — tuần 26–30/04 chỉ có 5 ngày (kỳ chưa đủ)")
viz("p1", "barBrand", "barChart", 652, 266, 300, 250,
    {"Category": [C("dim_store", "brand")], "Y": [M("GMV (Top 12 Brands)")]},
    "Top 12 thương hiệu theo GMV")
viz("p1", "donutChan", "donutChart", 960, 266, 296, 250,
    {"Category": [C("dim_channel", "channel_type")], "Values": [M("GMV")]}, "GMV theo loại kênh")
viz("p1", "colCancMonth", "columnChart", 24, 524, 400, 254,
    {"Category": [C("dim_date", "Month", True)], "Y": [M("Cancellation Rate")]},
    "Tỷ lệ hủy theo tháng (4,35% → 5,03%)")
viz("p1", "colCityGMV", "columnChart", 432, 524, 400, 254,
    {"Category": [C("dim_hub", "hub_city")], "Y": [M("GMV")]}, "GMV theo thành phố")
textbox("p1", "insight", 840, 524, 416, 262, [
    [("Rủi ro tập trung lớn nhất: 1 thương hiệu = 34,5% GMV", 12, True, RISK)],
    [("IUMPICA (14 chi nhánh) = R$12,17M/R$35,29M. Top 3 brand = 46,3%; top 10 = 61,8%. "
      "Ở grain store_id con số này bị chia thành 14 dòng nên dashboard cũ không thấy.", 10, False, MUT)],
    [("Kênh: FOOD PLACE 68,2% GMV · own-channel AOV R$217,8 vs marketplace R$87,7.", 10, False, MUT)],
    [("Tăng trưởng là same-store: 411 store hoạt động cả 4 tháng = 86,1% GMV, +50,2% M1→M4; "
      "store mới chỉ góp 2,4–9,1%.", 10, False, MUT)],
    [("Hành động: account plan + điều khoản hợp đồng cho top-3 brand; theo dõi KPI Top-1 brand %.", 10, True, INK)],
    [("Giới hạn: tên store ẩn danh nên “cùng tên = cùng chuỗi” là giả định; không có hoa hồng "
      "marketplace nên chưa định lượng thiệt hại phụ thuộc kênh.", 9, False, MUT2)]])

# ============================================================ P2 · US-2 Demand
page("p2", "2 · Demand & Order Mix",
     "US-2: là ops planner, tôi cần biết cầu theo giờ/thứ và chất lượng đơn từng khung để xếp ca shipper.",
     "73,5% đơn nằm trong 7/24 giờ · đỉnh 12h (50.471 đơn) & 19h (49.000) · đáy 6h (151)")
kpi_row("p2", [("dOrd", "Total Orders", "Tổng đơn"), ("dFin", "Finished Orders", "Đơn hoàn tất"),
               ("dAOV", "AOV", "AOV"), ("dMed", "Median Order Value", "Median order value"),
               ("dPay", "Payments", "Bản ghi thanh toán"), ("dCb", "Chargeback Rate", "Chargeback rate")])
viz("p2", "colHour", "columnChart", 24, 266, 616, 250,
    {"Category": [C("fact_orders", "order_hour", True)], "Y": [M("Finished Orders")]},
    "Đơn hoàn tất theo giờ (giờ địa phương UTC−3)")
viz("p2", "lineCancHour", "lineChart", 648, 266, 300, 250,
    {"Category": [C("fact_orders", "order_hour", True)], "Y": [M("Cancellation Rate")]},
    "Tỷ lệ hủy theo giờ — đỉnh 31% lúc 4h")
viz("p2", "colDow", "columnChart", 956, 266, 300, 250,
    {"Category": [C("dim_date", "DayOfWeek", True)], "Y": [M("Finished Orders")]}, "Đơn theo thứ")
viz("p2", "colDaypart", "columnChart", 24, 524, 300, 254,
    {"Category": [C("fact_orders", "daypart")], "Y": [M("Finished Orders")]}, "Đơn theo daypart")
viz("p2", "colValueBand", "columnChart", 332, 524, 340, 254,
    {"Category": [C("fact_orders", "order_value_band")], "Y": [M("Finished Orders")]},
    "Phân bố giá trị đơn (median R$71,9 « AOV R$100,3)")
viz("p2", "donutPay", "donutChart", 680, 524, 280, 254,
    {"Category": [C("fact_payments", "payment_method")], "Values": [M("Payments")]},
    "Cơ cấu thanh toán (ONLINE 87,2%)")
textbox("p2", "insight", 968, 524, 288, 262, [
    [("Cầu lưỡng đỉnh nhọn + đơn đêm rất bẩn", 12, True, INK)],
    [("Trưa 11–13h = 32,7% đơn; tối 18–21h = 40,8% → 73,5% cầu trong 7 giờ. Tỷ lệ đỉnh/đáy 334×.", 10, False, MUT)],
    [("Đơn 0–9h: 4.391 đơn, hủy 18,9% (ban ngày 4,4%) = 4,9% toàn bộ số hủy.", 10, False, RISK)],
    [("Hành động: ca theo daypart; ép giờ mở cửa vào listing (quick win, không cần đầu tư).", 10, True, INK)],
    [("Giới hạn: múi giờ UTC−3 là giả định; không có giờ mở cửa store để chứng minh.", 9, False, MUT2)]])

# ============================================================ P3 · US-3 SLA
page("p3", "3 · Fulfilment SLA",
     "US-3: là delivery performance manager, tôi cần biết SLA thật và pha nào ăn thời gian để đầu tư đúng khâu.",
     "KPI cycle gộp FOOD+GOOD là VÔ NGHĨA: P90 FOOD 64,6′ vs GOOD 947′ (GOOD = bán lẻ giao theo hẹn)")
kpi_row("p3", [("sFoodMed", "Median Cycle FOOD (min)", "Median cycle · FOOD"),
               ("sFoodP90", "P90 Cycle FOOD (min)", "P90 cycle · FOOD"),
               ("sGoodMed", "Median Cycle GOOD (min)", "Median cycle · GOOD"),
               ("sGoodP90", "P90 Cycle GOOD (min)", "P90 cycle · GOOD"),
               ("sBreach", "SLA Breach % (over 60min)", "Đơn > 60′"),
               ("sDist", "Median Distance (km)", "Median distance")])
viz("p3", "colPhase", "clusteredColumnChart", 24, 266, 420, 250,
    {"Category": [C("dim_store", "store_segment")],
     "Y": [M("Median Prep (min)"), M("Median Transit (min)"), M("Median Cycle (min)")]},
    "Prep vs Transit vs Cycle theo segment (phút)")
viz("p3", "colCycleHist", "columnChart", 452, 266, 400, 250,
    {"Category": [C("fact_orders", "cycle_bucket")], "Y": [M("Finished Orders")]},
    "Phân bố cycle time (đơn)")
viz("p3", "scatHub", "scatterChart", 860, 266, 396, 250,
    {"Category": [C("dim_hub", "hub_name", True)], "X": [M("Median Distance (km)")],
     "Y": [M("Median Cycle (min)")], "Size": [M("Finished Orders")]},
    "Hub: cự ly × cycle (size = đơn)")
viz("p3", "colDistBand", "columnChart", 24, 524, 420, 254,
    {"Category": [C("fact_orders", "order_distance_band")], "Y": [M("Median Cycle (min)")]},
    "Median cycle theo dải cự ly (>10km bị GOOD giao-hẹn kéo lên 400′)")
viz("p3", "colModal", "columnChart", 452, 524, 400, 254,
    {"Category": [C("dim_driver", "driver_modal")], "Y": [M("Delivered")], "Series": [C("dim_driver", "driver_type")]},
    "Lượt giao theo modal × loại shipper")
textbox("p3", "insight", 860, 524, 396, 262, [
    [("Cự ly không quyết định thời gian — pha transit thì có", 12, True, INK)],
    [("Cùng frame (cycle ≤150′, dist ≤15km, n=316.560): r(distance)=0,23 (R² 5%) · r(prep)=0,48 (23%) · "
      "r(transit)=0,66 (R² 44%).", 10, False, MUT)],
    [("→ Nút thắt là chờ gán/đón shipper & tốc độ thực tế, KHÔNG phải chiều dài tuyến. "
      "Prep là khâu lớn thứ hai.", 10, False, MUT)],
    [("Cung shipper mỏng: top 10% shipper làm 55,6% lượt; 23,6% shipper <5 lượt; 69,8% freelance.", 10, False, RISK)],
    [("Giới hạn: thiếu mốc collected/walking (phần dư median 6,8′). P90 dùng cap 1440′ = 75,1′ "
      "(mockup cũ cap 180′ = 67,5′). Tương quan ≠ nhân quả.", 9, False, MUT2)]])

# ============================================================ P4 · US-4 Hub
page("p4", "4 · Hub Operations",
     "US-4: là hub manager, tôi cần benchmark hub theo hủy & cycle (đã chặn mẫu nhỏ) để audit đúng hub.",
     "Ranking áp min-volume ≥500 đơn: 26/32 hub đủ điều kiện, 6 hub bị loại khỏi xếp hạng")
kpi_row("p4", [("hOrd", "Total Orders", "Tổng đơn"), ("hCanc", "Cancellation Rate", "Tỷ lệ hủy"),
               ("hRisk", "Canceled GMV (at risk)", "GMV hủy (đã lọc outlier)"),
               ("hCyc", "Median Cycle FOOD (min)", "Median cycle · FOOD"),
               ("hSucc", "Delivery Success Rate", "Delivery success (lượt)"),
               ("hDrv", "Active Drivers", "Shipper active")])
viz("p4", "barHubCancel", "barChart", 24, 266, 620, 250,
    {"Category": [C("dim_hub", "hub_name")], "Y": [M("Cancellation Rate (min 500 orders)")]},
    "Tỷ lệ hủy theo hub (chỉ hub ≥500 đơn)")
viz("p4", "scatHubQuad", "scatterChart", 652, 266, 604, 250,
    {"Category": [C("dim_hub", "hub_name", True)], "X": [M("Finished Orders")],
     "Y": [M("Cancellation Rate (min 500 orders)")], "Size": [M("GMV")]},
    "Quadrant: khối lượng × hủy (size = GMV) — góc phải-trên = xử lý trước")
viz("p4", "tblHub", "tableEx", 24, 524, 828, 254,
    {"Values": [C("dim_hub", "hub_name"), C("dim_hub", "hub_city"), M("Total Orders"), M("GMV"),
                M("Cancellation Rate (min 500 orders)"), M("Median Cycle (min)"), M("Median Prep (min)")]},
    "Bảng hiệu suất hub")
textbox("p4", "insight", 860, 524, 396, 262, [
    [("ELIXIR SHOPPING: hủy 30,8% và median cycle 26 giờ", 12, True, RISK)],
    [("10.249 đơn (≥500) · hủy 30,82% (6,7× TB 4,6%) · median cycle 1.565′ · median prep 944′. "
      "Kế tiếp: STAR 9,25% · REACT 8,12% · RUBY 7,76%.", 10, False, MUT)],
    [("Giải thích mới: ELIXIR là hub GOOD-heavy → 26 giờ là bán lẻ giao hẹn, còn 30,8% hủy khớp bài toán "
      "GOOD×MARKETPLACE (trang 6). Không phải “hub vận hành tệ toàn diện”.", 10, False, MUT)],
    [("Hành động: audit ELIXIR theo góc tồn kho/độ sẵn có GOOD, không phải điều phối shipper.", 10, True, INK)],
    [("Giới hạn: 6 hub <500 đơn bị loại khỏi ranking (vd HUBLESS 60% hủy do 2 đơn).", 9, False, MUT2)]])

# ============================================================ P5 · US-5 Partner
page("p5", "5 · Partner & Brand",
     "US-5: là account manager, tôi cần xếp đối tác theo đóng góp × rủi ro để biết chăm ai và siết ai.",
     "294 store ≥100 đơn · ngưỡng median GMV R$34.211 · median hủy 3,44% · store_name KHÔNG phải khóa")
kpi_row("p5", [("pBrand", "Active Brands", "Thương hiệu active"), ("pStore", "Active Stores", "Store active"),
               ("pTop1", "GMV Concentration Top1 Brand %", "Top-1 brand / GMV"),
               ("pGMV", "GMV", "GMV"), ("pAOV", "AOV", "AOV"),
               ("pCanc", "Cancellation Rate", "Tỷ lệ hủy")])
viz("p5", "barBrand", "barChart", 24, 266, 500, 250,
    {"Category": [C("dim_store", "brand")], "Y": [M("GMV (Top 12 Brands)")]},
    "Top 12 thương hiệu (gộp chi nhánh cùng tên)")
viz("p5", "scatPartner", "scatterChart", 532, 266, 724, 250,
    {"Category": [C("dim_store", "store_label", True)], "X": [M("GMV")],
     "Y": [M("Cancellation Rate (min 100 orders)")], "Size": [M("Finished Orders")]},
    "Ma trận đối tác: GMV × hủy (store ≥100 đơn) — ô phải-trên = Fix-first")
viz("p5", "tblPlan", "tableEx", 24, 524, 500, 254,
    {"Values": [C("dim_store", "plan_tier"), M("Active Stores"), M("Finished Orders"), M("GMV"), M("AOV"),
                M("Cancellation Rate")]},
    "Gói thuê (store_plan_price) × giá trị mang lại")
viz("p5", "tblStore", "tableEx", 532, 524, 460, 254,
    {"Values": [C("dim_store", "store_label"), C("dim_store", "store_segment"), M("GMV"), M("Finished Orders"),
                M("Cancellation Rate (min 100 orders)")]},
    "Store (kèm store_id vì tên bị trùng)")
textbox("p5", "insight", 1000, 524, 256, 262, [
    [("Fix-first: 53 store = 17,8% GMV, hủy 9,8%", 11, True, RISK)],
    [("⭐ Star 94 store = 74,5% GMV, hủy 1,63% · 🔧 Fix-first 53 = 17,8%, hủy 9,77% · 🌱 Nurture 53 = 3,0% · "
      "👀 Review 94 = 4,7%, hủy 11,4%.", 9.5, False, MUT)],
    [("Gói thuê ngược với giá trị: 56 store gói R$0 = 34,1% GMV, hủy 2,33%; gói R$29,9 (99% đơn GOOD) "
      "hủy 12,87%.", 9.5, False, MUT)],
    [("Hành động: pricing theo GMV/đơn thay vì phí phẳng.", 9.5, True, INK)]])

# ============================================================ P6 · US-6 Cancellation
page("p6", "6 · Cancellation Root-cause",
     "US-6: là ops/commercial lead, tôi cần biết hủy tập trung ở tổ hợp nào để sửa đúng nguyên nhân.",
     "Hủy KHÔNG phải vấn đề “GOOD”: GOOD×MARKETPLACE 22,54% vs GOOD×OWN 4,76% (cùng loại hàng hoá)")
kpi_row("p6", [("xCanc", "Cancellation Rate", "Tỷ lệ hủy"), ("xOrd", "Canceled Orders", "Đơn hủy"),
               ("xRisk", "Canceled GMV (at risk)", "GMV hủy (lọc outlier)"),
               ("xPct", "Canceled GMV % of GMV", "% GMV rủi ro"),
               ("xRaw", "Canceled GMV (raw, incl. outliers)", "GMV hủy thô (audit)"),
               ("xFul", "Fulfillment Rate", "Fulfillment")])
viz("p6", "matSegChan", "pivotTable", 24, 266, 480, 250,
    {"Rows": [C("dim_store", "store_segment")], "Columns": [C("dim_channel", "channel_type")],
     "Values": [M("Cancellation Rate"), M("Total Orders")]},
    "Hủy theo Segment × Loại kênh (ô nóng: GOOD×MARKETPLACE)")
viz("p6", "colCancHour", "columnChart", 512, 266, 420, 250,
    {"Category": [C("fact_orders", "order_hour", True)], "Y": [M("Cancellation Rate")]},
    "Hủy theo giờ — 0–9h là 18,9%")
viz("p6", "colCancValue", "columnChart", 940, 266, 316, 250,
    {"Category": [C("fact_orders", "order_value_band")], "Y": [M("Cancellation Rate")]},
    "Hủy theo dải giá trị (hình chữ U)")
viz("p6", "lineCancMonth", "lineChart", 24, 524, 380, 254,
    {"Category": [C("dim_date", "Month", True)], "Y": [M("Cancellation Rate")]},
    "Hủy theo tháng — xu hướng xấu dần")
viz("p6", "barCancHub", "barChart", 412, 524, 380, 254,
    {"Category": [C("dim_hub", "hub_name")], "Y": [M("Canceled GMV (at risk)")]},
    "Tiền hủy theo hub (đã lọc outlier)")
textbox("p6", "insight", 800, 524, 456, 262, [
    [("Hủy là bài toán GOOD × MARKETPLACE, không phải “GOOD”", 12, True, RISK)],
    [("FOOD×MKT 3,34% (311.965 đơn) · FOOD×OWN 5,63% · GOOD×MKT 22,54% (21.200 đơn) · GOOD×OWN 4,76% "
      "(26.024 đơn). Cùng hàng hoá GOOD: qua marketplace hủy gấp 4,7× qua own channel.", 10, False, MUT)],
    [("Counterfactual: kéo GOOD về mức FOOD (3,41%) ⇒ ~4.409 đơn ⇒ ~R$969k GMV cứu được "
      "(giả định chuyển đổi tại AOV GOOD).", 10, False, MUT)],
    [("Hành động: sửa luồng marketplace cho hàng bán lẻ (đồng bộ tồn kho / độ sẵn có / thời gian phản hồi) "
      "trước khi scale GOOD.", 10, True, INK)],
    [("Giới hạn: KHÔNG có cancel_reason → nguyên nhân vẫn là giả thuyết; chỉ khẳng định vị trí tập trung.",
      9, False, MUT2)]])

# ============================================================ P7 · US-7 Economics
page("p7", "7 · Delivery Economics",
     "US-7: là finance/pricing lead, tôi cần biết giao hàng lỗ ở đâu theo giá trị × cự ly để đặt ngưỡng free-ship.",
     "Toàn bộ khoản lỗ nằm ở free-ship: −R$920k; đơn có thu phí LÃI +R$466k (+R$2,07/đơn)")
kpi_row("p7", [("eMar", "Delivery Margin", "Delivery margin (net)"),
               ("eFree", "Free-ship Margin", "Margin đơn free-ship"),
               ("ePaid", "Paid-ship Margin", "Margin đơn có phí"),
               ("ePer", "Delivery Margin / Order", "Margin / đơn"),
               ("eFreePct", "Free-ship Order %", "% đơn free-ship"),
               ("eSub", "Delivery Subsidy / Order", "Bù lỗ / đơn")])
viz("p7", "colMarDist", "columnChart", 24, 266, 616, 250,
    {"Category": [C("fact_orders", "order_distance_band")], "Y": [M("Delivery Margin")]},
    "Margin giao hàng theo dải cự ly — <2km hoà/lãi, 3–5km lỗ nặng nhất")
viz("p7", "colMarValue", "columnChart", 648, 266, 608, 250,
    {"Category": [C("fact_orders", "order_value_band")], "Y": [M("Delivery Margin")]},
    "Margin theo dải giá trị đơn — chỉ R$100–200 có lãi")
viz("p7", "colFeeCost", "clusteredColumnChart", 24, 524, 380, 254,
    {"Category": [C("dim_store", "store_segment")], "Y": [M("Mean Delivery Fee"), M("Mean Delivery Cost")]},
    "Phí thu vs chi phí theo segment (GOOD: 4,42 vs 9,37)")
viz("p7", "matPolicy", "pivotTable", 412, 524, 460, 254,
    {"Rows": [C("fact_orders", "order_value_band")], "Columns": [C("fact_orders", "order_distance_band")],
     "Values": [M("Delivery Margin")]},
    "Ma trận chính sách: margin theo giá trị × cự ly")
textbox("p7", "insight", 880, 524, 376, 262, [
    [("Ngưỡng free-ship đề xuất: đơn ≥ R$60 VÀ cự ly ≤ 2km", 12, True, GOOD)],
    [("Phí TB R$6,27 < chi phí R$7,58 ⇒ bù R$1,31/đơn (−R$454.555/4 tháng). Bóc tách: free-ship (35,05% đơn) "
      "lỗ R$920.272; đơn có phí lãi +R$465.717.", 10, False, MUT)],
    [("Theo cự ly: <1km +R$10,6k · 1–2km +R$2,6k · 2–3km −R$110k · 3–5km −R$164k · 5–10km −R$99k · "
      "10–50km −R$77k (chỉ 8.631 đơn, −R$9/đơn).", 10, False, MUT)],
    [("Theo giá trị: ≤R$30 −R$172k (56% free-ship) · R$30–60 −R$275k · R$100–200 +R$98k · >R$500 −R$14k "
      "(63% free-ship!). GOOD free-ship 61,8%.", 10, False, MUT)],
    [("Giới hạn: không có elasticity → phải A/B, không suy ra tác động volume từ dữ liệu; "
      "thiếu 1,7% bản ghi cost.", 9, False, MUT2)]])

# ============================================================ P8 · US-8 Data trust
page("p8", "8 · Data Trust & Actions",
     "US-8: là BI analyst, tôi cần biết mọi bẫy đo lường trước khi đưa lên C-level.",
     "12 bẫy đã xử lý trong model · 6 khuyến nghị ưu tiên · những gì dữ liệu KHÔNG trả lời được")
kpi_row("p8", [("tRisk", "Canceled GMV (at risk)", "GMV hủy (đã lọc)"),
               ("tRaw", "Canceled GMV (raw, incl. outliers)", "GMV hủy thô"),
               ("tCb", "Chargeback Rate", "Chargeback (426 đơn)"),
               ("tSucc", "Delivery Success Rate", "Delivery success (lượt)"),
               ("tFul", "Fulfillment Rate", "Fulfillment (đơn)"),
               ("tDlv", "Deliveries", "Lượt giao")])
viz("p8", "tblAnomaly", "tableEx", 24, 266, 620, 250,
    {"Values": [C("dim_store", "store_label"), C("dim_hub", "hub_name"),
                M("Canceled GMV (raw, incl. outliers)"), M("Canceled GMV (at risk)"), M("Canceled Orders")]},
    "Anomaly register — chênh lệch raw vs at-risk = outlier cần business xác nhận")
textbox("p8", "traps", 652, 266, 604, 250, [
    [("12 bẫy đo lường đã xử lý", 12, True, INK)],
    [("1 · 1 đơn hủy R$1.788.306 (GRIME CRU @ SAMPA) = 51% “tiền rủi ro” → measure at-risk loại "
      "flag_extreme_amount (>R$1.500) ⇒ R$1,62M = 4,58% GMV.", 9.5, False, MUT)],
    [("2 · store_name không phải khóa: 137 tên → tối đa 15 store_id ⇒ thêm grain brand + store_label.",
      9.5, False, MUT)],
    [("3 · Cycle FOOD vs GOOD là 2 quy trình (P90 64,6′ vs 947′; 87,3% đơn >180′ là GOOD) ⇒ card SLA tách segment.",
      9.5, False, MUT)],
    [("4 · P90 bất nhất: 67,5′ (cap 180′, mockup cũ) vs 75,1′ (cap 1440′, measure) ⇒ chuẩn hoá cap 1440′.",
      9.5, False, MUT)],
    [("5 · Tuần 26–30/04 chỉ 5 ngày ⇒ đánh dấu kỳ chưa đủ. 6 · 10.345 đơn không có bản ghi giao "
      "(2,8%) ⇒ success 98,03% (lượt) ≠ 95,4% (đơn).", 9.5, False, MUT)],
    [("7 · 18.665 đơn không có bản ghi thanh toán → any_chargeback NULL ≠ FALSE (chargeback thật 426 đơn = 0,12%). "
      "8 · 48.818 đơn tách thanh toán ⇒ không bao giờ SUM(payment_amount) làm doanh thu.", 9.5, False, MUT)],
    [("9 · Thiếu order_delivery_cost 6.000 (1,7%). 10 · Cycle >1440′: 7.469 đơn loại khỏi SLA. "
      "11 · 30 đơn FINISHED amount=0. 12 · Min-volume: hub ≥500 · store ≥100 bằng measure guard.",
      9.5, False, MUT)]])
textbox("p8", "actions", 24, 524, 1232, 262, [
    [("6 khuyến nghị ưu tiên (kèm bằng chứng · mức chắc chắn)", 12, True, INK)],
    [("1 · Sửa luồng GOOD trên marketplace trước khi scale GOOD — GOOD×MKT hủy 22,54% vs GOOD×OWN 4,76%; "
      "quy mô ~R$969k GMV. [Chứng minh: vị trí tập trung · Giả thuyết: nguyên nhân]", 10, False, MUT)],
    [("2 · Đặt ngưỡng free-ship: đơn ≥R$60 VÀ ≤2km; thu phí thực chi cho 10–50km và đơn >R$500 — "
      "free-ship lỗ R$920k, đơn có phí lãi R$466k. [Chứng minh · tác động volume cần A/B]", 10, False, MUT)],
    [("3 · Account plan cho top-3 brand (46,3% GMV) + KPI Top-1 brand % — IUMPICA 34,5% GMV/14 chi nhánh. "
      "[Chứng minh, với giả định cùng tên = cùng chuỗi]", 10, False, MUT)],
    [("4 · Audit ELIXIR SHOPPING theo góc tồn kho GOOD (hủy 30,8%, cycle 26h) thay vì điều phối shipper. "
      "[Chứng minh + giải thích mới]", 10, False, MUT)],
    [("5 · Rút ngắn giao hàng nhắm pha transit & chờ gán shipper (r=0,66; R² 44%) — KHÔNG tối ưu quãng đường "
      "(r=0,23). Giữ chân ~458 shipper nòng cốt (10% shipper = 55,6% lượt). [Chứng minh, phản trực giác]",
      10, False, MUT)],
    [("6 · Ép giờ mở cửa vào listing / auto-reject 0–9h — 4.391 đơn, hủy 18,9% (4,9% tổng số hủy). "
      "[Chứng minh tương quan; giả thuyết store đóng cửa]", 10, False, MUT)],
    [("KHÔNG trả lời được với dữ liệu này: lý do hủy (không có cancel_reason) · giữ chân/LTV "
      "(không có customer_id) · YoY (chỉ 4 tháng) · thiệt hại phụ thuộc kênh (không có hoa hồng) · "
      "elasticity free-ship · giờ mở cửa store.", 9.5, False, MUT2)]])

# ============================================================ pages.json
order = [f"p{i}" for i in range(1, 9)]
with open(os.path.join(PAGES, "pages.json"), "w", encoding="utf-8") as f:
    json.dump({"$schema": PAGES_SCHEMA, "pageOrder": order, "activePageName": "p1"}, f, indent=2)

total = 0
for pid in order:
    n = len(os.listdir(os.path.join(PAGES, pid, "visuals")))
    total += n
    print(f"  {pid}: {n} visuals")
print(f"8 pages · {total} visuals written")
