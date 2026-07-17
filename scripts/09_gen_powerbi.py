"""
09_gen_powerbi.py — Emit a Power BI project in PBIP/TMDL text format.
Targets Power BI Desktop with TMDL + PBIR (preview) enabled.

Produces powerbi/:
  BrazilianDeliveryCenter.pbip
  BrazilianDeliveryCenter.SemanticModel/  (TMDL model: tables w/ Power Query M partitions, DAX measures, relationships)
  BrazilianDeliveryCenter.Report/         (report skeleton + reference; theme is standalone import)
  DeliveryCenter_Light.theme.json         (importable Power BI theme, light)

Data source: the 7 Kaggle CSVs. Each import query reads from the `SourceFolder`
parameter (set it to the folder holding the CSVs when you open in Desktop).
Timestamps converted to Brazil local time (UTC-3) per stakeholder decision.
"""
import os, json, textwrap

ROOT = os.path.join(os.path.dirname(__file__), "..", "powerbi")
SM = os.path.join(ROOT, "BrazilianDeliveryCenter.SemanticModel")
RP = os.path.join(ROOT, "BrazilianDeliveryCenter.Report")
for d in [ROOT, SM, os.path.join(SM, "definition", "tables"),
          RP, os.path.join(RP, "definition", "pages"),
          os.path.join(RP, "StaticResources", "RegisteredResources")]:
    os.makedirs(d, exist_ok=True)

def w(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", os.path.relpath(path, ROOT))

# ---------------------------------------------------------------- .pbip
w(os.path.join(ROOT, "BrazilianDeliveryCenter.pbip"), json.dumps({
    "version": "1.0",
    "artifacts": [{"report": {"path": "BrazilianDeliveryCenter.Report"}}],
    "settings": {"enableAutoRecovery": True}
}, indent=2))

# ---------------------------------------------------------------- SemanticModel platform + pbism
w(os.path.join(SM, ".platform"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": "BrazilianDeliveryCenter"},
    "config": {"version": "2.0", "logicalId": "bdc-semantic-0001"}
}, indent=2))
w(os.path.join(SM, "definition.pbism"), json.dumps({"version": "4.0", "settings": {}}, indent=2))

# ---------------------------------------------------------------- database.tmdl / model.tmdl / expressions
w(os.path.join(SM, "definition", "database.tmdl"),
"database\n\tcompatibilityLevel: 1567\n")

w(os.path.join(SM, "definition", "expressions.tmdl"),
'expression SourceFolder = "C:\\\\BDC\\\\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
'\tlineageTag: exp-sourcefolder\n'
'\tannotation PBI_ResultType = Text\n')

MODEL = """model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tdiscourageImplicitMeasures
\tsourceQueryCulture: en-US
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

ref table fact_orders
ref table fact_deliveries
ref table fact_payments
ref table dim_store
ref table dim_hub
ref table dim_channel
ref table dim_driver
ref table dim_date

ref cultureInfo en-US
"""
w(os.path.join(SM, "definition", "model.tmdl"), MODEL)

# ---------------------------------------------------------------- relationships
REL = """relationship rel_store_orders
\tfromColumn: fact_orders.store_id
\ttoColumn: dim_store.store_id

relationship rel_channel_orders
\tfromColumn: fact_orders.channel_id
\ttoColumn: dim_channel.channel_id

relationship rel_hub_store
\tfromColumn: dim_store.hub_id
\ttoColumn: dim_hub.hub_id

relationship rel_date_orders
\tfromColumn: fact_orders.order_date
\ttoColumn: dim_date.Date

relationship rel_orders_deliveries
\tfromColumn: fact_deliveries.delivery_order_id
\ttoColumn: fact_orders.order_id

relationship rel_orders_payments
\tfromColumn: fact_payments.payment_order_id
\ttoColumn: fact_orders.order_id

relationship rel_driver_deliveries
\tfromColumn: fact_deliveries.driver_id
\ttoColumn: dim_driver.driver_id
"""
w(os.path.join(SM, "definition", "relationships.tmdl"), REL)

# ---------------------------------------------------------------- helper builders
def col(name, dtype, summarize="none", fmt=None, hidden=False):
    s = f"\tcolumn {name}\n\t\tdataType: {dtype}\n\t\tsummarizeBy: {summarize}\n\t\tsourceColumn: {name}\n"
    if fmt: s += f"\t\tformatString: {fmt}\n"
    if hidden: s += "\t\tisHidden\n"
    s += f"\t\tlineageTag: lt-{name}\n"
    return s

def m_partition(tbl, mcode):
    body = "\n".join("\t\t\t" + ln for ln in mcode.strip("\n").split("\n"))
    return f"\tpartition {tbl} = m\n\t\tmode: import\n\t\tsource =\n{body}\n"

# ---------------------------------------------------------------- fact_orders (+ all measures)
ORDERS_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "orders.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {
        {"order_id", Int64.Type}, {"store_id", Int64.Type}, {"channel_id", Int64.Type},
        {"order_status", type text}, {"order_amount", type number},
        {"order_delivery_fee", type number}, {"order_delivery_cost", type number},
        {"order_metric_cycle_time", type number}, {"order_metric_production_time", type number},
        {"order_metric_transit_time", type number},
        {"order_moment_created", type text}, {"order_moment_finished", type text}}),
    // parse created (source format M/d/yyyy h:mm:ss tt) -> assume UTC, shift to Brazil local (UTC-3)
    AddUtc = Table.AddColumn(Typ, "created_utc", each try DateTime.FromText([order_moment_created], [Format="M/d/yyyy h:mm:ss tt", Culture="en-US"]) otherwise null, type datetime),
    AddLoc = Table.AddColumn(AddUtc, "created_local", each if [created_utc] = null then null else [created_utc] - #duration(0,3,0,0), type datetime),
    AddDate = Table.AddColumn(AddLoc, "order_date", each if [created_local] = null then null else Date.From([created_local]), type date),
    AddHour = Table.AddColumn(AddDate, "order_hour", each if [created_local] = null then null else Time.Hour([created_local]), Int64.Type),
    AddDow = Table.AddColumn(AddHour, "order_dow", each if [created_local] = null then null else Date.DayOfWeek([created_local], Day.Monday), Int64.Type),
    // quality flags (kept, never dropped)
    AddF1 = Table.AddColumn(AddDow, "flag_zero_amount", each [order_amount] <= 0, type logical),
    AddF2 = Table.AddColumn(AddF1, "flag_extreme_amount", each [order_amount] > 1500, type logical),
    AddF3 = Table.AddColumn(AddF2, "flag_long_cycle", each [order_metric_cycle_time] <> null and [order_metric_cycle_time] > 1440, type logical)
in
    AddF3
'''

MEASURES = r'''
\tmeasure 'Total Orders' = COUNTROWS(fact_orders)
\t\tformatString: #,0
\tmeasure 'Finished Orders' = CALCULATE([Total Orders], fact_orders[order_status] = "FINISHED")
\t\tformatString: #,0
\tmeasure 'Canceled Orders' = CALCULATE([Total Orders], fact_orders[order_status] = "CANCELED")
\t\tformatString: #,0
\tmeasure 'GMV' = CALCULATE(SUM(fact_orders[order_amount]), fact_orders[order_status] = "FINISHED")
\t\tformatString: "R$"#,0
\tmeasure 'AOV' = DIVIDE([GMV], [Finished Orders])
\t\tformatString: "R$"#,0.00
\tmeasure 'Median Order Value' = MEDIANX(FILTER(fact_orders, fact_orders[order_status] = "FINISHED"), fact_orders[order_amount])
\t\tformatString: "R$"#,0.00
\tmeasure 'Cancellation Rate' = DIVIDE([Canceled Orders], [Total Orders])
\t\tformatString: 0.00%
\tmeasure 'Fulfillment Rate' = DIVIDE([Finished Orders], [Total Orders])
\t\tformatString: 0.00%
\tmeasure 'Active Stores' = CALCULATE(DISTINCTCOUNT(fact_orders[store_id]), fact_orders[order_status] = "FINISHED")
\t\tformatString: #,0
\tmeasure 'Median Cycle (min)' = MEDIANX(FILTER(fact_orders, fact_orders[order_status] = "FINISHED" && fact_orders[order_metric_cycle_time] > 0 && fact_orders[order_metric_cycle_time] <= 1440), fact_orders[order_metric_cycle_time])
\t\tformatString: #,0.0
\tmeasure 'P90 Cycle (min)' = PERCENTILEX.INC(FILTER(fact_orders, fact_orders[order_status] = "FINISHED" && fact_orders[order_metric_cycle_time] > 0 && fact_orders[order_metric_cycle_time] <= 1440), fact_orders[order_metric_cycle_time], 0.9)
\t\tformatString: #,0.0
\tmeasure 'Mean Delivery Fee' = CALCULATE(AVERAGE(fact_orders[order_delivery_fee]), fact_orders[order_status] = "FINISHED")
\t\tformatString: "R$"#,0.00
\tmeasure 'Mean Delivery Cost' = CALCULATE(AVERAGEX(FILTER(fact_orders, NOT(ISBLANK(fact_orders[order_delivery_cost]))), fact_orders[order_delivery_cost]), fact_orders[order_status] = "FINISHED")
\t\tformatString: "R$"#,0.00
\tmeasure 'Delivery Subsidy / Order' = [Mean Delivery Cost] - [Mean Delivery Fee]
\t\tformatString: "R$"#,0.00
\tmeasure 'Free-ship Order %' = DIVIDE(CALCULATE([Finished Orders], fact_orders[order_delivery_fee] = 0), [Finished Orders])
\t\tformatString: 0.0%
\tmeasure 'GMV Concentration Top1 Channel %' =
\t\tVAR Total = [GMV]
\t\tVAR Top1 = MAXX(VALUES(dim_channel[channel_name]), [GMV])
\t\tRETURN DIVIDE(Top1, CALCULATE([GMV], ALL(dim_channel)))
\t\tformatString: 0.0%
'''

FACT_ORDERS = (
    "table fact_orders\n\tlineageTag: tbl-fact-orders\n\n"
    + col("order_id", "int64")
    + col("store_id", "int64")
    + col("channel_id", "int64")
    + col("order_status", "string")
    + col("order_amount", "double", "sum", '"R$"#,0.00')
    + col("order_delivery_fee", "double", "sum", '"R$"#,0.00')
    + col("order_delivery_cost", "double", "sum", '"R$"#,0.00')
    + col("order_metric_cycle_time", "double", "none")
    + col("order_metric_production_time", "double", "none")
    + col("order_metric_transit_time", "double", "none")
    + col("order_date", "dateTime", "none", "General Date")
    + col("order_hour", "int64", "none")
    + col("order_dow", "int64", "none")
    + col("flag_zero_amount", "boolean", "none")
    + col("flag_extreme_amount", "boolean", "none")
    + col("flag_long_cycle", "boolean", "none")
    + "\n" + MEASURES.replace("\\t", "\t").strip("\n") + "\n\n"
    + m_partition("fact_orders", ORDERS_M)
)
w(os.path.join(SM, "definition", "tables", "fact_orders.tmdl"), FACT_ORDERS)

# ---------------------------------------------------------------- fact_deliveries
DELIV_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "deliveries.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {
        {"delivery_id", Int64.Type}, {"delivery_order_id", Int64.Type}, {"driver_id", Int64.Type},
        {"delivery_distance_meters", type number}, {"delivery_status", type text}}),
    AddF = Table.AddColumn(Typ, "flag_extreme_distance", each [delivery_distance_meters] <> null and [delivery_distance_meters] > 50000, type logical)
in
    AddF
'''
DELIV_MEAS = (
    "\n\tmeasure 'Deliveries' = COUNTROWS(fact_deliveries)\n\t\tformatString: #,0\n"
    "\tmeasure 'Delivered' = CALCULATE([Deliveries], fact_deliveries[delivery_status] = \"DELIVERED\")\n\t\tformatString: #,0\n"
    "\tmeasure 'Delivery Success Rate' = DIVIDE([Delivered], [Deliveries])\n\t\tformatString: 0.00%\n"
    "\tmeasure 'Median Distance (km)' = DIVIDE(MEDIANX(FILTER(fact_deliveries, fact_deliveries[delivery_status] = \"DELIVERED\" && fact_deliveries[delivery_distance_meters] <= 50000), fact_deliveries[delivery_distance_meters]), 1000)\n\t\tformatString: #,0.00\n"
    "\tmeasure 'Active Drivers' = CALCULATE(DISTINCTCOUNT(fact_deliveries[driver_id]), fact_deliveries[delivery_status] = \"DELIVERED\")\n\t\tformatString: #,0\n"
)
FACT_DELIV = (
    "table fact_deliveries\n\tlineageTag: tbl-fact-deliveries\n\n"
    + col("delivery_id", "int64")
    + col("delivery_order_id", "int64")
    + col("driver_id", "int64")
    + col("delivery_distance_meters", "double", "none")
    + col("delivery_status", "string")
    + col("flag_extreme_distance", "boolean", "none")
    + DELIV_MEAS + "\n"
    + m_partition("fact_deliveries", DELIV_M)
)
w(os.path.join(SM, "definition", "tables", "fact_deliveries.tmdl"), FACT_DELIV)

# ---------------------------------------------------------------- fact_payments
PAY_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "payments.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {
        {"payment_id", Int64.Type}, {"payment_order_id", Int64.Type},
        {"payment_amount", type number}, {"payment_fee", type number},
        {"payment_method", type text}, {"payment_status", type text}})
in
    Typ
'''
PAY_MEAS = (
    "\n\tmeasure 'Payments' = COUNTROWS(fact_payments)\n\t\tformatString: #,0\n"
    "\tmeasure 'Chargeback Orders' = CALCULATE(DISTINCTCOUNT(fact_payments[payment_order_id]), fact_payments[payment_status] = \"CHARGEBACK\")\n\t\tformatString: #,0\n"
    "\tmeasure 'Chargeback Rate' = DIVIDE([Chargeback Orders], [Total Orders])\n\t\tformatString: 0.000%\n"
    "\t/* NOTE: never SUM(payment_amount) as revenue — payments fan out (48,818 orders split). Revenue = [GMV] from fact_orders. */\n"
)
FACT_PAY = (
    "table fact_payments\n\tlineageTag: tbl-fact-payments\n\n"
    + col("payment_id", "int64")
    + col("payment_order_id", "int64")
    + col("payment_amount", "double", "sum", '"R$"#,0.00')
    + col("payment_fee", "double", "sum")
    + col("payment_method", "string")
    + col("payment_status", "string")
    + PAY_MEAS + "\n"
    + m_partition("fact_payments", PAY_M)
)
w(os.path.join(SM, "definition", "tables", "fact_payments.tmdl"), FACT_PAY)

# ---------------------------------------------------------------- dim_store (+ hub merge for city/state convenience)
STORE_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "stores.csv"), [Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {
        {"store_id", Int64.Type}, {"hub_id", Int64.Type}, {"store_name", type text},
        {"store_segment", type text}, {"store_plan_price", type number},
        {"store_latitude", type number}, {"store_longitude", type number}})
in
    Typ
'''
DIM_STORE = (
    "table dim_store\n\tlineageTag: tbl-dim-store\n\n"
    + col("store_id", "int64")
    + col("hub_id", "int64")
    + col("store_name", "string")
    + col("store_segment", "string")
    + col("store_plan_price", "double", "none", '"R$"#,0.00')
    + col("store_latitude", "double", "none")
    + col("store_longitude", "double", "none")
    + "\n" + m_partition("dim_store", STORE_M)
)
w(os.path.join(SM, "definition", "tables", "dim_store.tmdl"), DIM_STORE)

# ---------------------------------------------------------------- dim_hub
HUB_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "hubs.csv"), [Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {
        {"hub_id", Int64.Type}, {"hub_name", type text}, {"hub_city", type text},
        {"hub_state", type text}, {"hub_latitude", type number}, {"hub_longitude", type number}})
in
    Typ
'''
DIM_HUB = (
    "table dim_hub\n\tlineageTag: tbl-dim-hub\n\n"
    + col("hub_id", "int64")
    + col("hub_name", "string")
    + col("hub_city", "string")
    + col("hub_state", "string")
    + col("hub_latitude", "double", "none")
    + col("hub_longitude", "double", "none")
    + "\n" + m_partition("dim_hub", HUB_M)
)
w(os.path.join(SM, "definition", "tables", "dim_hub.tmdl"), DIM_HUB)

# ---------------------------------------------------------------- dim_channel
CH_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "channels.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {{"channel_id", Int64.Type}, {"channel_name", type text}, {"channel_type", type text}})
in
    Typ
'''
DIM_CH = (
    "table dim_channel\n\tlineageTag: tbl-dim-channel\n\n"
    + col("channel_id", "int64") + col("channel_name", "string") + col("channel_type", "string")
    + "\n" + m_partition("dim_channel", CH_M)
)
w(os.path.join(SM, "definition", "tables", "dim_channel.tmdl"), DIM_CH)

# ---------------------------------------------------------------- dim_driver
DR_M = r'''
let
    Src = Csv.Document(File.Contents(SourceFolder & "drivers.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Head = Table.PromoteHeaders(Src, [PromoteAllScalars=true]),
    Typ = Table.TransformColumnTypes(Head, {{"driver_id", Int64.Type}, {"driver_modal", type text}, {"driver_type", type text}})
in
    Typ
'''
DIM_DR = (
    "table dim_driver\n\tlineageTag: tbl-dim-driver\n\n"
    + col("driver_id", "int64") + col("driver_modal", "string") + col("driver_type", "string")
    + "\n" + m_partition("dim_driver", DR_M)
)
w(os.path.join(SM, "definition", "tables", "dim_driver.tmdl"), DIM_DR)

# ---------------------------------------------------------------- dim_date (calculated)
DIM_DATE = r'''table dim_date
	lineageTag: tbl-dim-date
	isPrivate

	column Date
		dataType: dateTime
		isKey
		summarizeBy: none
		sourceColumn: [Date]
		formatString: General Date
		lineageTag: lt-date-date

	column Year = YEAR('dim_date'[Date])
		dataType: int64
		summarizeBy: none
		lineageTag: lt-date-year

	column MonthNo = MONTH('dim_date'[Date])
		dataType: int64
		summarizeBy: none
		lineageTag: lt-date-monthno

	column Month = FORMAT('dim_date'[Date], "mmm")
		dataType: string
		summarizeBy: none
		sortByColumn: MonthNo
		lineageTag: lt-date-month

	column DayOfWeekNo = WEEKDAY('dim_date'[Date], 2)
		dataType: int64
		summarizeBy: none
		lineageTag: lt-date-downo

	column DayOfWeek = FORMAT('dim_date'[Date], "ddd")
		dataType: string
		summarizeBy: none
		sortByColumn: DayOfWeekNo
		lineageTag: lt-date-dow

	column IsWeekend = WEEKDAY('dim_date'[Date], 2) >= 6
		dataType: boolean
		summarizeBy: none
		lineageTag: lt-date-wknd

	partition dim_date = calculated
		mode: import
		source = CALENDAR(DATE(2021,1,1), DATE(2021,5,7))

	annotation PBI_Id = dimdate
'''
w(os.path.join(SM, "definition", "tables", "dim_date.tmdl"), DIM_DATE)

# ================================================================ REPORT
w(os.path.join(RP, ".platform"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": "BrazilianDeliveryCenter"},
    "config": {"version": "2.0", "logicalId": "bdc-report-0001"}
}, indent=2))
w(os.path.join(RP, "definition.pbir"), json.dumps({
    "version": "1.0",
    "datasetReference": {"byPath": {"path": "../BrazilianDeliveryCenter.SemanticModel"}}
}, indent=2))

# report.json (report-level: theme + settings)
w(os.path.join(RP, "definition", "report.json"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json",
    "themeCollection": {"customTheme": {"name": "DeliveryCenter_Light"}},
    "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True}
}, indent=2))

# pages
PAGES = [
    ("p1", "1 · Executive Overview"), ("p2", "2 · Order & Revenue"),
    ("p3", "3 · Delivery Performance"), ("p4", "4 · Hub & Geographic"),
    ("p5", "5 · Store & Partner"), ("p6", "6 · Insight Lab"),
    ("p7", "7 · Khuyến nghị & Hành động"),
]
w(os.path.join(RP, "definition", "pages", "pages.json"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [p[0] for p in PAGES], "activePageName": "p1"
}, indent=2))
for pid, disp in PAGES:
    pdir = os.path.join(RP, "definition", "pages", pid)
    os.makedirs(pdir, exist_ok=True)
    w(os.path.join(pdir, "page.json"), json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.0.0/schema.json",
        "name": pid, "displayName": disp,
        "displayOption": "FitToPage", "height": 720, "width": 1280
    }, indent=2))

print("\nPBIP tree written.")
