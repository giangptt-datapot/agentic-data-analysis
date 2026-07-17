"""
11_gen_visuals.py — Author visual.json for all 7 report pages (PBIR), bound to the
real semantic model measures/columns. Uses the exact visualContainer/2.4.0 format
verified against a working PBIP sample. Run AFTER 09_gen_powerbi.py.
"""
import os, json

RP = os.path.join(os.path.dirname(__file__), "..", "powerbi", "BrazilianDeliveryCenter.Report")
PAGES_DIR = os.path.join(RP, "definition", "pages")
VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json"

# measure -> home table entity
HOME = {}
for m in ["Total Orders","Finished Orders","Canceled Orders","GMV","AOV","Median Order Value",
          "Cancellation Rate","Fulfillment Rate","Active Stores","Median Cycle (min)","P90 Cycle (min)",
          "Mean Delivery Fee","Mean Delivery Cost","Delivery Subsidy / Order","Free-ship Order %",
          "GMV Concentration Top1 Channel %"]:
    HOME[m] = "fact_orders"
for m in ["Deliveries","Delivered","Delivery Success Rate","Median Distance (km)","Active Drivers"]:
    HOME[m] = "fact_deliveries"
for m in ["Payments","Chargeback Orders","Chargeback Rate"]:
    HOME[m] = "fact_payments"

def M(prop):  # measure projection
    e = HOME[prop]
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": prop}},
            "queryRef": f"{e}.{prop}", "nativeQueryRef": prop}

def COL(entity, prop, active=False):
    d = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
         "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if active: d["active"] = True
    return d

def AGG(entity, prop, func=0):
    fn = {0: "Sum", 1: "Avg", 2: "Min", 3: "Max", 4: "Count", 5: "CountNonNull"}[func]
    return {"field": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}, "Function": func}},
            "queryRef": f"{fn}({entity}.{prop})", "nativeQueryRef": f"{fn} of {prop}"}

def title_obj(text):
    return {"title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": f"'{text}'"}}}}}]}

def write_visual(pid, name, obj):
    d = os.path.join(PAGES_DIR, pid, "visuals", name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "visual.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

YOFF = 54  # push content down to make room for the top page-navigator menu
LABEL_TYPES = {"barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart", "lineChart"}
# single-series bar/column: color each category from the palette instead of all-one-color
MULTICOLOR_TYPES = {"barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart"}

def viz(pid, name, vtype, x, y, w, h, z, tab, roles, title=None, labels=None):
    qs = {r: {"projections": p} for r, p in roles.items()}
    v = {"visualType": vtype, "query": {"queryState": qs}, "drillFilterOtherVisuals": True}
    if title: v["visualContainerObjects"] = title_obj(title)
    objects = {}
    show = labels if labels is not None else (vtype in LABEL_TYPES)
    if show:
        objects["labels"] = [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}]
    # multi-color per category (only when no Series/Legend and a single Y measure)
    if vtype in MULTICOLOR_TYPES and "Series" not in roles and len(roles.get("Y", [])) == 1:
        objects["dataPoint"] = [{"properties": {"showAllDataPoints": {"expr": {"Literal": {"Value": "true"}}}}}]
    if objects:
        v["objects"] = objects
    write_visual(pid, name, {"$schema": VC_SCHEMA, "name": name,
        "position": {"x": x, "y": y + YOFF, "z": z, "height": h, "width": w, "tabOrder": tab},
        "visual": v})

def page_nav(pid):
    """Top page-navigator visual = menu + pagination across all pages."""
    write_visual(pid, "pageNav", {"$schema": VC_SCHEMA, "name": "pageNav",
        "position": {"x": 24, "y": 8, "z": 6000, "height": 40, "width": 1232, "tabOrder": -1000},
        "visual": {"visualType": "pageNavigator", "drillFilterOtherVisuals": True}})

def textbox(pid, name, x, y, w, h, z, tab, paragraphs):
    # paragraphs: list of list of (text, size_pt, bold, color)
    paras = []
    for runs in paragraphs:
        paras.append({"textRuns": [{"value": t, "textStyle": {"fontSize": f"{sz}pt", "fontWeight": ("bold" if b else "normal"), "color": c}} for (t, sz, b, c) in runs]})
    obj = {"$schema": VC_SCHEMA, "name": name,
           "position": {"x": x, "y": y + YOFF, "z": z, "height": h, "width": w, "tabOrder": tab},
           "visual": {"visualType": "textbox",
               "objects": {"general": [{"properties": {"paragraphs": paras}}]},
               "visualContainerObjects": {
                   "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]},
               "drillFilterOtherVisuals": True}}
    write_visual(pid, name, obj)

def card(pid, name, x, y, w, measure, label):
    viz(pid, name, "card", x, y, w, 88, 2000, 1000, {"Values": [M(measure)]}, title=label)

INK = "#0f1a30"; MUT = "#4c587a"
def head(pid, text, sub):
    page_nav(pid)  # top menu + pagination
    textbox(pid, "title", 24, 12, 1000, 48, 900, 0,
            [[(text, 20, True, INK)], [(sub, 10.5, False, MUT)]])

# ============================ P1 Executive ============================
head("p1", "Executive Overview", "GMV · orders · cancellation — sức khỏe kinh doanh tổng thể")
cards1 = [("cGMV","GMV","GMV (Finished)"),("cOrd","Finished Orders","Đơn hoàn tất"),
          ("cCanc","Cancellation Rate","Tỷ lệ hủy"),("cAOV","AOV","AOV"),
          ("cCyc","Median Cycle (min)","Median cycle (phút)"),("cStore","Active Stores","Cửa hàng active")]
for i,(n,m,l) in enumerate(cards1):
    card("p1", n, 24 + i*206, 66, 198, m, l)
viz("p1","lineGMV","lineChart",24,166,620,250,3000,2000,
    {"Category":[COL("dim_date","Date",True)],"Y":[M("GMV")]}, "GMV theo thời gian")
viz("p1","donutChan","donutChart",660,166,300,250,3010,2010,
    {"Category":[COL("dim_channel","channel_type")],"Values":[M("GMV")]}, "GMV theo loại kênh")
viz("p1","barCity","barChart",976,166,280,250,3020,2020,
    {"Category":[COL("dim_hub","hub_city")],"Y":[M("GMV")]}, "GMV theo thành phố")
viz("p1","colCancMonth","columnChart",24,430,620,268,3030,2030,
    {"Category":[COL("dim_date","Month",True)],"Y":[M("Cancellation Rate")]}, "Tỷ lệ hủy theo tháng")
viz("p1","colHour","columnChart",660,430,596,268,3040,2040,
    {"Category":[COL("fact_orders","order_hour",True)],"Y":[M("Finished Orders")]}, "Đơn theo giờ (giờ địa phương)")

# ============================ P2 Order & Revenue ============================
head("p2","Order & Revenue Analysis","Xu hướng đơn – doanh thu – kênh – thanh toán – cao điểm")
viz("p2","lineOrders","lineChart",24,66,620,250,3000,2000,
    {"Category":[COL("dim_date","Date",True)],"Y":[M("Finished Orders")]}, "Đơn hoàn tất theo thời gian")
viz("p2","barChannels","barChart",660,66,596,250,3010,2010,
    {"Category":[COL("dim_channel","channel_name")],"Y":[M("GMV")]}, "GMV theo kênh (Top)")
viz("p2","colHour2","columnChart",24,332,404,364,3020,2020,
    {"Category":[COL("fact_orders","order_hour",True)],"Y":[M("Finished Orders")]}, "Đơn theo giờ")
viz("p2","colDow","columnChart",448,332,404,364,3030,2030,
    {"Category":[COL("dim_date","DayOfWeek",True)],"Y":[M("Finished Orders")]}, "Đơn theo ngày trong tuần")
viz("p2","donutPay","donutChart",872,332,384,364,3040,2040,
    {"Category":[COL("fact_payments","payment_method")],"Values":[M("Payments")]}, "Cơ cấu thanh toán")

# ============================ P3 Delivery Performance ============================
head("p3","Delivery Performance","SLA giao hàng · cự ly · đội xe · nút thắt thời gian")
cards3 = [("dCyc","Median Cycle (min)","Median cycle"),("dP90","P90 Cycle (min)","P90 cycle"),
          ("dDist","Median Distance (km)","Median distance (km)"),("dSucc","Delivery Success Rate","Delivery success")]
for i,(n,m,l) in enumerate(cards3):
    card("p3", n, 24 + i*310, 66, 300, m, l)
viz("p3","colModal","columnChart",24,166,410,250,3000,2000,
    {"Category":[COL("dim_driver","driver_modal")],"Y":[M("Median Cycle (min)")]}, "Cycle time theo đội xe")
viz("p3","colStatus","columnChart",448,166,404,250,3010,2010,
    {"Category":[COL("fact_deliveries","delivery_status")],"Y":[M("Deliveries")]}, "Lượt giao theo trạng thái")
viz("p3","scatHub","scatterChart",872,166,384,250,3020,2020,
    {"Category":[COL("dim_hub","hub_name",True)],"X":[M("Median Distance (km)")],"Y":[M("Median Cycle (min)")],"Size":[M("Deliveries")]},
    "Cự ly vs Cycle time (theo hub)")
viz("p3","barHubCyc","barChart",24,430,1232,268,3030,2030,
    {"Category":[COL("dim_hub","hub_name")],"Y":[M("Median Cycle (min)")]}, "Median cycle theo hub")

# ============================ P4 Hub & Geographic ============================
head("p4","Hub & Geographic Performance","Hub nào khối lượng cao nhưng hiệu suất thấp?")
viz("p4","barHubCancel","barChart",24,66,620,320,3000,2000,
    {"Category":[COL("dim_hub","hub_name")],"Y":[M("Cancellation Rate")]}, "Tỷ lệ hủy theo hub (benchmark)")
viz("p4","scatHubQuad","scatterChart",660,66,596,320,3010,2010,
    {"Category":[COL("dim_hub","hub_name",True)],"X":[M("Finished Orders")],"Y":[M("Cancellation Rate")],"Size":[M("GMV")]},
    "Hub: Volume vs Cancel Rate")
viz("p4","colCityGMV","columnChart",24,400,404,298,3020,2020,
    {"Category":[COL("dim_hub","hub_city")],"Y":[M("GMV")]}, "GMV theo thành phố")
viz("p4","tblHub","tableEx",448,400,808,298,3030,2030,
    {"Values":[COL("dim_hub","hub_name"),M("Finished Orders"),M("GMV"),M("Cancellation Rate"),M("Median Cycle (min)")]},
    "Bảng hiệu suất hub")

# ============================ P5 Store & Partner ============================
head("p5","Store & Partner Performance","Đóng góp doanh thu vs rủi ro hủy của đối tác")
viz("p5","barTopStore","barChart",24,66,620,320,3000,2000,
    {"Category":[COL("dim_store","store_name")],"Y":[M("GMV")]}, "Top cửa hàng theo GMV")
viz("p5","scatPartner","scatterChart",660,66,596,320,3010,2010,
    {"Category":[COL("dim_store","store_name",True)],"X":[M("GMV")],"Y":[M("Cancellation Rate")],"Size":[M("Finished Orders")]},
    "Ma trận ưu tiên đối tác (GMV × Hủy)")
viz("p5","colSegCancel","columnChart",24,400,300,298,3020,2020,
    {"Category":[COL("dim_store","store_segment")],"Y":[M("Cancellation Rate")]}, "Tỷ lệ hủy theo segment")
viz("p5","donutSeg","donutChart",332,400,300,298,3030,2030,
    {"Category":[COL("dim_store","store_segment")],"Values":[M("GMV")]}, "GMV theo segment")
viz("p5","tblStore","tableEx",656,400,600,298,3040,2040,
    {"Values":[COL("dim_store","store_name"),M("GMV"),M("Finished Orders"),M("Cancellation Rate")]}, "Bảng cửa hàng")

# ============================ P6 Insight Lab ============================
head("p6","Insight Lab (deep-dive)","Bóc tách hủy · kinh tế giao hàng · rủi ro")
cards6 = [("iSub","Delivery Subsidy / Order","Bù lỗ giao/đơn"),("iFree","Free-ship Order %","% đơn free-ship"),
          ("iCb","Chargeback Rate","Chargeback rate")]
for i,(n,m,l) in enumerate(cards6):
    card("p6", n, 24 + i*410, 66, 400, m, l)
viz("p6","barCancSeg","clusteredBarChart",24,166,616,250,3000,2000,
    {"Category":[COL("dim_store","store_segment")],"Y":[M("Cancellation Rate")]}, "Hủy theo segment")
viz("p6","barCancChan","clusteredBarChart",660,166,596,250,3010,2010,
    {"Category":[COL("dim_channel","channel_type")],"Y":[M("Cancellation Rate")]}, "Hủy theo loại kênh")
viz("p6","colFeeCost","columnChart",24,430,616,268,3020,2020,
    {"Category":[COL("dim_store","store_segment")],"Y":[M("Mean Delivery Fee"),M("Mean Delivery Cost")]}, "Phí thu vs Chi phí giao")
viz("p6","colChanGMV","columnChart",660,430,596,268,3030,2030,
    {"Category":[COL("dim_channel","channel_type")],"Y":[M("AOV")]}, "AOV theo loại kênh")

# ============================ P7 Recommendations ============================
head("p7","Khuyến nghị & Hành động", "5 khuyến nghị ưu tiên · số liệu chứng minh")
c7 = [("rGMV","GMV","GMV (Finished)"),("rSub","Delivery Subsidy / Order","Bù lỗ giao/đơn"),
      ("rConc","GMV Concentration Top1 Channel %","Phụ thuộc kênh top-1")]
for i,(n,m,l) in enumerate(c7):
    card("p7", n, 24 + i*410, 66, 400, m, l)
recs = [
 [("1 · Giảm hủy đơn GOOD trước khi mở rộng", 13, True, INK)],
 [("GOOD hủy 12.7% vs FOOD 3.4% → ~R$1.32M GMV bị hủy; kéo về mức FOOD cứu ~R$0.97M. (Nguyên nhân: giả thuyết — thiếu cancel reason)", 11, False, MUT)],
 [("2 · Đặt ngưỡng free-ship theo AOV & khoảng cách", 13, True, INK)],
 [("Bù lỗ giao ~R$480k/4 tháng · 35.6% đơn free-ship · 53% đơn phí < chi phí. (Chứng minh)", 11, False, MUT)],
 [("3 · Giảm phụ thuộc kênh, kéo giỏ giá trị cao về kênh riêng", 13, True, INK)],
 [("1 kênh = 68% GMV; kênh riêng AOV R$218 vs marketplace R$88. (Thiệt hại: cần data hoa hồng)", 11, False, MUT)],
 [("4 · Audit vận hành 3 hub lệch chuẩn (ELIXIR 30.8%)", 13, True, INK)],
 [("ELIXIR hủy gấp ~6.7× TB hệ thống dù ≥500 đơn → audit khu trú. (Chứng minh)", 11, False, MUT)],
 [("5 · Rút ngắn giao hàng nhắm khâu CHUẨN BỊ, không phải quãng đường", 13, True, INK)],
 [("Cự ly↔thời gian chỉ r=0.25; production 15′ nhưng cycle 41′ (phần lớn là hàng chờ). (Chứng minh, phản trực giác)", 11, False, MUT)],
 [("Giới hạn: no customer_id (retention/LTV) · chỉ 4 tháng (YoY) · timezone giả định UTC−3.", 10, False, "#8b95ad")],
]
textbox("p7","recBody",24,170,1232,528,3000,2000,recs)

print("visuals written for 7 pages")
for pid in ["p1","p2","p3","p4","p5","p6","p7"]:
    n = len([d for d in os.listdir(os.path.join(PAGES_DIR,pid,"visuals"))]) if os.path.isdir(os.path.join(PAGES_DIR,pid,"visuals")) else 0
    print(f"  {pid}: {n} visuals")
