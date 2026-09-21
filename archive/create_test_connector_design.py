#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
create_test_connector_design.py
--------------------------------
Creates a clean, component-free mechanical test design demonstrating exactly
how the vertical plug-in blade connection works:
1. test_motherboard_connector.kicad_pcb:
   - Baseboard with standard Vertical Female Sockets (PinSocket_2x20_P2.54mm_Vertical).
   - Socket holes point UP (+Z) to receive vertical cards.
2. test_daughtercard_connector.kicad_pcb:
   - Daughtercard blade with Right-Angle Male Pin Headers (PinHeader_2x20_P2.54mm_Horizontal).
   - Right-angle pins extend past the bottom edge, pointing DOWN into the motherboard sockets.
"""

import os
import pcbnew
import subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
TEST_DIR = os.path.join(WORKSPACE_DIR, "test_connector_system")
os.makedirs(TEST_DIR, exist_ok=True)

MB_PATH = os.path.join(TEST_DIR, "test_motherboard_connector.kicad_pcb")
DC_PATH = os.path.join(TEST_DIR, "test_daughtercard_connector.kicad_pcb")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
FP_LIB_HEADER = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
FP_LIB_SOCKET = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinSocket_2.54mm.pretty"

def mm(v): return int(v * 1000000)

def create_motherboard():
    b = pcbnew.BOARD()
    
    # 100 x 60 mm outline
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(100), mm(60)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    # Text
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("TEST MOTHERBOARD: VERTICAL 2.54mm FEMALE SOCKETS (FACE UP)")
    txt.SetPosition(pcbnew.VECTOR2I(mm(50), mm(10)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)
    
    # Dual 2x20 Vertical Female Sockets (centered at X=50, Y=25 and Y=32.62)
    # Pitch 2.54mm, 20 pins = 19 * 2.54 = 48.26mm length
    for idx, (ref, val, y_pos) in enumerate([("J_SLOT_A", "Slot_A_Female", 25.0), ("J_SLOT_B", "Slot_B_Female", 32.62)]):
        fp = pcbnew.FootprintLoad(FP_LIB_SOCKET, "PinSocket_2x20_P2.54mm_Vertical")
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetOrientationDegrees(90)
        # Position so that pin array is centered at X=50
        # In this footprint, rot 90 places pin 1 at (0,0) and pin 40 at (48.26, -2.54)
        fp.SetPosition(pcbnew.VECTOR2I(mm(50.0 - 24.13), mm(y_pos + 1.27)))
        b.Add(fp)
        
    b.Save(MB_PATH)
    print(f"Created: {MB_PATH}")

def create_daughtercard():
    b = pcbnew.BOARD()
    
    # 100 x 100 mm blade outline
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(100), mm(100)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    # Text
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("TEST DAUGHTERCARD: RIGHT-ANGLE MALE HEADERS (PLUG DOWN)")
    txt.SetPosition(pcbnew.VECTOR2I(mm(50), mm(20)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.8), mm(1.8)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)
    
    txt2 = pcbnew.PCB_TEXT(b)
    txt2.SetText("Pins bend 90 deg off bottom edge into Motherboard sockets")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(50), mm(30)))
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt2.SetLayer(pcbnew.F_SilkS)
    b.Add(txt2)

    # Right-Angle 2x20 Male Pin Headers placed near the bottom edge
    # In PinHeader_2x20_P2.54mm_Horizontal:
    # At rot=90, pins extend in +Y direction by ~10.5 mm past the through-hole pads!
    # Pads are at Y=92 mm, so pins reach Y=102.5 mm (extending 2.5 mm past bottom edge of PCB)
    fp = pcbnew.FootprintLoad(FP_LIB_HEADER, "PinHeader_2x20_P2.54mm_Horizontal")
    fp.SetReference("J_BLADE_A")
    fp.SetValue("Right_Angle_Header_A")
    fp.SetOrientationDegrees(90)
    fp.SetPosition(pcbnew.VECTOR2I(mm(50.0 - 24.13), mm(92.0)))
    b.Add(fp)

    b.Save(DC_PATH)
    print(f"Created: {DC_PATH}")

if __name__ == "__main__":
    create_motherboard()
    create_daughtercard()
