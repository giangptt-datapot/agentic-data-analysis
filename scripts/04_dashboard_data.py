"""
04_dashboard_data.py — Build the single JSON payload the dashboard/mockup render from.
All timestamps converted to Brazil local time (UTC-3) per stakeholder decision;
this is documented as an ASSUMPTION (source tz not stated in dataset).
"""
import pandas as pd, numpy as np, os, json

HERE = os.path.dirname(__file__)
PROC = os.path.join(HERE, "..", "data", "processed")
DASH = os.path.join(HERE, "..", "dashboard")
os.makedirs(DASH, exist_ok=True)

f = pd.read_csv(os.path.join(PROC, "fact_orders.csv"), low_memory=False)
d = pd.read_csv(os.path.join(PROC, "dim_deliveries.csv"), low_memory=False)
f["order_moment_created"] = pd.to_datetime(f["order_moment_created"])
# Brazil local time = UTC-3 (ASSUMPTION)
f["ts_local"] = f["order_moment_created"] - pd.Timedelta(hours=3)
f["hour_local"] = f["ts_local"].dt.hour
f["date_local"] = f["ts_local"].dt.date
f["dow_local"] = f["ts_local"].dt.dayofweek
f["week_local"] = f["ts_local"].dt.to_period("W-SUN").apply(lambda p: p.start_time.date())
f["month_local"] = f["ts_local"].dt.month

fin = f[f.order_status == "FINISHED"].copy()
D = {}

# ---- headline KPIs ----
D["kpi"] = {
    "total_orders": int(len(f)),
    "finished_orders": int(len(fin)),
    "gmv": round(float(fin.order_amount.sum()), 0),
    "aov": round(float(fin.order_amount.mean()), 2),
    "median_order": round(float(fin.order_amount.median()), 2),
    "cancel_rate": round(float((f.order_status == "CANCELED").mean() * 100), 2),
    "n_stores_active": int(fin.store_id.nunique()),
    "n_stores_total": int(f.store_id.nunique()),
    "n_hubs": int(f.hub_id.nunique()),
    "n_cities": int(f.hub_city.nunique()),
    "median_cycle_min": round(float(fin.loc[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 1440), "order_metric_cycle_time"].median()), 1),
    "median_distance_km": round(float(d.loc[(d.delivery_status == "DELIVERED") & (d.delivery_distance_meters <= 50000), "delivery_distance_meters"].median()) / 1000, 2),
    "chargeback_rate": round(float(f.any_chargeback.fillna(0).astype(bool).mean() * 100), 3),
    "date_min": str(f.order_moment_created.min().date()),
    "date_max": str(f.order_moment_created.max().date()),
}

# ---- GMV weekly trend (line) ----
wk = fin.groupby("week_local").agg(gmv=("order_amount", "sum"), orders=("order_id", "count")).reset_index()
wk = wk[(wk.week_local >= pd.to_datetime("2021-01-04").date())]  # drop the partial pre-week if tiny
D["weekly"] = [{"week": str(r.week_local), "gmv": round(r.gmv, 0), "orders": int(r.orders)} for r in wk.itertuples()]

# ---- Segment (FOOD vs GOOD) ----
seg = fin.groupby("store_segment").agg(orders=("order_id", "count"), gmv=("order_amount", "sum"),
                                       aov=("order_amount", "mean")).reset_index()
segc = f.groupby("store_segment").apply(lambda x: (x.order_status == "CANCELED").mean() * 100, include_groups=False)
D["segment"] = [{"segment": r.store_segment, "orders": int(r.orders), "gmv": round(r.gmv, 0),
                 "aov": round(r.aov, 2), "cancel_rate": round(float(segc[r.store_segment]), 2)} for r in seg.itertuples()]

# ---- Channel type + top channels ----
cht = fin.groupby("channel_type").agg(orders=("order_id", "count"), gmv=("order_amount", "sum"),
                                      aov=("order_amount", "mean")).reset_index()
D["channel_type"] = [{"type": r.channel_type, "orders": int(r.orders), "gmv": round(r.gmv, 0), "aov": round(r.aov, 2)} for r in cht.itertuples()]
topch = fin.groupby(["channel_name", "channel_type"]).agg(orders=("order_id", "count"), gmv=("order_amount", "sum")).reset_index()
topch = topch.sort_values("gmv", ascending=False).head(8)
D["top_channels"] = [{"channel": r.channel_name, "type": r.channel_type, "orders": int(r.orders), "gmv": round(r.gmv, 0)} for r in topch.itertuples()]

# ---- City (bar + map bubble) ----
city = fin.groupby(["hub_city", "hub_state"]).agg(orders=("order_id", "count"), gmv=("order_amount", "sum"),
                                                  aov=("order_amount", "mean"), stores=("store_id", "nunique")).reset_index()
city = city.sort_values("gmv", ascending=False)
# city centroid from hubs
hubs = pd.read_csv(os.path.join(HERE, "..", "data", "raw", "hubs.csv"), encoding="latin-1")
cent = hubs.groupby("hub_city")[["hub_latitude", "hub_longitude"]].mean()
D["city"] = [{"city": r.hub_city, "state": r.hub_state, "orders": int(r.orders), "gmv": round(r.gmv, 0),
              "aov": round(r.aov, 2), "stores": int(r.stores),
              "lat": round(float(cent.loc[r.hub_city, "hub_latitude"]), 4),
              "lng": round(float(cent.loc[r.hub_city, "hub_longitude"]), 4)} for r in city.itertuples()]

# ---- Cancellation by month + trend ----
cbm = f.groupby("month_local").agg(orders=("order_id", "count"),
                                   cancel=("order_status", lambda s: (s == "CANCELED").sum())).reset_index()
cbm = cbm[cbm.month_local.isin([1, 2, 3, 4])]
D["cancel_month"] = [{"month": int(r.month_local), "orders": int(r.orders), "cancel": int(r.cancel),
                      "cancel_rate": round(r.cancel / r.orders * 100, 2)} for r in cbm.itertuples()]

# ---- Payment method ----
pm = fin.groupby("primary_payment_method").agg(orders=("order_id", "count")).reset_index().sort_values("orders", ascending=False)
pm = pm.head(6)
other = int(len(fin) - pm.orders.sum())
D["payment_method"] = [{"method": r.primary_payment_method, "orders": int(r.orders),
                        "share": round(r.orders / len(fin) * 100, 2)} for r in pm.itertuples()]
D["payment_method"].append({"method": "OTHER", "orders": other, "share": round(other / len(fin) * 100, 2)})

# ---- Orders by hour (local) — bimodal ----
byh = fin.groupby("hour_local").size().reindex(range(24), fill_value=0)
D["orders_by_hour"] = [{"hour": int(h), "orders": int(v)} for h, v in byh.items()]

# ---- Orders by day-of-week (local) ----
dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
bydow = fin.groupby("dow_local").size().reindex(range(7), fill_value=0)
D["orders_by_dow"] = [{"dow": dow_names[i], "orders": int(bydow[i])} for i in range(7)]

# ---- Heatmap dow x hour ----
hm = fin.groupby(["dow_local", "hour_local"]).size().reset_index(name="orders")
D["heatmap"] = [{"dow": dow_names[int(r.dow_local)], "hour": int(r.hour_local), "orders": int(r.orders)} for r in hm.itertuples()]

# ---- Driver modal / type + distance ----
dd = d[(d.delivery_status == "DELIVERED") & (d.delivery_distance_meters <= 50000)]
dm = d.dropna(subset=["driver_modal"]).groupby("driver_modal").size()
D["driver_modal"] = [{"modal": k, "deliveries": int(v), "share": round(v / dm.sum() * 100, 1),
                      "median_km": round(float(dd[dd.driver_modal == k].delivery_distance_meters.median()) / 1000, 2)} for k, v in dm.items()]
dt = d.dropna(subset=["driver_type"]).groupby("driver_type").size()
D["driver_type"] = [{"type": k, "deliveries": int(v), "share": round(v / dt.sum() * 100, 1)} for k, v in dt.items()]

# ---- Cycle time distribution (finished, sane) ----
ct = fin[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 180)].order_metric_cycle_time
bins = [0, 20, 30, 40, 50, 60, 75, 90, 120, 180]
labels = ["<20", "20-30", "30-40", "40-50", "50-60", "60-75", "75-90", "90-120", "120-180"]
cut = pd.cut(ct, bins=bins, labels=labels)
D["cycle_hist"] = [{"bucket": str(k), "orders": int(v)} for k, v in cut.value_counts().reindex(labels).items()]
D["cycle_pct"] = {"p50": round(float(ct.median()), 1), "p90": round(float(ct.quantile(0.9)), 1), "p95": round(float(ct.quantile(0.95)), 1)}

# ---- Delivery fee economics ----
ff = fin[fin.order_delivery_cost.notna()]
D["delivery_econ"] = {
    "mean_fee": round(float(fin.order_delivery_fee.mean()), 2),
    "mean_cost": round(float(ff.order_delivery_cost.mean()), 2),
    "free_ship_share": round(float((fin.order_delivery_fee == 0).mean() * 100), 1),
    "fee_below_cost_share": round(float((ff.order_delivery_fee < ff.order_delivery_cost).mean() * 100), 1),
    "subsidy_per_order": round(float(ff.order_delivery_cost.mean() - fin.order_delivery_fee.mean()), 2),
}

# ---- Store Pareto curve ----
sto = fin.groupby("store_id").order_amount.sum().sort_values(ascending=False).values
cum = np.cumsum(sto) / sto.sum()
n = len(sto)
# sample the curve at 25 points for plotting
idx = np.linspace(0, n - 1, 25).astype(int)
D["pareto"] = [{"store_pct": round((i + 1) / n * 100, 1), "gmv_pct": round(float(cum[i]) * 100, 1)} for i in idx]
D["pareto_stat"] = {"top20_share": round(float(cum[int(np.ceil(n * 0.2)) - 1]) * 100, 1),
                    "stores_for_80": int((cum <= 0.8).sum()) + 1, "n_stores": int(n)}

# ---- Segment monthly stacked (orders) ----
segmon = fin.groupby(["month_local", "store_segment"]).size().reset_index(name="orders")
segmon = segmon[segmon.month_local.isin([1, 2, 3, 4])]
D["segment_month"] = [{"month": int(r.month_local), "segment": r.store_segment, "orders": int(r.orders)} for r in segmon.itertuples()]

# ---- data quality summary for footer ----
D["quality"] = {
    "flag_extreme_amount": int(f.flag_extreme_amount.sum()),
    "flag_extreme_distance": int((d.delivery_distance_meters > 50000).sum()),
    "flag_long_cycle": int(f.flag_long_cycle.sum()),
    "flag_zero_amount": int(f.flag_zero_amount.sum()),
    "orders_no_payment": int((~f.has_payment).sum()),
    "orders_no_delivery": int((~f.has_delivery).sum()),
    "null_driver_deliveries": int(d.driver_id.isna().sum()),
    "delivered_missing_pct": 94.7,
}

json.dump(D, open(os.path.join(DASH, "dashboard_data.json"), "w"), indent=2, default=str)
print("wrote dashboard/dashboard_data.json")
print(json.dumps(D["kpi"], indent=2))
print("hours peak (local):", sorted(D["orders_by_hour"], key=lambda x: -x["orders"])[:4])
print("dow:", D["orders_by_dow"])
