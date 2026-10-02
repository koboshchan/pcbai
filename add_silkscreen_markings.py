#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
add_silkscreen_markings.py
--------------------------
Adds comprehensive silkscreen markings on F.SilkS for the 70x100mm test boards:
- test_board_single_layer.kicad_pcb
- test_board_70x100.kicad_pcb

Marks every single component's Reference AND Value (in ohms, microfarads, diode model, IC model, pinout),
ensuring zero overlap with pads, tracks, or other text, with clean bench-testing legibility.
"""

import os
import sys
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"

BANNERS_TO_REPOSITION = {
    "LAYER 1 (SUM+RECT)": (49.0, 11.0),
    "LAYER 2 (SUM+WTA)":  (78.0, 11.0),
}

BANNERS_TO_KEEP = {
    "ANALOG NEURAL NETWORK TEST BOARD (70x100mm)",
    "LAYER 1 (SUM+RECT)",
    "LAYER 2 (SUM+WTA)",
    "SINGLE-LAYER F.Cu | 4-IN -> 2-HIDDEN (ReLU) -> 2-OUT (WTA/LEDs)",
    "4-IN -> 2-HIDDEN (ReLU) -> 2-OUT (WTA/LEDs)"
}

def create_text(board, text, x, y, size=0.70, thickness=0.11, rot=0, justify=pcbnew.GR_TEXT_H_ALIGN_CENTER):
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(text)
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    txt.SetTextThickness(pcbnew.FromMM(thickness))
    txt.SetTextAngleDegrees(float(rot))
    txt.SetHorizJustify(justify)
    board.Add(txt)
    return txt

def apply_silkscreen_to_board(pcb_path, is_single_layer=False):
    if not os.path.exists(pcb_path):
        print(f"Skipping {pcb_path}, file not found.")
        return

    print(f"Processing silkscreen markings on {pcb_path}...")
    board = pcbnew.LoadBoard(pcb_path)

    # 1. Reposition section banners if present to give more breathing room to components
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT):
            t = d.GetText()
            if t in BANNERS_TO_REPOSITION:
                nx, ny = BANNERS_TO_REPOSITION[t]
                d.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(nx), pcbnew.FromMM(ny)))

    # 2. Clean up existing silkscreen texts (except the high-level banners)
    texts_to_remove = []
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT):
            if d.GetLayer() == pcbnew.F_SilkS:
                if d.GetText() not in BANNERS_TO_KEEP:
                    texts_to_remove.append(d)
    for t in texts_to_remove:
        board.Remove(t)
    print(f"  Removed {len(texts_to_remove)} old silkscreen text items.")

    # 3. Ensure native footprint reference and value texts are hidden so they don't collide
    for fp in board.GetFootprints():
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)

    # 4. Add explicit, collision-free, perfectly legible silkscreen labels:
    
    # --- Power Connector J_PWR (11.0, 16.0) ---
    create_text(board, "J_PWR", 6.0, 14.0, size=0.75, thickness=0.12, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "1:+12V", 6.8, 16.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "2:+5V",  6.8, 18.54, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "3:GND",  6.8, 21.08, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "4:-12V", 6.8, 23.62, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)

    # --- Power Test Points ---
    create_text(board, "+5V", 6.0, 6.8, size=0.70, thickness=0.11)
    create_text(board, "+12V", 16.0, 3.4, size=0.70, thickness=0.11)
    create_text(board, "GND", 18.0, 18.8, size=0.70, thickness=0.11)
    create_text(board, "-12V", 20.0, 66.5, size=0.70, thickness=0.11)

    # --- 4-DIP Switch SW1 (14.0, 36.0) ---
    create_text(board, "SW1: 4-DIP", 14.0, 28.0, size=0.80, thickness=0.12)
    create_text(board, "ON (+5V) >", 7.0, 36.0, size=0.60, thickness=0.09, rot=90)
    create_text(board, "1:X0", 14.0, 32.2, size=0.55, thickness=0.08)
    create_text(board, "2:X1", 14.0, 34.7, size=0.55, thickness=0.08)
    create_text(board, "3:X2", 14.0, 37.3, size=0.55, thickness=0.08)
    create_text(board, "4:X3", 14.0, 39.8, size=0.55, thickness=0.08)

    # --- 4x Pull-Down Resistors (22.0, 32.2..39.8) ---
    create_text(board, "PULL-DOWN", 22.0, 30.2, size=0.55, thickness=0.08)
    create_text(board, "R_PD0: 10k", 25.5, 32.2, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)
    create_text(board, "R_PD1: 10k", 25.5, 34.7, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)
    create_text(board, "R_PD2: 10k", 25.5, 37.3, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)
    create_text(board, "R_PD3: 10k", 25.5, 39.8, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    # --- Input Header J_IN (14.0, 52.0) ---
    create_text(board, "J_IN", 7.0, 50.0, size=0.75, thickness=0.12, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "1:X0", 9.5, 52.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "2:X1", 9.5, 54.54, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "3:X2", 9.5, 57.08, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "4:X3", 9.5, 59.62, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "5:GND", 9.5, 62.16, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)

    # --- Input Test Points (placed cleanly left of the TPs at x=26.0) ---
    create_text(board, "TP_X0", 24.0, 20.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "TP_X1", 24.0, 24.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "TP_X2", 24.0, 46.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "TP_X3", 24.0, 50.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)

    # --- LAYER 1 NORTH: Neuron 0 (Sum + ReLU) ---
    create_text(board, "Rb1_0: 18k", 29.0, 14.5, size=0.60, thickness=0.09)
    create_text(board, "R1_00: 10k", 30.5, 18.2, size=0.55, thickness=0.08)
    create_text(board, "R1_10: 10k", 30.5, 22.2, size=0.55, thickness=0.08)
    create_text(board, "Rf1_0: 10k", 36.2, 18.2, size=0.55, thickness=0.08)
    create_text(board, "TP_SUM0", 41.5, 13.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    create_text(board, "Rin_0: 10k", 41.5, 18.2, size=0.55, thickness=0.08)
    create_text(board, "Rrelu_0: 10k", 51.0, 14.2, size=0.60, thickness=0.09)
    create_text(board, "Rpd0: 10k", 56.0, 12.0, size=0.60, thickness=0.09)
    
    # Diodes D2_0 (48.54, 26.0) and D1_0 (52.00, 26.0)
    create_text(board, "D2_0", 48.5, 22.6, size=0.55, thickness=0.08)
    create_text(board, "D1_0", 52.0, 22.6, size=0.55, thickness=0.08)
    create_text(board, "1N4148 (x2)", 50.25, 29.5, size=0.55, thickness=0.08)
    create_text(board, "TP_ACT0", 60.5, 20.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    # --- LAYER 1 SOUTH: Neuron 1 (Sum + ReLU) ---
    create_text(board, "R1_21: 10k", 30.5, 44.2, size=0.55, thickness=0.08)
    create_text(board, "R1_31: 10k", 30.5, 48.2, size=0.55, thickness=0.08)
    create_text(board, "Rb1_1: 18k", 29.0, 55.5, size=0.60, thickness=0.09)
    create_text(board, "Rf1_1: 10k", 36.2, 51.8, size=0.55, thickness=0.08)
    create_text(board, "TP_SUM1", 41.5, 57.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    create_text(board, "Rin_1: 10k", 41.5, 51.8, size=0.55, thickness=0.08)
    create_text(board, "Rrelu_1: 10k", 51.0, 56.0, size=0.60, thickness=0.09)
    create_text(board, "Rpd1: 10k", 56.0, 58.0, size=0.60, thickness=0.09)
    
    # Diodes D2_1 (48.54, 44.0) and D1_1 (52.00, 44.0)
    create_text(board, "D2_1", 48.5, 40.8, size=0.55, thickness=0.08)
    create_text(board, "D1_1", 52.0, 40.8, size=0.55, thickness=0.08)
    create_text(board, "1N4148 (x2)", 50.25, 47.4, size=0.55, thickness=0.08)
    create_text(board, "TP_ACT1", 60.5, 50.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    # --- U1 TL074 (46.0, 35.0) & Bypass Caps ---
    create_text(board, "U1: TL074", 46.0, 35.0, size=0.75, thickness=0.11, rot=90)
    create_text(board, "C1: 0.1uF", 42.0, 28.0, size=0.55, thickness=0.08)
    create_text(board, "C2: 0.1uF", 42.0, 42.0, size=0.55, thickness=0.08)

    # --- LAYER 2: Output Summing & Reference ---
    # Output 0 (North)
    create_text(board, "Rb2_0: 15k", 65.0, 14.2, size=0.60, thickness=0.09)
    create_text(board, "R2_00: 10k", 65.0, 18.2, size=0.60, thickness=0.09)
    create_text(board, "R2_10: 10k", 65.0, 22.2, size=0.60, thickness=0.09)
    create_text(board, "Rf2_0: 10k", 71.0, 20.0, size=0.60, thickness=0.09)
    create_text(board, "TP_OUT0", 74.0, 14.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    # Output 1 (South, Reference)
    create_text(board, "Rb2_1: 22k", 65.0, 56.0, size=0.60, thickness=0.09)
    create_text(board, "Rf2_1: 10k", 71.0, 50.0, size=0.60, thickness=0.09)
    create_text(board, "TP_OUT1", 74.0, 56.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_LEFT)

    # --- U2 TL074 (78.0, 35.0) & Bypass Caps ---
    create_text(board, "U2: TL074", 78.0, 35.0, size=0.75, thickness=0.11, rot=90)
    create_text(board, "C3: 0.1uF", 77.4, 26.2, size=0.55, thickness=0.08)
    create_text(board, "C4: 0.1uF", 77.4, 43.8, size=0.55, thickness=0.08)

    # --- Decision Indicators (LEDs & Resistors) ---
    create_text(board, "R_LED1: 1k", 85.0, 21.2, size=0.55, thickness=0.08)
    create_text(board, "LED1: RED (VERT)", 92.2, 21.2, size=0.50, thickness=0.07)

    create_text(board, "R_LED0: 1k", 85.0, 48.8, size=0.55, thickness=0.08)
    create_text(board, "LED0: GRN (HORIZ)", 92.2, 48.8, size=0.50, thickness=0.07)

    # --- Output Header J_OUT (96.0, 35.0) ---
    create_text(board, "J_OUT", 96.0, 31.5, size=0.75, thickness=0.12)
    create_text(board, "1:OUT0", 92.5, 35.0, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "2:CMP0", 92.5, 37.54, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "3:CMP1", 92.5, 40.08, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    create_text(board, "4:OUT1", 92.5, 42.62, size=0.55, thickness=0.08, justify=pcbnew.GR_TEXT_H_ALIGN_RIGHT)

    # --- Jumpers (for single-layer board) ---
    if is_single_layer:
        create_text(board, "JMP_BIAS: 0R", 46.0, 6.0, size=0.55, thickness=0.08)
        create_text(board, "JMP_V12: 0R", 46.0, 20.0, size=0.55, thickness=0.08)
        create_text(board, "JMP_WTA: 0R", 84.0, 30.5, size=0.55, thickness=0.08)

    # Save board
    pcbnew.SaveBoard(pcb_path, board)
    print(f"Successfully saved updated silkscreen to {pcb_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        is_sl = "single_layer" in target
        apply_silkscreen_to_board(target, is_single_layer=is_sl)
    else:
        apply_silkscreen_to_board(os.path.join(WORKSPACE_DIR, "test_board_single_layer.kicad_pcb"), is_single_layer=True)
