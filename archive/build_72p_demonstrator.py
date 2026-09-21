#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
build_72p_demonstrator.py
-------------------------
Implements the EXACT datasheet specifications from Shenzhen Yiwei Technology Co., Ltd.
Part: S-072M-2.54-5-** (72-Pin Straight DIP Female Edge Card Connector Slot):
- Motherboard: 100.0 mm x 100.0 mm
- Daughtercard Blade: 94.28 mm x 100.0 mm (Exact Dimension B from datasheet!)
- Pin Span A: 88.90 mm (35 x 2.54mm, 36 pins per row, 72 pins total)
- Outer Body Length C: 97.73 mm
- Body Width: 9.25 mm
- Body Height: 15.60 mm
- Slot Depth: 9.00 mm
- Pad Dimensions: 1.60 mm wide x 8.00 mm long, Pitch 2.54 mm
- Row Spacing: 5.08 mm
"""

import os
import pcbnew
import subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
TEST_DIR = os.path.join(WORKSPACE_DIR, "test_edgecard_system")
os.makedirs(TEST_DIR, exist_ok=True)

WRL_SOCKET = os.path.join(TEST_DIR, "edge_card_72p_exact.wrl")
WRL_BLADE = os.path.join(TEST_DIR, "dc_blade_72p_exact.wrl")
MB_PATH = os.path.join(TEST_DIR, "test_motherboard_72p.kicad_pcb")
DC_PATH = os.path.join(TEST_DIR, "test_daughtercard_72p.kicad_pcb")
ASM_PATH = os.path.join(TEST_DIR, "test_assembly_72p.kicad_pcb")
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def mm(v): return int(v * 1000000)

# Datasheet exact values (in mm)
DIM_A = 88.90   # Pin span: 35 * 2.54
DIM_B = 94.28   # Slot cavity length & recommended card width
DIM_C = 97.73   # Outer body length
DIM_D = 95.98   # Shoulder length
BODY_WIDTH = 9.25
BODY_HEIGHT = 15.60
SLOT_DEPTH = 9.00
ROW_SPACING = 5.08
PAD_WIDTH = 1.60
PAD_HEIGHT = 8.00
PITCH = 2.54

# =========================================================================
# 1. 3D VRML Model of the 72-Pin Connector (Exact to Datasheet)
# =========================================================================
def generate_socket_wrl():
    # In KiCad VRML, 1 unit = 2.54 mm, so m_Scale = 1/2.54
    # Wall thickness on sides: (9.25 - 2.0) / 2 = 3.625 mm
    wall_th = 3.625
    y_wall = 1.0 + (wall_th / 2.0)  # 2.8125 mm
    endcap_th = (DIM_C - DIM_B) / 2.0  # (97.73 - 94.28)/2 = 1.725 mm
    x_endcap = (DIM_B / 2.0) + (endcap_th / 2.0) # 47.14 + 0.8625 = 48.0025 mm
    z_floor = (BODY_HEIGHT - SLOT_DEPTH) # 15.60 - 9.00 = 6.60 mm
    
    wrl = f"""#VRML V2.0 utf8
# Exact 72-Pin (2x36) Straight Edge Card Connector Slot
# Datasheet: S-072M-2.54-5-** (Shenzhen Yiwei Technology Co., Ltd.)
Transform {{
  children [
    # Front side wall of the socket body
    Transform {{
      translation 0 {y_wall:.4f} {BODY_HEIGHT/2:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }}
          }}
          geometry Box {{ size {DIM_C:.2f} {wall_th:.3f} {BODY_HEIGHT:.2f} }}
        }}
      ]
    }},
    # Back side wall of the socket body
    Transform {{
      translation 0 -{y_wall:.4f} {BODY_HEIGHT/2:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }}
          }}
          geometry Box {{ size {DIM_C:.2f} {wall_th:.3f} {BODY_HEIGHT:.2f} }}
        }}
      ]
    }},
    # Left end cap
    Transform {{
      translation -{x_endcap:.4f} 0 {BODY_HEIGHT/2:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }}
          }}
          geometry Box {{ size {endcap_th:.3f} {BODY_WIDTH:.2f} {BODY_HEIGHT:.2f} }}
        }}
      ]
    }},
    # Right end cap
    Transform {{
      translation {x_endcap:.4f} 0 {BODY_HEIGHT/2:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }}
          }}
          geometry Box {{ size {endcap_th:.3f} {BODY_WIDTH:.2f} {BODY_HEIGHT:.2f} }}
        }}
      ]
    }},
    # Floor of the slot cavity (leaves {SLOT_DEPTH:.1f}mm slot depth)
    Transform {{
      translation 0 0 {z_floor/2:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.08 0.08 0.08
              specularColor 0.2 0.2 0.2
              shininess 0.2
            }}
          }}
          geometry Box {{ size {DIM_B:.2f} 2.00 {z_floor:.2f} }}
        }}
      ]
    }},
    # Gold Contact Springs inside the slot (visible dual rows)
    Transform {{
      translation 0 0.88 {BODY_HEIGHT - 4.5:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.15 5.5 }}
        }}
      ]
    }},
    Transform {{
      translation 0 -0.88 {BODY_HEIGHT - 4.5:.4f}
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.15 5.5 }}
        }}
      ]
    }},
    # Solder Pins extending down through the PCB (at Y = -2.54 and Y = +2.54)
    Transform {{
      translation 0 -{ROW_SPACING/2:.2f} -1.90
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.85 0.80
              specularColor 0.9 0.9 0.9
              shininess 0.8
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.64 3.8 }}
        }}
      ]
    }},
    Transform {{
      translation 0 {ROW_SPACING/2:.2f} -1.90
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.85 0.80
              specularColor 0.9 0.9 0.9
              shininess 0.8
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.64 3.8 }}
        }}
      ]
    }}
  ]
}}
"""
    with open(WRL_SOCKET, "w") as f:
        f.write(wrl)
    print(f"Generated Exact 72P Socket 3D WRL: {WRL_SOCKET}")

# =========================================================================
# 2. 3D Model of the 94.28mm x 100mm Daughtercard Blade Plugged In
# =========================================================================
def generate_blade_wrl():
    # Card Width: 94.28 mm, Height: 100.0 mm, Thickness: 1.57 mm (1.6 mm nominal)
    # The slot floor is at Z = 6.60 mm. The blade bottom edge sits at Z = 6.60 mm.
    # Center of blade in Z = 6.60 + 50.0 = 56.60 mm.
    wrl = f"""#VRML V2.0 utf8
# Exact 94.28mm x 100.0mm Daughtercard Blade standing vertically in 72P Slot
Transform {{
  children [
    # Green FR4 PCB Blade
    Transform {{
      translation 0 0 56.60
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.08 0.32 0.18
              specularColor 0.3 0.4 0.3
              shininess 0.5
            }}
          }}
          geometry Box {{ size {DIM_B:.2f} 1.57 100.0 }}
        }}
      ]
    }},
    # Silkscreen Text Banner on Daughtercard
    Transform {{
      translation 0 0.81 72.0
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.9 0.9 0.9
              specularColor 0.5 0.5 0.5
              shininess 0.2
            }}
          }}
          geometry Box {{ size 84.0 0.04 16.0 }}
        }}
      ]
    }},
    # Gold Contact Fingers (Front Row wiping inside socket)
    Transform {{
      translation 0 0.80 10.60
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.04 {PAD_HEIGHT:.2f} }}
        }}
      ]
    }},
    # Gold Contact Fingers (Back Row wiping inside socket)
    Transform {{
      translation 0 -0.80 10.60
      children [
        Shape {{
          appearance Appearance {{
            material Material {{
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }}
          }}
          geometry Box {{ size {DIM_A:.2f} 0.04 {PAD_HEIGHT:.2f} }}
        }}
      ]
    }}
  ]
}}
"""
    with open(WRL_BLADE, "w") as f:
        f.write(wrl)
    print(f"Generated Exact 72P Blade 3D WRL: {WRL_BLADE}")

# =========================================================================
# 3. Build Full-Size 100.0 x 100.0 mm Motherboard with 72P Straight Slot
# =========================================================================
def build_motherboard():
    b = pcbnew.BOARD()
    
    # Board Outline: Exactly 100.0 x 100.0 mm
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(100), mm(100)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    # Corner Mounting Holes (M3): at (5, 5), (95, 5), (5, 95), (95, 95)
    for hx, hy in [(5, 5), (95, 5), (5, 95), (95, 95)]:
        mh = pcbnew.FOOTPRINT(b)
        mh.SetPosition(pcbnew.VECTOR2I(mm(hx), mm(hy)))
        pad = pcbnew.PAD(mh)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(pcbnew.VECTOR2I(mm(5.5), mm(5.5)))
        pad.SetDrillSize(pcbnew.VECTOR2I(mm(3.2), mm(3.2)))
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        mh.Add(pad)
        b.Add(mh)

    # Silkscreen Titles
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("MOTHERBOARD 100.0 x 100.0 mm (4-LAYER FULL SIZE)")
    txt.SetPosition(pcbnew.VECTOR2I(mm(50), mm(15)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    txt2 = pcbnew.PCB_TEXT(b)
    txt2.SetText("72-PIN 2.54mm STRAIGHT SLOT (S-072M-2.54-5)")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(50), mm(22)))
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt2.SetLayer(pcbnew.F_SilkS)
    b.Add(txt2)

    txt3 = pcbnew.PCB_TEXT(b)
    txt3.SetText("Pin Budget: 64 Analog Inputs + 4 L1 Outputs + 4 Power/GND")
    txt3.SetPosition(pcbnew.VECTOR2I(mm(50), mm(28)))
    txt3.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
    txt3.SetLayer(pcbnew.F_SilkS)
    b.Add(txt3)

    # 72P Edge Card Footprint: 2 rows of 36 pins, pitch 2.54mm, row spacing 5.08mm
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference("J_SLOT1")
    fp.SetValue("S-072M-2.54-5")
    fx = 50.0
    fy = 50.0 # Centered at X=50, Y=50
    fp.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(fy)))

    x_start = - (17.5 * PITCH) # 36 pins: 35 * 2.54 = 88.90mm span

    for i in range(36):
        px = x_start + i * PITCH
        # Row A (Y = -2.54): Pin A1..A36
        pad_a = pcbnew.PAD(fp)
        pad_a.SetNumber(f"A{i+1}")
        pad_a.SetShape(pcbnew.PAD_SHAPE_CIRCLE if i > 0 else pcbnew.PAD_SHAPE_RECT)
        pad_a.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad_a.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy - 2.54)))
        pad_a.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        pad_a.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        pad_a.SetLayerSet(pcbnew.LSET.AllCuMask())
        fp.Add(pad_a)

        # Row B (Y = +2.54): Pin B1..B36
        pad_b = pcbnew.PAD(fp)
        pad_b.SetNumber(f"B{i+1}")
        pad_b.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad_b.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad_b.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy + 2.54)))
        pad_b.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        pad_b.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        pad_b.SetLayerSet(pcbnew.LSET.AllCuMask())
        fp.Add(pad_b)

    # Footprint Courtyard / Silk Outline: 97.73mm x 9.25mm
    fp_line = pcbnew.PCB_SHAPE(fp)
    fp_line.SetShape(pcbnew.SHAPE_T_RECT)
    fp_line.SetStart(pcbnew.VECTOR2I(mm(fx - DIM_C/2), mm(fy - BODY_WIDTH/2)))
    fp_line.SetEnd(pcbnew.VECTOR2I(mm(fx + DIM_C/2), mm(fy + BODY_WIDTH/2)))
    fp_line.SetLayer(pcbnew.F_SilkS)
    fp_line.SetWidth(mm(0.15))
    fp.Add(fp_line)

    # Attach 3D Model of the 72P Socket with 1/2.54 scale
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = WRL_SOCKET
    m.m_Scale = pcbnew.VECTOR3D(1.0/2.54, 1.0/2.54, 1.0/2.54)
    fp.Add3DModel(m)

    b.Add(fp)
    b.Save(MB_PATH)
    print(f"Saved 72P Motherboard (100.0x100.0mm): {MB_PATH}")

# =========================================================================
# 4. Build Exact 94.28 mm x 100.0 mm Daughtercard Blade
# =========================================================================
def build_daughtercard():
    b = pcbnew.BOARD()

    # Board Outline: Exactly 94.28 mm wide x 100.0 mm high
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(DIM_B), mm(100.0)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)

    # Top corner pull/mounting holes (M3): (5, 5) and (89.28, 5)
    for hx, hy in [(5, 5), (DIM_B - 5, 5)]:
        mh = pcbnew.FOOTPRINT(b)
        mh.SetPosition(pcbnew.VECTOR2I(mm(hx), mm(hy)))
        pad = pcbnew.PAD(mh)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(pcbnew.VECTOR2I(mm(5.5), mm(5.5)))
        pad.SetDrillSize(pcbnew.VECTOR2I(mm(3.2), mm(3.2)))
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        mh.Add(pad)
        b.Add(mh)

    # Silkscreen Text
    cx = DIM_B / 2.0 # 47.14 mm
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("DAUGHTERCARD BLADE: 94.28 x 100.0 mm")
    txt.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(24)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.9), mm(1.9)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    txt2 = pcbnew.PCB_TEXT(b)
    txt2.SetText("72 Gold Contacts (36 Front F.Cu + 36 Back B.Cu, Pitch 2.54mm)")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(33)))
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(1.3), mm(1.3)))
    txt2.SetLayer(pcbnew.F_SilkS)
    b.Add(txt2)

    txt3 = pcbnew.PCB_TEXT(b)
    txt3.SetText("ZERO SOLDERED CONNECTORS | Direct ENIG Edge Finger Contact")
    txt3.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(41)))
    txt3.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
    txt3.SetLayer(pcbnew.F_SilkS)
    b.Add(txt3)

    txt4 = pcbnew.PCB_TEXT(b)
    txt4.SetText("<< INSERTION STOP LINE (9.0mm Socket Depth) >>")
    txt4.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(89.0)))
    txt4.SetTextSize(pcbnew.VECTOR2I(mm(1.1), mm(1.1)))
    txt4.SetLayer(pcbnew.F_SilkS)
    b.Add(txt4)

    # Gold Fingers Footprint:
    # 36 fingers on F.Cu + 36 fingers on B.Cu along Y = 100mm bottom edge!
    # Datasheet: Pad width = 1.60mm, Pad length = 8.00mm.
    # Fingers reach exactly to Y = 100.0mm bottom edge.
    # Center of pads: Y = 100.0 - (8.00 / 2) = 96.0 mm.
    fp_fingers = pcbnew.FOOTPRINT(b)
    fp_fingers.SetReference("J_EDGE_FINGERS")
    fp_fingers.SetValue("72P_Gold_Fingers")
    fx = cx # 47.14 mm
    fy = 96.0 # Center at X=47.14, Y=96.0
    fp_fingers.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(96.0)))

    x_start = - (17.5 * PITCH) # 36 fingers: 35 * 2.54 = 88.90mm span

    for i in range(36):
        px = x_start + i * PITCH
        # Front Finger (F.Cu + F.Mask)
        pad_f = pcbnew.PAD(fp_fingers)
        pad_f.SetNumber(f"A{i+1}")
        pad_f.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        pad_f.SetRoundRectRadiusRatio(0.2)
        pad_f.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad_f.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(96.0)))
        pad_f.SetSize(pcbnew.VECTOR2I(mm(PAD_WIDTH), mm(PAD_HEIGHT)))
        lset_f = pcbnew.LSET()
        lset_f.AddLayer(pcbnew.F_Cu)
        lset_f.AddLayer(pcbnew.F_Mask) # Fully exposed gold plating!
        pad_f.SetLayerSet(lset_f)
        fp_fingers.Add(pad_f)

        # Back Finger (B.Cu + B.Mask)
        pad_b = pcbnew.PAD(fp_fingers)
        pad_b.SetNumber(f"B{i+1}")
        pad_b.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        pad_b.SetRoundRectRadiusRatio(0.2)
        pad_b.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad_b.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(96.0)))
        pad_b.SetSize(pcbnew.VECTOR2I(mm(PAD_WIDTH), mm(PAD_HEIGHT)))
        lset_b = pcbnew.LSET()
        lset_b.AddLayer(pcbnew.B_Cu)
        lset_b.AddLayer(pcbnew.B_Mask) # Fully exposed gold plating!
        pad_b.SetLayerSet(lset_b)
        fp_fingers.Add(pad_b)

    # Insertion guideline line on silkscreen (marking 9.0mm insertion depth at Y = 91.0mm)
    silk_line = pcbnew.PCB_SHAPE(fp_fingers)
    silk_line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    silk_line.SetStart(pcbnew.VECTOR2I(mm(fx + x_start - 1.0), mm(91.0)))
    silk_line.SetEnd(pcbnew.VECTOR2I(mm(fx - x_start + 1.0), mm(91.0)))
    silk_line.SetLayer(pcbnew.F_SilkS)
    silk_line.SetWidth(mm(0.2))
    fp_fingers.Add(silk_line)

    b.Add(fp_fingers)
    b.Save(DC_PATH)
    print(f"Saved Exact 72P Daughtercard (94.28x100.0mm): {DC_PATH}")

# =========================================================================
# 5. Build Mechanical Assembly: 100x100 MB + 94.28x100 Blade Plugged In
# =========================================================================
def build_assembly():
    b = pcbnew.BOARD()
    
    # Board Outline: 100.0 x 100.0 mm
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(100), mm(100)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    # Mounting Holes (M3)
    for hx, hy in [(5, 5), (95, 5), (5, 95), (95, 95)]:
        mh = pcbnew.FOOTPRINT(b)
        mh.SetPosition(pcbnew.VECTOR2I(mm(hx), mm(hy)))
        pad = pcbnew.PAD(mh)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(pcbnew.VECTOR2I(mm(5.5), mm(5.5)))
        pad.SetDrillSize(pcbnew.VECTOR2I(mm(3.2), mm(3.2)))
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        mh.Add(pad)
        b.Add(mh)

    # Silkscreen Title
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("COMPLETE ASSEMBLY: 100x100mm BASEBOARD + 94.28x100mm VERTICAL BLADE")
    txt.SetPosition(pcbnew.VECTOR2I(mm(50), mm(14)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.3), mm(1.3)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    # Footprint with both socket and blade attached
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference("J_SLOT1")
    fp.SetValue("72P_Mechanical_Assembly")
    fx = 50.0
    fy = 50.0
    fp.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(fy)))

    x_start = - (17.5 * PITCH)

    for i in range(36):
        px = x_start + i * PITCH
        pad_a = pcbnew.PAD(fp)
        pad_a.SetNumber(f"A{i+1}")
        pad_a.SetShape(pcbnew.PAD_SHAPE_CIRCLE if i > 0 else pcbnew.PAD_SHAPE_RECT)
        pad_a.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad_a.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy - 2.54)))
        pad_a.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        pad_a.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        pad_a.SetLayerSet(pcbnew.LSET.AllCuMask())
        fp.Add(pad_a)

        pad_b = pcbnew.PAD(fp)
        pad_b.SetNumber(f"B{i+1}")
        pad_b.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad_b.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad_b.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy + 2.54)))
        pad_b.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        pad_b.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        pad_b.SetLayerSet(pcbnew.LSET.AllCuMask())
        fp.Add(pad_b)

    # 1. Add Socket 3D Model
    m_sock = pcbnew.FP_3DMODEL()
    m_sock.m_Filename = WRL_SOCKET
    m_sock.m_Scale = pcbnew.VECTOR3D(1.0/2.54, 1.0/2.54, 1.0/2.54)
    fp.Add3DModel(m_sock)

    # 2. Add Daughtercard Blade 3D Model plugged straight into the slot!
    m_blade = pcbnew.FP_3DMODEL()
    m_blade.m_Filename = WRL_BLADE
    m_blade.m_Scale = pcbnew.VECTOR3D(1.0/2.54, 1.0/2.54, 1.0/2.54)
    fp.Add3DModel(m_blade)

    b.Add(fp)
    b.Save(ASM_PATH)
    print(f"Saved Exact 72P Assembly: {ASM_PATH}")

if __name__ == "__main__":
    generate_socket_wrl()
    generate_blade_wrl()
    build_motherboard()
    build_daughtercard()
    build_assembly()
