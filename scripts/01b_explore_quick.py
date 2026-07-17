import pandas as pd, os
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 60)

def rd(f, enc="utf-8"):
    try: return pd.read_csv(os.path.join(RAW, f+".csv"), low_memory=False)
    except UnicodeDecodeError: return pd.read_csv(os.path.join(RAW, f+".csv"), low_memory=False, encoding="latin-1")

hb = rd("hubs")
print("HUBS shape", hb.shape); print(hb.to_string()); print()
print("hub_state counts:\n", hb.hub_state.value_counts().to_string())
print("hub_city counts:\n", hb.hub_city.value_counts().to_string())

o = rd("orders")
print("\nORDERS head:\n", o.head(3).to_string())
print("\norder_status:\n", o.order_status.value_counts(dropna=False).to_string())
print("\norder_amount describe:\n", o.order_amount.describe().to_string())
print("order_delivery_fee describe:\n", o.order_delivery_fee.describe().to_string())
print("order_delivery_cost describe:\n", o.order_delivery_cost.describe().to_string())
print("order_metric_cycle_time describe:\n", o.order_metric_cycle_time.describe().to_string())
print("\nmonth counts:\n", o.order_created_month.value_counts().sort_index().to_string())
print("\nzero order_amount rows:", (o.order_amount==0).sum(), "| negative:", (o.order_amount<0).sum())

d = rd("deliveries")
print("\ndelivery_status:\n", d.delivery_status.value_counts(dropna=False).to_string())
print("delivery_distance describe:\n", d.delivery_distance_meters.describe().to_string())

p = rd("payments")
print("\npayment_method:\n", p.payment_method.value_counts(dropna=False).to_string())
print("payment_status:\n", p.payment_status.value_counts(dropna=False).to_string())
print("payment_amount describe:\n", p.payment_amount.describe().to_string())

st = rd("stores")
print("\nstore_segment:\n", st.store_segment.value_counts(dropna=False).to_string())
print("store_plan_price:\n", st.store_plan_price.value_counts(dropna=False).sort_index().to_string())

ch = rd("channels")
print("\nchannel_type:\n", ch.channel_type.value_counts().to_string())
print("channel sample:\n", ch.head(15).to_string())

dr = rd("drivers")
print("\ndriver_modal:\n", dr.driver_modal.value_counts().to_string())
print("driver_type:\n", dr.driver_type.value_counts().to_string())

# FK integrity
print("\n--- FK integrity ---")
print("orders.store_id not in stores:", (~o.store_id.isin(st.store_id)).sum(), "of", len(o))
print("orders with store_id null:", o.store_id.isna().sum())
print("orders.channel_id not in channels:", (~o.channel_id.isin(ch.channel_id)).sum())
print("deliveries.delivery_order_id not in orders:", (~d.delivery_order_id.isin(o.order_id)).sum())
print("payments.payment_order_id not in orders:", (~p.payment_order_id.isin(o.order_id)).sum())
print("orders without delivery:", (~o.order_id.isin(d.delivery_order_id)).sum())
print("orders without payment:", (~o.order_id.isin(p.payment_order_id)).sum())
# multiple deliveries per order?
print("orders with >1 delivery:", (d.delivery_order_id.value_counts()>1).sum())
print("orders with >1 payment:", (p.payment_order_id.value_counts()>1).sum())
print("stores.hub_id not in hubs:", (~st.hub_id.isin(hb.hub_id)).sum())
