"""06_model_checks.py — extra stats to ground the PBI data model + concept proposal."""
import pandas as pd, numpy as np, os
HERE=os.path.dirname(__file__); PROC=os.path.join(HERE,"..","data","processed"); RAW=os.path.join(HERE,"..","data","raw")
f=pd.read_csv(os.path.join(PROC,"fact_orders.csv"),low_memory=False)
d=pd.read_csv(os.path.join(PROC,"dim_deliveries.csv"),low_memory=False)
o=pd.read_csv(os.path.join(RAW,"orders.csv"),low_memory=False)

print("=== orders columns (check customer_id presence) ===")
print([c for c in o.columns])
print("has customer_id:", any('custom' in c.lower() for c in o.columns))
print("has product/item cols:", any(k in c.lower() for c in o.columns for k in ['product','item','sku']))

fin=f[f.order_status=='FINISHED']
print("\n=== Hub-level spread (finished) ===")
hub=fin.groupby(['hub_name','hub_city']).agg(orders=('order_id','count'),gmv=('order_amount','sum'),
    aov=('order_amount','mean')).reset_index()
# cancel rate by hub (all)
hc=f.groupby('hub_name').apply(lambda x:(x.order_status=='CANCELED').mean()*100,include_groups=False)
hub['cancel_rate']=hub['hub_name'].map(hc).round(2)
hub=hub.sort_values('orders',ascending=False)
print("n_hubs:",len(hub),"| orders range:",hub.orders.min(),"-",hub.orders.max())
print("cancel_rate range: %.2f - %.2f"%(hub.cancel_rate.min(),hub.cancel_rate.max()))
print(hub.head(5).to_string(index=False))
print("...tail:"); print(hub.tail(3).to_string(index=False))

print("\n=== Driver-level (deliveries with driver, delivered, sane dist) ===")
dd=d[(d.delivery_status=='DELIVERED')&(d.delivery_distance_meters<=50000)&(d.driver_id.notna())]
drv=dd.groupby('driver_id').agg(deliveries=('delivery_id','count'),dist=('delivery_distance_meters','mean'))
print("active drivers (delivered):",dd.driver_id.nunique())
print("deliveries per driver: median %.0f, p90 %.0f, max %.0f"%(drv.deliveries.median(),drv.deliveries.quantile(.9),drv.deliveries.max()))
print("top10 drivers share of deliveries: %.1f%%"%(drv.deliveries.sort_values(ascending=False).head(10).sum()/drv.deliveries.sum()*100))

print("\n=== distance vs cycle_time relationship (finished, sane) ===")
m=fin[(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=180)&(fin.dist_total_m>0)&(fin.dist_total_m<=50000)]
print("n:",len(m),"corr(dist, cycle):",round(m['dist_total_m'].corr(m['order_metric_cycle_time']),3))
print("corr(order_amount, cycle):",round(m['order_amount'].corr(m['order_metric_cycle_time']),3))
print("corr(dist, order_amount):",round(m['dist_total_m'].corr(m['order_amount']),3))

print("\n=== delivery success rate ===")
print("delivered/total deliveries: %.2f%%"%((d.delivery_status=='DELIVERED').mean()*100))
print("order fulfillment (finished/total orders): %.2f%%"%((f.order_status=='FINISHED').mean()*100))

print("\n=== payment vs order amount (double-count risk demo) ===")
print("sum(order_amount) finished:  R$%.0f"%fin.order_amount.sum())
pay=pd.read_csv(os.path.join(RAW,'payments.csv'),low_memory=False)
print("sum(payment_amount) all:     R$%.0f  <-- would DOUBLE COUNT if used as revenue"%pay.payment_amount.sum())
print("payments per order >1:", (pay.payment_order_id.value_counts()>1).sum())
