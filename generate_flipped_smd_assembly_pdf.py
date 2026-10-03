#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_flipped_smd_assembly_pdf.py
------------------------------------
Generates a complete, publication-grade SMD Assembly & Soldering Guide PDF for the
70x100mm Analog Neural Network Test Board.

Features:
- Board layout, traces, pads, and components are FLIPPED horizontally (X-mirrored: 100 - x)
  matching the bottom/through-hole view or translucent PCB inspection.
- All text annotations, component references, resistance values, IC models,
  diode polarities, and jumper designations are strictly in the CORRECT,
  NORMAL (left-to-right, upright) orientation.
- ZERO label collisions: Dedicated, quadrant-separated clearance coordinates for every
  component, resistor, diode, jumper, and test point.
- Shows exactly where:
  * Chips go: U1 (TL074), U2 (TL074) with Pin 1 index dots & notch
  * Diodes go: D1_0, D1_1, D2_0, D2_1 (1N4148) with Cathode [K] band markings
  * Resistors go: All 26 resistors with exact values (10k, 18k, 15k, 22k, 1k)
  * Jumpers go:
    - 10 Wire Jumpers (W1..W10) with through-hole pads & bridge routing lines
    - 5 SMD 0-Ohm Jumpers (JMP_BIAS, JMP_V12, JMP_N12, JMP_WTA, JMP_GND)
  * Capacitors: C1..C4 (0.1uF)
  * LEDs: LED0 (Green: Horiz), LED1 (Red: Vert) with Cathode [K] markings
  * Headers & Switch: J_IN, J_PWR, J_OUT, SW1 (4-DIP)
  * Test points: TP_X0..X3, TP_SUM0/1, TP_ACT0/1, TP_OUT0/1, TP_+12V/-12V/+5V/GND

Formats:
- Page 1: 1:1 True-Scale Flipped Assembly Map on US Letter Landscape
- Page 2: Enlarged High-Legibility Bench Soldering Guide (1.82x Zoom)
- Page 3: Complete SMD Bill of Materials & Assembly Checklist Table
"""

import os
import sys
import subprocess
import shutil
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
GS_CLI = "/opt/homebrew/bin/gs"
PDFUNITE = "/opt/homebrew/bin/pdfunite"
PDFTOPPM = "/opt/homebrew/bin/pdftoppm"
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"
SCRATCH_DIR = os.path.join(WORKSPACE_DIR, ".tmp_assembly")
RENDERS_DIR = os.path.join(WORKSPACE_DIR, "renders")

os.makedirs(SCRATCH_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

PAGE_W_PT = 792.0
PAGE_H_PT = 612.0
MM_TO_PT = 72.0 / 25.4  # ~2.8346 pt/mm

BOARD_W_MM = 100.0
BOARD_H_MM = 70.0


def extract_board_data():
    board_path = os.path.join(WORKSPACE_DIR, "test_board_freerouted.kicad_pcb")
    board = pcbnew.LoadBoard(board_path)

    components = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        val = fp.GetValue()
        pos = fp.GetPosition()
        rot = fp.GetOrientationDegrees()
        pads = []
        for p in fp.Pads():
            p_pos = p.GetPosition()
            pads.append({
                "num": p.GetNumber(),
                "net": p.GetNetname(),
                "x_mm": p_pos.x / 1e6,
                "y_mm": p_pos.y / 1e6,
                "w_mm": p.GetSize().x / 1e6,
                "h_mm": p.GetSize().y / 1e6,
                "shape": p.GetShape()
            })
        components.append({
            "ref": ref,
            "val": val,
            "x_mm": pos.x / 1e6,
            "y_mm": pos.y / 1e6,
            "rot": rot,
            "pads": pads
        })

    tracks = []
    for t in board.GetTracks():
        tracks.append({
            "start_x": t.GetStart().x / 1e6,
            "start_y": t.GetStart().y / 1e6,
            "end_x": t.GetEnd().x / 1e6,
            "end_y": t.GetEnd().y / 1e6,
            "width": t.GetWidth() / 1e6
        })

    return components, tracks


def build_ps_code(components, tracks, scale=1.0, is_zoomed=False):
    """
    Builds PostScript code for a single page assembly map.
    Flipping rule: x_flipped = 100.0 - x_original.
    Text is rendered upright and left-to-right (no mirroring).
    """
    scale_pt = MM_TO_PT * scale
    board_w_pt = BOARD_W_MM * scale_pt
    board_h_pt = BOARD_H_MM * scale_pt

    # Center board on Letter Landscape
    ox = (PAGE_W_PT - board_w_pt) / 2.0
    oy = (PAGE_H_PT - board_h_pt) / 2.0 - (18.0 if not is_zoomed else 5.0)

    def to_ps(fx, fy):
        px = ox + fx * scale_pt
        py = oy + board_h_pt - (fy * scale_pt)
        return px, py

    ps = []
    ps.append("%!PS-Adobe-3.0")
    ps.append("%%BoundingBox: 0 0 792 612")
    ps.append("%%Pages: 1")
    ps.append("%%EndComments")
    ps.append("%%Page: 1 1")

    # Helper procedures
    ps.append("""
    /rectfill_c { % x y w h r g b
        setrgbcolor
        newpath 4 2 roll moveto
        1 index 0 rlineto
        0 exch rlineto
        neg 0 rlineto
        closepath fill
    } def
    /rectstroke_c { % x y w h lw r g b
        setrgbcolor setlinewidth
        newpath 4 2 roll moveto
        1 index 0 rlineto
        0 exch rlineto
        neg 0 rlineto
        closepath stroke
    } def
    /circlefill_c { % cx cy r red green blue
        setrgbcolor
        newpath 0 360 arc fill
    } def
    /circlestroke_c { % cx cy r lw red green blue
        setrgbcolor setlinewidth
        newpath 0 360 arc stroke
    } def
    /centertext { % (string) x y font_name size red green blue
        setrgbcolor
        exch findfont exch scalefont setfont
        moveto
        dup stringwidth pop 2 div neg -2.5 rmoveto
        show
    } def
    /lefttext { % (string) x y font_name size red green blue
        setrgbcolor
        exch findfont exch scalefont setfont
        moveto
        0 -2.5 rmoveto
        show
    } def
    /righttext { % (string) x y font_name size red green blue
        setrgbcolor
        exch findfont exch scalefont setfont
        moveto
        dup stringwidth pop neg -2.5 rmoveto
        show
    } def
    /badgecentertext { % (string) x y font_name size red green blue
        /t_b exch def /t_g exch def /t_r exch def
        /f_sz exch def /f_nm exch def
        /t_y exch def /t_x exch def
        /str exch def
        f_nm findfont f_sz scalefont setfont
        str stringwidth pop /sw exch def
        /bw sw 3 add def
        /bh f_sz 2 add def
        t_x bw 2 div sub t_y bh 2 div sub bw bh 0.08 0.17 0.12 rectfill_c
        t_r t_g t_b setrgbcolor
        t_x t_y moveto
        sw 2 div neg f_sz 0.35 mul neg rmoveto
        str show
    } def
    /badgelefttext { % (string) x y font_name size red green blue
        /t_b exch def /t_g exch def /t_r exch def
        /f_sz exch def /f_nm exch def
        /t_y exch def /t_x exch def
        /str exch def
        f_nm findfont f_sz scalefont setfont
        str stringwidth pop /sw exch def
        /bw sw 3 add def
        /bh f_sz 2 add def
        t_x 1 sub t_y bh 2 div sub bw bh 0.08 0.17 0.12 rectfill_c
        t_r t_g t_b setrgbcolor
        t_x t_y moveto
        0 f_sz 0.35 mul neg rmoveto
        str show
    } def
    /badgerighttext { % (string) x y font_name size red green blue
        /t_b exch def /t_g exch def /t_r exch def
        /f_sz exch def /f_nm exch def
        /t_y exch def /t_x exch def
        /str exch def
        f_nm findfont f_sz scalefont setfont
        str stringwidth pop /sw exch def
        /bw sw 3 add def
        /bh f_sz 2 add def
        t_x bw sub 1 add t_y bh 2 div sub bw bh 0.08 0.17 0.12 rectfill_c
        t_r t_g t_b setrgbcolor
        t_x t_y moveto
        sw neg f_sz 0.35 mul neg rmoveto
        str show
    } def
    """)

    # 1. Header & Title Block
    if not is_zoomed:
        title_y = PAGE_H_PT - 36.0
        ps.append(f"(ANALOG NEURAL NETWORK TEST BOARD (70x100mm) - SMD ASSEMBLY MAP) {PAGE_W_PT/2.0:.1f} {title_y:.1f} /Helvetica-Bold 15 0.1 0.1 0.15 centertext")
        ps.append(f"(FLIPPED VIEW [X-MIRRORED] - ALL TEXT IN CORRECT UPRIGHT ORIENTATION | SCALE: 1:1 TRUE SIZE) {PAGE_W_PT/2.0:.1f} {title_y - 16.0:.1f} /Helvetica-Bold 9.5 0.15 0.3 0.6 centertext")
        ps.append(f"(Designed for bottom/translucent inspection & hand-soldering. Traces/Pads are flipped; Text is upright left-to-right.) {PAGE_W_PT/2.0:.1f} {title_y - 28.0:.1f} /Helvetica 8 0.4 0.4 0.4 centertext")
    else:
        title_y = PAGE_H_PT - 26.0
        ps.append(f"(ANALOG NEURAL NETWORK TEST BOARD - ENLARGED BENCH SOLDERING GUIDE) {PAGE_W_PT/2.0:.1f} {title_y:.1f} /Helvetica-Bold 14 0.1 0.1 0.15 centertext")
        ps.append(f"(FLIPPED VIEW [X-MIRRORED] | ALL TEXT UPRIGHT | 1.82x BENCH SCALE) {PAGE_W_PT/2.0:.1f} {title_y - 14.0:.1f} /Helvetica-Bold 9.5 0.8 0.2 0.1 centertext")

    # 2. Board Substrate (FR-4 Dark Olive Background)
    ps.append(f"{ox:.2f} {oy:.2f} {board_w_pt:.2f} {board_h_pt:.2f} 0.08 0.17 0.12 rectfill_c")
    ps.append(f"{ox:.2f} {oy:.2f} {board_w_pt:.2f} {board_h_pt:.2f} 1.2 0.85 0.8 0.3 rectstroke_c")

    # 3. F.Cu Copper Tracks in Muted Bronze / Dark Copper
    ps.append("""
    gsave
    1 setlinecap 1 setlinejoin
    0.14 0.28 0.18 setrgbcolor
    """)
    for t in tracks:
        fx1 = 100.0 - t["start_x"]
        fy1 = t["start_y"]
        fx2 = 100.0 - t["end_x"]
        fy2 = t["end_y"]
        px1, py1 = to_ps(fx1, fy1)
        px2, py2 = to_ps(fx2, fy2)
        tw = max(0.3, t["width"]) * scale_pt
        ps.append(f"{tw:.2f} setlinewidth newpath {px1:.2f} {py1:.2f} moveto {px2:.2f} {py2:.2f} lineto stroke")
    ps.append("grestore")

    # 4. Corner Mounting Holes (H1..H4)
    for hx, hy in [(4.0, 4.0), (96.0, 4.0), (4.0, 66.0), (96.0, 66.0)]:
        fx = 100.0 - hx
        px, py = to_ps(fx, hy)
        r_pad = (3.2 / 2.0 + 1.4) * scale_pt
        r_hole = (3.2 / 2.0) * scale_pt
        ps.append(f"{px:.2f} {py:.2f} {r_pad:.2f} 0.75 0.7 0.4 circlefill_c")
        ps.append(f"{px:.2f} {py:.2f} {r_hole:.2f} 0.95 0.95 0.95 circlefill_c")
        ps.append(f"{px:.2f} {py:.2f} {r_hole:.2f} 0.5 0.2 0.2 0.2 circlestroke_c")

    # 5. Wire Jumpers (W1..W10) Bridge Lines, Pads & Badges
    jumpers = {fp["ref"]: fp for fp in components if fp["ref"].startswith("W") and fp["ref"][1:].isdigit()}
    jumper_colors = [
        (0.95, 0.3, 0.2),   # W1: Coral
        (0.2, 0.85, 0.3),   # W2: Green
        (0.2, 0.65, 1.0),   # W3: Blue
        (1.0, 0.75, 0.1),   # W4: Amber
        (0.95, 0.2, 0.8),   # W5: Magenta
        (0.1, 0.9, 0.9),    # W6: Cyan
        (0.85, 0.5, 0.1),   # W7: Brown
        (0.7, 0.3, 0.9),    # W8: Purple
        (0.4, 0.95, 0.5),   # W9: Mint
        (1.0, 0.4, 0.6),    # W10: Rose
    ]

    # Carefully curated badge locations along each jumper bridge
    jumper_badge_locs = {
        "W1":  (20.5, 45.5),
        "W2":  (76.0, 27.5),  # away from SW1
        "W3":  (74.0, 23.5),
        "W4":  (62.0, 43.0),  # open middle corridor away from PD resistors
        "W5":  (16.5, 28.0),  # clear of U2, JMP_WTA, and W1
        "W6":  (55.5, 6.5),   # top rail
        "W7":  (72.5, 44.5),
        "W8":  (56.0, 61.5),
        "W9":  (64.0, 9.5),   # open top margin, clear of Rin_0, Rb1_0, & JMP_V12
        "W10": (72.5, 49.5),
    }

    for j_idx in range(1, 11):
        jref = f"W{j_idx}"
        if jref in jumpers:
            jfp = jumpers[jref]
            pads = jfp["pads"]
            if len(pads) >= 2:
                p1, p2 = pads[0], pads[1]
                fx1 = 100.0 - p1["x_mm"]
                fy1 = p1["y_mm"]
                fx2 = 100.0 - p2["x_mm"]
                fy2 = p2["y_mm"]

                px1, py1 = to_ps(fx1, fy1)
                px2, py2 = to_ps(fx2, fy2)

                cr, cg, cb = jumper_colors[(j_idx - 1) % len(jumper_colors)]

                # Dashed bridge line
                ps.append(f"""
                gsave
                [{3.5*scale:.1f} {2.5*scale:.1f}] 0 setdash
                {2.2*scale:.2f} setlinewidth
                {cr:.2f} {cg:.2f} {cb:.2f} setrgbcolor
                newpath {px1:.2f} {py1:.2f} moveto {px2:.2f} {py2:.2f} lineto stroke
                grestore
                """)

                # Through-hole pads
                r_annular = (2.0 / 2.0) * scale_pt
                r_drill = (1.0 / 2.0) * scale_pt
                for px, py in [(px1, py1), (px2, py2)]:
                    ps.append(f"{px:.2f} {py:.2f} {r_annular:.2f} 0.88 0.75 0.3 circlefill_c")
                    ps.append(f"{px:.2f} {py:.2f} {r_drill:.2f} 0.1 0.1 0.1 circlefill_c")
                    ps.append(f"{px:.2f} {py:.2f} {r_annular:.2f} 0.5 0.2 0.2 0.2 circlestroke_c")

                # Badge
                bfx, bfy = jumper_badge_locs.get(jref, ((fx1 + fx2) / 2.0, (fy1 + fy2) / 2.0))
                b_px, b_py = to_ps(bfx, bfy)

                bw = 14.0 * scale
                bh = 8.5 * scale
                f_size = 7.5 * scale if not is_zoomed else 10.0
                ps.append(f"""
                gsave
                newpath {b_px - bw/2:.2f} {b_py - bh/2:.2f} moveto {bw:.2f} 0 rlineto 0 {bh:.2f} rlineto {-bw:.2f} 0 rlineto closepath
                1.0 1.0 1.0 setrgbcolor fill
                newpath {b_px - bw/2:.2f} {b_py - bh/2:.2f} moveto {bw:.2f} 0 rlineto 0 {bh:.2f} rlineto {-bw:.2f} 0 rlineto closepath
                0.8 setlinewidth {cr:.2f} {cg:.2f} {cb:.2f} setrgbcolor stroke
                grestore
                ({jref}) {b_px:.2f} {b_py:.2f} /Helvetica-Bold {f_size:.1f} 0.1 0.1 0.1 centertext
                """)

    # 6. Connectors & DIP Switch
    connector_labels = {
        "J_PWR": ("J_PWR (PWR IN)", 90.0, 22.0, "center"),
        "J_IN":  ("J_IN (4-BIT IN)", 84.0, 55.0, "center"),
        "J_OUT": ("J_OUT",          4.0,  36.5, "left"),
        "SW1":   ("SW1: 4-DIP",     82.2, 42.0, "center"),
    }
    for ref, (lbl, l_fx, l_fy, align) in connector_labels.items():
        fp = next((f for f in components if f["ref"] == ref), None)
        if fp:
            for p in fp["pads"]:
                p_fx = 100.0 - p["x_mm"]
                p_fy = p["y_mm"]
                p_px, p_py = to_ps(p_fx, p_fy)
                pw = p["w_mm"] * scale_pt
                ph = p["h_mm"] * scale_pt
                if p["shape"] == pcbnew.PAD_SHAPE_RECT:
                    ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.92 0.78 0.28 rectfill_c")
                else:
                    ps.append(f"{p_px:.2f} {p_py:.2f} {pw/2:.2f} 0.92 0.78 0.28 circlefill_c")
                ps.append(f"{p_px:.2f} {p_py:.2f} {0.5*scale_pt:.2f} 0.1 0.1 0.1 circlefill_c")

            lbl_px, lbl_py = to_ps(l_fx, l_fy)
            f_size = 7.2 * scale if not is_zoomed else 9.5
            ps.append(f"({lbl}) {lbl_px:.2f} {lbl_py:.2f} /Helvetica-Bold {f_size:.1f} 0.95 0.95 0.95 {align}text")

    # 7. ICs (U1, U2 - TL074 SOIC-14)
    for uref in ["U1", "U2"]:
        ufp = next((f for f in components if f["ref"] == uref), None)
        if ufp:
            fx = 100.0 - ufp["x_mm"]
            fy = ufp["y_mm"]
            px, py = to_ps(fx, fy)

            bw = 4.2 * scale_pt
            bh = 9.2 * scale_pt

            # Body shadow & fill
            ps.append(f"{px - bw/2:.2f} {py - bh/2:.2f} {bw:.2f} {bh:.2f} 0.14 0.15 0.18 rectfill_c")
            ps.append(f"{px - bw/2:.2f} {py - bh/2:.2f} {bw:.2f} {bh:.2f} 1.0 0.4 0.45 0.5 rectstroke_c")

            # Silver gull-wing pads
            for p in ufp["pads"]:
                p_fx = 100.0 - p["x_mm"]
                p_fy = p["y_mm"]
                p_px, p_py = to_ps(p_fx, p_fy)
                pw = (1.5 if p["w_mm"] < p["h_mm"] else 0.6) * scale_pt
                ph = (0.6 if p["w_mm"] < p["h_mm"] else 1.5) * scale_pt
                ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.85 0.85 0.88 rectfill_c")

            # Pin 1 Marker Dot
            p1 = ufp["pads"][0]
            p1_fx = 100.0 - p1["x_mm"]
            p1_fy = p1["y_mm"]
            p1_px, p1_py = to_ps(p1_fx, p1_fy)
            ps.append(f"{p1_px:.2f} {p1_py:.2f} {0.65*scale_pt:.2f} 1.0 0.8 0.1 circlefill_c")

            # Laser Marking inside IC body
            f_size = 7.8 * scale if not is_zoomed else 10.0
            lbl_px, lbl_py1 = to_ps(fx, fy - 1.0)
            _, lbl_py2 = to_ps(fx, fy + 1.8)
            ps.append(f"({uref}: TL074) {lbl_px:.2f} {lbl_py1:.2f} /Helvetica-Bold {f_size:.1f} 1.0 1.0 1.0 centertext")
            ps.append(f"(SOIC-14) {lbl_px:.2f} {lbl_py2:.2f} /Helvetica {f_size*0.75:.1f} 0.8 0.8 0.8 centertext")

    # 8. Diodes (D1_0, D1_1, D2_0, D2_1 - 1N4148 SOD-123)
    # Dedicated 2-line labels in open gaps
    diode_configs = {
        "D1_0": {"l_fx": 41.5, "l_fy": 26.0},
        "D2_0": {"l_fx": 48.5, "l_fy": 29.5},
        "D1_1": {"l_fx": 41.5, "l_fy": 44.0},
        "D2_1": {"l_fx": 48.5, "l_fy": 40.5},
    }

    for dref, cfg in diode_configs.items():
        dfp = next((f for f in components if f["ref"] == dref), None)
        if dfp:
            fx = 100.0 - dfp["x_mm"]
            fy = dfp["y_mm"]
            px, py = to_ps(fx, fy)

            # Pads
            for p in dfp["pads"]:
                p_fx = 100.0 - p["x_mm"]
                p_fy = p["y_mm"]
                p_px, p_py = to_ps(p_fx, p_fy)
                pw = 1.0 * scale_pt
                ph = 1.0 * scale_pt
                if str(p["num"]) == "1":
                    # Cathode Pad (Bright Yellow)
                    ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 1.0 0.85 0.2 rectfill_c")
                else:
                    ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.85 0.85 0.85 rectfill_c")

            # SOD-123 body
            bw = 1.6 * scale_pt
            bh = 2.6 * scale_pt
            ps.append(f"{px - bw/2:.2f} {py - bh/2:.2f} {bw:.2f} {bh:.2f} 0.15 0.15 0.15 rectfill_c")

            # Yellow Cathode stripe on body
            p1_fy = dfp["pads"][0]["y_mm"]
            c_stripe_y = py + (0.9 if p1_fy < fy else -0.9) * scale_pt
            ps.append(f"{px - bw/2:.2f} {c_stripe_y - 0.2*scale_pt:.2f} {bw:.2f} {0.4*scale_pt:.2f} 1.0 0.9 0.1 rectfill_c")

            # Diode Label (2-line: Ref [K] on line 1, Model on line 2)
            f_size = 5.2 * scale if not is_zoomed else 7.2
            lbl_px, _ = to_ps(cfg["l_fx"], cfg["l_fy"])
            _, py_top = to_ps(cfg["l_fx"], cfg["l_fy"] - 1.0)
            _, py_bot = to_ps(cfg["l_fx"], cfg["l_fy"] + 1.0)
            ps.append(f"({dref} [K]) {lbl_px:.2f} {py_top:.2f} /Helvetica-Bold {f_size:.1f} 1.0 0.9 0.2 badgecentertext")
            ps.append(f"(1N4148) {lbl_px:.2f} {py_bot:.2f} /Helvetica {f_size*0.9:.1f} 0.9 0.9 0.9 badgecentertext")

    # 9. LEDs (LED0, LED1)
    led_configs = {
        "LED1": ("LED1 [Red]", 7.56, 21.0, (0.95, 0.2, 0.1)),
        "LED0": ("LED0 [Grn]", 7.56, 49.0, (0.1, 0.9, 0.2)),
    }
    for lref, (lbl, l_fx, l_fy, col) in led_configs.items():
        lfp = next((f for f in components if f["ref"] == lref), None)
        if lfp:
            fx = 100.0 - lfp["x_mm"]
            fy = lfp["y_mm"]
            px, py = to_ps(fx, fy)

            for p in lfp["pads"]:
                p_fx = 100.0 - p["x_mm"]
                p_fy = p["y_mm"]
                p_px, p_py = to_ps(p_fx, p_fy)
                pw = 1.0 * scale_pt
                ph = 1.2 * scale_pt
                ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.88 0.75 0.3 rectfill_c")

            ps.append(f"{px:.2f} {py:.2f} {1.2*scale_pt:.2f} {col[0]:.2f} {col[1]:.2f} {col[2]:.2f} circlefill_c")
            ps.append(f"{px:.2f} {py:.2f} {1.2*scale_pt:.2f} 0.8 1.0 1.0 1.0 circlestroke_c")

            f_size = 6.2 * scale if not is_zoomed else 8.2
            lbl_px, lbl_py = to_ps(l_fx, l_fy)
            ps.append(f"({lbl}) {lbl_px:.2f} {lbl_py:.2f} /Helvetica-Bold {f_size:.1f} {col[0]:.2f} {col[1]:.2f} {col[2]:.2f} badgecentertext")

    # 10. SMD 0805 Capacitors (C1..C4: 0.1uF)
    cap_configs = {
        "C1": (54.36, 22.0),
        "C2": (54.36, 48.0),
        "C3": (18.0, 7.5),
        "C4": (18.0, 61.5),
    }
    for cref, (l_fx, l_fy) in cap_configs.items():
        cfp = next((f for f in components if f["ref"] == cref), None)
        if cfp:
            fx = 100.0 - cfp["x_mm"]
            fy = cfp["y_mm"]
            px, py = to_ps(fx, fy)

            for p in cfp["pads"]:
                p_fx = 100.0 - p["x_mm"]
                p_fy = p["y_mm"]
                p_px, p_py = to_ps(p_fx, p_fy)
                pw = 1.0 * scale_pt
                ph = 1.2 * scale_pt
                ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.88 0.75 0.3 rectfill_c")

            bw = 1.6 * scale_pt
            bh = 1.0 * scale_pt
            ps.append(f"{px - bw/2:.2f} {py - bh/2:.2f} {bw:.2f} {bh:.2f} 0.72 0.55 0.35 rectfill_c")

            f_size = 6.0 * scale if not is_zoomed else 8.0
            lbl_px, lbl_py = to_ps(l_fx, l_fy)
            ps.append(f"({cref}: 0.1uF) {lbl_px:.2f} {lbl_py:.2f} /Helvetica-Bold {f_size:.1f} 0.95 0.85 0.6 badgecentertext")

    # 11. SMD 0-Ohm Jumpers (JMP_*)
    jmp_configs = {
        "JMP_BIAS": (87.5, 11.0),
        "JMP_V12":  (55.5, 18.0),
        "JMP_N12":  (55.5, 52.0),
        "JMP_WTA":  (13.5, 31.5),
        "JMP_GND":  (27.0, 59.0),
    }
    for jref, (l_fx, l_fy) in jmp_configs.items():
        jfp = next((f for f in components if f["ref"] == jref), None)
        if jfp:
            fx = 100.0 - jfp["x_mm"]
            fy = jfp["y_mm"]
            px, py = to_ps(fx, fy)

            for p in jfp["pads"]:
                p_fx = 100.0 - p["x_mm"]
                p_fy = p["y_mm"]
                p_px, p_py = to_ps(p_fx, p_fy)
                pw = 1.0 * scale_pt
                ph = 1.2 * scale_pt
                ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.88 0.75 0.3 rectfill_c")

            bw = 1.6 * scale_pt
            bh = 1.0 * scale_pt
            ps.append(f"{px - bw/2:.2f} {py - bh/2:.2f} {bw:.2f} {bh:.2f} 0.1 0.6 0.7 rectfill_c")

            f_size = 5.6 * scale if not is_zoomed else 7.6
            lbl_px, _ = to_ps(l_fx, l_fy)
            _, py_top = to_ps(l_fx, l_fy - 1.0)
            _, py_bot = to_ps(l_fx, l_fy + 1.0)
            ps.append(f"({jref}) {lbl_px:.2f} {py_top:.2f} /Helvetica-Bold {f_size:.1f} 0.2 0.9 1.0 badgecentertext")
            ps.append(f"([0R]) {lbl_px:.2f} {py_bot:.2f} /Helvetica-Bold {f_size*0.9:.1f} 0.2 0.9 1.0 badgecentertext")

    # 12. All Resistors with Curated Zero-Collision Coordinates
    # Format: (l_fx, l_fy, align, is_two_line)
    resistor_layout = {
        # Input Pull-downs (compact names, right-aligned to left of pads)
        "R_PD0":    (71.0, 32.19, "right", False),
        "R_PD1":    (71.0, 34.73, "right", False),
        "R_PD2":    (71.0, 37.27, "right", False),
        "R_PD3":    (71.0, 39.81, "right", False),
        # Neuron 0 Weights & Bias (stacked 2-line: ref on top, val below)
        "Rb1_0":    (66.0, 13.5, "center", True),
        "R1_00":    (66.0, 20.0, "center", True),
        "R1_10":    (66.0, 26.5, "center", True),
        "Rf1_0":    (60.5, 16.0, "center", True),
        "Rin_0":    (51.0, 11.0, "center", True),
        "Rpd_act0": (43.5, 15.5, "center", True),
        "Rrelu_0":  (47.25, 20.5, "center", True),
        # Neuron 1 Weights & Bias
        "R1_21":    (66.0, 43.5, "center", True),
        "R1_31":    (66.0, 50.0, "center", True),
        "Rb1_1":    (66.0, 57.0, "center", True),
        "Rf1_1":    (60.5, 54.0, "center", True),
        "Rin_1":    (51.0, 59.0, "center", True),
        "Rpd_act1": (43.5, 54.5, "center", True),
        "Rrelu_1":  (47.25, 49.5, "center", True),
        # Output Layer 2 Resistors
        "Rb2_0":    (35.0, 13.5, "center", True),
        "R2_00":    (35.0, 19.5, "center", True),
        "R2_10":    (35.0, 25.5, "center", True),
        "Rf2_0":    (28.0, 31.0, "center", True),
        "Rb2_1":    (35.0, 57.0, "center", True),
        "Rf2_1":    (28.0, 39.0, "center", True),
        # LED Current Limiters (staggered vertically)
        "R_LED1":   (12.0, 27.5, "center", False),
        "R_LED0":   (12.0, 42.5, "center", False),
    }

    resistors = [f for f in components if f["ref"].startswith("R") and f["ref"] in resistor_layout]

    for rfp in resistors:
        ref = rfp["ref"]
        val = rfp["val"]
        fx = 100.0 - rfp["x_mm"]
        fy = rfp["y_mm"]
        px, py = to_ps(fx, fy)

        # Pads
        for p in rfp["pads"]:
            p_fx = 100.0 - p["x_mm"]
            p_fy = p["y_mm"]
            p_px, p_py = to_ps(p_fx, p_fy)
            pw = 1.0 * scale_pt
            ph = 1.1 * scale_pt
            ps.append(f"{p_px - pw/2:.2f} {p_py - ph/2:.2f} {pw:.2f} {ph:.2f} 0.88 0.75 0.3 rectfill_c")

        # Color-code resistors:
        if val == "10k":
            r_col = (1.0, 0.9, 0.2)   # Yellow
        elif val == "18k":
            r_col = (1.0, 0.55, 0.1)  # Orange
        elif val == "15k":
            r_col = (0.95, 0.4, 0.95) # Pink
        elif val == "22k":
            r_col = (0.3, 0.85, 1.0)  # Cyan
        elif val == "1k":
            r_col = (1.0, 0.35, 0.35) # Red
        else:
            r_col = (0.9, 0.9, 0.9)

        # 0805 body
        bw = 1.6 * scale_pt
        bh = 0.9 * scale_pt
        ps.append(f"{px - bw/2:.2f} {py - bh/2:.2f} {bw:.2f} {bh:.2f} 0.18 0.18 0.2 rectfill_c")

        # Label position
        l_fx, l_fy, align, is_two_line = resistor_layout[ref]
        lbl_px, lbl_py = to_ps(l_fx, l_fy)
        f_size = 5.2 * scale if not is_zoomed else 7.2

        if is_two_line:
            _, py_top = to_ps(l_fx, l_fy - 1.1)
            _, py_bot = to_ps(l_fx, l_fy + 1.1)
            ps.append(f"({ref}) {lbl_px:.2f} {py_top:.2f} /Helvetica-Bold {f_size:.1f} {r_col[0]:.2f} {r_col[1]:.2f} {r_col[2]:.2f} badge{align}text")
            ps.append(f"({val}) {lbl_px:.2f} {py_bot:.2f} /Helvetica-Bold {f_size*0.95:.1f} 0.95 0.95 0.95 badge{align}text")
        else:
            lbl = f"{ref}: {val}"
            ps.append(f"({lbl}) {lbl_px:.2f} {lbl_py:.2f} /Helvetica-Bold {f_size:.1f} {r_col[0]:.2f} {r_col[1]:.2f} {r_col[2]:.2f} badge{align}text")

    # 13. Test Points (TP_*)
    tp_configs = {
        "TP_X0":    (76.0, 17.5),
        "TP_X1":    (79.0, 21.5),
        "TP_X2":    (79.0, 47.0),
        "TP_X3":    (76.0, 52.5),
        "TP_SUM0":  (59.0, 10.5),
        "TP_SUM1":  (59.0, 60.0),
        "TP_ACT0":  (43.5, 9.5),
        "TP_ACT1":  (38.5, 50.0),
        "TP_OUT0":  (29.0, 21.5),
        "TP_OUT1":  (29.0, 48.5),
        "TP_+12V":  (84.0, 4.5),
        "TP_+5V":   (86.5, 27.5),
        "TP_-12V":  (80.0, 59.0),
        "TP_GND":   (40.0, 63.5),
    }
    for fp in components:
        if fp["ref"].startswith("TP_"):
            fx = 100.0 - fp["x_mm"]
            fy = fp["y_mm"]
            px, py = to_ps(fx, fy)
            r_tp = 0.85 * scale_pt
            ps.append(f"{px:.2f} {py:.2f} {r_tp:.2f} 1.0 0.85 0.1 circlefill_c")
            ps.append(f"{px:.2f} {py:.2f} {0.35*scale_pt:.2f} 0.1 0.1 0.1 circlefill_c")

            l_fx, l_fy = tp_configs.get(fp["ref"], (fx, fy + 3.8))
            lbl_px, lbl_py = to_ps(l_fx, l_fy)
            f_size = 5.2 * scale if not is_zoomed else 7.2
            ps.append(f"({fp['ref']}) {lbl_px:.2f} {lbl_py:.2f} /Helvetica {f_size:.1f} 0.9 0.9 0.5 badgecentertext")

    # 14. Caliper Calibration Scale (at bottom of board)
    if not is_zoomed:
        cal_x = ox + (board_w_pt - 50.0 * scale_pt) / 2.0
        cal_y = oy - 22.0
        ps.append(f"""
        gsave
        1.0 setlinewidth 0.1 0.1 0.1 setrgbcolor
        newpath {cal_x:.2f} {cal_y:.2f} moveto {50.0*scale_pt:.2f} 0 rlineto stroke
        """)
        for tick in [0, 10, 20, 30, 40, 50]:
            tx = cal_x + tick * scale_pt
            th = 6.0 if tick in [0, 50] else 3.5
            ps.append(f"newpath {tx:.2f} {cal_y - th/2:.2f} moveto 0 {th:.2f} rlineto stroke\n")
        ps.append(f"""
        grestore
        (50.0 mm [1:1 TRUE SCALE CALIBRATION BAR - MEASURE WITH CALIPERS]) {cal_x + 25.0*scale_pt:.2f} {cal_y - 11.0:.2f} /Helvetica-Bold 8.0 0.1 0.1 0.15 centertext
        """)

    # 15. Bottom Legend / Quick Assembly Color Key
    leg_y = 16.0 if not is_zoomed else 10.0
    ps.append(f"""
    (LEGEND:  [Gold] TL074 ICs  |  [Yellow] 10k Resistors  |  [Orange] 18k Bias  |  [Pink] 15k Bias  |  [Cyan] 22k Bias  |  [Red] 1k Limiters  |  [Dashed Lines] W1..W10 Jumpers  |  [Cyan] 0R Jumpers) {PAGE_W_PT/2.0:.1f} {leg_y:.1f} /Helvetica-Bold 7.8 0.2 0.25 0.35 centertext
    """)

    ps.append("showpage")
    ps.append("%%EOF")
    return "\n".join(ps)


def build_bom_page_ps():
    """Builds PostScript code for Page 3: Complete SMD Bill of Materials & Soldering Checklist."""
    ps = []
    ps.append("%!PS-Adobe-3.0")
    ps.append("%%BoundingBox: 0 0 792 612")
    ps.append("%%Pages: 1")
    ps.append("%%EndComments")
    ps.append("%%Page: 1 1")

    ps.append("""
    /Helvetica-Bold findfont 15 scalefont setfont
    45 568 moveto
    (ANALOG NEURAL NETWORK TEST BOARD - SMD BILL OF MATERIALS & CHECKLIST) show

    /Helvetica findfont 9.5 scalefont setfont
    45 552 moveto
    (Flipped View Assembly Guide | Component Directory with Resistance Values, Packages, Footprints & Polarity) show

    % Top divider rule
    newpath 45 542 moveto 747 542 lineto 1.2 setlinewidth 0 setgray stroke

    % Procedures
    /row { % y_pos
        /ry exch def
        newpath 45 ry moveto 747 ry lineto 0.4 setlinewidth 0.85 setgray stroke
    } def

    /hdr { % (col1) (col2) (col3) (col4) (col5) (col6) y
        /hy exch def
        /c6 exch def
        /c5 exch def
        /c4 exch def
        /c3 exch def
        /c2 exch def
        /c1 exch def
        /Helvetica-Bold findfont 8.8 scalefont setfont
        0.1 setgray
        46  hy moveto c1 show
        82  hy moveto c2 show
        195 hy moveto c3 show
        295 hy moveto c4 show
        375 hy moveto c5 show
        415 hy moveto c6 show
        % Underline header row
        newpath 45 hy 5 sub moveto 747 hy 5 sub lineto 1.0 setlinewidth 0.2 setgray stroke
    } def

    /item { % (Ref) (Val/Model) (Package) (Qty) (Notes) y
        /iy exch def
        /notes exch def
        /qty exch def
        /pkg exch def
        /val exch def
        /ref exch def
        % Checkbox box at x=50, y=iy-3
        newpath 50 iy 3 sub moveto 8 0 rlineto 0 8 rlineto -8 0 rlineto closepath 0.5 setlinewidth 0.4 setgray stroke
        /Helvetica findfont 8.0 scalefont setfont
        0.15 setgray
        82  iy 2 sub moveto ref show
        195 iy 2 sub moveto val show
        295 iy 2 sub moveto pkg show
        375 iy 2 sub moveto qty show
        415 iy 2 sub moveto notes show
    } def
    """)

    # Table Header
    y = 526
    ps.append(f"(DONE) (DESIGNATOR) (VALUE / MODEL) (PACKAGE) (QTY) (FUNCTIONAL BLOCK & NOTES) {y} hdr")

    bom_items = [
        # ICs
        ("(U1, U2)", "(TL074)", "(SOIC-14)", "(2)", "(Quad Op-Amp: U1=Layer 1 Sum+ReLU, U2=Layer 2 Sum+WTA [Pin 1 Dot])"),
        # Diodes
        ("(D1_0, D1_1)", "(1N4148)", "(SOD-123)", "(2)", "(Layer 1 Precision Inverting Half-Wave ReLU Series Diodes [Cathode K])"),
        ("(D2_0, D2_1)", "(1N4148)", "(SOD-123)", "(2)", "(Layer 1 Precision ReLU Feedback Clamp Diodes [Cathode K])"),
        # LEDs
        ("(LED1)", "(Red / Vert)", "(0805 SMD)", "(1)", "(Winner-Take-All Vertical Class Winner Indicator [Cathode to GND])"),
        ("(LED0)", "(Green / Horiz)", "(0805 SMD)", "(1)", "(Winner-Take-All Horizontal Class Winner Indicator [Cathode to GND])"),
        # Resistors 10k
        ("(R1_00, 10, 21, 31)", "(10k 1%)", "(0805 SMD)", "(4)", "(Neuron Input Summing Resistors (X0..X3 into Hidden Layer 1))"),
        ("(Rf1_0, Rf1_1)", "(10k 1%)", "(0805 SMD)", "(2)", "(Hidden Layer 1 Feedback Resistors (Gain = 1.0))"),
        ("(Rin_0, Rin_1)", "(10k 1%)", "(0805 SMD)", "(2)", "(ReLU Inverter Input Coupling Resistors)"),
        ("(Rpd_act0, act1)", "(10k 1%)", "(0805 SMD)", "(2)", "(ReLU Active Output Stage Pull-down to Ground)"),
        ("(Rrelu_0, relu_1)", "(10k 1%)", "(0805 SMD)", "(2)", "(ReLU Inverting Translinear Feedback Resistors)"),
        ("(R2_00, R2_10)", "(10k 1%)", "(0805 SMD)", "(2)", "(Output Layer 2 Hidden Activation Weight Resistors)"),
        ("(Rf2_0, Rf2_1)", "(10k 1%)", "(0805 SMD)", "(2)", "(Output Layer 2 Summing Feedback Resistors)"),
        ("(R_PD0..R_PD3)", "(10k 1%)", "(0805 SMD)", "(4)", "(DIP Switch 4-Channel Input Pull-Down Resistors (X0..X3 to GND))"),
        # Resistors other values
        ("(Rb1_0, Rb1_1)", "(18k 1%)", "(0805 SMD)", "(2)", "(Hidden Layer 1 Negative Bias Resistors (Connected to -12V Rail))"),
        ("(Rb2_0)", "(15k 1%)", "(0805 SMD)", "(1)", "(Output Class 0 Bias Resistor (Connected to -12V Rail))"),
        ("(Rb2_1)", "(22k 1%)", "(0805 SMD)", "(1)", "(Output Class 1 Bias Resistor (Connected to -12V Rail))"),
        ("(R_LED0, R_LED1)", "(1k 5%)", "(0805 SMD)", "(2)", "(LED Current Limiting Resistors (From Comparator Outputs))"),
        # Capacitors
        ("(C1, C2, C3, C4)", "(0.1uF 50V)", "(0805 SMD)", "(4)", "(Power Supply Decoupling MLCC Ceramic Caps (+12V & -12V Rails))"),
        # SMD 0R Jumpers
        ("(JMP_BIAS, V12, N12)", "(0 Ohm (0R))", "(0805 SMD)", "(3)", "(Power Rail Planar Corridors (-12V Bias, +12V Rail, -12V Rail))"),
        ("(JMP_WTA, JMP_GND)", "(0 Ohm (0R))", "(0805 SMD)", "(2)", "(WTA Comparator Cross-Link Corridor & Ground Plane Return)"),
        # Through-hole Wire Jumpers
        ("(W1..W10)", "(Wire Jumpers)", "(1.0mm TH)", "(10)", "(Through-Hole Insulated Wire Jumper Bridges (See Flipped Wire Routing Map))"),
        # Connectors & Switches
        ("(SW1)", "(4-DIP Switch)", "(SMD Low-Prof)", "(1)", "(Manual 4-Bit Binary Pattern Input Selector (X0..X3))"),
        ("(J_PWR)", "(PinHeader 1x04)", "(2.54mm TH)", "(1)", "(Main Power Connector: Pin 1=+12V, 2=+5V, 3=GND, 4=-12V)"),
        ("(J_IN)", "(PinHeader 1x05)", "(2.54mm TH)", "(1)", "(External Signal Input Connector: Pins 1..4=X0..X3, Pin 5=GND)"),
        ("(J_OUT)", "(PinHeader 1x04)", "(2.54mm TH)", "(1)", "(WTA Output Header: Pin 1=OUT0, 2=OUT1, 3=+5V, 4=GND)"),
    ]

    for item in bom_items:
        y -= 15.5
        ps.append(f"{item[0]} {item[1]} {item[2]} {item[3]} {item[4]} {y} item")
        ps.append(f"{y - 3} row")

    # Bottom Soldering Order Recommendation Callout
    call_y = y - 36
    ps.append(f"""
    newpath 45 {call_y - 24} moveto 747 {call_y - 24} lineto 747 {call_y + 10} lineto 45 {call_y + 10} lineto closepath
    0.96 setgray fill
    newpath 45 {call_y - 24} moveto 747 {call_y - 24} lineto 747 {call_y + 10} lineto 45 {call_y + 10} lineto closepath
    0.5 setlinewidth 0 setgray stroke

    /Helvetica-Bold findfont 9.0 scalefont setfont
    0.1 setgray
    58 {call_y} moveto
    (RECOMMENDED HAND-SOLDERING ORDER FOR BEST ACCESSIBILITY:) show

    /Helvetica findfont 8.0 scalefont setfont
    58 {call_y - 12} moveto
    (1. Solder SOIC-14 ICs \\(U1, U2\\) first -> 2. Diodes & 0805 Resistors/Caps -> 3. LEDs & 0-Ohm Jumpers -> 4. Wire Jumpers W1..W10 -> 5. Headers & Switch) show
    """)

    ps.append("showpage")
    ps.append("%%EOF")
    return "\n".join(ps)


def main():
    print("=" * 75)
    print("GENERATING REFINED FLIPPED SMD ASSEMBLY & SOLDERING GUIDE PDF")
    print("=" * 75)

    components, tracks = extract_board_data()
    print(f"Extracted {len(components)} components and {len(tracks)} copper tracks.")

    # 1. Page 1: 1:1 True-Scale Flipped Assembly Map
    ps_p1 = os.path.join(SCRATCH_DIR, "page1_1to1.ps")
    pdf_p1 = os.path.join(SCRATCH_DIR, "page1_1to1.pdf")
    with open(ps_p1, "w") as f:
        f.write(build_ps_code(components, tracks, scale=1.0, is_zoomed=False))
    subprocess.run([GS_CLI, "-sDEVICE=pdfwrite", f"-sOutputFile={pdf_p1}", "-dNOPAUSE", "-dBATCH",
                    "-dDEVICEWIDTHPOINTS=792", "-dDEVICEHEIGHTPOINTS=612", "-dFIXEDMEDIA", "-dPDFFitPage", ps_p1], check=True)
    print("   [OK] Page 1: 1:1 True-Scale Flipped Map")

    # 2. Page 2: Enlarged Bench Soldering Guide (1.82x Zoom)
    ps_p2 = os.path.join(SCRATCH_DIR, "page2_enlarged.ps")
    pdf_p2 = os.path.join(SCRATCH_DIR, "page2_enlarged.pdf")
    with open(ps_p2, "w") as f:
        f.write(build_ps_code(components, tracks, scale=1.82, is_zoomed=True))
    subprocess.run([GS_CLI, "-sDEVICE=pdfwrite", f"-sOutputFile={pdf_p2}", "-dNOPAUSE", "-dBATCH",
                    "-dDEVICEWIDTHPOINTS=792", "-dDEVICEHEIGHTPOINTS=612", "-dFIXEDMEDIA", "-dPDFFitPage", ps_p2], check=True)
    print("   [OK] Page 2: Enlarged Bench Soldering Guide (1.82x Zoom)")

    # 3. Page 3: Complete SMD Bill of Materials & Soldering Checklist
    ps_p3 = os.path.join(SCRATCH_DIR, "page3_bom.ps")
    pdf_p3 = os.path.join(SCRATCH_DIR, "page3_bom.pdf")
    with open(ps_p3, "w") as f:
        f.write(build_bom_page_ps())
    subprocess.run([GS_CLI, "-sDEVICE=pdfwrite", f"-sOutputFile={pdf_p3}", "-dNOPAUSE", "-dBATCH",
                    "-dDEVICEWIDTHPOINTS=792", "-dDEVICEHEIGHTPOINTS=612", "-dFIXEDMEDIA", "-dPDFFitPage", ps_p3], check=True)
    print("   [OK] Page 3: Complete SMD Bill of Materials & Checklist")

    # Assemble Unified 3-Page PDF Document
    out_pdf = os.path.join(WORKSPACE_DIR, "test_board_smd_assembly_flipped.pdf")
    subprocess.run([PDFUNITE, pdf_p1, pdf_p2, pdf_p3, out_pdf], check=True)
    shutil.copyfile(out_pdf, os.path.join(ARTIFACTS_DIR, "test_board_smd_assembly_flipped.pdf"))
    print(f"\n   [SUCCESS] Created: {out_pdf} (3 Pages)")

    # Render High-Resolution Previews of all 3 pages
    print("\n4. Rendering High-Resolution Previews...")
    for idx, (pname, ppath) in enumerate([("preview_smd_assembly_flipped_1to1.png", pdf_p1),
                                          ("preview_smd_assembly_flipped_enlarged.png", pdf_p2),
                                          ("preview_smd_assembly_bom.png", pdf_p3)]):
        tmp_base = os.path.join(SCRATCH_DIR, f"prev_p{idx+1}")
        subprocess.run([PDFTOPPM, "-png", "-r", "150", ppath, tmp_base], check=True)
        src_png = f"{tmp_base}-1.png"
        dest_render = os.path.join(RENDERS_DIR, pname)
        dest_art = os.path.join(ARTIFACTS_DIR, pname)
        if os.path.exists(src_png):
            shutil.copyfile(src_png, dest_render)
            shutil.copyfile(src_png, dest_art)
            print(f"   [RENDERED] {pname}")

    # Clean up scratch PostScript files
    shutil.rmtree(SCRATCH_DIR, ignore_errors=True)

    print("\n" + "=" * 75)
    print("FLIPPED SMD ASSEMBLY PDF SUITE GENERATED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
