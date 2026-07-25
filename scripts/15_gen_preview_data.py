"""
15_gen_preview_data.py — Compute exactly the series each v2 Power BI visual will display, so the
offline preview shows the SAME numbers Power BI will render after Refresh.
Output: dashboard/pbi_v2_data.json
"""
import json, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
O = json.load(open(os.path.join(ROOT, "outputs", "userstory_insights.json"), encoding="utf-8"))
P = json.load(open(os.path.join(ROOT, "dashboard", "page_data.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "dashboard", "pbi_v2_data.json")

cols = ["order_id", "store_id", "store_name", "store_segment", "store_plan_price", "hub_name", "hub_city",
        "channel_type", "order_status", "order_amount", "order_delivery_fee", "order_delivery_cost",
        "order_metric_cycle_time", "order_metric_production_time", "order_metric_transit_time",
        "order_hour", "dist_mean_m", "primary_driver_modal", "primary_driver_type"]
o = pd.read_csv(os.path.join(ROOT, "data", "processed", "fact_orders.csv"), usecols=cols)
o["hour_local"] = (o.order_hour - 3) % 24
fin = o[o.order_status == "FINISHED"]
can = o[o.order_status == "CANCELED"]
clean_can = can[can.order_amount <= 1500]          # flag_extreme_amount = FALSE
r = lambda x: None if pd.isna(x) else round(float(x), 2)
D = {}

VB = ["≤R$30", "R$30–60", "R$60–100", "R$100–200", "R$200–500", ">R$500"]
DB = ["<1 km", "1-2 km", "2-3 km", "3-5 km", "5-10 km", ">10 km"]
vband = pd.cut(o.order_amount, [-.01, 30, 60, 100, 200, 500, 1e12], labels=VB)
dband = pd.cut(o.dist_mean_m, [0, 1000, 2000, 3000, 5000, 10000, 1e9], labels=DB)

# ---- cards (measure -> display string), mirroring the DAX definitions
k = O["kpi"]; e = O["delivery_econ"]; a = O["addendum"]
cyc = fin[(fin.order_metric_cycle_time > 0) & (fin.order_metric_cycle_time <= 1440)]
sla = O["cycle"]
D["cards"] = {
    "GMV": f"R${k['gmv']/1e6:.2f}M", "Finished Orders": f"{k['finished']:,}".replace(",", "."),
    "Total Orders": f"{k['orders']:,}".replace(",", "."), "AOV": f"R${k['aov']:.2f}",
    "Median Order Value": f"R${k['median_order_value']:.2f}",
    "Cancellation Rate": f"{k['cancel_rate_pct']:.2f}%",
    "Canceled Orders": f"{k['canceled']:,}".replace(",", "."),
    "Canceled GMV (at risk)": f"R${a['at_risk']['canceled_amount_clean']/1e6:.2f}M",
    "Canceled GMV (raw, incl. outliers)": f"R${a['at_risk']['canceled_amount_raw']/1e6:.2f}M",
    "Canceled GMV % of GMV": f"{a['at_risk']['clean_pct_of_gmv']:.2f}%",
    "GMV Concentration Top1 Brand %": f"{a['brand_grain']['top1_brand_gmv_share_pct']:.1f}%",
    "Fulfillment Rate": f"{100-k['cancel_rate_pct']:.2f}%",
    "Median Cycle FOOD (min)": f"{a['sla_by_segment'][0]['p50']:.1f}",
    "P90 Cycle FOOD (min)": f"{a['sla_by_segment'][0]['p90']:.1f}",
    "Median Cycle GOOD (min)": f"{a['sla_by_segment'][1]['p50']:.1f}",
    "P90 Cycle GOOD (min)": f"{a['sla_by_segment'][1]['p90']:.0f}",
    "SLA Breach % (over 60min)": f"{sla['over_60min_pct']:.1f}%",
    "Median Distance (km)": f"{O['fleet']['median_km']:.2f} km",
    "Delivery Success Rate": f"{O['fleet']['success_rate_pct']:.2f}%",
    "Active Drivers": f"{O['fleet']['active_drivers']:,}".replace(",", "."),
    "Deliveries": f"{O['fleet']['deliveries']:,}".replace(",", "."),
    "Active Stores": f"{O['concentration']['n_active_stores']:,}".replace(",", "."),
    "Active Brands": f"{a['brand_grain']['n_brands']:,}".replace(",", "."),
    "Payments": "400.834", "Chargeback Rate": f"{O['data_quality']['chargeback_rate_pct']:.2f}%",
    "Delivery Margin": f"−R${e['subsidy_total']/1000:.0f}k",
    "Free-ship Margin": f"−R${e['loss_freeship_orders']/1000:.0f}k",
    "Paid-ship Margin": f"+R${e['margin_paidship_orders']/1000:.0f}k",
    "Delivery Margin / Order": f"−R${e['subsidy_per_order']:.2f}",
    "Free-ship Order %": f"{e['free_ship_pct']:.1f}%",
    "Delivery Subsidy / Order": f"R${e['subsidy_per_order']:.2f}",
    "Median Cycle (min)": f"{sla['p50']:.1f}", "P90 Cycle (min)": f"{sla['p90']:.1f}",
}

# ---- P1
D["lineGMV"] = [{"x": w["week"][5:], "y": w["gmv"]} for w in P["weekly"]]
D["barBrand"] = [{"k": b["brand"], "v": b["gmv"]} for b in a["brand_top"]]
D["donutChan"] = [{"k": c["type"], "v": c["gmv"]} for c in P["channel_type"]]
D["colCancMonth"] = [{"k": f"T{m['month']}", "v": m["cancel_rate_pct"]} for m in O["monthly"]]
D["colCityGMV"] = [{"k": c["city"].title(), "v": c["gmv"]} for c in P["city_gmv"]]

# ---- P2
D["colHour"] = [{"k": str(h["hour"]), "v": h["orders"]} for h in O["by_hour"]]
D["lineCancHour"] = [{"x": str(h["hour"]), "y": h["cancel_rate_pct"]} for h in O["by_hour"]]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
dmap = {d["dow"][:3]: d["orders"] for d in O["by_dow"]}
D["colDow"] = [{"k": d, "v": dmap[d]} for d in DOW]
dp = o.assign(dp=pd.cut(o.hour_local, [-1, 9, 14, 17, 23],
                        labels=["Đêm 0–9h", "Trưa 10–14h", "Chiều 15–17h", "Tối 18–23h"]))
D["colDaypart"] = [{"k": str(kk), "v": int(v)} for kk, v in
                   dp[dp.order_status == "FINISHED"].groupby("dp", observed=True).size().items()]
D["colValueBand"] = [{"k": b["band"].replace("≤30", "≤R$30").replace("30-60", "R$30–60")
                      .replace("60-100", "R$60–100").replace("100-200", "R$100–200")
                      .replace("200-500", "R$200–500").replace(">500", ">R$500"), "v": b["orders"]}
                     for b in O["cancel_by_value_band"]]
D["donutPay"] = [{"k": p["method"], "v": p["orders"]} for p in P["payment"]]

# ---- P3
D["colPhase"] = [{"k": s["segment"], "series": [("Prep", s["prep_median"]), ("Transit", s["transit_median"]),
                                                ("Cycle", s["p50"])]} for s in a["sla_by_segment"]]
CB = ["<=30m", "30-45m", "45-60m", "60-90m", "90-180m", ">180m"]
cb = pd.cut(cyc.order_metric_cycle_time, [0, 30, 45, 60, 90, 180, 1440], labels=CB)
D["colCycleHist"] = [{"k": str(kk), "v": int(v)} for kk, v in cyc.groupby(cb, observed=True).size().items()]
hub_sc = fin.groupby("hub_name").agg(cyc=("order_metric_cycle_time", "median"),
                                     dist=("dist_mean_m", "median"), n=("order_id", "count")).reset_index()
hub_sc = hub_sc[(hub_sc.n >= 500) & (hub_sc.cyc <= 200)]
D["scatHub"] = [{"k": x.hub_name.strip(), "x": r(x.dist / 1000), "y": r(x.cyc), "s": int(x.n)} for x in hub_sc.itertuples()]
D["colDistBand"] = [{"k": b["band_km"].replace("<1", "<1 km").replace("1-2", "1-2 km").replace("2-3", "2-3 km")
                     .replace("3-5", "3-5 km").replace("5-10", "5-10 km").replace("10-50", ">10 km"),
                     "v": b["median_cycle"]} for b in O["distance_band"]]
md = fin.dropna(subset=["primary_driver_modal"]).groupby(["primary_driver_modal", "primary_driver_type"]).size()
D["colModal"] = [{"k": m, "series": [(t, int(md.get((m, t), 0))) for t in ["FREELANCE", "LOGISTIC OPERATOR"]]}
                 for m in ["MOTOBOY", "BIKER"]]

# ---- P4
hubs = [h for h in O["hubs"] if h["orders"] >= 500]
D["barHubCancel"] = [{"k": h["hub"], "v": h["cancel_rate_pct"]} for h in
                     sorted(hubs, key=lambda h: -h["cancel_rate_pct"])[:14]]
D["scatHubQuad"] = [{"k": h["hub"], "x": h["orders"], "y": h["cancel_rate_pct"], "s": h["gmv"]} for h in hubs]
D["tblHub"] = {"cols": ["hub_name", "city", "Orders", "GMV", "Cancel%", "Cycle", "Prep"],
               "rows": [[h["hub"], h["city"].title(), f"{h['orders']:,}".replace(",", "."),
                         f"R${h['gmv']/1e6:.2f}M", f"{h['cancel_rate_pct']:.2f}%",
                         f"{h['median_cycle']:.1f}" if h["median_cycle"] else "–",
                         f"{h['median_prep']:.1f}" if h["median_prep"] else "–"]
                        for h in sorted(hubs, key=lambda h: -h["orders"])[:9]]}

# ---- P5
D["barBrand5"] = D["barBrand"]
sq = P["store_quadrant"]
D["scatPartner"] = [{"k": s["store"].strip(), "x": s["gmv"], "y": s["cancel_rate"], "s": s["orders"]} for s in sq]
D["tblPlan"] = {"cols": ["plan_tier", "Stores", "Orders", "GMV", "AOV", "Cancel%"],
                "rows": [[f"R${p['plan_price']:.2f}", f"{p['stores']}", f"{p['orders']:,}".replace(",", "."),
                          f"R${p['gmv']/1e6:.2f}M", f"R${p['aov']:.2f}", f"{p['cancel_rate_pct']:.2f}%"]
                         for p in O["plan_tier"][:6]]}
st = fin.groupby(["store_id", "store_name", "store_segment"]).agg(
    gmv=("order_amount", "sum"), n=("order_id", "count")).reset_index()
sc = o.groupby("store_id").apply(lambda d: (d.order_status == "CANCELED").mean() * 100, include_groups=False)
st["cr"] = st.store_id.map(sc)
D["tblStore"] = {"cols": ["store_label", "seg", "GMV", "Orders", "Cancel%"],
                 "rows": [[f"{x.store_name.strip()} #{x.store_id}", x.store_segment, f"R${x.gmv/1e3:.0f}k",
                           f"{x.n:,}".replace(",", "."), f"{x.cr:.2f}%"]
                          for x in st.sort_values("gmv", ascending=False).head(8).itertuples()]}

# ---- P6
D["matSegChan"] = {"rows": ["FOOD", "GOOD"], "cols": ["MARKETPLACE", "OWN CHANNEL"],
                   "cells": {f"{x['segment']}|{x['channel_type']}": (x["cancel_rate_pct"], x["orders"])
                             for x in O["cancel_by_segment_channel"]}}
D["colCancHour"] = D["lineCancHour"]
D["colCancValue"] = [{"k": b["band"], "v": b["cancel_rate_pct"]} for b in O["cancel_by_value_band"]]
D["lineCancMonth"] = [{"x": f"T{m['month']}", "y": m["cancel_rate_pct"]} for m in O["monthly"]]
ch = clean_can.groupby(clean_can.hub_name.str.strip()).order_amount.sum().sort_values(ascending=False).head(10)
D["barCancHub"] = [{"k": kk, "v": r(v)} for kk, v in ch.items()]

# ---- P7 (margin = fee - cost, only orders with cost)
ec = fin.dropna(subset=["order_delivery_cost"]).copy()
ec["margin"] = ec.order_delivery_fee - ec.order_delivery_cost
ec["vb"] = pd.cut(ec.order_amount, [-.01, 30, 60, 100, 200, 500, 1e12], labels=VB)
ec["db"] = pd.cut(ec.dist_mean_m, [0, 1000, 2000, 3000, 5000, 10000, 1e9], labels=DB)
D["colMarDist"] = [{"k": str(kk), "v": r(v)} for kk, v in ec.groupby("db", observed=True).margin.sum().items()]
D["colMarValue"] = [{"k": str(kk), "v": r(v)} for kk, v in ec.groupby("vb", observed=True).margin.sum().items()]
D["colFeeCost"] = [{"k": s["segment"], "series": [("Fee", s["mean_fee"]), ("Cost", s["mean_cost"])]}
                   for s in O["econ_by_segment"]]
piv = ec.pivot_table(index="vb", columns="db", values="margin", aggfunc="sum", observed=True)
D["matPolicy"] = {"rows": VB, "cols": DB,
                  "cells": {f"{i}|{c}": r(piv.loc[i, c]) for i in piv.index for c in piv.columns
                            if not pd.isna(piv.loc[i, c])}}

# ---- P8 anomaly register: raw vs outlier-filtered canceled money per store
raw = can.groupby([can.store_name.str.strip(), can.hub_name.str.strip()]).order_amount.agg(["sum", "count"])
cln = clean_can.groupby([clean_can.store_name.str.strip(), clean_can.hub_name.str.strip()]).order_amount.sum()
an = raw.join(cln.rename("clean")).fillna(0).sort_values("sum", ascending=False).head(8).reset_index()
an.columns = ["store", "hub", "raw", "n", "clean"]
D["tblAnomaly"] = {"cols": ["store_label", "hub", "Canceled raw", "Canceled at-risk", "Đơn hủy"],
                   "rows": [[x.store, x.hub, f"R${x.raw/1e3:,.0f}k", f"R${x.clean/1e3:,.0f}k", f"{int(x.n)}"]
                            for x in an.itertuples()]}

json.dump(D, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"wrote {OUT}  ({len(D)} keys)")
print("cards:", len(D["cards"]), "| sample:", {k: D['cards'][k] for k in list(D['cards'])[:6]})
