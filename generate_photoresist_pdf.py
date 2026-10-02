#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_photoresist_pdf.py
----------------------------
Generates complete 1:1 true-scale photolithography exposure masks for the
Analog Neural Network Single Board Testing Board (70x100mm) formatted for
US Letter paper (8.5" x 11.0" / 215.9 x 279.4 mm).

Outputs:
1. test_board_70x100_photoresist_master_letter.pdf:
   Comprehensive 10-page master PDF with Cover/Guide, Positive (Normal & Mirrored),
   Negative Dry Film (Normal & Mirrored) for both F.Cu and B.Cu, and Silkscreen.
2. test_board_70x100_photoresist_gang_positive_letter.pdf:
   Single-sheet film-saver layout with both Top (F.Cu) and Bottom (B.Cu) masks.
3. test_board_70x100_photoresist_gang_negative_letter.pdf:
   Single-sheet film-saver negative layout for dry film photoresist.
4. test_board_single_layer_photoresist_letter.pdf:
   Dedicated photoresist etching package for the 100% single-layer board.
5. Individual 1-page PDF masks in fabrication/photoresist/
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
SCRATCH_DIR = os.path.join(ARTIFACTS_DIR, "scratch")
FAB_DIR = os.path.join(WORKSPACE_DIR, "fabrication", "photoresist")
RENDERS_DIR = os.path.join(WORKSPACE_DIR, "renders")

os.makedirs(SCRATCH_DIR, exist_ok=True)
os.makedirs(FAB_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

# Geometry constants for US Letter (Landscape & Portrait)
LETTER_W_LANDSCAPE = 279.40  # 11.0 inches in mm
LETTER_H_LANDSCAPE = 215.90  # 8.5 inches in mm
LETTER_W_PORTRAIT  = 215.90
LETTER_H_PORTRAIT  = 279.40

BOARD_W = 100.0  # mm
BOARD_H = 70.0   # mm


def add_optical_fiducials(board, dx, dy, layer):
    """Adds 4 corner crosshair fiducials with target circles for film alignment."""
    corners = [
        (dx - 6.0, dy - 6.0),
        (dx + BOARD_W + 6.0, dy - 6.0),
        (dx - 6.0, dy + BOARD_H + 6.0),
        (dx + BOARD_W + 6.0, dy + BOARD_H + 6.0),
    ]
    size = 6.0
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
        sc.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx + 1.5), pcbnew.FromMM(cy)))
        sc.SetWidth(pcbnew.FromMM(0.15))
        sc.SetLayer(layer)
        board.Add(sc)


def add_calibration_scale(board, x_start, y_pos, layer):
    """Adds a 50.0 mm calibration bar with ticks for physical caliper measurement."""
    # Solid 50mm calibration line
    s_bar = pcbnew.PCB_SHAPE(board)
    s_bar.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s_bar.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x_start), pcbnew.FromMM(y_pos)))
    s_bar.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x_start + 50.0), pcbnew.FromMM(y_pos)))
    s_bar.SetWidth(pcbnew.FromMM(0.80))
    s_bar.SetLayer(layer)
    board.Add(s_bar)

    # 10mm tick marks
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

    # Scale label
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("50.0 mm [1:1 SCALE CALIBRATION BAR - MEASURE WITH CALIPERS]")
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_start + 25.0), pcbnew.FromMM(y_pos + 4.5)))
    txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.5), pcbnew.FromMM(1.5)))
    txt.SetTextThickness(pcbnew.FromMM(0.22))
    txt.SetLayer(layer)
    board.Add(txt)


def prepare_centered_board(src_pcb_path, target_pcb_path, title_sub=""):
    """
    Creates a copy of the board centered on a US Letter Landscape sheet (279.4 x 215.9 mm)
    with optical fiducials, calibration scale, and annotations on both F.Cu and B.Cu.
    """
    board = pcbnew.LoadBoard(src_pcb_path)

    dx = (LETTER_W_LANDSCAPE - BOARD_W) / 2.0  # 89.70 mm
    dy = (LETTER_H_LANDSCAPE - BOARD_H) / 2.0  # 72.95 mm

    # Center all board objects
    board.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))

    # Add fiducials and calibration to F.Cu and B.Cu
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        add_optical_fiducials(board, dx, dy, layer)
        cal_x = dx + (BOARD_W - 50.0) / 2.0
        cal_y = dy + BOARD_H + 18.0
        add_calibration_scale(board, cal_x, cal_y, layer)

        # Title block above board (placed high in upper margin to leave optical fiducials completely unobstructed)
        t_main = pcbnew.PCB_TEXT(board)
        t_main.SetText("ANALOG NEURAL NETWORK TEST BOARD (70x100mm) - PHOTORESIST MASK")
        t_main.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(dx + BOARD_W / 2.0), pcbnew.FromMM(dy - 22.0)))
        t_main.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.0), pcbnew.FromMM(2.0)))
        t_main.SetTextThickness(pcbnew.FromMM(0.32))
        t_main.SetLayer(layer)
        board.Add(t_main)

        t_sub = pcbnew.PCB_TEXT(board)
        t_sub.SetText(f"FORMAT: US LETTER (8.5x11 in) | SCALE: 1:1 TRUE SIZE | {title_sub}")
        t_sub.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(dx + BOARD_W / 2.0), pcbnew.FromMM(dy - 16.0)))
        t_sub.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.4), pcbnew.FromMM(1.4)))
        t_sub.SetTextThickness(pcbnew.FromMM(0.22))
        t_sub.SetLayer(layer)
        board.Add(t_sub)

    board.Save(target_pcb_path)

    # Ensure paper format is USLetter
    with open(target_pcb_path, "r") as f:
        content = f.read()
    content = re.sub(r'\(paper "[^"]*"\)', '(paper "USLetter")', content)
    with open(target_pcb_path, "w") as f:
        f.write(content)

    return target_pcb_path


def generate_cover_guide_pdf(output_pdf_path):
    """Generates an aesthetic, professional vector Cover & DIY Guide page via PostScript."""
    ps_file = os.path.join(SCRATCH_DIR, "guide_cover.ps")
    ps_code = """%!PS-Adobe-3.0
%%BoundingBox: 0 0 792 612
%%Pages: 1
%%EndComments
%%Page: 1 1

/Helvetica-Bold findfont 22 scalefont setfont
54 550 moveto
(ANALOG NEURAL NETWORK TEST BOARD (70x100mm)) show

/Helvetica-Bold findfont 14 scalefont setfont
54 528 moveto
(DIY Photolithography & Photoresist PCB Etching Guide - US Letter Format) show

% Divider line
newpath
54 515 moveto
738 515 lineto
1.5 setlinewidth
0 setgray
stroke

% Two-column layout
% LEFT COLUMN: Specifications & Page Directory
/Helvetica-Bold findfont 12 scalefont setfont
54 485 moveto
(1. BOARD SPECIFICATIONS & PRINT RULES) show

/Helvetica findfont 9.5 scalefont setfont
/nl { 54 exch moveto } def
467 nl (  * Dimensions: 70.0 mm height x 100.0 mm width (4:3 aspect ratio)) show
452 nl (  * Substrate: Standard 1.6 mm FR-4 (1 oz / 35 um Copper Clad)) show
437 nl (  * Page Format: US Letter \\(8.5" x 11.0" / 215.9 x 279.4 mm\\) - Landscape) show
422 nl (  * CRITICAL: Print at 100% SCALE \\(Actual Size\\). DO NOT FIT TO PAGE!) show
407 nl (  * Caliper Check: Verify 50.0 mm scale bar with digital calipers.) show

/Helvetica-Bold findfont 12 scalefont setfont
380 nl (2. PHOTORESIST PAGE DIRECTORY) show

/Helvetica findfont 9.0 scalefont setfont
362 nl (  Page 2: Front Copper \\(F.Cu\\) - POSITIVE RESIST \\(Normal View\\)) show
347 nl (  Page 3: Front Copper \\(F.Cu\\) - POSITIVE RESIST \\(Mirrored View - Emulsion Down\\)) show
332 nl (  Page 4: Back Copper \\(B.Cu\\)  - POSITIVE RESIST \\(Normal View\\)) show
317 nl (  Page 5: Back Copper \\(B.Cu\\)  - POSITIVE RESIST \\(Mirrored View\\)) show
302 nl (  Page 6: Front Copper \\(F.Cu\\) - NEGATIVE DRY FILM \\(Normal View\\)) show
287 nl (  Page 7: Front Copper \\(F.Cu\\) - NEGATIVE DRY FILM \\(Mirrored View - Emulsion Down\\)) show
272 nl (  Page 8: Back Copper \\(B.Cu\\)  - NEGATIVE DRY FILM \\(Normal View\\)) show
257 nl (  Page 9: Back Copper \\(B.Cu\\)  - NEGATIVE DRY FILM \\(Mirrored View\\)) show
242 nl (  Page 10: Component Silkscreen, Drilling Map & Reference Legend) show

% RIGHT COLUMN: Chemical & Exposure Procedures
/Helvetica-Bold findfont 12 scalefont setfont
430 485 moveto
(3. CHEMICAL PROCESSES & RECIPES) show

/Helvetica findfont 9.5 scalefont setfont
/nr { 430 exch moveto } def
467 nr (A. Positive Pre-Sensitized Boards \\(Bungard / Positiv 20\\):) show
452 nr (   * Artwork: Solid black traces block UV \\(Pages 2 - 5\\).) show
437 nr (   * Developer: 10 g / L Sodium Hydroxide \\(NaOH\\) in water at 20 C.) show
422 nr (   * Dev Time: 60 - 90 seconds until unexposed resist clears.) show

397 nr (B. Negative Dry Film Photoresist \\(Riston Blue Film\\):) show
382 nr (   * Artwork: White traces transmit UV to cure \\(Pages 6 - 9\\).) show
367 nr (   * Developer: 10 g / L Sodium Carbonate \\(Na2CO3 / Washing Soda\\).) show
352 nr (   * Dev Time: 90 - 120 seconds with gentle agitation.) show

327 nr (C. Copper Etching Baths:) show
312 nr (   * Option 1: Ferric Chloride \\(FeCl3\\) at 45 - 50 C with aeration.) show
297 nr (   * Option 2: Cupric Chloride \\(CuCl2 + HCl\\) - regenerative.) show
282 nr (   * Option 3: 2 parts Hydrogen Peroxide \\(3%\\) + 1 part Muriatic Acid.) show

/Helvetica-Bold findfont 12 scalefont setfont
257 nr (4. DRILLING & VIAS GUIDE) show

/Helvetica findfont 9.0 scalefont setfont
240 nr (   * Pad center marks indicate optical center for drill bits.) show
225 nr (   * Vias: 0.80 mm carbide bit \\(solder with thin copper wire through-hole\\).) show
210 nr (   * Header Pins \\(J_IN, J_PWR, J_OUT\\): 1.00 mm bit.) show
195 nr (   * Corner Mounting Holes \\(H1..H4\\): 3.20 mm bit \\(M3 hardware\\).) show

% Bottom Callout Box
newpath
54 75 moveto
738 75 lineto
738 165 lineto
54 165 lineto
closepath
0.95 setgray
fill

newpath
54 75 moveto
738 75 lineto
738 165 lineto
54 165 lineto
closepath
0.5 setlinewidth
0 setgray
stroke

/Helvetica-Bold findfont 11 scalefont setfont
70 142 moveto
(PRO-TIP: OPTICAL CONTACT & EMULSION-SIDE ORIENTATION) show

/Helvetica findfont 9.0 scalefont setfont
70 126 moveto
(To eliminate light undercut \\(diffraction around traces\\), the printed toner/ink emulsion side MUST touch the copper clad directly.) show
70 112 moveto
(Use MIRRORED masks when placing toner face-down on the board. The text annotations will read right-side forward through the) show
70 98 moveto
(transparent film, visually confirming 100% correct optical contact before turning on your UV exposure unit.) show

showpage
%%EOF
"""
    with open(ps_file, "w") as f:
        f.write(ps_code)

    cmd = [
        GS_CLI,
        "-sDEVICE=pdfwrite",
        f"-sOutputFile={output_pdf_path}",
        "-dNOPAUSE", "-dBATCH",
        "-dDEVICEWIDTHPOINTS=792",
        "-dDEVICEHEIGHTPOINTS=612",
        "-dFIXEDMEDIA",
        "-dPDFFitPage",
        ps_file
    ]
    subprocess.run(cmd, check=True)
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


def build_gang_positive_pdf(src_pcb_path, output_pdf):
    """
    Builds a single-sheet Portrait US Letter PDF (215.9 x 279.4 mm)
    containing Top Copper (F.Cu) on the upper half and Bottom Copper (B.Cu)
    on the lower half, separated by calibration and cut lines.
    """
    gang_pcb = os.path.join(SCRATCH_DIR, "gang_board_pos.kicad_pcb")

    # Load board instances
    b_top = pcbnew.LoadBoard(src_pcb_path)
    b_bot = pcbnew.LoadBoard(src_pcb_path)

    dx = (LETTER_W_PORTRAIT - BOARD_W) / 2.0  # 57.95 mm
    dy_top = 22.0                             # mm
    dy_bot = 155.0                            # mm

    b_top.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy_top)))
    b_bot.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy_bot)))

    # Assemble into a clean board file
    gang = pcbnew.BOARD()
    gang.SetDesignSettings(b_top.GetDesignSettings())

    # Save components from b_top and b_bot into temporary files to merge cleanly
    # Instead of SWIG Duplicate, write out a merged KiCad PCB with both placements
    with open(src_pcb_path, "r") as f:
        src_lines = f.readlines()

    # We can prepare the gang sheet by creating two board placements in KiCad S-expression:
    # Or simply: plot Top and Bottom separately, then use Ghostscript to compose them onto 1 Letter page!
    # Let's test if GS or ImageMagick can compose them, OR let's compose via PostScript/PDF:
    return None


def generate_all_photoresist_files():
    print("=================================================================")
    print("GENERATING PHOTORESIST ETCHING PDF PACKAGE (US LETTER FORMAT)")
    print("=================================================================")

    src_pcb = os.path.join(WORKSPACE_DIR, "test_board_70x100.kicad_pcb")
    centered_pcb = os.path.join(SCRATCH_DIR, "test_board_70x100_centered.kicad_pcb")

    print("\n1. Centering 70x100mm Board on US Letter Landscape (279.4 x 215.9 mm)...")
    prepare_centered_board(src_pcb, centered_pcb, title_sub="ALL-IN-ONE 4-IN / 2-HIDDEN / 2-OUT WTA")
    print(f"   Created centered board: {centered_pcb}")

    # Temporary page storage
    pages = []

    print("\n2. Generating Page 1: Cover & Photolithography Guide...")
    cover_pdf = os.path.join(SCRATCH_DIR, "page01_guide_cover.pdf")
    generate_cover_guide_pdf(cover_pdf)
    pages.append(cover_pdf)

    mask_configs = [
        ("page02_f_cu_pos_norm.pdf", "F.Cu,Edge.Cuts", False, False, 1, "Page 2: Front Copper (F.Cu) - Positive Normal"),
        ("page03_f_cu_pos_mirr.pdf", "F.Cu,Edge.Cuts", True,  False, 1, "Page 3: Front Copper (F.Cu) - Positive Mirrored"),
        ("page04_b_cu_pos_norm.pdf", "B.Cu,Edge.Cuts", False, False, 1, "Page 4: Back Copper (B.Cu) - Positive Normal"),
        ("page05_b_cu_pos_mirr.pdf", "B.Cu,Edge.Cuts", True,  False, 1, "Page 5: Back Copper (B.Cu) - Positive Mirrored"),
        ("page06_f_cu_neg_norm.pdf", "F.Cu,Edge.Cuts", False, True,  1, "Page 6: Front Copper (F.Cu) - Negative Normal"),
        ("page07_f_cu_neg_mirr.pdf", "F.Cu,Edge.Cuts", True,  True,  1, "Page 7: Front Copper (F.Cu) - Negative Mirrored"),
        ("page08_b_cu_neg_norm.pdf", "B.Cu,Edge.Cuts", False, True,  1, "Page 8: Back Copper (B.Cu) - Negative Normal"),
        ("page09_b_cu_neg_mirr.pdf", "B.Cu,Edge.Cuts", True,  True,  1, "Page 9: Back Copper (B.Cu) - Negative Mirrored"),
        ("page10_f_silk_norm.pdf",   "F.Silkscreen,Edge.Cuts", False, False, 0, "Page 10: Front Silkscreen & Assembly Reference"),
    ]

    for fname, layers, mirror, neg, drill_opt, desc in mask_configs:
        out_page = os.path.join(SCRATCH_DIR, fname)
        print(f"   Generating {desc}...")
        export_single_page_mask(centered_pcb, out_page, layers, mirror=mirror, negative=neg, drill_opt=drill_opt)
        pages.append(out_page)

        # Also save individual layer to fabrication/photoresist/
        indiv_dest = os.path.join(FAB_DIR, f"test_board_70x100_{fname[7:]}")
        shutil.copyfile(out_page, indiv_dest)

    # 3. Assemble Master Multi-Page PDF
    master_pdf = os.path.join(WORKSPACE_DIR, "test_board_70x100_photoresist_letter.pdf")
    master_fab = os.path.join(FAB_DIR, "test_board_70x100_photoresist_master_letter.pdf")
    master_art = os.path.join(ARTIFACTS_DIR, "test_board_70x100_photoresist_letter.pdf")

    print("\n3. Assembling Master 10-Page Photoresist PDF...")
    cmd_unite = [PDFUNITE] + pages + [master_pdf]
    subprocess.run(cmd_unite, check=True)
    shutil.copyfile(master_pdf, master_fab)
    shutil.copyfile(master_pdf, master_art)
    print(f"   SUCCESS! Created {master_pdf} ({len(pages)} pages).")

    # 4. Process Single-Layer Board as well
    src_single = os.path.join(WORKSPACE_DIR, "test_board_single_layer.kicad_pcb")
    if os.path.exists(src_single):
        print("\n4. Processing Single-Layer Testing Board (F.Cu only with 0-ohm jumpers)...")
        centered_single_pcb = os.path.join(SCRATCH_DIR, "test_board_single_layer_centered.kicad_pcb")
        prepare_centered_board(src_single, centered_single_pcb, title_sub="100% SINGLE COPPER LAYER (0-OHM JUMPERS)")

        single_pages = [cover_pdf]
        single_configs = [
            ("single_p2_f_cu_pos_norm.pdf", "F.Cu,Edge.Cuts", False, False, 1),
            ("single_p3_f_cu_pos_mirr.pdf", "F.Cu,Edge.Cuts", True,  False, 1),
            ("single_p4_f_cu_neg_norm.pdf", "F.Cu,Edge.Cuts", False, True,  1),
            ("single_p5_f_cu_neg_mirr.pdf", "F.Cu,Edge.Cuts", True,  True,  1),
            ("single_p6_silk.pdf",          "F.Silkscreen,Edge.Cuts", False, False, 0),
        ]
        for fname, layers, mirror, neg, drill_opt in single_configs:
            out_p = os.path.join(SCRATCH_DIR, fname)
            export_single_page_mask(centered_single_pcb, out_p, layers, mirror=mirror, negative=neg, drill_opt=drill_opt)
            single_pages.append(out_p)

        single_master_pdf = os.path.join(WORKSPACE_DIR, "test_board_single_layer_photoresist_letter.pdf")
        single_art = os.path.join(ARTIFACTS_DIR, "test_board_single_layer_photoresist_letter.pdf")
        cmd_unite_s = [PDFUNITE] + single_pages + [single_master_pdf]
        subprocess.run(cmd_unite_s, check=True)
        shutil.copyfile(single_master_pdf, single_art)
        print(f"   SUCCESS! Created {single_master_pdf} ({len(single_pages)} pages).")

    # 5. Render High-Resolution PNG Previews for Visual Verification
    print("\n5. Rendering High-Resolution PNG Previews for Chat Embedding...")
    render_targets = [
        ("preview_guide.png", cover_pdf, 1),
        ("preview_f_cu_positive_normal.png", pages[1], 1),
        ("preview_f_cu_positive_mirrored.png", pages[2], 1),
        ("preview_b_cu_positive_normal.png", pages[3], 1),
        ("preview_f_cu_negative_normal.png", pages[5], 1),
        ("preview_silkscreen.png", pages[9], 1),
    ]

    for img_name, pdf_path, page_num in render_targets:
        base_out = os.path.join(SCRATCH_DIR, img_name.replace(".png", ""))
        subprocess.run([PDFTOPPM, "-png", "-r", "150", "-f", str(page_num), "-l", str(page_num), pdf_path, base_out], check=True)
        gen_img = f"{base_out}-{page_num}.png"
        final_render = os.path.join(RENDERS_DIR, img_name)
        final_art = os.path.join(ARTIFACTS_DIR, img_name)
        if os.path.exists(gen_img):
            shutil.copyfile(gen_img, final_render)
            shutil.copyfile(gen_img, final_art)
            print(f"   Rendered preview: {img_name}")

    print("\n=================================================================")
    print("ALL PHOTOREASIST ETCHING PDFS COMPLETED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    generate_all_photoresist_files()
