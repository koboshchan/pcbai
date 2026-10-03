#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
render_negative_masks_letter_mirrored.py
-----------------------------------------
Generates the exact 1:1 true-scale photolithography package requested:
- All Mirrored View (horizontally mirrored / emulsion-down for contact exposure)
- 1. Negative Copper (F.Cu) with drill center-punch dimples
- 2. Solder Mask (F.Mask) for negative dry-film photoresist (black pads, clear substrate)
- 3. Negative Silkscreen (F.SilkS) for stencil/screen/photoresist legend

Formatted strictly for US Letter (8.5" x 11.0" / 215.9 x 279.4 mm) Landscape.

Outputs:
1. test_board_photoresist_mirrored_letter.pdf (3-page unified PDF)
2. test_board_photoresist_letter.pdf (updated main photoresist file)
3. Individual 1-page PDF masks in fabrication/photoresist/
4. High-resolution preview images in renders/ and artifacts directory
"""

import os
import sys
import re
import subprocess
import shutil
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PDFUNITE = "/opt/homebrew/bin/pdfunite"
PDFTOPPM = "/opt/homebrew/bin/pdftoppm"
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"
SCRATCH_DIR = os.path.join(WORKSPACE_DIR, ".tmp_photoresist_mirrored")
FAB_DIR = os.path.join(WORKSPACE_DIR, "fabrication", "photoresist")
RENDERS_DIR = os.path.join(WORKSPACE_DIR, "renders")

os.makedirs(SCRATCH_DIR, exist_ok=True)
os.makedirs(FAB_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

LETTER_W = 279.40  # 11.0 in (Landscape width in mm)
LETTER_H = 215.90  # 8.5 in (Landscape height in mm)
BOARD_W  = 100.0   # mm
BOARD_H  = 70.0    # mm

DX = (LETTER_W - BOARD_W) / 2.0  # 89.70 mm
DY = (LETTER_H - BOARD_H) / 2.0  # 72.95 mm


def add_optical_fiducials(board, layer):
    """Adds 4 corner crosshairs with target rings for optical registration."""
    corners = [
        (DX - 8.0, DY - 8.0),
        (DX + BOARD_W + 8.0, DY - 8.0),
        (DX - 8.0, DY + BOARD_H + 8.0),
        (DX + BOARD_W + 8.0, DY + BOARD_H + 8.0),
    ]
    size = 8.0
    for cx, cy in corners:
        # Horizontal crosshair line
        sh = pcbnew.PCB_SHAPE(board)
        sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx - size / 2.0), pcbnew.FromMM(cy)))
        sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx + size / 2.0), pcbnew.FromMM(cy)))
        sh.SetWidth(pcbnew.FromMM(0.25))
        sh.SetLayer(layer)
        board.Add(sh)

        # Vertical crosshair line
        sv = pcbnew.PCB_SHAPE(board)
        sv.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sv.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy - size / 2.0)))
        sv.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy + size / 2.0)))
        sv.SetWidth(pcbnew.FromMM(0.25))
        sv.SetLayer(layer)
        board.Add(sv)

        # Concentric alignment circle
        sc = pcbnew.PCB_SHAPE(board)
        sc.SetShape(pcbnew.SHAPE_T_CIRCLE)
        sc.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
        sc.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(cx + 2.0), pcbnew.FromMM(cy)))
        sc.SetWidth(pcbnew.FromMM(0.20))
        sc.SetLayer(layer)
        board.Add(sc)


def add_calibration_scale(board, layer):
    """Adds a 50.0 mm caliper verification scale bar with 10 mm ticks."""
    x_start = DX + (BOARD_W - 50.0) / 2.0
    y_pos = DY + BOARD_H + 18.0

    # 50mm solid baseline
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
    txt.SetText("50.0 mm [1:1 TRUE SCALE - MEASURE WITH CALIPERS]")
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_start + 25.0), pcbnew.FromMM(y_pos + 4.5)))
    txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.5), pcbnew.FromMM(1.5)))
    txt.SetTextThickness(pcbnew.FromMM(0.22))
    txt.SetLayer(layer)
    board.Add(txt)


def add_title_block(board, layer, title_text):
    """Adds clear title and print scale instructions in upper margin."""
    t_main = pcbnew.PCB_TEXT(board)
    t_main.SetText("ANALOG NEURAL NETWORK TEST BOARD (70x100mm)")
    t_main.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(DX + BOARD_W / 2.0), pcbnew.FromMM(DY - 22.0)))
    t_main.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.0), pcbnew.FromMM(2.0)))
    t_main.SetTextThickness(pcbnew.FromMM(0.32))
    t_main.SetLayer(layer)
    board.Add(t_main)

    t_sub = pcbnew.PCB_TEXT(board)
    t_sub.SetText(title_text)
    t_sub.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(DX + BOARD_W / 2.0), pcbnew.FromMM(DY - 16.0)))
    t_sub.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.4), pcbnew.FromMM(1.4)))
    t_sub.SetTextThickness(pcbnew.FromMM(0.22))
    t_sub.SetLayer(layer)
    board.Add(t_sub)


def create_centered_board(src_pcb_path, target_pcb_path):
    """Centers the PCB on US Letter Landscape and adds registration markings."""
    board = pcbnew.LoadBoard(src_pcb_path)
    board.Move(pcbnew.VECTOR2I(pcbnew.FromMM(DX), pcbnew.FromMM(DY)))

    fcu_sub  = "FORMAT: US LETTER (8.5x11 in) | SCALE: 1:1 TRUE SIZE | NEGATIVE COPPER (F.Cu) [MIRRORED VIEW - EMULSION DOWN]"
    mask_sub = "FORMAT: US LETTER (8.5x11 in) | SCALE: 1:1 TRUE SIZE | SOLDER MASK (F.Mask) [MIRRORED VIEW - EMULSION DOWN]"
    silk_sub = "FORMAT: US LETTER (8.5x11 in) | SCALE: 1:1 TRUE SIZE | NEGATIVE SILKSCREEN (F.SilkS) [MIRRORED VIEW - EMULSION DOWN]"

    for lyr in [pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_SilkS]:
        add_optical_fiducials(board, lyr)
        add_calibration_scale(board, lyr)

    add_title_block(board, pcbnew.F_Cu, fcu_sub)
    add_title_block(board, pcbnew.F_Mask, mask_sub)
    add_title_block(board, pcbnew.F_SilkS, silk_sub)

    board.Save(target_pcb_path)

    # Force USLetter page format
    with open(target_pcb_path, "r") as f:
        content = f.read()
    if '(paper' in content:
        content = re.sub(r'\(paper \"[^\"]*\"\)', '(paper "USLetter")', content)
    else:
        content = content.replace('(general', '(paper "USLetter")\n  (general')
    with open(target_pcb_path, "w") as f:
        f.write(content)

    return target_pcb_path


def export_pdf_mask(pcb_path, output_pdf, layers, negative=True, drill_opt=1):
    """Exports a 1:1 scale Mirrored View PDF mask using kicad-cli."""
    cmd = [
        KICAD_CLI, "pcb", "export", "pdf",
        "--layers", layers,
        "--scale", "1",
        "--black-and-white",
        "--mirror",
        "--drill-shape-opt", str(drill_opt),
        "-o", output_pdf
    ]
    if negative:
        cmd.append("--negative")
    cmd.append(pcb_path)
    subprocess.run(cmd, check=True)
    return output_pdf


def main():
    print("=" * 75)
    print("GENERATING EXCLUSIVE 3-LAYER PHOTORESIST SUITE (ALL MIRRORED VIEW)")
    print("  1. Negative Copper (F.Cu) - Mirrored")
    print("  2. Solder Mask (F.Mask) - Mirrored")
    print("  3. Negative Silkscreen (F.SilkS) - Mirrored")
    print("=" * 75)

    src_pcb = os.path.join(WORKSPACE_DIR, "test_board_freerouted.kicad_pcb")
    centered_pcb = os.path.join(SCRATCH_DIR, "test_board_centered_mirrored.kicad_pcb")

    print("\n1. Centering PCB on US Letter (279.4 x 215.9 mm)...")
    create_centered_board(src_pcb, centered_pcb)
    print(f"   Centered PCB: {centered_pcb}")

    print("\n2. Exporting 1:1 Mirrored View PDF Masks...")
    p1_cu_neg   = os.path.join(SCRATCH_DIR, "page1_negative_cu_mirrored.pdf")
    p2_mask     = os.path.join(SCRATCH_DIR, "page2_mask_mirrored.pdf")
    p3_silk_neg = os.path.join(SCRATCH_DIR, "page3_negative_silkscreen_mirrored.pdf")

    # Page 1: Negative Cu (drill_opt=1 for center punch dimples, mirrored)
    export_pdf_mask(centered_pcb, p1_cu_neg, "F.Cu,Edge.Cuts", negative=True, drill_opt=1)

    # Page 2: Mask (Solder mask photoresist for negative dry-film: black pads, clear background, mirrored)
    export_pdf_mask(centered_pcb, p2_mask, "F.Mask,Edge.Cuts", negative=False, drill_opt=0)

    # Page 3: Negative Silkscreen (drill_opt=0, mirrored)
    export_pdf_mask(centered_pcb, p3_silk_neg, "F.Silkscreen,Edge.Cuts", negative=True, drill_opt=0)

    print("   [OK] Page 1: Negative Cu (Mirrored)")
    print("   [OK] Page 2: Mask (Mirrored)")
    print("   [OK] Page 3: Negative Silkscreen (Mirrored)")

    # Save individual 1-page masks to fabrication/photoresist/
    fab_cu   = os.path.join(FAB_DIR, "test_board_freerouted_negative_cu_mirrored.pdf")
    fab_mask = os.path.join(FAB_DIR, "test_board_freerouted_mask_mirrored.pdf")
    fab_silk = os.path.join(FAB_DIR, "test_board_freerouted_negative_silkscreen_mirrored.pdf")

    shutil.copyfile(p1_cu_neg, fab_cu)
    shutil.copyfile(p2_mask, fab_mask)
    shutil.copyfile(p3_silk_neg, fab_silk)

    print("\n3. Assembling Unified 3-Page PDF (US Letter Size)...")
    doc_mirrored_letter = os.path.join(WORKSPACE_DIR, "test_board_photoresist_mirrored_letter.pdf")
    doc_default_letter = os.path.join(WORKSPACE_DIR, "test_board_photoresist_letter.pdf")

    subprocess.run([PDFUNITE, p1_cu_neg, p2_mask, p3_silk_neg, doc_mirrored_letter], check=True)
    shutil.copyfile(doc_mirrored_letter, doc_default_letter)
    shutil.copyfile(doc_mirrored_letter, os.path.join(FAB_DIR, "test_board_photoresist_mirrored_letter.pdf"))
    shutil.copyfile(doc_mirrored_letter, os.path.join(FAB_DIR, "test_board_photoresist_letter.pdf"))
    shutil.copyfile(doc_mirrored_letter, os.path.join(ARTIFACTS_DIR, "test_board_photoresist_mirrored_letter.pdf"))
    shutil.copyfile(doc_mirrored_letter, os.path.join(ARTIFACTS_DIR, "test_board_photoresist_letter.pdf"))
    print(f"   [CREATED] {doc_mirrored_letter}")
    print(f"   [UPDATED] {doc_default_letter}")

    print("\n4. Rendering High-Resolution Previews (150 DPI)...")
    renders = [
        ("preview_negative_cu_mirrored.png", p1_cu_neg),
        ("preview_mask_mirrored.png", p2_mask),
        ("preview_negative_silkscreen_mirrored.png", p3_silk_neg),
    ]

    for img_name, pdf_path in renders:
        tmp_base = os.path.join(SCRATCH_DIR, img_name.replace(".png", ""))
        subprocess.run([PDFTOPPM, "-png", "-r", "150", pdf_path, tmp_base], check=True)
        src_png = f"{tmp_base}-1.png"
        dest_render = os.path.join(RENDERS_DIR, img_name)
        dest_art = os.path.join(ARTIFACTS_DIR, img_name)
        if os.path.exists(src_png):
            shutil.copyfile(src_png, dest_render)
            shutil.copyfile(src_png, dest_art)
            print(f"   [RENDERED] {img_name}")

    # Clean up scratch directory
    shutil.rmtree(SCRATCH_DIR, ignore_errors=True)

    print("\n" + "=" * 75)
    print("SUCCESS: ALL MIRRORED VIEW PHOTORESIST MASKS GENERATED FOR US LETTER")
    print("=" * 75)


if __name__ == "__main__":
    main()
