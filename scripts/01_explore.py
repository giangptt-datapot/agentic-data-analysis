"""
01_explore.py — Data audit / exploration for Brazilian Delivery Center dataset.
Prints structure, grain, date ranges, missing values, duplicates, and basic distributions
for every table. Read-only: does not modify any raw file.
"""
import pandas as pd
import numpy as np
import os, sys

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 60)

FILES = ["channels", "deliveries", "drivers", "hubs", "orders", "payments", "stores"]


def read_csv_safe(path):
    """Read a CSV trying utf-8 first, then latin-1 (Portuguese accents)."""
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, low_memory=False, encoding=enc), enc
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, low_memory=False, encoding="latin-1", encoding_errors="replace"), "latin-1?"


def line(c="="):
    print(c * 90)


def audit(name, df):
    line()
    print(f"TABLE: {name}   shape={df.shape}")
    line("-")
    print("DTYPES:")
    print(df.dtypes.to_string())
    print("\nHEAD:")
    print(df.head(3).to_string())
    print("\nMISSING (count / %):")
    miss = pd.DataFrame({
        "null": df.isna().sum(),
        "pct": (df.isna().mean() * 100).round(2),
        "nunique": df.nunique(dropna=True),
    })
    print(miss.to_string())
    dup = df.duplicated().sum()
    print(f"\nFully-duplicated rows: {dup}")
    # candidate keys: any column that is unique
    for col in df.columns:
        if df[col].is_unique and df[col].notna().all():
            print(f"  candidate PK (unique+non-null): {col}")
    return df


def main():
    dfs = {}
    for f in FILES:
        path = os.path.join(RAW, f + ".csv")
        df, enc = read_csv_safe(path)
        print(f"[loaded {f} with encoding={enc}]")
        dfs[f] = df
        audit(f, df)

    # Date ranges for orders
    line()
    print("ORDERS date columns exploration")
    o = dfs["orders"]
    for c in o.columns:
        if "moment" in c.lower() or "date" in c.lower() or "created" in c.lower():
            try:
                s = pd.to_datetime(o[c], errors="coerce")
                print(f"  {c}: min={s.min()}  max={s.max()}  parsed={s.notna().sum()}/{len(s)}")
            except Exception as e:
                print(f"  {c}: parse fail {e}")

    # Relationship sanity: FK coverage
    line()
    print("FK COVERAGE CHECKS")
    o = dfs["orders"]; d = dfs["deliveries"]; p = dfs["payments"]
    st = dfs["stores"]; hb = dfs["hubs"]; ch = dfs["channels"]; dr = dfs["drivers"]
    print("orders columns:", list(o.columns))
    print("deliveries columns:", list(d.columns))
    print("payments columns:", list(p.columns))
    print("stores columns:", list(st.columns))
    print("hubs columns:", list(hb.columns))
    print("channels columns:", list(ch.columns))
    print("drivers columns:", list(dr.columns))


if __name__ == "__main__":
    main()
