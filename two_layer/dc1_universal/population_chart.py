#!/usr/bin/env python3
"""Generate hand-soldering population charts for the universal DC1 board.

Inputs : manifest.json (same folder)
Outputs: population_chart.pdf, POPULATION.md
Run    : python3 population_chart.py
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import mm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "manifest.json").read_text())
ROWS = M["rows"]
CARDS = "abcd"
COLS = [f"{k}_N{n}" for n in range(4) for k in ("POS", "INV")]
NO_FP = "\u2013"  # union has no footprint at this position

grid = {}       # (input, colnet) -> row
central = []
for r in ROWS:
    ins = [n for n in r["nets"] if n.startswith("IN_")]
    if ins:
        other = [n for n in r["nets"] if not n.startswith("IN_")][0]
        grid[(int(ins[0][3:]), other)] = r
    else:
        central.append(r)

def _role(r):
    n = set(r["nets"])
    return ("bias" if "+5V_REF" in n else "balance" if "GND" in n else "feedback")


def _target(r):
    return [n for n in r["nets"] if n not in ("GND", "+5V_REF") and not n.startswith("V_SUM")][0]


# group central parts by net pair (role, then local node), not by ref number
central.sort(key=lambda r: (("bias", "balance", "feedback").index(_role(r)),
                            int(_target(r)[-1]), _target(r).split("_")[0] != "POS"))

# Original boards had 420 positions (R001..R420); the 112 future-proof sites were
# appended as R421..R532 and are DNP on every card.
N_ORIG = 420
ADDED = {r["reference"] for r in ROWS if int(r["reference"][1:]) > N_ORIG}
assert len(ROWS) == M["universal_resistor_positions"] == 532
assert len(grid) == M["input_positions"] == 512 and len(central) == 20
assert len(ADDED) == M["added_default_dnp_positions"] and all(
    not r["cards"] for r in ROWS if r["reference"] in ADDED)


def neuron(card, n):
    return CARDS.index(card) * 4 + n


def cell(card, i, col):
    r = grid.get((i, col))
    if r is None:
        return ("", NO_FP, None)
    c = r["cards"].get(card)
    if c is None:
        return (r["reference"], "DNP+" if r["reference"] in ADDED else "DNP", None)
    return (r["reference"], c["value"], c["tolerance"])


def counts(card):
    pop = [r for r in ROWS if card in r["cards"]]
    p1 = sum(1 for r in pop if r["cards"][card]["tolerance"] <= 0.01)
    return len(pop), len(pop) - p1, p1


# ---------------- PDF ----------------
ss = getSampleStyleSheet()
H = ParagraphStyle("h", parent=ss["Heading2"], fontName="Helvetica-Bold",
                   fontSize=13, spaceAfter=2, spaceBefore=0)
S = ParagraphStyle("s", parent=ss["Normal"], fontName="Helvetica", fontSize=7.5,
                   leading=9.5)
CELL = ParagraphStyle("c", fontName="Helvetica", fontSize=6.6, leading=7.6,
                      alignment=1)
INK, MUTED, DNPBG, NOFPBG, PRECBG = (colors.HexColor(x) for x in
    ("#111111", "#8a8a8a", "#ffe9e6", "#ededed", "#e3efff"))
ADDBG = colors.HexColor("#f3e6ff")

LEGEND = ("<b>value</b> = solder 5% 0805.  <b>value</b> with <b>1%</b> tag on blue = "
          "solder 1% precision part.  <font color='#c0392b'><b>DNP</b></font> = leave pads "
          "OPEN (never 0\u03a9).  <font color='#7d3c98'><b>DNP+</b></font> on purple = "
          "future-proof site added in the 532-site layout, open on all four cards.")


def weight_table(card, lo, hi):
    hdr = ["IN"] + [f"{c.split('_')[0]}<br/>N{neuron(card, int(c[-1]))} "
                    f"<font size=5 color='#bbbbbb'>({c})</font>" for c in COLS]
    data = [[Paragraph(f"<b>{h}</b>", CELL) for h in hdr]]
    style = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0b0b0")),
             ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 1),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]
    data[0] = [Paragraph(f"<font color='white'><b>{h}</b></font>", CELL) for h in hdr]
    for ri, i in enumerate(range(lo, hi), start=1):
        row = [Paragraph(f"<b>IN{i}</b>", CELL)]
        for ci, col in enumerate(COLS, start=1):
            ref, val, tol = cell(card, i, col)
            if val == NO_FP:
                row.append(Paragraph(f"<font color='#999'>{NO_FP}</font>", CELL))
                style.append(("BACKGROUND", (ci, ri), (ci, ri), NOFPBG))
            elif val in ("DNP", "DNP+"):
                add = val == "DNP+"
                row.append(Paragraph(f"<font size=5.5 color='#888'>{ref}</font> "
                                     f"<font color='{'#7d3c98' if add else '#c0392b'}'><b>{val}</b></font>", CELL))
                style.append(("BACKGROUND", (ci, ri), (ci, ri), ADDBG if add else DNPBG))
            else:
                tag = " <font color='#1f5fbf'><b>1%</b></font>" if tol <= 0.01 else ""
                row.append(Paragraph(f"<font size=5.5 color='#555'>{ref}</font> "
                                     f"<b>{val}</b>{tag}", CELL))
                if tol <= 0.01:
                    style.append(("BACKGROUND", (ci, ri), (ci, ri), PRECBG))
        data.append(row)
    w = [14 * mm] + [30 * mm] * 8
    t = Table(data, colWidths=w, rowHeights=[9 * mm] + [4.95 * mm] * (hi - lo),
              repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


def central_table(card):
    hdr = ["Ref", "X mm", "Y mm", "Pad 1", "Pad 2", "Role", "Neuron", "Value", "Tol",
           "Original ref"]
    data = [hdr]
    style = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0b0b0")),
             ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
             ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
             ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
             ("FONTSIZE", (0, 0), (-1, -1), 8.5),
             ("ALIGN", (0, 0), (-1, -1), "CENTER")]
    for ri, r in enumerate(central, start=1):
        p1, p2 = r["pads"]["1"], r["pads"]["2"]
        role = _role(r)
        idx = int(_target(r)[-1])
        c = r["cards"].get(card)
        if c:
            val, tol, orig = c["value"], f"{c['tolerance']*100:g}%", c["ref"]
            if c["tolerance"] <= 0.01:
                style.append(("BACKGROUND", (7, ri), (8, ri), PRECBG))
            style.append(("FONTNAME", (7, ri), (7, ri), "Helvetica-Bold"))
        else:
            add = r["reference"] in ADDED
            val, tol, orig = ("DNP+ (new)" if add else "DNP (open)"), "", ""
            style.append(("BACKGROUND", (0, ri), (-1, ri), ADDBG if add else DNPBG))
            style.append(("TEXTCOLOR", (7, ri), (7, ri),
                          colors.HexColor("#7d3c98" if add else "#c0392b")))
        data.append([r["reference"], f"{r['x_mm']:g}", f"{r['y_mm']:g}", p1, p2, role,
                     f"N{neuron(card, idx)}", val, tol, orig])
    t = Table(data, colWidths=[16*mm, 14*mm, 14*mm, 24*mm, 24*mm, 20*mm, 16*mm,
                               26*mm, 12*mm, 28*mm])
    t.setStyle(TableStyle(style))
    return t


FIXED = [["U1", "TL074 quad op-amp, SOIC-14", "all cards"],
         ["C_U1P, C_U1N", "0.1 \u00b5F 50 V 0805 decoupling", "all cards"],
         ["J_STRADDLE_EDGE", "76-pin edge straddle", "all cards"]]


def footer(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 7)
    canv.setFillColor(colors.HexColor("#777"))
    canv.drawString(10 * mm, 6 * mm, "DC1 universal board \u00b7 population chart \u00b7 "
                    "generated by population_chart.py from manifest.json")
    canv.drawRightString(269 * mm, 6 * mm, f"page {doc.page}")
    canv.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(str(HERE / "population_chart.pdf"),
                            pagesize=landscape(letter), leftMargin=10*mm,
                            rightMargin=10*mm, topMargin=8*mm, bottomMargin=11*mm,
                            title="DC1 universal population chart")
    st = [Paragraph("DC1 universal board: population summary", H),
          Paragraph("One 100\u00d7100 mm board, four builds (a\u2013d). Each build fits only "
                    "the parts listed for its letter; every other resistor footprint "
                    "is left open. Never fit a 0 \u03a9 link in a DNP position. "
                    f"{len(ROWS)} resistor sites total: {len(grid)} input sites (full 64 inputs "
                    f"\u00d7 4 neurons \u00d7 POS/INV matrix, every cell has a footprint) + "
                    f"{len(central)} central bias/balance/feedback sites. {len(ADDED)} of these "
                    "are future-proof additions, DNP on every card.", S),
          Spacer(1, 4)]
    data = [["Card", "Neurons", "Resistors fitted", "5% (weights, bias)", "1% (balance, feedback)",
             "DNP footprints", "of which new (DNP+)"]]
    for k in CARDS:
        n, p5, p1 = counts(k)
        data.append([f"DC1{k}", f"N{neuron(k,0)}\u2013N{neuron(k,3)}", n, p5, p1, len(ROWS) - n, len(ADDED)])
    t = Table(data, colWidths=[20*mm, 24*mm, 32*mm, 34*mm, 40*mm, 30*mm, 36*mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTSIZE", (0, 0), (-1, -1), 9),
                           ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    st += [t, Spacer(1, 8), Paragraph("<b>Fixed parts (fit on every card)</b>", S)]
    t = Table([["Ref", "Part", "Cards"]] + FIXED, colWidths=[40*mm, 80*mm, 30*mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                           ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                           ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    st += [t, Spacer(1, 8), Paragraph(LEGEND, S), Spacer(1, 4),
           Paragraph("Board layout: IN0\u2013IN31 bank on the left half, IN32\u2013IN63 on the right, "
                     "one row per input, eight columns per bank (POS/INV for local N0\u2013N3). "
                     "The 20 central resistors sit in two columns at x = 47 / 52.6 mm, "
                     "y = 44\u201394 mm (bias on +5V_REF to every POS/INV node, balance on GND "
                     "to every node, feedback to V_SUM). Reference numbers in each cell match the silkscreen.", S),
           PageBreak()]
    for k in CARDS:
        for lo, hi, side in ((0, 32, "left bank"), (32, 64, "right bank")):
            n, p5, p1 = counts(k)
            st += [Paragraph(f"DC1{k} \u00b7 weights IN{lo}\u2013IN{hi-1} ({side}) \u00b7 "
                             f"neurons N{neuron(k,0)}\u2013N{neuron(k,3)}", H),
                   Paragraph(LEGEND, S), Spacer(1, 2), weight_table(k, lo, hi), PageBreak()]
        st += [Paragraph(f"DC1{k} \u00b7 central resistors (feedback, bias, balance)", H),
               Paragraph("x = 47 / 52.6 mm, y = 44\u201394 mm, grouped by net pair. Balance and "
                         "feedback are 1% (blue); bias is 5%. Red and purple rows stay open.", S), Spacer(1, 4),
               central_table(k), Spacer(1, 8),
               Paragraph("Also fit the fixed parts: U1 TL074, C_U1P and C_U1N 0.1 \u00b5F 50 V "
                         "0805, J_STRADDLE_EDGE.", S), PageBreak()]
    st.pop()
    doc.build(st, onFirstPage=footer, onLaterPages=footer)


# ---------------- Markdown ----------------
def build_md():
    L = ["# DC1 universal board: population chart", "",
         "Generated by `population_chart.py` from `manifest.json`. The PDF "
         "(`population_chart.pdf`) has the same data laid out for printing.", "",
         "Legend: `value` = fit 5% 0805, `value*` = fit 1% precision, `DNP` = leave "
         "pads open (never 0 Ω), `DNP+` = future-proof site added in the 532-site layout, "
         "open on every card.", "",
         f"{len(ROWS)} sites: {len(grid)} input sites (64 inputs × 4 neurons × POS/INV, every "
         f"matrix cell populated with a footprint) + {len(central)} central bias/balance/feedback "
         f"sites at x 47/52.6 mm, y 44–94 mm. {len(ADDED)} sites are new and DNP on all cards.", "",
         "Fixed on every card: U1 TL074, C_U1P/C_U1N 0.1 µF 50 V 0805, J_STRADDLE_EDGE (76 pins).", "",
         "| Card | Neurons | Fitted | 5% | 1% | DNP | of which new (DNP+) |", "|---|---|---|---|---|---|---|"]
    for k in CARDS:
        n, p5, p1 = counts(k)
        L.append(f"| DC1{k} | N{neuron(k,0)}–N{neuron(k,3)} | {n} | {p5} | {p1} | {len(ROWS)-n} | {len(ADDED)} |")
    for k in CARDS:
        L += ["", f"## DC1{k} (neurons N{neuron(k,0)}–N{neuron(k,3)})", ""]
        L += ["| IN | " + " | ".join(f"{c} (N{neuron(k,int(c[-1]))})" for c in COLS) + " |",
              "|---" * 9 + "|"]
        for i in range(64):
            cells = []
            for col in COLS:
                ref, val, tol = cell(k, i, col)
                if val == NO_FP:
                    cells.append("–")
                elif val in ("DNP", "DNP+"):
                    cells.append(f"{ref} {val}")
                else:
                    cells.append(f"{ref} **{val}{'*' if tol <= 0.01 else ''}**")
            L.append(f"| IN{i} | " + " | ".join(cells) + " |")
        L += ["", f"Central resistors, DC1{k}:", "",
              "| Ref | X | Y | Pad 1 | Pad 2 | Role | Value | Tol | Original |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in central:
            c = r["cards"].get(k)
            v = (f"**{c['value']}{'*' if c['tolerance'] <= 0.01 else ''}**", f"{c['tolerance']*100:g}%",
                 c["ref"]) if c else ("DNP+" if r["reference"] in ADDED else "DNP", "", "")
            L.append(f"| {r['reference']} | {r['x_mm']:g} | {r['y_mm']:g} | {r['pads']['1']} | "
                     f"{r['pads']['2']} | {_role(r)} | {v[0]} | {v[1]} | {v[2]} |")
    (HERE / "POPULATION.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    build_pdf()
    build_md()
    print("wrote population_chart.pdf, POPULATION.md")
