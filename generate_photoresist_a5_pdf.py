#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_photoresist_a5_pdf.py
------------------------------
Generates complete 1:1 true-scale photolithography exposure masks for the
Analog Neural Network Test Board (70x100mm) formatted for ISO A5 paper
(210.0 x 148.0 mm / 8.27" x 5.83" Landscape).

Outputs:
1. test_board_single_layer_photoresist_a5.pdf:
   6-page true-scale A5 photolithography etching package for DIY single-layer fabrication.
2. test_board_70x100_photoresist_a5.pdf:
   10-page master A5 photolithography package for 2-layer fabrication.
3. Renders high-res PNG previews of the A5 sheets for instant visual inspection.
"""

import os
import sys
import re
import subprocess
import shutil
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
GS_CLI = "/opt/homebrew/bin/gs"
PDFUNITE = "/opt/homebrew/bin/pdfunite"
PDFTOPPM = "/opt/homebrew/bin/pdftoppm"
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"
SCRATCH_DIR = os.path.join(ARTIFACTS_DIR, "scratch_a5")
FAB_DIR = os.path.join(WORKSPACE_DIR, "fabrication", "photoresist_a5")

os.makedirs(SCRATCH_DIR, exist_ok=True)
os.makedirs(FAB_DIR, exist_ok=True)

# Geometry constants for ISO A5 Landscape
A5_W_LANDSCAPE = 210.00  # mm
A5_H_LANDSCAPE = 148.00  # mm

BOARD_W = 100.0  # mm
BOARD_H = 70.0   # mm

def add_optical_fiducials(board, dx, dy, layer):
    """Adds 4 corner crosshair fiducials with target circles for film alignment."""
    corners = [
        (dx - 5.0, dy - 5.0),
        (dx + BOARD_W + 5.0, dy - 5.0),
        (dx - 5.0, dy + BOARD_H + 5.0),
        (dx + BOARD_W + 5.0, dy + BOARD_H + 5.0),
    ]
    size = 5.0
    for cx, cy in corners:
        # Horizontal cross segment
        sh = pcbnew.PCB_SHAPE(board)
        sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx - size / 2.0), pcbnew.FromMM(cy)))
        sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx + size / 2.0), pcbnew.FromMM(cy)))
        sh.SetWidth(pcbnew.FromMM(0.20))
        sh.SetLayer(layer)
        board.Add(sh)

        # Vertical cross segment
        sv = pcbnew.PCB_SHAPE(board)
        sv.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sv.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy - size / 2.0)))
        sv.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy + size / 2.0)))
        sv.SetWidth(pcbnew.FromMM(0.20))
        sv.SetLayer(layer)
        board.Add(sv)

        # Alignment circle
        sc = pcbnew.PCB_SHAPE(board)
        sc.SetShape(pcbnew.SHAPE_T_CIRCLE)
        sc.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
        sc.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx + 1.2), pcbnew.FromMM(cy)))
        sc.SetWidth(pcbnew.FromMM(0.15))
        sc.SetLayer(layer)
        board.Add(sc)


def add_calibration_scale(board, x_start, y_pos, layer):
    """Adds a 50.0 mm calibration bar with ticks for physical caliper measurement."""
    s_bar = pcbnew.PCB_SHAPE(board)
    s_bar.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s_bar.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x_start), pcbnew.FromMM(y_pos)))
    s_bar.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x_start + 50.0), pcbnew.FromMM(y_pos)))
    s_bar.SetWidth(pcbnew.FromMM(0.80))
    s_bar.SetLayer(layer)
    board.Add(s_bar)

    for tick in [0, 10, 20, 30, 40, 50]:
        tx = x_start + tick
        th = 4.0 if tick in [0, 50] else 2.5
        st = pcbnew.PCB_SHAPE(board)
        st.SetShape(pcbnew.SHAPE_T_SEGMENT)
        st.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(tx), pcbnew.FromMM(y_pos - th / 2.0)))
        st.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(tx), pcbnew.FromMM(y_pos + th / 2.0)))
        st.SetWidth(pcbnew.FromMM(0.30))
        st.SetLayer(layer)
        board.Add(st)

    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("50.0 mm [1:1 CALIPER CALIBRATION SCALE]")
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_start + 25.0), pcbnew.FromMM(y_pos + 4.0)))
    txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
    txt.SetTextThickness(pcbnew.FromMM(0.18))
    txt.SetLayer(layer)
    board.Add(txt)


def prepare_centered_board_a5(src_pcb_path, target_pcb_path, title_sub=""):
    """Creates a copy of the board centered on an ISO A5 Landscape sheet (210 x 148 mm)."""
    board = pcbnew.LoadBoard(src_pcb_path)

    dx = (A5_W_LANDSCAPE - BOARD_W) / 2.0  # 55.0 mm
    dy = (A5_H_LANDSCAPE - BOARD_H) / 2.0  # 39.0 mm

    board.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))

    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        add_optical_fiducials(board, dx, dy, layer)
        cal_x = dx + (BOARD_W - 50.0) / 2.0
        cal_y = dy + BOARD_H + 13.0
        add_calibration_scale(board, cal_x, cal_y, layer)

        # Title block
        t_main = pcbnew.PCB_TEXT(board)
        t_main.SetText("ANALOG NEURAL NETWORK TEST BOARD (70x100mm) - PHOTORESIST MASK")
        t_main.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(dx + BOARD_W / 2.0), pcbnew.FromMM(dy - 17.0)))
        t_main.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.6), pcbnew.FromMM(1.6)))
        t_main.SetTextThickness(pcbnew.FromMM(0.24))
        t_main.SetLayer(layer)
        board.Add(t_main)

        t_sub = pcbnew.PCB_TEXT(board)
        t_sub.SetText(f"FORMAT: ISO A5 (210x148 mm) | SCALE: 1:1 TRUE SIZE | {title_sub}")
        t_sub.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(dx + BOARD_W / 2.0), pcbnew.FromMM(dy - 11.5)))
        t_sub.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.1), pcbnew.FromMM(1.1)))
        t_sub.SetTextThickness(pcbnew.FromMM(0.16))
        t_sub.SetLayer(layer)
        board.Add(t_sub)

    board.Save(target_pcb_path)

    with open(target_pcb_path, "r") as f:
        content = f.read()
    content = re.sub(r'\(paper "[^"]*"\)', '(paper "A5")', content)
    with open(target_pcb_path, "w") as f:
        f.write(content)

    return target_pcb_path


def generate_cover_guide_a5_pdf(output_pdf_path):
    """Generates an aesthetic vector Cover & DIY Guide page for A5 landscape."""
    ps_file = os.path.join(SCRATCH_DIR, "guide_cover_a5.ps")
    ps_code = """%!PS-Adobe-3.0
%%BoundingBox: 0 0 595 420
%%Pages: 1
%%EndComments
%%Page: 1 1

/Helvetica-Bold findfont 16 scalefont setfont
36 385 moveto
(ANALOG NEURAL NETWORK TEST BOARD (70x100mm)) show

/Helvetica-Bold findfont 10.5 scalefont setfont
36 368 moveto
(DIY Photolithography & Photoresist PCB Etching Guide - ISO A5 Format) show

% Divider line
newpath
36 358 moveto
559 358 lineto
1.2 setlinewidth
0 setgray
stroke

% LEFT COLUMN
/Helvetica-Bold findfont 9.5 scalefont setfont
36 338 moveto
(1. BOARD SPECIFICATIONS & PRINT RULES) show

/Helvetica findfont 7.5 scalefont setfont
/nl { 36 exch moveto } def
324 nl (  * Dimensions: 70.0 mm height x 100.0 mm width (4:3 aspect ratio)) show
312 nl (  * Substrate: Standard 1.6 mm FR-4 (1 oz / 35 um Copper Clad)) show
300 nl (  * Page Format: ISO A5 (148 x 210 mm) - Landscape) show
288 nl (  * CRITICAL: Print at 100% SCALE (Actual Size). DO NOT FIT TO PAGE!) show
276 nl (  * Caliper Check: Verify 50.0 mm scale bar with digital calipers.) show

/Helvetica-Bold findfont 9.5 scalefont setfont
256 nl (2. PHOTORESIST PAGE DIRECTORY) show

/Helvetica findfont 7.2 scalefont setfont
242 nl (  Page 2: Front Copper (F.Cu) - POSITIVE RESIST (Normal View)) show
230 nl (  Page 3: Front Copper (F.Cu) - POSITIVE RESIST (Mirrored - Emulsion Down)) show
218 nl (  Page 4: Front Copper (F.Cu) - NEGATIVE DRY FILM (Normal View)) show
206 nl (  Page 5: Front Copper (F.Cu) - NEGATIVE DRY FILM (Mirrored View)) show
194 nl (  Page 6: Component Silkscreen, Drilling Map & Reference Legend) show

% RIGHT COLUMN
/Helvetica-Bold findfont 9.5 scalefont setfont
310 338 moveto
(3. CHEMICAL PROCESSES & RECIPES) show

/Helvetica findfont 7.5 scalefont setfont
/nr { 310 exch moveto } def
324 nr (A. Positive Pre-Sensitized Boards (Bungard / Positiv 20):) show
312 nr (   * Artwork: Solid black traces block UV (Pages 2 & 3).) show
300 nr (   * Developer: 10 g / L Sodium Hydroxide (NaOH) at 20 C (60-90 s).) show

284 nr (B. Negative Dry Film Photoresist (Riston Blue Film):) show
272 nr (   * Artwork: Transparent traces transmit UV to cure (Pages 4 & 5).) show
260 nr (   * Developer: 10 g / L Sodium Carbonate (Na2CO3) (90-120 s).) show

244 nr (C. Etching Baths:) show
232 nr (   * Ferric Chloride (FeCl3) at 45-50 C with continuous aeration.) show
220 nr (   * Alternatively: 2 parts Hydrogen Peroxide (3%) + 1 part Muriatic Acid.) show

/Helvetica-Bold findfont 9.5 scalefont setfont
200 nr (4. DRILLING & VIAS GUIDE) show

/Helvetica findfont 7.2 nr
188 nr (   * Vias & Jumpers: 0.80 mm carbide bit.) show
176 nr (   * Header Pins (J_IN, J_PWR, J_OUT): 1.00 mm bit.) show
164 nr (   * Mounting Holes (H1..H4): 3.20 mm bit (M3 hardware).) show

% Bottom Callout Box
newpath
36 45 moveto
559 45 lineto
559 135 lineto
36 135 lineto
closepath
0.95 setgray
fill

newpath
36 45 moveto
559 45 lineto
559 135 lineto
36 135 lineto
closepath
0.8 setlinewidth
0.2 setgray
stroke

0 setgray
/Helvetica-Bold findfont 8.5 scalefont setfont
46 120 moveto
(PRO PHOTOLITHOGRAPHY TIP: EMULSION-TO-COPPER CONTACT) show

/Helvetica findfont 7.2 scalefont setfont
/nb { 46 exch moveto } def
108 nb (Always print the Mirrored View (Page 3 for Positive, Page 5 for Negative) onto transparency film) show
96  nb (so that the toner/ink emulsion directly contacts the photoresist surface during UV exposure.) show
84  nb (This eliminates light undercutting beneath traces, yielding pin-sharp 0.25 mm tracks and clean pads.) show
72  nb (Check transparency density with a strong light - double up two printed sheets if necessary.) show
58  nb (Use standard 365-405 nm UV LED exposure box for 45-120 seconds depending on lamp wattage.) show

showpage
%%EOF
"""
    with open(ps_file, "w") as f:
        f.write(ps_code)

    cmd = [
        GS_CLI,
        "-dNOPAUSE", "-dBATCH", "-dSAFER",
        "-sDEVICE=pdfwrite",
        "-sOutputFile=" + output_pdf_path,
        "-dDEVICEWIDTHPOINTS=595",
        "-dDEVICEHEIGHTPOINTS=420",
        "-dFIXEDMEDIA",
        "-f", ps_file
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_pdf_path


def export_single_page_mask(pcb_path, output_pdf, layers, mirror=False, negative=False, drill_opt=1):
    """Exports a single 1:1 true-scale PDF mask using kicad-cli."""
    cmd = [
        KICAD_CLI, "pcb", "export", "pdf",
        "--layers", layers,
        "--black-and-white",
        "--scale", "1",
        "--drill-shape-opt", str(drill_opt),
        "-o", output_pdf
    ]
    if mirror:
        cmd.append("--mirror")
    if negative:
        cmd.append("--negative")
    cmd.append(pcb_path)

    subprocess.run(cmd, check=True)
    return output_pdf


def generate_single_layer_a5_package():
    """Generates the 6-page A5 DIY photolithography package for test_board_single_layer.kicad_pcb."""
    src_pcb = os.path.join(WORKSPACE_DIR, "test_board_single_layer.kicad_pcb")
    centered_pcb = os.path.join(SCRATCH_DIR, "test_board_single_layer_centered_a5.kicad_pcb")

    print("\nProcessing Single-Layer Testing Board for ISO A5...")
    prepare_centered_board_a5(src_pcb, centered_pcb, title_sub="100% SINGLE COPPER LAYER (0-OHM JUMPERS)")

    # 1. Guide
    p1 = os.path.join(SCRATCH_DIR, "single_p1_guide_a5.pdf")
    generate_cover_guide_a5_pdf(p1)

    # 2. Masks
    single_configs = [
        ("single_p2_f_cu_pos_norm.pdf", "F.Cu,Edge.Cuts", False, False, 1),
        ("single_p3_f_cu_pos_mirr.pdf", "F.Cu,Edge.Cuts", True,  False, 1),
        ("single_p4_f_cu_neg_norm.pdf", "F.Cu,Edge.Cuts", False, True,  1),
        ("single_p5_f_cu_neg_mirr.pdf", "F.Cu,Edge.Cuts", True,  True,  1),
        ("single_p6_silk.pdf",          "F.Silkscreen,Edge.Cuts", False, False, 0),
    ]
    single_pages = [p1]
    for fname, layers, mirror, neg, drill_opt in single_configs:
        out_p = os.path.join(SCRATCH_DIR, fname)
        export_single_page_mask(centered_pcb, out_p, layers, mirror=mirror, negative=neg, drill_opt=drill_opt)
        single_pages.append(out_p)

    output_pdf = os.path.join(WORKSPACE_DIR, "test_board_single_layer_photoresist_a5.pdf")
    cmd = [PDFUNITE] + single_pages + [output_pdf]
    subprocess.run(cmd, check=True)
    print(f"   SUCCESS! Created {output_pdf} (6 pages, ISO A5).")

    # Copy to artifacts and fab dir
    shutil.copyfile(output_pdf, os.path.join(ARTIFACTS_DIR, "test_board_single_layer_photoresist_a5.pdf"))
    shutil.copyfile(output_pdf, os.path.join(FAB_DIR, "test_board_single_layer_photoresist_a5.pdf"))

    # Render PNG preview of Page 2 (Positive Normal) and Page 6 (Silkscreen)
    cmd_ppm = [PDFTOPPM, "-png", "-r", "150", "-f", "2", "-l", "2", output_pdf, os.path.join(ARTIFACTS_DIR, "preview_a5_f_cu_pos")]
    subprocess.run(cmd_ppm, check=True)
    cmd_ppm_silk = [PDFTOPPM, "-png", "-r", "150", "-f", "6", "-l", "6", output_pdf, os.path.join(ARTIFACTS_DIR, "preview_a5_silkscreen")]
    subprocess.run(cmd_ppm_silk, check=True)

    return output_pdf


def generate_two_layer_a5_package():
    """Generates the 10-page master A5 photolithography package for test_board_70x100.kicad_pcb."""
    src_pcb = os.path.join(WORKSPACE_DIR, "test_board_70x100.kicad_pcb")
    centered_pcb = os.path.join(SCRATCH_DIR, "test_board_70x100_centered_a5.kicad_pcb")

    print("\nProcessing 2-Layer Testing Board for ISO A5...")
    prepare_centered_board_a5(src_pcb, centered_pcb, title_sub="2-LAYER FR-4 TEST BOARD")

    # 1. Guide
    p1 = os.path.join(SCRATCH_DIR, "two_p1_guide_a5.pdf")
    generate_cover_guide_a5_pdf(p1)

    configs = [
        ("two_p02_f_cu_pos_norm.pdf", "F.Cu,Edge.Cuts", False, False, 1),
        ("two_p03_f_cu_pos_mirr.pdf", "F.Cu,Edge.Cuts", True,  False, 1),
        ("two_p04_b_cu_pos_norm.pdf", "B.Cu,Edge.Cuts", False, False, 1),
        ("two_p05_b_cu_pos_mirr.pdf", "B.Cu,Edge.Cuts", True,  False, 1),
        ("two_p06_f_cu_neg_norm.pdf", "F.Cu,Edge.Cuts", False, True,  1),
        ("two_p07_f_cu_neg_mirr.pdf", "F.Cu,Edge.Cuts", True,  True,  1),
        ("two_p08_b_cu_neg_norm.pdf", "B.Cu,Edge.Cuts", False, True,  1),
        ("two_p09_b_cu_neg_mirr.pdf", "B.Cu,Edge.Cuts", True,  True,  1),
        ("two_p10_f_silk_norm.pdf",   "F.Silkscreen,Edge.Cuts", False, False, 0),
    ]
    pages = [p1]
    for fname, layers, mirror, neg, drill_opt in configs:
        out_p = os.path.join(SCRATCH_DIR, fname)
        export_single_page_mask(centered_pcb, out_p, layers, mirror=mirror, negative=neg, drill_opt=drill_opt)
        pages.append(out_p)

    output_pdf = os.path.join(WORKSPACE_DIR, "test_board_70x100_photoresist_a5.pdf")
    cmd = [PDFUNITE] + pages + [output_pdf]
    subprocess.run(cmd, check=True)
    print(f"   SUCCESS! Created {output_pdf} (10 pages, ISO A5).")

    shutil.copyfile(output_pdf, os.path.join(ARTIFACTS_DIR, "test_board_70x100_photoresist_a5.pdf"))
    shutil.copyfile(output_pdf, os.path.join(FAB_DIR, "test_board_70x100_photoresist_a5.pdf"))
    return output_pdf


if __name__ == "__main__":
    generate_single_layer_a5_package()
    generate_two_layer_a5_package()
    print("\nALL ISO A5 PHOTORESIST PACKAGES CREATED SUCCESSFULLY!")
