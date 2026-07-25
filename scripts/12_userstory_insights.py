"""
12_userstory_insights.py — Deep-dive analysis organised by USER STORY.
Recomputes headline KPIs from data/processed/fact_orders.csv (verification) and adds
new angles not covered by reports/03: subscription plan tier, cancel-by-hour,
cancel-by-value-band, store cohort (new vs existing), free-ship economics by
distance/value band, prep-vs-transit share by hub/store, driver supply concentration.
Output: outputs/userstory_insights.json (+ console table).
"""
import json, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FO = os.path.join(ROOT, "data", "processed", "fact_orders.csv")
DD = os.path.join(ROOT, "data", "processed", "dim_deliveries.csv")
OUT = os.path.join(ROOT, "outputs", "userstory_insights.json")

R = {}


def r2(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 2)


print("loading fact_orders ...")
usecols = [
    "order_id", "store_id", "store_name", "store_segment", "store_plan_price",
    "hub_id", "hub_name", "hub_city", "channel_name", "channel_type",
    "order_status", "order_amount", "order_delivery_fee", "order_delivery_cost",
    "order_metric_cycle_time", "order_metric_production_time", "order_metric_transit_time",
    "order_date", "order_dow_name", "order_hour", "order_week",
    "dist_mean_m", "primary_driver_modal", "primary_payment_method",
    "any_chargeback", "n_payments", "has_delivery", "has_payment",
]
o = pd.read_csv(FO, usecols=usecols, parse_dates=["order_date"])
o["month"] = o["order_date"].dt.month
# raw order_hour is UTC; Brazil local = UTC-3 (same assumption as page_data.json)
o["hour_local"] = (o["order_hour"] - 3) % 24
fin = o[o.order_status == "FINISHED"]
print(f"  {len(o):,} orders · {len(fin):,} finished")

# ---------------------------------------------------------------- baseline KPI
R["kpi"] = {
    "orders": int(len(o)),
    "finished": int(len(fin)),
    "canceled": int((o.order_status == "CANCELED").sum()),
    "gmv": r2(fin.order_amount.sum()),
    "aov": r2(fin.order_amount.mean()),
    "median_order_value": r2(fin.order_amount.median()),
    "cancel_rate_pct": r2((o.order_status == "CANCELED").mean() * 100),
    "date_min": str(o.order_date.min().date()),
    "date_max": str(o.order_date.max().date()),
    "status_mix": {k: int(v) for k, v in o.order_status.value_counts().items()},
}

# GMV at risk = amount of canceled orders (order_amount is present on canceled rows too)
can = o[o.order_status == "CANCELED"]
R["kpi"]["canceled_amount"] = r2(can.order_amount.sum())
R["kpi"]["canceled_amount_pct_of_gmv"] = r2(can.order_amount.sum() / fin.order_amount.sum() * 100)

# ------------------------------------------------- US-1 exec: growth decomposition
# monthly GMV + whether growth comes from NEW stores (first month seen) or existing
first_month = fin.groupby("store_id")["month"].min()
fin_m = fin.assign(first_month=fin.store_id.map(first_month))
gm = fin_m.groupby("month").agg(gmv=("order_amount", "sum"), orders=("order_id", "count"),
                                stores=("store_id", "nunique")).reset_index()
gm["aov"] = gm.gmv / gm.orders
newstore = fin_m[fin_m.month == fin_m.first_month].groupby("month")["order_amount"].sum()
gm["gmv_new_stores"] = gm.month.map(newstore).fillna(0)
gm["new_store_share_pct"] = gm.gmv_new_stores / gm.gmv * 100
cancel_m = o.groupby("month").apply(lambda d: (d.order_status == "CANCELED").mean() * 100,
                                    include_groups=False)
gm["cancel_rate_pct"] = gm.month.map(cancel_m)
R["monthly"] = [{k: (r2(v) if isinstance(v, (int, float, np.floating)) and k != "month" else int(v) if k in ("month", "orders", "stores") else r2(v))
                 for k, v in row.items()} for row in gm.to_dict("records")]

# same-store (present in every month) growth
allm = set(gm.month)
per = fin.groupby(["store_id", "month"])["order_amount"].sum().unstack(fill_value=0)
same = per[(per > 0).all(axis=1)]
R["same_store"] = {
    "n_stores": int(len(same)),
    "gmv_m1": r2(same[1].sum()), "gmv_m4": r2(same[4].sum()),
    "growth_pct": r2((same[4].sum() / same[1].sum() - 1) * 100),
    "share_of_gmv_pct": r2(same.values.sum() / fin.order_amount.sum() * 100),
}
# weekly (truncation check on last week)
wk = fin.groupby("order_week").agg(gmv=("order_amount", "sum"), orders=("order_id", "count"),
                                   dmin=("order_date", "min"), dmax=("order_date", "max")).reset_index()
wk["days"] = (wk.dmax - wk.dmin).dt.days + 1
R["weekly_tail"] = [{"week": str(x.order_week), "gmv": r2(x.gmv), "orders": int(x.orders),
                     "days": int(x.days), "from": str(x.dmin.date()), "to": str(x.dmax.date())}
                    for x in wk.tail(4).itertuples()]

# ------------------------------------------------- US-1 concentration (channel/store/city)
ch = fin.groupby(["channel_name", "channel_type"]).agg(
    orders=("order_id", "count"), gmv=("order_amount", "sum")).reset_index()
ch["gmv_share_pct"] = ch.gmv / ch.gmv.sum() * 100
ch["aov"] = ch.gmv / ch.orders
ch = ch.sort_values("gmv", ascending=False)
R["channels"] = [{"channel": x.channel_name.strip(), "type": x.channel_type,
                  "orders": int(x.orders), "gmv": r2(x.gmv),
                  "gmv_share_pct": r2(x.gmv_share_pct), "aov": r2(x.aov)}
                 for x in ch.head(10).itertuples()]
st = fin.groupby("store_id")["order_amount"].sum().sort_values(ascending=False)
cum = st.cumsum() / st.sum()
R["concentration"] = {
    "n_active_stores": int(len(st)),
    "stores_for_80pct": int((cum <= 0.8).sum() + 1),
    "stores_for_80pct_share_pct": r2(((cum <= 0.8).sum() + 1) / len(st) * 100),
    "top20pct_gmv_share_pct": r2(st.head(int(len(st) * 0.2)).sum() / st.sum() * 100),
    "top1_channel_gmv_share_pct": r2(ch.gmv.max() / ch.gmv.sum() * 100),
    "top1_city_gmv_share_pct": r2(fin.groupby("hub_city").order_amount.sum().max() / fin.order_amount.sum() * 100),
}

# ------------------------------------------------- US-NEW: subscription plan tier
pl = fin.groupby("store_plan_price").agg(
    stores=("store_id", "nunique"), orders=("order_id", "count"),
    gmv=("order_amount", "sum")).reset_index()
pl["aov"] = pl.gmv / pl.orders
pl["gmv_per_store"] = pl.gmv / pl.stores
pl["orders_per_store"] = pl.orders / pl.stores
canc_pl = o.groupby("store_plan_price").apply(lambda d: (d.order_status == "CANCELED").mean() * 100,
                                              include_groups=False)
pl["cancel_rate_pct"] = pl.store_plan_price.map(canc_pl)
pl["gmv_share_pct"] = pl.gmv / pl.gmv.sum() * 100
seg_pl = fin.groupby("store_plan_price").store_segment.apply(
    lambda s: r2((s == "GOOD").mean() * 100))
pl["good_order_share_pct"] = pl.store_plan_price.map(seg_pl)
R["plan_tier"] = [{"plan_price": r2(x.store_plan_price), "stores": int(x.stores),
                   "orders": int(x.orders), "gmv": r2(x.gmv), "aov": r2(x.aov),
                   "gmv_per_store": r2(x.gmv_per_store), "orders_per_store": r2(x.orders_per_store),
                   "cancel_rate_pct": r2(x.cancel_rate_pct), "gmv_share_pct": r2(x.gmv_share_pct),
                   "good_order_share_pct": r2(x.good_order_share_pct)}
                  for x in pl.sort_values("gmv", ascending=False).itertuples()]

# ------------------------------------------------- US-2 ops: demand vs cancel by hour
byhour = o.groupby("hour_local").agg(orders=("order_id", "count")).reset_index()
ch_hour = o.groupby("hour_local").apply(lambda d: (d.order_status == "CANCELED").mean() * 100,
                                        include_groups=False)
cyc_hour = fin.assign(hour_local=(fin.order_hour - 3) % 24)[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 1440)] \
    .groupby("hour_local").order_metric_cycle_time.median()
byhour["cancel_rate_pct"] = byhour.hour_local.map(ch_hour)
byhour["median_cycle"] = byhour.hour_local.map(cyc_hour)
R["by_hour"] = [{"hour": int(x.hour_local), "orders": int(x.orders),
                 "cancel_rate_pct": r2(x.cancel_rate_pct), "median_cycle": r2(x.median_cycle)}
                for x in byhour.itertuples()]
peak = byhour.sort_values("orders", ascending=False).head(1).iloc[0]
trough = byhour[byhour.orders > 0].sort_values("orders").head(1).iloc[0]
R["demand_shape"] = {
    "peak_hour": int(peak.hour_local), "peak_orders": int(peak.orders),
    "trough_hour": int(trough.hour_local), "trough_orders": int(trough.orders),
    "peak_to_trough_x": r2(peak.orders / trough.orders),
}
dow = o.groupby("order_dow_name").agg(orders=("order_id", "count")).reset_index()
dow_c = o.groupby("order_dow_name").apply(lambda d: (d.order_status == "CANCELED").mean() * 100,
                                          include_groups=False)
dow["cancel_rate_pct"] = dow.order_dow_name.map(dow_c)
R["by_dow"] = [{"dow": x.order_dow_name, "orders": int(x.orders),
                "cancel_rate_pct": r2(x.cancel_rate_pct)} for x in dow.itertuples()]
# share of orders inside the two dayparts
lunch = o.hour_local.between(11, 13).mean() * 100
dinner = o.hour_local.between(18, 21).mean() * 100
R["demand_shape"]["lunch_11_13_share_pct"] = r2(lunch)
R["demand_shape"]["dinner_18_21_share_pct"] = r2(dinner)
R["demand_shape"]["two_dayparts_share_pct"] = r2(lunch + dinner)

# ------------------------------------------------- US-3 delivery: prep vs transit
cyc = fin[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 1440)].copy()
cyc["queue"] = cyc.order_metric_cycle_time - cyc.order_metric_production_time.fillna(0) \
    - cyc.order_metric_transit_time.fillna(0)
R["cycle"] = {
    "n": int(len(cyc)),
    "p50": r2(cyc.order_metric_cycle_time.median()),
    "p90": r2(cyc.order_metric_cycle_time.quantile(0.9)),
    "p95": r2(cyc.order_metric_cycle_time.quantile(0.95)),
    "mean": r2(cyc.order_metric_cycle_time.mean()),
    "prep_median": r2(cyc.order_metric_production_time.median()),
    "transit_median": r2(cyc.order_metric_transit_time.median()),
    "residual_median": r2(cyc.queue.median()),
    "prep_share_of_cycle_pct": r2(cyc.order_metric_production_time.median() / cyc.order_metric_cycle_time.median() * 100),
    "transit_share_of_cycle_pct": r2(cyc.order_metric_transit_time.median() / cyc.order_metric_cycle_time.median() * 100),
    "over_60min_pct": r2((cyc.order_metric_cycle_time > 60).mean() * 100),
    "over_90min_pct": r2((cyc.order_metric_cycle_time > 90).mean() * 100),
}
# trimmed view (cycle<=180) — the filter the existing mockup/page_data used
trim = fin[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 180)].order_metric_cycle_time
R["cycle"]["trimmed180"] = {"p50": r2(trim.median()), "p90": r2(trim.quantile(0.9)),
                            "p95": r2(trim.quantile(0.95)), "mean": r2(trim.mean()),
                            "note": "cap 180' — dùng bởi mockup/page_data; DAX measure dùng cap 1440' -> P90 khác"}
# correlations on one consistent frame: cycle<=150', 0<dist<=15km, prep/transit present
cf = fin[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 150) &
         (fin.dist_mean_m > 0) & (fin.dist_mean_m <= 15000)].dropna(
             subset=["order_metric_production_time", "order_metric_transit_time"])
R["cycle"]["corr_frame_n"] = int(len(cf))
R["cycle"]["corr_dist_cycle"] = r2(cf.dist_mean_m.corr(cf.order_metric_cycle_time))
R["cycle"]["corr_prep_cycle"] = r2(cf.order_metric_production_time.corr(cf.order_metric_cycle_time))
R["cycle"]["corr_transit_cycle"] = r2(cf.order_metric_transit_time.corr(cf.order_metric_cycle_time))
R["cycle"]["corr_amount_cycle"] = r2(cf.order_amount.corr(cf.order_metric_cycle_time))
# variance explained (single-predictor R^2)
for k in ("dist", "prep", "transit"):
    c = R["cycle"][f"corr_{k}_cycle"]
    R["cycle"][f"r2_{k}_pct"] = r2(c * c * 100)
# distance band vs cycle
cyc["dist_km"] = cyc.dist_mean_m / 1000
bands = pd.cut(cyc.dist_km, [0, 1, 2, 3, 5, 10, 50], labels=["<1", "1-2", "2-3", "3-5", "5-10", "10-50"])
db = cyc.groupby(bands, observed=True).agg(orders=("order_id", "count"),
                                           median_cycle=("order_metric_cycle_time", "median"),
                                           median_prep=("order_metric_production_time", "median"),
                                           median_transit=("order_metric_transit_time", "median")).reset_index()
R["distance_band"] = [{"band_km": str(x.dist_km), "orders": int(x.orders),
                       "median_cycle": r2(x.median_cycle), "median_prep": r2(x.median_prep),
                       "median_transit": r2(x.median_transit)} for x in db.itertuples()]

# slowest stores by prep time (min 200 finished orders) — actionable bottleneck list
sp = fin.groupby(["store_id", "store_name", "store_segment", "hub_city"]).agg(
    orders=("order_id", "count"), prep=("order_metric_production_time", "median"),
    gmv=("order_amount", "sum")).reset_index()
sp = sp[sp.orders >= 200]
R["slow_prep_stores"] = [{"store": x.store_name.strip(), "seg": x.store_segment, "city": x.hub_city,
                          "orders": int(x.orders), "median_prep": r2(x.prep), "gmv": r2(x.gmv)}
                         for x in sp.sort_values("prep", ascending=False).head(10).itertuples()]
R["prep_spread"] = {"p10_store": r2(sp.prep.quantile(0.1)), "median_store": r2(sp.prep.median()),
                    "p90_store": r2(sp.prep.quantile(0.9)), "n_stores": int(len(sp))}

# ------------------------------------------------- US-4 hub
hub = o.groupby(["hub_name", "hub_city"]).agg(orders=("order_id", "count")).reset_index()
hf = fin.groupby(["hub_name", "hub_city"]).agg(
    finished=("order_id", "count"), gmv=("order_amount", "sum"),
    cycle=("order_metric_cycle_time", "median"), prep=("order_metric_production_time", "median"),
    transit=("order_metric_transit_time", "median")).reset_index()
hc = o.groupby(["hub_name", "hub_city"]).apply(lambda d: (d.order_status == "CANCELED").mean() * 100,
                                               include_groups=False).rename("cancel_rate_pct").reset_index()
hub = hub.merge(hf, on=["hub_name", "hub_city"], how="left").merge(hc, on=["hub_name", "hub_city"], how="left")
R["hubs"] = [{"hub": x.hub_name.strip(), "city": x.hub_city, "orders": int(x.orders),
              "gmv": r2(x.gmv), "cancel_rate_pct": r2(x.cancel_rate_pct),
              "median_cycle": r2(x.cycle), "median_prep": r2(x.prep), "median_transit": r2(x.transit)}
             for x in hub.sort_values("orders", ascending=False).itertuples()]
big = hub[hub.orders >= 500]
R["hub_outliers"] = {
    "min_volume": 500, "n_hubs_qualified": int(len(big)), "n_hubs_excluded": int((hub.orders < 500).sum()),
    "worst_cancel": [{"hub": x.hub_name.strip(), "city": x.hub_city, "orders": int(x.orders),
                      "cancel_rate_pct": r2(x.cancel_rate_pct), "gmv": r2(x.gmv)}
                     for x in big.sort_values("cancel_rate_pct", ascending=False).head(5).itertuples()],
    "worst_cycle": [{"hub": x.hub_name.strip(), "city": x.hub_city, "orders": int(x.orders),
                     "median_cycle": r2(x.cycle), "median_prep": r2(x.prep)}
                    for x in big.sort_values("cycle", ascending=False).head(5).itertuples()],
}
# GMV lost to cancellation concentrated in which hubs
can_hub = can.groupby("hub_name").order_amount.sum().sort_values(ascending=False)
R["cancel_gmv_by_hub"] = [{"hub": k.strip(), "canceled_amount": r2(v),
                           "share_pct": r2(v / can.order_amount.sum() * 100)}
                          for k, v in can_hub.head(8).items()]

# ------------------------------------------------- US-5 store / partner
sg = fin.groupby(["store_id", "store_name", "store_segment", "hub_city"]).agg(
    finished=("order_id", "count"), gmv=("order_amount", "sum")).reset_index()
sc = o.groupby("store_id").apply(lambda d: (d.order_status == "CANCELED").mean() * 100,
                                 include_groups=False)
sg["cancel_rate_pct"] = sg.store_id.map(sc)
sg["aov"] = sg.gmv / sg.finished
q = sg[sg.finished >= 100]
med_gmv, med_can = q.gmv.median(), q.cancel_rate_pct.median()
quad = {
    "star (GMV cao · hủy thấp)": q[(q.gmv >= med_gmv) & (q.cancel_rate_pct < med_can)],
    "fix-first (GMV cao · hủy cao)": q[(q.gmv >= med_gmv) & (q.cancel_rate_pct >= med_can)],
    "nurture (GMV thấp · hủy thấp)": q[(q.gmv < med_gmv) & (q.cancel_rate_pct < med_can)],
    "review (GMV thấp · hủy cao)": q[(q.gmv < med_gmv) & (q.cancel_rate_pct >= med_can)],
}
R["partner_quadrant"] = {k: {"stores": int(len(v)), "gmv": r2(v.gmv.sum()),
                             "gmv_share_pct": r2(v.gmv.sum() / q.gmv.sum() * 100),
                             "mean_cancel_pct": r2(v.cancel_rate_pct.mean())}
                         for k, v in quad.items()}
R["partner_quadrant"]["_thresholds"] = {"min_finished": 100, "median_gmv": r2(med_gmv),
                                        "median_cancel_pct": r2(med_can), "n_stores": int(len(q))}
fixfirst = quad["fix-first (GMV cao · hủy cao)"].sort_values("gmv", ascending=False).head(10)
R["fix_first_stores"] = [{"store": x.store_name.strip(), "seg": x.store_segment, "city": x.hub_city,
                          "finished": int(x.finished), "gmv": r2(x.gmv),
                          "cancel_rate_pct": r2(x.cancel_rate_pct)} for x in fixfirst.itertuples()]

# ------------------------------------------------- cancellation deep-dive
seg = o.groupby("store_segment").apply(
    lambda d: pd.Series({"orders": len(d), "cancel_rate_pct": (d.order_status == "CANCELED").mean() * 100,
                         "canceled_amount": d.loc[d.order_status == "CANCELED", "order_amount"].sum()}),
    include_groups=False).reset_index()
R["cancel_by_segment"] = [{"segment": x.store_segment, "orders": int(x.orders),
                           "cancel_rate_pct": r2(x.cancel_rate_pct),
                           "canceled_amount": r2(x.canceled_amount)} for x in seg.itertuples()]
sxc = o.groupby(["store_segment", "channel_type"]).apply(
    lambda d: pd.Series({"orders": len(d), "cancel_rate_pct": (d.order_status == "CANCELED").mean() * 100}),
    include_groups=False).reset_index()
R["cancel_by_segment_channel"] = [{"segment": x.store_segment, "channel_type": x.channel_type,
                                   "orders": int(x.orders), "cancel_rate_pct": r2(x.cancel_rate_pct)}
                                  for x in sxc.itertuples()]
vb = pd.cut(o.order_amount, [-0.01, 30, 60, 100, 200, 500, 1e9],
            labels=["≤30", "30-60", "60-100", "100-200", "200-500", ">500"])
vbd = o.groupby(vb, observed=True).apply(
    lambda d: pd.Series({"orders": len(d), "cancel_rate_pct": (d.order_status == "CANCELED").mean() * 100}),
    include_groups=False).reset_index()
R["cancel_by_value_band"] = [{"band": str(x.order_amount), "orders": int(x.orders),
                              "cancel_rate_pct": r2(x.cancel_rate_pct)} for x in vbd.itertuples()]
# GOOD counterfactual: bring GOOD cancel down to FOOD level
g = o[o.store_segment == "GOOD"]; f = o[o.store_segment == "FOOD"]
g_rate = (g.order_status == "CANCELED").mean(); f_rate = (f.order_status == "CANCELED").mean()
g_aov = g.loc[g.order_status == "FINISHED", "order_amount"].mean()
R["good_counterfactual"] = {
    "good_cancel_pct": r2(g_rate * 100), "food_cancel_pct": r2(f_rate * 100),
    "ratio_x": r2(g_rate / f_rate), "good_orders": int(len(g)),
    "orders_recoverable": int(round(len(g) * (g_rate - f_rate))),
    "gmv_recoverable": r2(len(g) * (g_rate - f_rate) * g_aov),
    "assumption": "recovered orders would convert at GOOD AOV; correlation only, no cancel_reason in data",
}

# ------------------------------------------------- delivery economics / free-ship
e = fin.dropna(subset=["order_delivery_cost"]).copy()
e["margin"] = e.order_delivery_fee - e.order_delivery_cost
R["delivery_econ"] = {
    "n_orders_with_cost": int(len(e)),
    "mean_fee": r2(e.order_delivery_fee.mean()), "mean_cost": r2(e.order_delivery_cost.mean()),
    "subsidy_per_order": r2(e.order_delivery_cost.mean() - e.order_delivery_fee.mean()),
    "subsidy_total": r2(-e.margin.sum()),
    "free_ship_pct": r2((e.order_delivery_fee == 0).mean() * 100),
    "fee_below_cost_pct": r2((e.margin < 0).mean() * 100),
    "aov_freeship": r2(e.loc[e.order_delivery_fee == 0, "order_amount"].mean()),
    "aov_paidship": r2(e.loc[e.order_delivery_fee > 0, "order_amount"].mean()),
    "loss_freeship_orders": r2(-e.loc[e.order_delivery_fee == 0, "margin"].sum()),
    "margin_paidship_orders": r2(e.loc[e.order_delivery_fee > 0, "margin"].sum()),
    "mean_cost_freeship": r2(e.loc[e.order_delivery_fee == 0, "order_delivery_cost"].mean()),
    "mean_margin_paidship": r2(e.loc[e.order_delivery_fee > 0, "margin"].mean()),
}
vb2 = pd.cut(e.order_amount, [-0.01, 30, 60, 100, 200, 500, 1e9],
             labels=["≤30", "30-60", "60-100", "100-200", "200-500", ">500"])
eb = e.groupby(vb2, observed=True).agg(orders=("order_id", "count"), fee=("order_delivery_fee", "mean"),
                                       cost=("order_delivery_cost", "mean"),
                                       free=("order_delivery_fee", lambda s: (s == 0).mean() * 100),
                                       subsidy=("margin", lambda s: -s.sum())).reset_index()
R["econ_by_value_band"] = [{"band": str(x.order_amount), "orders": int(x.orders), "mean_fee": r2(x.fee),
                            "mean_cost": r2(x.cost), "free_ship_pct": r2(x.free),
                            "subsidy_total": r2(x.subsidy)} for x in eb.itertuples()]
e["dist_km"] = e.dist_mean_m / 1000
db2 = pd.cut(e.dist_km, [0, 1, 2, 3, 5, 10, 50], labels=["<1", "1-2", "2-3", "3-5", "5-10", "10-50"])
ed = e.groupby(db2, observed=True).agg(orders=("order_id", "count"), fee=("order_delivery_fee", "mean"),
                                        cost=("order_delivery_cost", "mean"),
                                        subsidy=("margin", lambda s: -s.sum())).reset_index()
R["econ_by_distance_band"] = [{"band_km": str(x.dist_km), "orders": int(x.orders), "mean_fee": r2(x.fee),
                               "mean_cost": r2(x.cost), "subsidy_total": r2(x.subsidy)}
                              for x in ed.itertuples()]
seg_e = e.groupby("store_segment").agg(fee=("order_delivery_fee", "mean"), cost=("order_delivery_cost", "mean"),
                                        subsidy=("margin", lambda s: -s.sum()),
                                        free=("order_delivery_fee", lambda s: (s == 0).mean() * 100)).reset_index()
R["econ_by_segment"] = [{"segment": x.store_segment, "mean_fee": r2(x.fee), "mean_cost": r2(x.cost),
                         "subsidy_total": r2(x.subsidy), "free_ship_pct": r2(x.free)} for x in seg_e.itertuples()]

# ------------------------------------------------- fleet / driver supply
print("loading deliveries ...")
d = pd.read_csv(DD)
dv = d[d.delivery_status == "DELIVERED"]
per_driver = dv.groupby("driver_id").size().sort_values(ascending=False)
R["fleet"] = {
    "deliveries": int(len(d)), "delivered": int(len(dv)),
    "success_rate_pct": r2(len(dv) / len(d) * 100),
    "active_drivers": int(dv.driver_id.nunique()),
    "median_deliveries_per_driver": r2(per_driver.median()),
    "p90_deliveries_per_driver": r2(per_driver.quantile(0.9)),
    "top10pct_drivers_share_pct": r2(per_driver.head(max(1, int(len(per_driver) * 0.1))).sum() / len(dv) * 100),
    "drivers_under_5_deliveries_pct": r2((per_driver < 5).mean() * 100),
    "modal": [{"modal": k, "deliveries": int(v),
               "share_pct": r2(v / len(dv) * 100),
               "median_km": r2(dv.loc[dv.driver_modal == k, "delivery_distance_meters"].median() / 1000)}
              for k, v in dv.driver_modal.value_counts().items()],
    "type": [{"type": k, "deliveries": int(v), "share_pct": r2(v / len(dv) * 100)}
             for k, v in dv.driver_type.value_counts().items()],
    "median_km": r2(dv.loc[dv.delivery_distance_meters <= 50000, "delivery_distance_meters"].median() / 1000),
}

# ------------------------------------------------- data quality / trust
R["data_quality"] = {
    "orders_without_delivery_record": int((~o.has_delivery.astype(bool)).sum()),
    "orders_without_payment_record": int((~o.has_payment.astype(bool)).sum()),
    "finished_without_delivery_record": int((~fin.has_delivery.astype(bool)).sum()),
    "finished_without_delivery_pct": r2((~fin.has_delivery.astype(bool)).mean() * 100),
    "zero_amount_finished": int((fin.order_amount <= 0).sum()),
    "cycle_gt_1440": int((fin.order_metric_cycle_time > 1440).sum()),
    "missing_delivery_cost": int(fin.order_delivery_cost.isna().sum()),
    "missing_delivery_cost_pct": r2(fin.order_delivery_cost.isna().mean() * 100),
    "chargeback_orders": int((o.any_chargeback == True).sum()),
    "chargeback_rate_pct": r2((o.any_chargeback == True).mean() * 100),
    "split_payment_orders": int((o.n_payments > 1).sum()),
    "duplicate_store_names": int(fin.groupby("store_name").store_id.nunique().gt(1).sum()),
}

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(R, fh, ensure_ascii=False, indent=2)
print(f"\nwrote {OUT}")
for k in ["kpi", "concentration", "demand_shape", "cycle", "good_counterfactual",
          "delivery_econ", "fleet", "same_store", "prep_spread", "data_quality"]:
    print(f"\n### {k}\n{json.dumps(R[k], ensure_ascii=False, indent=2)[:1500]}")
print("\n### plan_tier"); print(json.dumps(R["plan_tier"], ensure_ascii=False)[:1200])
print("\n### partner_quadrant"); print(json.dumps(R["partner_quadrant"], ensure_ascii=False)[:900])

# ==================================================================== ADDENDUM
# Angles discovered during review: brand grain (store_name is NOT a key),
# one extreme canceled order distorting money-at-risk, and SLA validity per segment.
A = {}

# --- brand (store_name) grain vs store_id grain
brand = fin.assign(brand=fin.store_name.str.strip()).groupby("brand").agg(
    branches=("store_id", "nunique"), orders=("order_id", "count"), gmv=("order_amount", "sum")).reset_index()
brand["gmv_share_pct"] = brand.gmv / brand.gmv.sum() * 100
brand = brand.sort_values("gmv", ascending=False)
A["brand_top"] = [{"brand": x.brand, "branches": int(x.branches), "orders": int(x.orders),
                   "gmv": r2(x.gmv), "gmv_share_pct": r2(x.gmv_share_pct)} for x in brand.head(12).itertuples()]
A["brand_grain"] = {
    "n_brands": int(len(brand)), "n_store_ids": int(fin.store_id.nunique()),
    "names_with_multiple_ids": int((brand.branches > 1).sum()),
    "max_branches": int(brand.branches.max()),
    "top1_brand_gmv_share_pct": r2(brand.gmv_share_pct.iloc[0]),
    "top3_brand_gmv_share_pct": r2(brand.gmv_share_pct.head(3).sum()),
    "top10_brand_gmv_share_pct": r2(brand.gmv_share_pct.head(10).sum()),
}

# --- money at risk: with vs without the extreme-amount flag (>R$1,500)
ext = can[can.order_amount > 1500]
A["at_risk"] = {
    "canceled_amount_raw": r2(can.order_amount.sum()),
    "canceled_amount_clean": r2(can.loc[can.order_amount <= 1500, "order_amount"].sum()),
    "n_extreme_canceled": int(len(ext)),
    "largest_canceled_order": r2(can.order_amount.max()),
    "largest_share_of_raw_pct": r2(can.order_amount.max() / can.order_amount.sum() * 100),
    "clean_pct_of_gmv": r2(can.loc[can.order_amount <= 1500, "order_amount"].sum() / fin.order_amount.sum() * 100),
    "largest_order_store": can.loc[can.order_amount.idxmax(), "store_name"].strip(),
    "largest_order_hub": can.loc[can.order_amount.idxmax(), "hub_name"].strip(),
}

# --- SLA validity: cycle-time distribution is a different process per segment
c = fin[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 1440)]
A["sla_by_segment"] = [{
    "segment": sg, "orders": int(len(x)),
    "p50": r2(x.order_metric_cycle_time.median()), "p90": r2(x.order_metric_cycle_time.quantile(0.9)),
    "prep_median": r2(x.order_metric_production_time.median()),
    "transit_median": r2(x.order_metric_transit_time.median()),
    "over_180min_pct": r2((x.order_metric_cycle_time > 180).mean() * 100),
} for sg, x in c.groupby("store_segment")]
A["sla_by_segment_note"] = {
    "good_share_of_over180_pct": r2((c[c.order_metric_cycle_time > 180].store_segment == "GOOD").mean() * 100),
    "n_over180": int((c.order_metric_cycle_time > 180).sum()),
}

# --- night orders (store likely closed)
night = o[o.hour_local.between(0, 9)]
A["night_orders"] = {
    "orders": int(len(night)), "share_of_orders_pct": r2(len(night) / len(o) * 100),
    "cancel_rate_pct": r2((night.order_status == "CANCELED").mean() * 100),
    "share_of_all_cancels_pct": r2((night.order_status == "CANCELED").sum() / len(can) * 100),
    "day_cancel_rate_pct": r2((o[~o.hour_local.between(0, 9)].order_status == "CANCELED").mean() * 100),
}

R["addendum"] = A
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(R, fh, ensure_ascii=False, indent=2)
print("\n### addendum")
print(json.dumps(A, ensure_ascii=False, indent=1)[:3000])
