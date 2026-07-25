"""
13_extend_model.py — Extend the TMDL semantic model for the user-story dashboard v2.

Adds (idempotent — safe to re-run):
  * calculated columns: order_value_band / daypart (fact_orders), distance_band (fact_deliveries),
    brand (dim_store)  -> the grain that exposes the 34.5% single-brand concentration
  * measures v2: money-at-risk (outlier-safe), per-segment SLA, phase timings, delivery margin
    split free-ship vs paid-ship, min-volume ranking guards, Top-N guards, brand concentration.

Every DAX expression is single-line on purpose: multi-line TMDL measures previously broke the
`formatString` parse in Power BI Desktop.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, "..", "powerbi", "BrazilianDeliveryCenter.SemanticModel", "definition", "tables")

# --------------------------------------------------------------------- helpers
def insert_before_partition(path, block, marker):
    """Insert `block` just before the `partition` line, unless `marker` already present."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    if marker in src:
        print(f"  = {os.path.basename(path)}: already extended")
        return False
    m = re.search(r"^\tpartition ", src, re.M)
    if not m:
        raise SystemExit(f"no partition block in {path}")
    out = src[:m.start()] + block + src[m.start():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  + {os.path.basename(path)}: extended")
    return True


def col(name, dax, dtype, lineage, sort_by=None, fmt=None):
    s = f"\tcolumn {name} = {dax}\n\t\tdataType: {dtype}\n\t\tsummarizeBy: none\n"
    if fmt:
        s += f"\t\tformatString: {fmt}\n"
    if sort_by:
        s += f"\t\tsortByColumn: {sort_by}\n"
    s += f"\t\tlineageTag: {lineage}\n\n"
    return s


def mea(name, dax, fmt, desc=None):
    s = ""
    if desc:
        s += f"\t/// {desc}\n"
    s += f"\tmeasure '{name}' = {dax}\n\t\tformatString: {fmt}\n"
    return s


# =========================================================== fact_orders
VALID_CYCLE = ('fact_orders[order_status] = "FINISHED" && fact_orders[order_metric_cycle_time] > 0 '
               '&& fact_orders[order_metric_cycle_time] <= 1440')

fo = ""
# --- calculated columns (banding used by the demand / economics pages)
fo += col("order_value_band_no",
          'SWITCH(TRUE(), fact_orders[order_amount] <= 30, 1, fact_orders[order_amount] <= 60, 2, '
          'fact_orders[order_amount] <= 100, 3, fact_orders[order_amount] <= 200, 4, '
          'fact_orders[order_amount] <= 500, 5, 6)', "int64", "lt-fo-vbandno")
fo += col("order_value_band",
          'SWITCH(TRUE(), fact_orders[order_amount] <= 30, "≤R$30", fact_orders[order_amount] <= 60, "R$30–60", '
          'fact_orders[order_amount] <= 100, "R$60–100", fact_orders[order_amount] <= 200, "R$100–200", '
          'fact_orders[order_amount] <= 500, "R$200–500", ">R$500")', "string", "lt-fo-vband",
          sort_by="order_value_band_no")
fo += col("daypart_no",
          'SWITCH(TRUE(), fact_orders[order_hour] <= 9, 1, fact_orders[order_hour] <= 14, 2, '
          'fact_orders[order_hour] <= 17, 3, 4)', "int64", "lt-fo-dpno")
fo += col("daypart",
          'SWITCH(TRUE(), fact_orders[order_hour] <= 9, "1 Đêm/sáng (0–9h)", fact_orders[order_hour] <= 14, '
          '"2 Trưa (10–14h)", fact_orders[order_hour] <= 17, "3 Chiều (15–17h)", "4 Tối (18–23h)")',
          "string", "lt-fo-dp", sort_by="daypart_no")
fo += col("cycle_bucket_no",
          'IF(fact_orders[order_metric_cycle_time] > 0 && fact_orders[order_metric_cycle_time] <= 1440, '
          'SWITCH(TRUE(), fact_orders[order_metric_cycle_time] <= 30, 1, fact_orders[order_metric_cycle_time] <= 45, 2, '
          'fact_orders[order_metric_cycle_time] <= 60, 3, fact_orders[order_metric_cycle_time] <= 90, 4, '
          'fact_orders[order_metric_cycle_time] <= 180, 5, 6), BLANK())', "int64", "lt-fo-cbno")
fo += col("cycle_bucket",
          'SWITCH(fact_orders[cycle_bucket_no], 1, "<=30m", 2, "30-45m", 3, "45-60m", 4, "60-90m", 5, "90-180m", 6, ">180m")',
          "string", "lt-fo-cb", sort_by="cycle_bucket_no")

# --- measures v2
fo += "\n"
fo += mea("Canceled GMV (at risk)",
          'CALCULATE(SUM(fact_orders[order_amount]), fact_orders[order_status] = "CANCELED", fact_orders[flag_extreme_amount] = FALSE)',
          '"R$"#,0',
          'Giá trị đơn bị hủy, ĐÃ loại flag_extreme_amount (>R$1.500) — 1 đơn R$1,79M chiếm 51% nếu không loại')
fo += mea("Canceled GMV % of GMV", 'DIVIDE([Canceled GMV (at risk)], [GMV])', '0.00%')
fo += mea("Canceled GMV (raw, incl. outliers)",
          'CALCULATE(SUM(fact_orders[order_amount]), fact_orders[order_status] = "CANCELED")', '"R$"#,0',
          'Chỉ để đối chiếu/kiểm toán — KHÔNG dùng báo cáo')
fo += mea("P95 Cycle (min)",
          f'PERCENTILEX.INC(FILTER(fact_orders, {VALID_CYCLE}), fact_orders[order_metric_cycle_time], 0.95)', '#,0.0')
fo += mea("Median Prep (min)",
          f'MEDIANX(FILTER(fact_orders, {VALID_CYCLE} && NOT(ISBLANK(fact_orders[order_metric_production_time]))), fact_orders[order_metric_production_time])',
          '#,0.0')
fo += mea("Median Transit (min)",
          f'MEDIANX(FILTER(fact_orders, {VALID_CYCLE} && NOT(ISBLANK(fact_orders[order_metric_transit_time]))), fact_orders[order_metric_transit_time])',
          '#,0.0')
fo += mea("Orders with valid cycle", f'CALCULATE([Total Orders], FILTER(fact_orders, {VALID_CYCLE}))', '#,0')
fo += mea("SLA Breach % (over 60min)",
          f'DIVIDE(CALCULATE([Total Orders], FILTER(fact_orders, {VALID_CYCLE} && fact_orders[order_metric_cycle_time] > 60)), [Orders with valid cycle])',
          '0.0%', 'Tỷ lệ đơn hoàn tất có cycle > 60 phút (mẫu số = đơn có cycle hợp lệ)')
fo += mea("Median Cycle FOOD (min)",
          'CALCULATE([Median Cycle (min)], dim_store[store_segment] = "FOOD")', '#,0.0',
          'SLA chỉ có nghĩa khi tách segment: GOOD là bán lẻ giao theo hẹn (P90 ~947 phút)')
fo += mea("Median Cycle GOOD (min)", 'CALCULATE([Median Cycle (min)], dim_store[store_segment] = "GOOD")', '#,0.0')
fo += mea("P90 Cycle FOOD (min)", 'CALCULATE([P90 Cycle (min)], dim_store[store_segment] = "FOOD")', '#,0.0')
fo += mea("P90 Cycle GOOD (min)", 'CALCULATE([P90 Cycle (min)], dim_store[store_segment] = "GOOD")', '#,0.0')
# delivery economics
ECON = ('fact_orders[order_status] = "FINISHED", NOT(ISBLANK(fact_orders[order_delivery_cost]))')
fo += mea("Delivery Fee (total)", f'CALCULATE(SUM(fact_orders[order_delivery_fee]), {ECON})', '"R$"#,0')
fo += mea("Delivery Cost (total)", f'CALCULATE(SUM(fact_orders[order_delivery_cost]), {ECON})', '"R$"#,0')
fo += mea("Delivery Margin", '[Delivery Fee (total)] - [Delivery Cost (total)]', '"R$"#,0',
          'Âm = nền tảng bù lỗ giao hàng')
fo += mea("Delivery Margin / Order",
          f'DIVIDE([Delivery Margin], CALCULATE([Total Orders], {ECON}))', '"R$"#,0.00')
fo += mea("Free-ship Margin",
          f'CALCULATE([Delivery Margin], fact_orders[order_delivery_fee] = 0)', '"R$"#,0',
          'Toàn bộ khoản lỗ giao hàng nằm ở đây (−R$920k)')
fo += mea("Paid-ship Margin",
          f'CALCULATE([Delivery Margin], fact_orders[order_delivery_fee] > 0)', '"R$"#,0',
          'Đơn có thu phí giao thì CÓ LÃI (+R$466k)')
fo += mea("Free-ship Orders", f'CALCULATE([Finished Orders], fact_orders[order_delivery_fee] = 0)', '#,0')
# ranking guards (min-volume) + Top-N guards
fo += mea("Cancellation Rate (min 500 orders)",
          'IF([Total Orders] >= 500, [Cancellation Rate])', '0.00%',
          'Chặn mẫu nhỏ khi xếp hạng hub (vd HUBLESS 60% hủy do 2 đơn)')
fo += mea("Cancellation Rate (min 100 orders)", 'IF([Total Orders] >= 100, [Cancellation Rate])', '0.00%')
fo += mea("Median Prep (min 200 orders)", 'IF([Finished Orders] >= 200, [Median Prep (min)])', '#,0.0')
fo += mea("GMV (Top 12 Brands)",
          'IF(RANKX(ALLSELECTED(dim_store[brand]), [GMV], , DESC) <= 12, [GMV])', '"R$"#,0',
          'Top-N bằng measure guard (category rỗng tự ẩn) — không phụ thuộc visual-level filter')
fo += mea("GMV (Top 10 Channels)",
          'IF(RANKX(ALLSELECTED(dim_channel[channel_name]), [GMV], , DESC) <= 10, [GMV])', '"R$"#,0')
fo += mea("GMV (Top 15 Stores)",
          'IF(RANKX(ALLSELECTED(dim_store[store_label]), [GMV], , DESC) <= 15, [GMV])', '"R$"#,0')
fo += mea("GMV Concentration Top1 Brand %",
          'DIVIDE(MAXX(VALUES(dim_store[brand]), [GMV]), CALCULATE([GMV], ALL(dim_store)))', '0.0%',
          'IUMPICA = 34,5% GMV qua 14 chi nhánh — rủi ro tập trung lớn nhất')
fo += mea("GMV Share %", 'DIVIDE([GMV], CALCULATE([GMV], ALLSELECTED()))', '0.0%')
fo += mea("Active Brands", 'CALCULATE(DISTINCTCOUNT(dim_store[brand]), fact_orders[order_status] = "FINISHED")', '#,0')

insert_before_partition(os.path.join(T, "fact_orders.tmdl"), fo, "order_value_band_no")

# =========================================================== fact_deliveries
fd = ""
fd += col("distance_band_no",
          'IF(ISBLANK(fact_deliveries[delivery_distance_meters]), BLANK(), SWITCH(TRUE(), '
          'fact_deliveries[delivery_distance_meters] <= 1000, 1, fact_deliveries[delivery_distance_meters] <= 2000, 2, '
          'fact_deliveries[delivery_distance_meters] <= 3000, 3, fact_deliveries[delivery_distance_meters] <= 5000, 4, '
          'fact_deliveries[delivery_distance_meters] <= 10000, 5, 6))', "int64", "lt-fd-dbno")
fd += col("distance_band",
          'SWITCH(fact_deliveries[distance_band_no], 1, "<1 km", 2, "1–2 km", 3, "2–3 km", 4, "3–5 km", 5, "5–10 km", 6, ">10 km")',
          "string", "lt-fd-db", sort_by="distance_band_no")
fd += "\n"
fd += mea("P90 Distance (km)",
          'DIVIDE(PERCENTILEX.INC(FILTER(fact_deliveries, fact_deliveries[delivery_status] = "DELIVERED" && fact_deliveries[delivery_distance_meters] <= 50000), fact_deliveries[delivery_distance_meters], 0.9), 1000)',
          '#,0.00')
fd += mea("Deliveries per Driver (median)",
          'MEDIANX(VALUES(fact_deliveries[driver_id]), CALCULATE([Delivered]))', '#,0.0',
          'Median 20 lượt/shipper — nhưng top 10% shipper làm 55,6% lượt giao')
fd += mea("Failed Deliveries", 'CALCULATE([Deliveries], fact_deliveries[delivery_status] <> "DELIVERED")', '#,0')

insert_before_partition(os.path.join(T, "fact_deliveries.tmdl"), fd, "distance_band_no")

# =========================================================== dim_store (brand grain)
ds = ""
ds += col("brand", 'TRIM(dim_store[store_name])', "string", "lt-ds-brand",
          )
ds += col("store_label",
          'TRIM(dim_store[store_name]) & " #" & FORMAT(dim_store[store_id], "0")', "string", "lt-ds-slabel")
ds += col("plan_tier",
          'IF(ISBLANK(dim_store[store_plan_price]), "n/a", "R$" & FORMAT(dim_store[store_plan_price], "0.00"))',
          "string", "lt-ds-plan")
insert_before_partition(os.path.join(T, "dim_store.tmdl"), ds, "column brand =")

print("\nmodel extended — v2 columns + measures in place")

# =========================================================== fact_orders: distance at ORDER grain
# The orders↔deliveries relationship is single-direction (orders filter deliveries), so a delivery
# column can never slice an order measure. Free-ship economics and SLA-by-distance need distance at
# ORDER grain -> roll deliveries up inside Power Query (same logic as scripts/02_etl.py).
FO = os.path.join(T, "fact_orders.tmdl")
src = open(FO, encoding="utf-8").read()
if "dist_mean_m" not in src:
    old_tail = ('\t\t\t    AddF3 = Table.AddColumn(AddF2, "flag_long_cycle", each [order_metric_cycle_time] <> null '
                'and [order_metric_cycle_time] > 1440, type logical)\n\t\t\tin\n\t\t\t    AddF3\n')
    assert old_tail in src, "partition tail not found — check fact_orders.tmdl M block"
    new_tail = (
        '\t\t\t    AddF3 = Table.AddColumn(AddF2, "flag_long_cycle", each [order_metric_cycle_time] <> null '
        'and [order_metric_cycle_time] > 1440, type logical),\n'
        '\t\t\t    // roll deliveries up to order grain: distance must live on the order to slice money measures\n'
        '\t\t\t    DlvSrc = Csv.Document(File.Contents(SourceFolder & "deliveries.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
        '\t\t\t    DlvHead = Table.PromoteHeaders(DlvSrc, [PromoteAllScalars=true]),\n'
        '\t\t\t    DlvTyp = Table.TransformColumnTypes(DlvHead, {{"delivery_order_id", Int64.Type}, {"delivery_distance_meters", type number}}),\n'
        '\t\t\t    DlvGrp = Table.Group(DlvTyp, {"delivery_order_id"}, {{"dist_mean_m", each List.Average([delivery_distance_meters]), type number}, {"n_deliveries", each Table.RowCount(_), Int64.Type}}),\n'
        '\t\t\t    Joined = Table.NestedJoin(AddF3, {"order_id"}, DlvGrp, {"delivery_order_id"}, "dlv", JoinKind.LeftOuter),\n'
        '\t\t\t    Expanded = Table.ExpandTableColumn(Joined, "dlv", {"dist_mean_m", "n_deliveries"})\n'
        '\t\t\tin\n\t\t\t    Expanded\n')
    src = src.replace(old_tail, new_tail)
    # source columns + banding at order grain, inserted right before the first measure
    extra = (
        '\tcolumn dist_mean_m\n\t\tdataType: double\n\t\tsummarizeBy: none\n\t\tsourceColumn: dist_mean_m\n'
        '\t\tformatString: #,0\n\t\tlineageTag: lt-fo-distm\n\n'
        '\tcolumn n_deliveries\n\t\tdataType: int64\n\t\tsummarizeBy: none\n\t\tsourceColumn: n_deliveries\n'
        '\t\tlineageTag: lt-fo-ndlv\n\n'
        + col("order_dist_km", 'DIVIDE(fact_orders[dist_mean_m], 1000)', "double", "lt-fo-distkm", fmt="#,0.00")
        + col("order_distance_band_no",
              'IF(ISBLANK(fact_orders[dist_mean_m]), BLANK(), SWITCH(TRUE(), fact_orders[dist_mean_m] <= 1000, 1, '
              'fact_orders[dist_mean_m] <= 2000, 2, fact_orders[dist_mean_m] <= 3000, 3, '
              'fact_orders[dist_mean_m] <= 5000, 4, fact_orders[dist_mean_m] <= 10000, 5, 6))',
              "int64", "lt-fo-odbno")
        + col("order_distance_band",
              'SWITCH(fact_orders[order_distance_band_no], 1, "<1 km", 2, "1-2 km", 3, "2-3 km", 4, "3-5 km", '
              '5, "5-10 km", 6, ">10 km")', "string", "lt-fo-odb", sort_by="order_distance_band_no"))
    i = src.index("\tmeasure 'Total Orders'")
    src = src[:i] + extra + src[i:]
    open(FO, "w", encoding="utf-8").write(src)
    print("  + fact_orders.tmdl: order-grain distance (M rollup + bands)")
else:
    print("  = fact_orders.tmdl: distance already at order grain")
