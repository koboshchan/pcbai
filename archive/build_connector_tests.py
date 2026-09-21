#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
import os, subprocess, pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"

def mm(v): return int(v * 1000000)

# =========================================================================
# 1. Fix Right-Angle 2.54mm Pin Header (deg = 270 points pins DOWN off edge)
# =========================================================================
def fix_ra_daughtercard():
    dc_path = os.path.join(WORKSPACE_DIR, "test_connector_system/test_daughtercard_connector.kicad_pcb")
    b = pcbnew.BOARD()
    
    # 100 x 100 mm blade outline
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(100), mm(100)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("CORRECTED RIGHT-ANGLE PIN HEADER")
    txt.SetPosition(pcbnew.VECTOR2I(mm(50), mm(20)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(2.0), mm(2.0)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    txt2 = pcbnew.PCB_TEXT(b)
    txt2.SetText("Gold pins bend 90 deg DOWN past the bottom PCB edge")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(50), mm(28)))
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt2.SetLayer(pcbnew.F_SilkS)
    b.Add(txt2)

    # Footprint at rot=270:
    # Pads are at Y=92 mm. Pins extend past Y=100 mm bottom edge!
    fp_lib = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty"
    fp = pcbnew.FootprintLoad(fp_lib, "PinHeader_2x20_P2.54mm_Horizontal")
    fp.SetReference("J_BLADE_A")
    fp.SetValue("PinHeader_2x20_RA")
    fp.SetOrientationDegrees(270)
    # At rot=270, pads go from X=0 to -48.26. Center by placing at 50 + 24.13
    fp.SetPosition(pcbnew.VECTOR2I(mm(50.0 + 24.13), mm(92.0)))
    b.Add(fp)
    
    b.Save(dc_path)
    print("Saved corrected RA daughtercard:", dc_path)

# =========================================================================
# 2. Build Real Industrial Backplane: DIN 41612 (Eurocard 96-Pin Shrouded)
# =========================================================================
DIN_DIR = os.path.join(WORKSPACE_DIR, "test_din41612_system")
os.makedirs(DIN_DIR, exist_ok=True)
DIN_MB_PATH = os.path.join(DIN_DIR, "test_din_motherboard.kicad_pcb")
DIN_DC_PATH = os.path.join(DIN_DIR, "test_din_daughtercard.kicad_pcb")

def create_din_system():
    fp_lib_din = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_DIN.pretty"
    
    # Motherboard with Vertical Female Shrouded Socket
    b_mb = pcbnew.BOARD()
    gr_mb = pcbnew.PCB_SHAPE(b_mb)
    gr_mb.SetShape(pcbnew.SHAPE_T_RECT)
    gr_mb.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr_mb.SetEnd(pcbnew.VECTOR2I(mm(110), mm(60)))
    gr_mb.SetLayer(pcbnew.Edge_Cuts)
    gr_mb.SetWidth(mm(0.15))
    b_mb.Add(gr_mb)
    
    txt = pcbnew.PCB_TEXT(b_mb)
    txt.SetText("DIN 41612 VERTICAL BACKPLANE SOCKET (96 PINS)")
    txt.SetPosition(pcbnew.VECTOR2I(mm(55), mm(12)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.8), mm(1.8)))
    txt.SetLayer(pcbnew.F_SilkS)
    b_mb.Add(txt)

    fp_mb = pcbnew.FootprintLoad(fp_lib_din, "DIN41612_C_3x32_Female_Vertical_THT")
    fp_mb.SetReference("J_BACKPLANE_SLOT")
    fp_mb.SetValue("DIN41612_96P_Female")
    fp_mb.SetPosition(pcbnew.VECTOR2I(mm(15), mm(30)))
    b_mb.Add(fp_mb)
    b_mb.Save(DIN_MB_PATH)
    print("Saved DIN motherboard:", DIN_MB_PATH)

    # Daughtercard with Right-Angle Male Shrouded Plug & Screw Ears
    b_dc = pcbnew.BOARD()
    gr_dc = pcbnew.PCB_SHAPE(b_dc)
    gr_dc.SetShape(pcbnew.SHAPE_T_RECT)
    gr_dc.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr_dc.SetEnd(pcbnew.VECTOR2I(mm(100), mm(100)))
    gr_dc.SetLayer(pcbnew.Edge_Cuts)
    gr_dc.SetWidth(mm(0.15))
    b_dc.Add(gr_dc)
    
    txt_dc = pcbnew.PCB_TEXT(b_dc)
    txt_dc.SetText("DIN 41612 VERTICAL BLADE DAUGHTERCARD (96 PINS)")
    txt_dc.SetPosition(pcbnew.VECTOR2I(mm(50), mm(20)))
    txt_dc.SetTextSize(pcbnew.VECTOR2I(mm(1.8), mm(1.8)))
    txt_dc.SetLayer(pcbnew.F_SilkS)
    b_dc.Add(txt_dc)

    txt_dc2 = pcbnew.PCB_TEXT(b_dc)
    txt_dc2.SetText("Rigid Shrouded Male Connector with Mounting Screws")
    txt_dc2.SetPosition(pcbnew.VECTOR2I(mm(50), mm(30)))
    txt_dc2.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt_dc2.SetLayer(pcbnew.F_SilkS)
    b_dc.Add(txt_dc2)

    fp_dc = pcbnew.FootprintLoad(fp_lib_din, "DIN41612_C_3x32_Male_Horizontal_THT")
    fp_dc.SetReference("J_BLADE_CONNECTOR")
    fp_dc.SetValue("DIN41612_96P_Male_RA")
    # Place right at bottom edge so shroud locks onto edge
    fp_dc.SetPosition(pcbnew.VECTOR2I(mm(10), mm(92)))
    b_dc.Add(fp_dc)
    b_dc.Save(DIN_DC_PATH)
    print("Saved DIN daughtercard:", DIN_DC_PATH)

if __name__ == "__main__":
    fix_ra_daughtercard()
    create_din_system()
