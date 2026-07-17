"""
02_etl.py — Cleaning + ETL for Brazilian Delivery Center.

Design principles (per brief):
  * Do NOT drop anomalous rows whose cause is unknown. Instead FLAG them.
  * Aggregate one-to-many tables (payments, deliveries) BEFORE joining to orders
    to avoid revenue/count fan-out (double counting).
  * Keep order_id as the analytical grain for the curated fact table.

Outputs (to data/processed/):
  fact_orders.csv        one row per order + store/hub/channel dims + payment/delivery rollups + flags
  dim_deliveries.csv     one row per delivery (delivery-level analysis: distance, driver, status)
  etl_log.txt            human-readable record of every transformation + row counts
"""
import pandas as pd
import numpy as np
import os

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, "..", "data", "raw")
OUT = os.path.join(HERE, "..", "data", "processed")
os.makedirs(OUT, exist_ok=True)
LOG = []


def log(msg):
    print(msg)
    LOG.append(str(msg))


def rd(f):
    """utf-8 with latin-1 fallback (hubs/stores carry Portuguese accents)."""
    p = os.path.join(RAW, f + ".csv")
    try:
        return pd.read_csv(p, low_memory=False)
    except UnicodeDecodeError:
        log(f"  [encoding] {f}.csv read as latin-1 (utf-8 failed)")
        return pd.read_csv(p, low_memory=False, encoding="latin-1")


def main():
    log("=" * 70)
    log("ETL RUN — Brazilian Delivery Center")
    log("=" * 70)

    channels = rd("channels")
    deliveries = rd("deliveries")
    drivers = rd("drivers")
    hubs = rd("hubs")
    orders = rd("orders")
    payments = rd("payments")
    stores = rd("stores")

    for nm, df in [("orders", orders), ("payments", payments), ("deliveries", deliveries),
                   ("stores", stores), ("hubs", hubs), ("channels", channels), ("drivers", drivers)]:
        log(f"loaded {nm}: {df.shape[0]:,} rows x {df.shape[1]} cols")

    # ---------------------------------------------------------------
    # 1. Parse timestamps on orders (created + finished are most complete)
    # ---------------------------------------------------------------
    log("\n[1] Parse order timestamps")
    ts_cols = ["order_moment_created", "order_moment_accepted", "order_moment_ready",
               "order_moment_collected", "order_moment_in_expedition", "order_moment_delivering",
               "order_moment_delivered", "order_moment_finished"]
    for c in ts_cols:
        orders[c] = pd.to_datetime(orders[c], format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
    log(f"  order_moment_created range: {orders.order_moment_created.min()} -> {orders.order_moment_created.max()}")
    # canonical order timestamp = created; completion = finished (delivered is ~95% null)
    orders["order_date"] = orders["order_moment_created"].dt.date
    orders["order_dow"] = orders["order_moment_created"].dt.dayofweek       # 0=Mon
    orders["order_dow_name"] = orders["order_moment_created"].dt.day_name()
    orders["order_hour"] = orders["order_moment_created"].dt.hour
    orders["order_week"] = orders["order_moment_created"].dt.to_period("W").astype(str)
    log("  derived: order_date, order_dow, order_dow_name, order_hour, order_week")

    # ---------------------------------------------------------------
    # 2. Data-quality FLAGS on orders (no rows removed)
    # ---------------------------------------------------------------
    log("\n[2] Quality flags on orders (rows kept, only flagged)")
    orders["flag_zero_amount"] = orders["order_amount"] <= 0
    # Extreme order value: cap reference = 99.9th percentile of finished orders
    amt_p999 = orders.loc[orders.order_status == "FINISHED", "order_amount"].quantile(0.999)
    orders["flag_extreme_amount"] = orders["order_amount"] > amt_p999
    # Cycle time > 24h is operationally implausible for food/retail delivery
    orders["flag_long_cycle"] = orders["order_metric_cycle_time"] > 1440
    log(f"  flag_zero_amount: {int(orders.flag_zero_amount.sum()):,}")
    log(f"  flag_extreme_amount (> p99.9 = {amt_p999:,.0f} BRL): {int(orders.flag_extreme_amount.sum()):,}")
    log(f"  flag_long_cycle (>1440 min): {int(orders.flag_long_cycle.sum()):,}")

    # ---------------------------------------------------------------
    # 3. Payments rollup per order (avoid fan-out on join)
    # ---------------------------------------------------------------
    log("\n[3] Payments rollup per order")
    pay = payments.copy()
    pay["is_chargeback"] = pay["payment_status"].eq("CHARGEBACK")
    pay["is_paid"] = pay["payment_status"].eq("PAID")
    # primary method = method of the largest payment for that order
    pay_sorted = pay.sort_values("payment_amount", ascending=False)
    primary_method = pay_sorted.groupby("payment_order_id")["payment_method"].first()
    pay_roll = pay.groupby("payment_order_id").agg(
        pay_total=("payment_amount", "sum"),
        pay_fee_total=("payment_fee", "sum"),
        n_payments=("payment_id", "count"),
        any_chargeback=("is_chargeback", "max"),
        all_paid=("is_paid", "min"),
    ).reset_index()
    pay_roll["primary_payment_method"] = pay_roll["payment_order_id"].map(primary_method)
    pay_roll = pay_roll.rename(columns={"payment_order_id": "order_id"})
    log(f"  payments {len(payments):,} rows -> {len(pay_roll):,} order-level rows "
        f"(orders with split payment: {int((pay_roll.n_payments>1).sum()):,})")

    # ---------------------------------------------------------------
    # 4. Deliveries rollup per order + delivery-level dim
    # ---------------------------------------------------------------
    log("\n[4] Deliveries rollup per order + delivery dim")
    dv = deliveries.copy()
    dv["flag_extreme_distance"] = dv["delivery_distance_meters"] > 50000  # >50 km intra-city implausible
    dv = dv.merge(drivers, on="driver_id", how="left")
    dv_roll = dv.groupby("delivery_order_id").agg(
        n_deliveries=("delivery_id", "count"),
        dist_total_m=("delivery_distance_meters", "sum"),
        dist_mean_m=("delivery_distance_meters", "mean"),
        any_delivery_cancelled=("delivery_status", lambda s: (s == "CANCELLED").any()),
    ).reset_index().rename(columns={"delivery_order_id": "order_id"})
    # primary driver modal/type = from first (lowest delivery_id) delivery of the order
    first_del = dv.sort_values("delivery_id").groupby("delivery_order_id").first()
    dv_roll["primary_driver_modal"] = dv_roll["order_id"].map(first_del["driver_modal"])
    dv_roll["primary_driver_type"] = dv_roll["order_id"].map(first_del["driver_type"])
    log(f"  deliveries {len(deliveries):,} rows -> {len(dv_roll):,} order-level rows "
        f"(orders with >1 delivery: {int((dv_roll.n_deliveries>1).sum()):,})")
    log(f"  flag_extreme_distance (>50km) on delivery rows: {int(dv['flag_extreme_distance'].sum()):,}")

    # ---------------------------------------------------------------
    # 5. Dimension joins (store -> hub, channel)
    # ---------------------------------------------------------------
    log("\n[5] Join dims: store -> hub, channel")
    store_dim = stores.merge(hubs, on="hub_id", how="left", suffixes=("_store", "_hub"))
    fact = orders.merge(
        store_dim[["store_id", "store_name", "store_segment", "store_plan_price",
                   "hub_id", "hub_name", "hub_city", "hub_state"]],
        on="store_id", how="left")
    fact = fact.merge(channels, on="channel_id", how="left")
    fact = fact.merge(pay_roll, on="order_id", how="left")
    fact = fact.merge(dv_roll, on="order_id", how="left")
    log(f"  fact_orders shape: {fact.shape}")

    # coverage flags
    fact["has_payment"] = fact["n_payments"].notna()
    fact["has_delivery"] = fact["n_deliveries"].notna()
    log(f"  orders w/o payment record: {int((~fact.has_payment).sum()):,}")
    log(f"  orders w/o delivery record: {int((~fact.has_delivery).sum()):,}")

    # ---------------------------------------------------------------
    # 6. Save
    # ---------------------------------------------------------------
    log("\n[6] Write outputs")
    keep = ["order_id", "store_id", "store_name", "store_segment", "store_plan_price",
            "hub_id", "hub_name", "hub_city", "hub_state",
            "channel_id", "channel_name", "channel_type",
            "order_status", "order_amount", "order_delivery_fee", "order_delivery_cost",
            "order_metric_cycle_time", "order_metric_production_time", "order_metric_transit_time",
            "order_moment_created", "order_moment_finished",
            "order_date", "order_dow", "order_dow_name", "order_hour", "order_week",
            "pay_total", "pay_fee_total", "n_payments", "any_chargeback", "all_paid",
            "primary_payment_method",
            "n_deliveries", "dist_total_m", "dist_mean_m", "any_delivery_cancelled",
            "primary_driver_modal", "primary_driver_type",
            "has_payment", "has_delivery",
            "flag_zero_amount", "flag_extreme_amount", "flag_long_cycle"]
    fact[keep].to_csv(os.path.join(OUT, "fact_orders.csv"), index=False)
    dv.to_csv(os.path.join(OUT, "dim_deliveries.csv"), index=False)
    log(f"  wrote fact_orders.csv ({fact.shape[0]:,} rows) and dim_deliveries.csv ({dv.shape[0]:,} rows)")

    with open(os.path.join(OUT, "etl_log.txt"), "w") as f:
        f.write("\n".join(LOG))
    log("\nETL complete.")


if __name__ == "__main__":
    main()
