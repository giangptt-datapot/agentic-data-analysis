"""
03_eda.py — EDA + KPI computation on the curated fact table.
Emits a compact numeric report used to back the insights. Writes outputs/eda_metrics.json.
"""
import pandas as pd, numpy as np, os, json

HERE = os.path.dirname(__file__)
PROC = os.path.join(HERE, "..", "data", "processed")
OUT = os.path.join(HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)

f = pd.read_csv(os.path.join(PROC, "fact_orders.csv"), low_memory=False)
f["order_moment_created"] = pd.to_datetime(f["order_moment_created"])
fin = f[f.order_status == "FINISHED"].copy()   # completed orders
M = {}

def p(k, v):
    M[k] = v
    print(f"{k}: {v}")

print("="*70); print("HEADLINE KPIs"); print("="*70)
p("total_orders", int(len(f)))
p("finished_orders", int((f.order_status=="FINISHED").sum()))
p("canceled_orders", int((f.order_status=="CANCELED").sum()))
p("cancel_rate_pct", round((f.order_status=="CANCELED").mean()*100, 2))
p("gmv_finished_brl", round(fin.order_amount.sum(), 2))
p("aov_finished_brl", round(fin.order_amount.mean(), 2))
p("median_order_brl", round(fin.order_amount.median(), 2))
p("n_stores", int(f.store_id.nunique()))
p("n_hubs", int(f.hub_id.nunique()))
p("n_channels", int(f.channel_id.nunique()))
p("date_min", str(f.order_moment_created.min()))
p("date_max", str(f.order_moment_created.max()))

print("\n--- Cancellation by month ---")
f["month"] = f.order_moment_created.dt.month
cbm = f.groupby("month").agg(orders=("order_id","count"),
        cancel=("order_status", lambda s:(s=="CANCELED").sum()))
cbm["cancel_rate"]= (cbm.cancel/cbm.orders*100).round(2)
print(cbm.to_string()); M["cancel_by_month"]=cbm.reset_index().to_dict("records")

print("\n--- Segment (GOOD vs FOOD) ---")
seg = fin.groupby("store_segment").agg(orders=("order_id","count"),
        gmv=("order_amount","sum"), aov=("order_amount","mean")).round(2)
seg["gmv_share_pct"]=(seg.gmv/seg.gmv.sum()*100).round(2)
seg["order_share_pct"]=(seg.orders/seg.orders.sum()*100).round(2)
print(seg.to_string()); M["segment"]=seg.reset_index().to_dict("records")
# cancel rate by segment (all orders)
segc = f.groupby("store_segment").apply(lambda d:(d.order_status=="CANCELED").mean()*100, include_groups=False).round(2)
print("cancel_rate by segment:\n", segc.to_string()); M["cancel_by_segment"]=segc.to_dict()

print("\n--- Channel type ---")
cht = fin.groupby("channel_type").agg(orders=("order_id","count"),
        gmv=("order_amount","sum"), aov=("order_amount","mean")).round(2)
cht["gmv_share_pct"]=(cht.gmv/cht.gmv.sum()*100).round(2)
print(cht.to_string()); M["channel_type"]=cht.reset_index().to_dict("records")

print("\n--- Top channels by orders ---")
topch = fin.groupby("channel_name").agg(orders=("order_id","count"), gmv=("order_amount","sum")).sort_values("orders",ascending=False).head(8).round(0)
print(topch.to_string()); M["top_channels"]=topch.reset_index().to_dict("records")

print("\n--- City ---")
city = fin.groupby("hub_city").agg(orders=("order_id","count"), gmv=("order_amount","sum"),
        aov=("order_amount","mean"), stores=("store_id","nunique")).round(2)
city["gmv_share_pct"]=(city.gmv/city.gmv.sum()*100).round(2)
print(city.sort_values("gmv",ascending=False).to_string()); M["city"]=city.reset_index().to_dict("records")

print("\n--- Payment method (order-level primary) ---")
pm = fin.groupby("primary_payment_method").agg(orders=("order_id","count")).sort_values("orders",ascending=False)
pm["share_pct"]=(pm.orders/pm.orders.sum()*100).round(2)
print(pm.head(10).to_string()); M["payment_method"]=pm.reset_index().head(10).to_dict("records")

print("\n--- Chargeback ---")
p("orders_with_chargeback", int(f.any_chargeback.fillna(0).astype(bool).sum()))
p("chargeback_rate_pct", round(f.any_chargeback.fillna(0).astype(bool).mean()*100,3))

print("\n--- Delivery ops (finished, with delivery, sane distance <50km) ---")
d = pd.read_csv(os.path.join(PROC,"dim_deliveries.csv"), low_memory=False)
dd = d[(d.delivery_status=="DELIVERED") & (d.delivery_distance_meters<=50000)]
p("delivered_count", int((d.delivery_status=="DELIVERED").sum()))
p("delivery_cancel_rate_pct", round((d.delivery_status=="CANCELLED").mean()*100,2))
p("median_distance_m_sane", round(dd.delivery_distance_meters.median(),0))
p("mean_distance_m_sane", round(dd.delivery_distance_meters.mean(),0))
p("extreme_distance_rows", int((d.delivery_distance_meters>50000).sum()))
p("null_driver_rows", int(d.driver_id.isna().sum()))
print("\ndriver modal share of deliveries:")
dms = d.groupby("driver_modal").size(); print((dms/dms.sum()*100).round(2).to_string()); M["driver_modal"]=(dms/dms.sum()*100).round(2).to_dict()
print("driver type share:")
dts = d.groupby("driver_type").size(); print((dts/dts.sum()*100).round(2).to_string()); M["driver_type"]=(dts/dts.sum()*100).round(2).to_dict()
# distance by modal
print("median distance by modal (sane):")
print(dd.groupby("driver_modal").delivery_distance_meters.median().round(0).to_string())
M["dist_by_modal"]=dd.groupby("driver_modal").delivery_distance_meters.median().round(0).to_dict()

print("\n--- Cycle time (finished, sane <1440 min) ---")
ct = fin[(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=1440)]
p("median_cycle_min", round(ct.order_metric_cycle_time.median(),1))
p("mean_cycle_min", round(ct.order_metric_cycle_time.mean(),1))
p("p90_cycle_min", round(ct.order_metric_cycle_time.quantile(0.9),1))

print("\n--- Temporal: hour & dow ---")
byh = fin.groupby("order_hour").size(); M["orders_by_hour"]=byh.to_dict()
print("peak hours:", byh.sort_values(ascending=False).head(5).to_dict())
bydow = fin.groupby("order_dow_name").size().reindex(
    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
print("by dow:\n", bydow.to_string()); M["orders_by_dow"]=bydow.to_dict()

print("\n--- Store concentration (Pareto) ---")
sto = fin.groupby("store_id").order_amount.sum().sort_values(ascending=False)
cum = sto.cumsum()/sto.sum()
n20 = int(np.ceil(len(sto)*0.2))
p("top20pct_stores_gmv_share", round(sto.head(n20).sum()/sto.sum()*100,1))
p("active_stores_finished", int(len(sto)))
# stores needed for 80% gmv
n80 = int((cum<=0.8).sum())+1
p("stores_for_80pct_gmv", n80)
p("stores_for_80pct_gmv_pct_of_all", round(n80/len(sto)*100,1))

print("\n--- Delivery fee economics ---")
ff = fin[fin.order_delivery_cost.notna()]
p("mean_delivery_fee_charged", round(fin.order_delivery_fee.mean(),2))
p("mean_delivery_cost", round(ff.order_delivery_cost.mean(),2))
p("free_delivery_share_pct", round((fin.order_delivery_fee==0).mean()*100,1))
p("orders_fee_below_cost_pct", round((ff.order_delivery_fee < ff.order_delivery_cost).mean()*100,1))

json.dump(M, open(os.path.join(OUT,"eda_metrics.json"),"w"), indent=2, default=str)
print("\nwrote outputs/eda_metrics.json")
