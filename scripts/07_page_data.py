"""
07_page_data.py — Compute every aggregated series the 6-page PBI-style mockup needs.
Writes dashboard/page_data.json. Brazil local time (UTC-3) assumption for time series.
All rankings apply a MIN-VOLUME threshold (Senior DA Review requirement).
"""
import pandas as pd, numpy as np, os, json
HERE=os.path.dirname(__file__); PROC=os.path.join(HERE,"..","data","processed"); RAW=os.path.join(HERE,"..","data","raw")
DASH=os.path.join(HERE,"..","dashboard")
f=pd.read_csv(os.path.join(PROC,"fact_orders.csv"),low_memory=False)
d=pd.read_csv(os.path.join(PROC,"dim_deliveries.csv"),low_memory=False)
f["order_moment_created"]=pd.to_datetime(f["order_moment_created"])
f["ts"]=f["order_moment_created"]-pd.Timedelta(hours=3)
f["date"]=f["ts"].dt.date; f["hour"]=f["ts"].dt.hour; f["dow"]=f["ts"].dt.dayofweek; f["month"]=f["ts"].dt.month
f["week"]=f["ts"].dt.to_period("W-SUN").apply(lambda p:p.start_time.date())
fin=f[f.order_status=="FINISHED"].copy()
P={}
DOW=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
MINV=500  # min finished orders for hub/store ranking fairness

# ---------- P1 Executive ----------
P["exec_kpi"]={
 "gmv":round(float(fin.order_amount.sum())),"orders":int(len(f)),"finished":int(len(fin)),
 "aov":round(float(fin.order_amount.mean()),2),"cancel_rate":round(float((f.order_status=="CANCELED").mean()*100),2),
 "fulfill_rate":round(float((f.order_status=="FINISHED").mean()*100),2),
 "median_cycle":round(float(fin.loc[(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=1440),"order_metric_cycle_time"].median()),1),
 "median_km":round(float(d.loc[(d.delivery_status=="DELIVERED")&(d.delivery_distance_meters<=50000),"delivery_distance_meters"].median())/1000,2),
 "active_stores":int(fin.store_id.nunique()),"hubs":int(f.hub_id.nunique()),"cities":int(f.hub_city.nunique()),
 "chargeback":round(float(f.any_chargeback.fillna(0).astype(bool).mean()*100),3),
 "delivery_subsidy":round(float(fin[fin.order_delivery_cost.notna()].order_delivery_cost.mean()-fin.order_delivery_fee.mean()),2),
}
wk=fin.groupby("week").agg(gmv=("order_amount","sum"),orders=("order_id","count")).reset_index()
wk=wk[wk.week>=pd.to_datetime("2021-01-04").date()]
P["weekly"]=[{"week":str(r.week),"gmv":round(r.gmv),"orders":int(r.orders)} for r in wk.itertuples()]
# GMV waterfall by city (contribution)
cty=fin.groupby("hub_city").order_amount.sum().sort_values(ascending=False)
P["city_gmv"]=[{"city":k,"gmv":round(v)} for k,v in cty.items()]
# city cancel rate (all orders) for P1 city risk
citycancel=f.groupby("hub_city").apply(lambda x:(x.order_status=="CANCELED").mean()*100,include_groups=False)

# ---------- P2 Order & Revenue ----------
P["by_hour"]=[{"hour":int(h),"orders":int(v)} for h,v in fin.groupby("hour").size().reindex(range(24),fill_value=0).items()]
P["by_dow"]=[{"dow":DOW[i],"orders":int(v)} for i,v in fin.groupby("dow").size().reindex(range(7),fill_value=0).items()]
hm=fin.groupby(["dow","hour"]).size().reset_index(name="orders")
P["heatmap"]=[{"dow":DOW[int(r.dow)],"hour":int(r.hour),"orders":int(r.orders)} for r in hm.itertuples()]
# calendar heatmap (daily)
cal=fin.groupby("date").size().reset_index(name="orders")
P["calendar"]=[{"date":str(r.date),"orders":int(r.orders)} for r in cal.itertuples()]
# channel type + top channels + ribbon (channel share by month)
cht=fin.groupby("channel_type").agg(orders=("order_id","count"),gmv=("order_amount","sum"),aov=("order_amount","mean")).reset_index()
P["channel_type"]=[{"type":r.channel_type,"orders":int(r.orders),"gmv":round(r.gmv),"aov":round(r.aov,2)} for r in cht.itertuples()]
topch=fin.groupby(["channel_name","channel_type"]).agg(orders=("order_id","count"),gmv=("order_amount","sum")).reset_index().sort_values("gmv",ascending=False).head(8)
P["top_channels"]=[{"channel":r.channel_name,"type":r.channel_type,"orders":int(r.orders),"gmv":round(r.gmv)} for r in topch.itertuples()]
# payment method
pm=fin.groupby("primary_payment_method").size().sort_values(ascending=False)
top6=pm.head(6); other=int(pm.sum()-top6.sum())
P["payment"]=[{"method":k,"orders":int(v),"share":round(v/len(fin)*100,2)} for k,v in top6.items()]+[{"method":"OTHER","orders":other,"share":round(other/len(fin)*100,2)}]
# AOV distribution (histogram of order_amount, capped)
amt=fin[(fin.order_amount>0)&(fin.order_amount<=500)].order_amount
b=[0,25,50,75,100,150,200,300,500]; lab=["<25","25-50","50-75","75-100","100-150","150-200","200-300","300-500"]
P["aov_hist"]=[{"bucket":str(k),"orders":int(v)} for k,v in pd.cut(amt,b,labels=lab).value_counts().reindex(lab).items()]
# segment monthly stacked
sm=fin.groupby(["month","store_segment"]).size().reset_index(name="orders")
P["seg_month"]=[{"month":int(r.month),"segment":r.store_segment,"orders":int(r.orders)} for r in sm.itertuples() if r.month in [1,2,3,4]]

# ---------- P3 Delivery Performance ----------
ct=fin[(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=180)].order_metric_cycle_time
b=[0,20,30,40,50,60,75,90,120,180]; lab=["<20","20-30","30-40","40-50","50-60","60-75","75-90","90-120","120-180"]
P["cycle_hist"]=[{"bucket":str(k),"orders":int(v)} for k,v in pd.cut(ct,b,labels=lab).value_counts().reindex(lab).items()]
P["cycle_pct"]={"p50":round(float(ct.median()),1),"p90":round(float(ct.quantile(.9)),1),"p95":round(float(ct.quantile(.95)),1),"mean":round(float(ct.mean()),1)}
# box stats cycle time by segment
def box(s):
    s=s.dropna(); return {"min":round(float(s.min()),1),"q1":round(float(s.quantile(.25)),1),"med":round(float(s.median()),1),"q3":round(float(s.quantile(.75)),1),"p95":round(float(s.quantile(.95)),1)}
P["cycle_box_seg"]=[{"segment":sg,**box(fin[(fin.store_segment==sg)&(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=180)].order_metric_cycle_time)} for sg in ["FOOD","GOOD"]]
# box by primary driver modal (order-grain proxy)
P["cycle_box_modal"]=[{"modal":md,**box(fin[(fin.primary_driver_modal==md)&(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=180)].order_metric_cycle_time)} for md in ["MOTOBOY","BIKER"]]
# distance vs cycle scatter (sample) + correlation
sc=fin[(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=150)&(fin.dist_total_m>0)&(fin.dist_total_m<=15000)]
P["corr"]={"dist_cycle":round(float(sc.dist_total_m.corr(sc.order_metric_cycle_time)),3),
           "amt_cycle":round(float(sc.order_amount.corr(sc.order_metric_cycle_time)),3),
           "dist_amt":round(float(sc.dist_total_m.corr(sc.order_amount)),3)}
samp=sc.sample(n=600,random_state=7)
P["scatter"]=[{"dist":round(r.dist_total_m/1000,2),"cycle":round(r.order_metric_cycle_time,1),"seg":r.store_segment} for r in samp.itertuples()]
# funnel stage medians (minutes) — production/transit etc.
stages=[("order_metric_production_time","Chuẩn bị (production)"),
        ("order_metric_transit_time","Di chuyển (transit)")]
P["funnel_stage"]=[{"stage":nm,"median_min":round(float(fin.loc[(fin[c]>0)&(fin[c]<=180),c].median()),1)} for c,nm in stages]
# driver modal & type
dd=d[(d.delivery_status=="DELIVERED")&(d.delivery_distance_meters<=50000)]
dm=d.dropna(subset=["driver_modal"]).groupby("driver_modal").size()
P["driver_modal"]=[{"modal":k,"deliveries":int(v),"share":round(v/dm.sum()*100,1),"median_km":round(float(dd[dd.driver_modal==k].delivery_distance_meters.median())/1000,2)} for k,v in dm.items()]
dt=d.dropna(subset=["driver_type"]).groupby("driver_type").size()
P["driver_type"]=[{"type":k,"deliveries":int(v),"share":round(v/dt.sum()*100,1)} for k,v in dt.items()]
# driver productivity distribution
drv=dd[dd.driver_id.notna()].groupby("driver_id").size()
P["driver_prod"]={"active":int(dd.driver_id.nunique()),"median":int(drv.median()),"p90":int(drv.quantile(.9)),"max":int(drv.max()),
                  "top10_share":round(float(drv.sort_values(ascending=False).head(10).sum()/drv.sum()*100),1)}
P["delivery_success"]={"delivery_level":round(float((d.delivery_status=="DELIVERED").mean()*100),2),"order_level":round(float((f.order_status=="FINISHED").mean()*100),2)}

# ---------- P4 Hub & Geographic ----------
hubs=pd.read_csv(os.path.join(RAW,"hubs.csv"),encoding="latin-1")
hub=fin.groupby(["hub_id","hub_name","hub_city","hub_state"]).agg(orders=("order_id","count"),gmv=("order_amount","sum"),aov=("order_amount","mean")).reset_index()
hc=f.groupby("hub_id").apply(lambda x:(x.order_status=="CANCELED").mean()*100,include_groups=False)
# hub cycle time median
hcy=fin[(fin.order_metric_cycle_time>0)&(fin.order_metric_cycle_time<=180)].groupby("hub_id").order_metric_cycle_time.median()
hub["cancel_rate"]=hub.hub_id.map(hc).round(2); hub["cycle_med"]=hub.hub_id.map(hcy).round(1)
hub=hub.merge(hubs[["hub_id","hub_latitude","hub_longitude"]],on="hub_id",how="left")
hub_q=hub[hub.orders>=MINV].copy()
P["hub"]=[{"hub":r.hub_name.replace(" SHOPPING",""),"city":r.hub_city,"state":r.hub_state,"orders":int(r.orders),
           "gmv":round(r.gmv),"aov":round(r.aov,2),"cancel_rate":round(r.cancel_rate,2),"cycle_med":round(r.cycle_med,1) if pd.notna(r.cycle_med) else None,
           "lat":round(float(r.hub_latitude),4),"lng":round(float(r.hub_longitude),4)} for r in hub_q.sort_values("gmv",ascending=False).itertuples()]
P["hub_excluded"]=int((hub.orders<MINV).sum())
hubs2=pd.read_csv(os.path.join(RAW,"hubs.csv"),encoding="latin-1")
citycent=hubs2.groupby("hub_city")[["hub_latitude","hub_longitude"]].mean()
P["city"]=[{"city":r.hub_city,"state":r.hub_state,"orders":int(r.orders),"gmv":round(r.gmv),"aov":round(r.aov,2),"stores":int(r.stores),
            "cancel_rate":round(float(citycancel[r.hub_city]),2),
            "lat":round(float(citycent.loc[r.hub_city,"hub_latitude"]),4),"lng":round(float(citycent.loc[r.hub_city,"hub_longitude"]),4)}
           for r in fin.groupby(["hub_city","hub_state"]).agg(orders=("order_id","count"),gmv=("order_amount","sum"),aov=("order_amount","mean"),stores=("store_id","nunique")).reset_index().sort_values("gmv",ascending=False).itertuples()]

# ---------- P5 Store & Partner ----------
st=fin.groupby(["store_id","store_name","store_segment","hub_city"]).agg(orders=("order_id","count"),gmv=("order_amount","sum"),aov=("order_amount","mean")).reset_index()
sc2=f.groupby("store_id").apply(lambda x:(x.order_status=="CANCELED").mean()*100,include_groups=False)
st["cancel_rate"]=st.store_id.map(sc2).round(2)
st_q=st[st.orders>=100].copy()  # min 100 orders for store ranking
P["store_top"]=[{"store":r.store_name,"seg":r.store_segment,"city":r.hub_city,"orders":int(r.orders),"gmv":round(r.gmv),"cancel_rate":round(r.cancel_rate,2)} for r in st_q.sort_values("gmv",ascending=False).head(12).itertuples()]
P["store_bottom_cancel"]=[{"store":r.store_name,"seg":r.store_segment,"orders":int(r.orders),"cancel_rate":round(r.cancel_rate,2)} for r in st_q.sort_values("cancel_rate",ascending=False).head(10).itertuples()]
# quadrant: gmv (x) vs cancel_rate (y), size=orders — sample of qualifying stores
P["store_quadrant"]=[{"store":r.store_name,"seg":r.store_segment,"gmv":round(r.gmv),"cancel_rate":round(r.cancel_rate,2),"orders":int(r.orders),"aov":round(r.aov,2)} for r in st_q.itertuples()]
P["store_med_cancel"]=round(float(st_q.cancel_rate.median()),2); P["store_med_gmv"]=round(float(st_q.gmv.median()))
# pareto
sto=fin.groupby("store_id").order_amount.sum().sort_values(ascending=False).values
cum=np.cumsum(sto)/sto.sum(); n=len(sto); idx=np.linspace(0,n-1,25).astype(int)
P["pareto"]=[{"store_pct":round((i+1)/n*100,1),"gmv_pct":round(float(cum[i])*100,1)} for i in idx]
P["pareto_stat"]={"top20":round(float(cum[int(np.ceil(n*0.2))-1])*100,1),"stores_80":int((cum<=0.8).sum())+1,"n":int(n)}
# segment summary
seg=fin.groupby("store_segment").agg(orders=("order_id","count"),gmv=("order_amount","sum"),aov=("order_amount","mean"),stores=("store_id","nunique")).reset_index()
segc=f.groupby("store_segment").apply(lambda x:(x.order_status=="CANCELED").mean()*100,include_groups=False)
P["segment"]=[{"segment":r.store_segment,"orders":int(r.orders),"gmv":round(r.gmv),"aov":round(r.aov,2),"stores":int(r.stores),"cancel_rate":round(float(segc[r.store_segment]),2)} for r in seg.itertuples()]

# ---------- P6 Insight Lab ----------
P["delivery_econ"]={"mean_fee":round(float(fin.order_delivery_fee.mean()),2),"mean_cost":round(float(fin[fin.order_delivery_cost.notna()].order_delivery_cost.mean()),2),
                    "free_ship":round(float((fin.order_delivery_fee==0).mean()*100),1),"fee_below_cost":round(float((fin[fin.order_delivery_cost.notna()].order_delivery_fee<fin[fin.order_delivery_cost.notna()].order_delivery_cost).mean()*100),1)}
# cancel drivers: by channel_type, segment, month  (for key-influencers style)
P["cancel_by"]={
 "segment":[{"k":r.store_segment,"v":round(float(segc[r.store_segment]),2)} for r in seg.itertuples()],
 "channel_type":[{"k":k,"v":round(float(v),2)} for k,v in f.groupby("channel_type").apply(lambda x:(x.order_status=="CANCELED").mean()*100,include_groups=False).items()],
 "month":[{"k":"T"+str(int(m)),"v":round(float(v),2)} for m,v in f[f.month.isin([1,2,3,4])].groupby("month").apply(lambda x:(x.order_status=="CANCELED").mean()*100,include_groups=False).items()],
}
# channel_type x segment cross (sankey P5)
cs=fin.groupby(["channel_type","store_segment"]).size().reset_index(name="orders")
P["chan_seg_flow"]=[{"from":r.channel_type,"to":r.store_segment,"orders":int(r.orders)} for r in cs.itertuples()]
P["quality"]={"flag_extreme_amount":int(f.flag_extreme_amount.sum()),"flag_extreme_distance":int((d.delivery_distance_meters>50000).sum()),
 "flag_long_cycle":int(f.flag_long_cycle.sum()),"flag_zero_amount":int(f.flag_zero_amount.sum()),
 "orders_no_payment":int((~f.has_payment).sum()),"orders_no_delivery":int((~f.has_delivery).sum()),"null_driver":int(d.driver_id.isna().sum())}
P["meta"]={"date_min":str(f.order_moment_created.min().date()),"date_max":str(f.order_moment_created.max().date()),"tz":"UTC-3 (assumed)","min_vol_hub":MINV,"min_vol_store":100}

json.dump(P,open(os.path.join(DASH,"page_data.json"),"w"),ensure_ascii=False,indent=1,default=str)
print("wrote dashboard/page_data.json  keys:",len(P))
print("corr dist~cycle:",P["corr"],"| hub kept:",len(P["hub"]),"excluded<%d:"%MINV,P["hub_excluded"])
print("hub top:",P["hub"][0]["hub"],P["hub"][0]["orders"],"| worst cancel hub(≥%d):"%MINV,max(P["hub"],key=lambda h:h["cancel_rate"])["hub"],max(h["cancel_rate"] for h in P["hub"]))
print("funnel:",P["funnel_stage"])
print("store quadrant n:",len(P["store_quadrant"]),"median cancel:",P["store_med_cancel"])
