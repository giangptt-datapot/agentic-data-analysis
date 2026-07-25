"""
16_gen_pbi_preview.py — Render an offline preview of the rebuilt Power BI report.

It reads the ACTUAL PBIR definition (powerbi/.../definition/pages/**/visual.json) for page order,
visual type, position and title, then paints each visual with the real numbers from
dashboard/pbi_v2_data.json. So the preview is a faithful picture of what Power BI Desktop will show
after `Refresh` — not a hand-drawn mockup.

Output: dashboard/pbi_v2_preview.html  (+ PNG per page via chrome-headless-shell, see Makefile step)
"""
import json, os, glob, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PAGES = os.path.join(ROOT, "powerbi", "BrazilianDeliveryCenter.Report", "definition", "pages")
D = json.load(open(os.path.join(ROOT, "dashboard", "pbi_v2_data.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "dashboard", "pbi_v2_preview.html")

# Power BI light theme palette (DeliveryCenter_Light.theme.json)
PAL = ["#2f6bff", "#0d9488", "#7a3bf5", "#d97706", "#0f9d58", "#e11d48", "#0891b2", "#9333ea",
       "#65a30d", "#c2410c", "#0369a1", "#be185d"]
INK, MUT, MUT2, LINE, PANEL = "#0f1a30", "#4c587a", "#8b95ad", "#e2e8f5", "#ffffff"
RISK, OK = "#e11d48", "#0f9d58"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def fnum(v):
    a = abs(v)
    if a >= 1e6:
        return f"{v/1e6:.2f}M"
    if a >= 1e3:
        return f"{v/1e3:.0f}k"
    if a >= 10:
        return f"{v:.0f}"
    return f"{v:.2f}"


# ------------------------------------------------------------------ chart parts
def bars_h(data, w, h, color=None, fmt=fnum):
    """horizontal bars (barChart)"""
    if not data:
        return ""
    lab_w = min(120, int(w * 0.34))
    bw = w - lab_w - 46
    mx = max(abs(d["v"] or 0) for d in data) or 1
    row = max(13, min(24, int((h - 6) / len(data))))
    out = []
    for i, d in enumerate(data):
        y = i * row
        L = (bw * abs(d["v"] or 0) / mx)
        c = color or PAL[i % len(PAL)]
        out.append(f'<div style="position:absolute;left:0;top:{y}px;width:{lab_w}px;height:{row-3}px;'
                   f'font-size:9px;color:{MUT};overflow:hidden;white-space:nowrap;text-overflow:ellipsis;'
                   f'line-height:{row-3}px">{esc(d["k"])}</div>'
                   f'<div style="position:absolute;left:{lab_w}px;top:{y+1}px;width:{L:.1f}px;height:{row-6}px;'
                   f'background:{c};border-radius:2px"></div>'
                   f'<div style="position:absolute;left:{lab_w+L+4:.1f}px;top:{y}px;font-size:9px;color:{INK};'
                   f'line-height:{row-3}px">{fmt(d["v"] or 0)}</div>')
    return "".join(out)


def bars_v(data, w, h, color=None, fmt=fnum, rotate=False):
    """vertical columns (columnChart)"""
    if not data:
        return ""
    n = len(data)
    gap = 3 if n > 12 else 6
    cw = max(4, (w - gap * (n - 1)) / n)
    lab_h = 26 if rotate else 14
    ch = h - lab_h - 24   # reserve top room for data labels
    vals = [d["v"] or 0 for d in data]
    mx = max(vals) or 1
    mn = min(0, min(vals))
    span = (mx - mn) or 1
    zero_y = ch * (mx / span)
    out = [f'<div style="position:absolute;left:0;top:{zero_y+14:.1f}px;width:{w}px;height:1px;background:{LINE}"></div>']
    for i, d in enumerate(data):
        v = d["v"] or 0
        x = i * (cw + gap)
        bh = ch * abs(v) / span
        top = (zero_y - bh if v >= 0 else zero_y) + 14
        c = color or PAL[i % len(PAL)]
        if v < 0:
            c = RISK
        out.append(f'<div style="position:absolute;left:{x:.1f}px;top:{top:.1f}px;width:{cw:.1f}px;'
                   f'height:{max(1,bh):.1f}px;background:{c};border-radius:2px"></div>')
        if n <= 14 or i % 2 == 0:
            ty = (top - 12) if v >= 0 else (top + bh + 1)
            out.append(f'<div style="position:absolute;left:{x-6:.1f}px;top:{ty:.1f}px;width:{cw+12:.1f}px;'
                       f'text-align:center;font-size:8px;color:{INK}">{fmt(v)}</div>')
        st = ("transform:rotate(-35deg);transform-origin:left top;width:70px;text-align:left"
              if rotate else f"width:{cw+8:.1f}px;text-align:center")
        out.append(f'<div style="position:absolute;left:{x-4:.1f}px;top:{ch+4}px;font-size:8px;color:{MUT};'
                   f'white-space:nowrap;overflow:hidden;{st}">{esc(d["k"])}</div>')
    return "".join(out)


def bars_grouped(data, w, h, fmt=fnum):
    """clustered columns: data = [{k, series:[(name,val)]}]"""
    if not data:
        return ""
    names = [s[0] for s in data[0]["series"]]
    mx = max(abs(v) for d in data for _, v in d["series"]) or 1
    ch = h - 34
    gw = w / len(data)
    bw = min(34, (gw - 16) / len(names))
    out = []
    for gi, d in enumerate(data):
        for si, (nm, v) in enumerate(d["series"]):
            bh = ch * abs(v) / mx
            x = gi * gw + 10 + si * (bw + 4)
            out.append(f'<div style="position:absolute;left:{x:.1f}px;top:{ch-bh:.1f}px;width:{bw:.1f}px;'
                       f'height:{max(1,bh):.1f}px;background:{PAL[si]};border-radius:2px"></div>'
                       f'<div style="position:absolute;left:{x-6:.1f}px;top:{ch-bh-12:.1f}px;width:{bw+12:.1f}px;'
                       f'text-align:center;font-size:8px;color:{INK}">{fmt(v)}</div>')
        out.append(f'<div style="position:absolute;left:{gi*gw:.1f}px;top:{ch+4}px;width:{gw:.1f}px;'
                   f'text-align:center;font-size:9px;color:{MUT}">{esc(d["k"])}</div>')
    leg = "".join(f'<span style="margin-right:8px;font-size:8.5px;color:{MUT}">'
                  f'<i style="display:inline-block;width:7px;height:7px;background:{PAL[i]};'
                  f'border-radius:2px;margin-right:3px"></i>{esc(n)}</span>' for i, n in enumerate(names))
    out.append(f'<div style="position:absolute;left:0;top:{ch+18}px">{leg}</div>')
    return "".join(out)


def line(data, w, h, color=PAL[0], area=True, fmt=fnum):
    if not data:
        return ""
    ys = [d["y"] or 0 for d in data]
    mx, mn = max(ys), min(ys)
    if mx == mn:
        mx = mn + 1
    ch = h - 22
    pts = [(i * (w - 30) / max(1, len(data) - 1) + 15, ch - ch * 0.92 * (y - mn) / (mx - mn) - 4) for i, y in enumerate(ys)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    ar = (f'<path d="{path} L{pts[-1][0]:.1f},{ch} L{pts[0][0]:.1f},{ch} Z" fill="{color}" opacity=".12"/>'
          if area else "")
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{color}"/>' for x, y in pts)
    labs = ""
    step = max(1, len(data) // 6)
    for i, d in enumerate(data):
        if i % step == 0 or i == len(data) - 1:
            labs += (f'<text x="{pts[i][0]:.1f}" y="{ch+12}" font-size="8" fill="{MUT}" '
                     f'text-anchor="middle">{esc(d["x"])}</text>')
    vmax = ys.index(max(ys))
    peak = (f'<circle cx="{pts[vmax][0]:.1f}" cy="{pts[vmax][1]:.1f}" r="4" fill="{PAL[3]}"/>'
            f'<text x="{pts[vmax][0]:.1f}" y="{pts[vmax][1]-7:.1f}" font-size="8.5" fill="{PAL[3]}" '
            f'text-anchor="middle">{fmt(max(ys))}</text>')
    return (f'<svg width="{w}" height="{h}">{ar}<path d="{path}" fill="none" stroke="{color}" '
            f'stroke-width="1.8"/>{dots}{peak}{labs}</svg>')


def donut(data, w, h):
    if not data:
        return ""
    tot = sum(d["v"] for d in data) or 1
    r_out, r_in = min(w * 0.3, h * 0.38), min(w * 0.3, h * 0.38) * 0.58
    cx, cy = w * 0.32, h * 0.5
    ang, seg = -math.pi / 2, []
    for i, d in enumerate(data):
        a2 = ang + 2 * math.pi * d["v"] / tot
        x1, y1 = cx + r_out * math.cos(ang), cy + r_out * math.sin(ang)
        x2, y2 = cx + r_out * math.cos(a2), cy + r_out * math.sin(a2)
        xi2, yi2 = cx + r_in * math.cos(a2), cy + r_in * math.sin(a2)
        xi1, yi1 = cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)
        laf = 1 if (a2 - ang) > math.pi else 0
        seg.append(f'<path d="M{x1:.1f},{y1:.1f} A{r_out:.1f},{r_out:.1f} 0 {laf} 1 {x2:.1f},{y2:.1f} '
                   f'L{xi2:.1f},{yi2:.1f} A{r_in:.1f},{r_in:.1f} 0 {laf} 0 {xi1:.1f},{yi1:.1f} Z" '
                   f'fill="{PAL[i % len(PAL)]}"/>')
        ang = a2
    leg = ""
    for i, d in enumerate(data[:7]):
        leg += (f'<div style="font-size:8.5px;color:{MUT};margin-bottom:2px;white-space:nowrap">'
                f'<i style="display:inline-block;width:7px;height:7px;background:{PAL[i % len(PAL)]};'
                f'border-radius:2px;margin-right:4px"></i>{esc(d["k"])} '
                f'<b style="color:{INK}">{d["v"]/tot*100:.1f}%</b></div>')
    return (f'<svg width="{w*0.64:.0f}" height="{h}" style="position:absolute;left:0;top:0">{"".join(seg)}</svg>'
            f'<div style="position:absolute;left:{w*0.62:.0f}px;top:8px">{leg}</div>')


def scatter(data, w, h, xlab="", ylab="", logx=False):
    if not data:
        return ""
    xs = [d["x"] for d in data if d["x"] is not None]
    ys = [d["y"] for d in data if d["y"] is not None]
    if not xs or not ys:
        return ""
    fx = (lambda v: math.log10(max(v, 1))) if logx else (lambda v: v)
    x0, x1 = min(map(fx, xs)), max(map(fx, xs))
    y0, y1 = min(ys), max(ys)
    x1 = x1 if x1 > x0 else x0 + 1
    y1 = y1 if y1 > y0 else y0 + 1
    pw, ph = w - 34, h - 26
    smax = max(d.get("s") or 1 for d in data) or 1
    med_y = sorted(ys)[len(ys) // 2]
    med_x = sorted(map(fx, xs))[len(xs) // 2]
    gx = 30 + pw * (med_x - x0) / (x1 - x0)
    gy = ph - ph * (med_y - y0) / (y1 - y0)
    out = [f'<div style="position:absolute;left:{gx:.0f}px;top:0;width:1px;height:{ph}px;'
           f'background:{LINE}"></div>',
           f'<div style="position:absolute;left:30px;top:{gy:.0f}px;width:{pw}px;height:1px;background:{LINE}"></div>']
    for d in data:
        if d["x"] is None or d["y"] is None:
            continue
        px = 30 + pw * (fx(d["x"]) - x0) / (x1 - x0)
        py = ph - ph * (d["y"] - y0) / (y1 - y0)
        rr = 2.5 + 6 * math.sqrt((d.get("s") or 1) / smax)
        hot = d["y"] >= med_y and fx(d["x"]) >= med_x
        c = RISK if hot else PAL[0]
        out.append(f'<div style="position:absolute;left:{px-rr:.1f}px;top:{py-rr:.1f}px;width:{rr*2:.1f}px;'
                   f'height:{rr*2:.1f}px;border-radius:50%;background:{c};opacity:.55"></div>')
    lab = [d for d in data if d["x"] is not None and d["y"] is not None]
    for d in sorted(lab, key=lambda d: -(d["y"] or 0))[:3]:
        px = 30 + pw * (fx(d["x"]) - x0) / (x1 - x0)
        py = ph - ph * (d["y"] - y0) / (y1 - y0)
        out.append(f'<div style="position:absolute;left:{min(px+6,w-90):.0f}px;top:{max(py-6,0):.0f}px;'
                   f'font-size:8px;color:{INK};white-space:nowrap">{esc(d["k"])}</div>')
    out.append(f'<div style="position:absolute;left:30px;top:{ph+6}px;font-size:8px;color:{MUT2}">{esc(xlab)}</div>')
    out.append(f'<div style="position:absolute;left:0;top:0;font-size:8px;color:{MUT2}">{esc(ylab)}</div>')
    return "".join(out)


def table(spec, w, h):
    cols, rows = spec["cols"], spec["rows"]
    th = "".join(f'<th style="text-align:left;font-size:8.5px;color:{MUT};font-weight:600;padding:3px 5px;'
                 f'border-bottom:1px solid {LINE};white-space:nowrap">{esc(c)}</th>' for c in cols)
    tr = ""
    for row in rows:
        tds = "".join(f'<td style="font-size:8.5px;color:{INK};padding:3px 5px;border-bottom:1px solid #f1f4fb;'
                      f'white-space:nowrap;overflow:hidden;max-width:130px">{esc(c)}</td>' for c in row)
        tr += f"<tr>{tds}</tr>"
    return f'<table style="width:100%;border-collapse:collapse">{th and f"<thead><tr>{th}</tr></thead>"}<tbody>{tr}</tbody></table>'


def matrix(spec, w, h, pct=False):
    rows, cols, cells = spec["rows"], spec["cols"], spec["cells"]
    vals = [v[0] if isinstance(v, (list, tuple)) else v for v in cells.values() if v is not None]
    mx = max(abs(v) for v in vals) or 1
    th = f'<th style="border-bottom:1px solid {LINE}"></th>' + "".join(
        f'<th style="font-size:8px;color:{MUT};padding:3px;border-bottom:1px solid {LINE}">{esc(c)}</th>' for c in cols)
    tr = ""
    for rw in rows:
        tds = f'<td style="font-size:8.5px;color:{INK};padding:3px 4px;white-space:nowrap">{esc(rw)}</td>'
        for c in cols:
            v = cells.get(f"{rw}|{c}")
            if v is None:
                tds += '<td></td>'
                continue
            val, extra = (v[0], v[1]) if isinstance(v, (list, tuple)) else (v, None)
            inten = min(0.85, abs(val) / mx)
            bg = f"rgba(225,29,72,{inten:.2f})" if (val > 0 if pct else val < 0) else f"rgba(15,157,88,{inten:.2f})"
            txt = f"{val:.2f}%" if pct else fnum(val)
            sub = f'<br><span style="font-size:7px;opacity:.7">{extra:,}</span>'.replace(",", ".") if extra else ""
            tds += (f'<td style="font-size:8.5px;text-align:center;padding:3px;background:{bg};'
                    f'color:{INK}">{txt}{sub}</td>')
        tr += f"<tr>{tds}</tr>"
    return f'<table style="width:100%;border-collapse:collapse"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


# ------------------------------------------------------- visual dispatch table
def render_visual(pid, name, vis, pos, title):
    w, h = pos["width"], pos["height"]
    vt = vis["visualType"]
    inner_h = h - (26 if title else 8)

    if vt == "pageNavigator":
        tabs = "".join(
            f'<div style="padding:5px 12px;border-radius:7px;font-size:10.5px;'
            f'{"background:#2f6bff;color:#fff" if p == pid else f"background:#f4f7ff;color:{MUT};border:1px solid "+LINE};'
            f'white-space:nowrap">{esc(nm)}</div>' for p, nm in NAV)
        return f'<div style="display:flex;gap:6px;align-items:center;height:100%">{tabs}</div>', False

    if vt == "textbox":
        paras = vis["objects"]["general"][0]["properties"]["paragraphs"]
        html = ""
        for p in paras:
            runs = "".join(f'<span style="font-size:{tr["textStyle"]["fontSize"].replace("pt","")}pt;'
                           f'font-weight:{tr["textStyle"]["fontWeight"]};color:{tr["textStyle"]["color"]}">'
                           f'{esc(tr["value"])}</span>' for tr in p["textRuns"])
            html += f'<div style="margin-bottom:3px;line-height:1.3">{runs}</div>'
        return html, False

    if vt == "slicer":
        f = vis["query"]["queryState"]["Values"]["projections"][0]
        fld = f["nativeQueryRef"]
        vals = SLICER_VALUES.get(fld, [])
        chips = "".join(f'<span style="font-size:9px;color:{MUT};border:1px solid {LINE};border-radius:5px;'
                        f'padding:1px 6px;margin:0 4px 3px 0;display:inline-block">{esc(v)}</span>' for v in vals)
        return (f'<div style="font-size:9px;color:{MUT2};margin-bottom:3px">▾ {esc(fld)}</div>{chips}'), False

    if vt == "card":
        m = vis["query"]["queryState"]["Values"]["projections"][0]["nativeQueryRef"]
        val = D["cards"].get(m, "—")
        colr = RISK if ("Canceled" in m and "%" in m) or "Margin" in m and "Paid" not in m else INK
        if m == "Paid-ship Margin":
            colr = OK
        return (f'<div style="font-size:8.5px;color:{MUT};text-transform:uppercase;letter-spacing:.3px;'
                f'margin-bottom:2px;line-height:1.15">{esc(title or m)}</div>'
                f'<div style="font-size:21px;font-weight:700;color:{colr};line-height:1.1">{esc(val)}</div>'
                f'<div style="font-size:8px;color:{MUT2};margin-top:2px">{esc(m)}</div>'), True

    data = D.get(name)
    if isinstance(data, list) and data and "x" in data[0] and vt in ("columnChart", "barChart", "clusteredColumnChart", "clusteredBarChart", "donutChart"):
        data = [{"k": d["x"], "v": d["y"]} for d in data]   # same series, categorical axis
    if isinstance(data, list) and data and "k" in data[0] and vt == "lineChart":
        data = [{"x": d["k"], "y": d["v"]} for d in data]
    if data is None:
        return f'<div style="font-size:9px;color:{MUT2}">[{vt}]</div>', False

    if vt == "barChart":
        pctfmt = name in ("barHubCancel",)
        return bars_h(data, w - 16, inner_h, fmt=(lambda v: f"{v:.2f}%") if pctfmt else fnum), False
    if isinstance(data, list) and data and "series" in data[0]:
        f = (lambda v: f"{v:.1f}") if name == "colPhase" else (lambda v: f"R${v:.2f}") if name == "colFeeCost" else fnum
        return bars_grouped(data, w - 16, inner_h, fmt=f), False
    if vt in ("columnChart",):
        pct = name in ("colCancMonth", "colCancValue", "colCancHour")
        rot = name in ("colValueBand", "colDistBand", "colCycleHist", "colDaypart", "colCancValue")
        f = (lambda v: f"{v:.1f}%") if pct else (lambda v: f"{v:.0f}′") if name == "colDistBand" else fnum
        return bars_v(data, w - 16, inner_h, fmt=f, rotate=rot), False
    if vt == "clusteredColumnChart":
        f = (lambda v: f"{v:.1f}") if name == "colPhase" else (lambda v: f"R${v:.2f}") if name == "colFeeCost" else fnum
        return bars_grouped(data, w - 16, inner_h, fmt=f), False
    if vt == "lineChart":
        pct = "Canc" in name
        return line(data, w - 16, inner_h, fmt=(lambda v: f"{v:.2f}%") if pct else fnum), False
    if vt == "donutChart":
        return donut(data, w - 16, inner_h), False
    if vt == "scatterChart":
        meta = {"scatHub": ("Median distance (km)", "Median cycle (phút)", False),
                "scatHubQuad": ("Đơn hoàn tất", "Tỷ lệ hủy %", False),
                "scatPartner": ("GMV (log)", "Tỷ lệ hủy %", True)}[name]
        return scatter(data, w - 16, inner_h, meta[0], meta[1], logx=meta[2]), False
    if vt == "tableEx":
        return table(data, w, inner_h), False
    if vt == "pivotTable":
        return matrix(data, w, inner_h, pct=(name == "matSegChan")), False
    return f'<div style="font-size:9px;color:{MUT2}">[{vt}]</div>', False


# ------------------------------------------------------------------ page build
SLICER_VALUES = {
    "Date": ["01/01/2021 → 30/04/2021"],
    "hub_city": ["São Paulo", "Rio de Janeiro", "Porto Alegre", "Curitiba"],
    "store_segment": ["FOOD", "GOOD"],
    "channel_type": ["MARKETPLACE", "OWN CHANNEL"],
}
order = json.load(open(os.path.join(PAGES, "pages.json"), encoding="utf-8"))["pageOrder"]
NAV = []
for pid in order:
    NAV.append((pid, json.load(open(os.path.join(PAGES, pid, "page.json"), encoding="utf-8"))["displayName"]))

sections = []
for pid in order:
    meta = json.load(open(os.path.join(PAGES, pid, "page.json"), encoding="utf-8"))
    vfiles = sorted(glob.glob(os.path.join(PAGES, pid, "visuals", "*", "visual.json")))
    items = []
    for vf in vfiles:
        j = json.load(open(vf, encoding="utf-8"))
        name, pos, vis = j["name"], j["position"], j["visual"]
        tobj = vis.get("visualContainerObjects", {}).get("title", [{}])
        props = tobj[0].get("properties", {}) if tobj else {}
        title = None
        if props.get("show", {}).get("expr", {}).get("Literal", {}).get("Value") == "true":
            title = props.get("text", {}).get("expr", {}).get("Literal", {}).get("Value", "''").strip("'")
        body, is_card = render_visual(pid, name, vis, pos, title)
        chrome = (f'background:{PANEL};border:1px solid {LINE};border-radius:10px;'
                  f'box-shadow:0 1px 3px rgba(15,26,48,.06);padding:8px 8px 6px')
        if vis["visualType"] in ("pageNavigator", "textbox", "slicer"):
            chrome = (f'background:#fbfcff;border:1px dashed {LINE};border-radius:10px;padding:8px'
                      if vis["visualType"] == "slicer" else
                      (f'background:#f6f8ff;border:1px solid {LINE};border-radius:10px;padding:9px 11px'
                       if vis["visualType"] == "textbox" else "padding:0"))
        head = (f'<div style="font-size:9.5px;font-weight:600;color:{INK};margin-bottom:4px;'
                f'line-height:1.2">{esc(title)}</div>' if title and not is_card else "")
        items.append(f'<div style="position:absolute;left:{pos["x"]}px;top:{pos["y"]}px;'
                     f'width:{pos["width"]}px;height:{pos["height"]}px;{chrome};overflow:hidden;'
                     f'box-sizing:border-box">{head}<div style="position:relative;height:calc(100% - '
                     f'{18 if head else 0}px)">{body}</div></div>')
    sections.append(f'<section class="page" id="{pid}"><div class="canvas">{"".join(items)}</div>'
                    f'<div class="cap">{esc(meta["displayName"])} — canvas {meta["width"]}×{meta["height"]} '
                    f'· {len(vfiles)} visual · render từ PBIR definition</div></section>')

html = f"""<meta charset="utf-8"><title>Power BI v2 — Brazilian Delivery Center (8 user-story pages)</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#e9eefb;font:13px/1.45 "Segoe UI",Inter,system-ui,sans-serif;color:{INK}}}
.wrap{{max-width:1360px;margin:0 auto;padding:22px 16px 60px}}
h1{{font-size:19px;margin:0 0 4px}}
.sub{{color:{MUT};font-size:12px;margin-bottom:18px}}
.page{{margin-bottom:26px}}
.canvas{{position:relative;width:1280px;height:800px;background:linear-gradient(180deg,#f7f9ff,#eef2fc);
        border:1px solid #d8e0f4;border-radius:12px;overflow:hidden}}
.cap{{font-size:10.5px;color:{MUT2};padding:6px 2px}}
</style>
<div class="wrap">
<h1>Power BI — Brazilian Delivery Center · bản dựng lại theo user story (8 trang)</h1>
<div class="sub">Preview render trực tiếp từ <b>PBIR definition</b> (toạ độ/loại visual/tiêu đề lấy từ
<code>powerbi/BrazilianDeliveryCenter.Report/definition/pages/**/visual.json</code>), số liệu từ
<code>dashboard/pbi_v2_data.json</code> — tức là đúng những gì Power BI Desktop sẽ hiện sau khi Refresh.
Slicer/nav vẽ dạng chrome minh hoạ (tương tác thật chỉ có trong Desktop).</div>
{"".join(sections)}
</div>"""
open(OUT, "w", encoding="utf-8").write(html)
print(f"wrote {OUT} ({len(html)/1024:.0f} KB, {len(order)} pages)")
