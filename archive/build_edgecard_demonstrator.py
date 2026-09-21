#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
build_edgecard_demonstrator.py
------------------------------
Generates a complete mechanical test design for the 80-pin 2.54mm Edge Card Connector
from the user's reference image:
1. edge_card_80p.wrl: 3D model of the black straight 80-pin edge connector socket.
2. dc_blade_3d.wrl: 3D model of the daughtercard blade plugged into the socket.
3. test_motherboard_edgecard.kicad_pcb: Motherboard with the 80-pin edge connector slot.
4. test_daughtercard_edgecard.kicad_pcb: 102x100mm Daughtercard blade with 80 gold fingers
   (40 on Front, 40 on Back, pitch 2.54mm, exposed ENIG gold pads, zero soldered components).
5. test_assembly_edgecard.kicad_pcb: Motherboard with the daughtercard plugged vertically into the slot.
"""

import os
import pcbnew
import subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
TEST_DIR = os.path.join(WORKSPACE_DIR, "test_edgecard_system")
os.makedirs(TEST_DIR, exist_ok=True)

WRL_SOCKET = os.path.join(TEST_DIR, "edge_card_80p.wrl")
WRL_BLADE = os.path.join(TEST_DIR, "dc_blade_3d.wrl")
MB_PATH = os.path.join(TEST_DIR, "test_motherboard_edgecard.kicad_pcb")
DC_PATH = os.path.join(TEST_DIR, "test_daughtercard_edgecard.kicad_pcb")
ASM_PATH = os.path.join(TEST_DIR, "test_assembly_edgecard.kicad_pcb")
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def mm(v): return int(v * 1000000)

# =========================================================================
# 1. Generate Realistic 3D Model of the 80P Edge Card Connector Socket
# =========================================================================
def generate_socket_wrl():
    # In KiCad VRML, 1 unit = 2.54 mm (0.1 inch).
    # When m.m_Scale = VECTOR3D(1/2.54, 1/2.54, 1/2.54), coordinates in WRL are in mm!
    wrl = """#VRML V2.0 utf8
# 80-Pin 2.54mm Pitch Straight Edge Card Connector Socket
Transform {
  children [
    # Left side wall of the socket body
    Transform {
      translation 0 2.775 7.75
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }
          }
          geometry Box { size 107.5 3.65 15.5 }
        }
      ]
    },
    # Right side wall of the socket body
    Transform {
      translation 0 -2.775 7.75
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }
          }
          geometry Box { size 107.5 3.65 15.5 }
        }
      ]
    },
    # Left end cap
    Transform {
      translation -52.5 0 7.75
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }
          }
          geometry Box { size 2.5 9.2 15.5 }
        }
      ]
    },
    # Right end cap
    Transform {
      translation 52.5 0 7.75
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.12 0.12 0.12
              specularColor 0.3 0.3 0.3
              shininess 0.35
            }
          }
          geometry Box { size 2.5 9.2 15.5 }
        }
      ]
    },
    # Floor of the slot cavity (leaves 9mm slot depth)
    Transform {
      translation 0 0 3.25
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.08 0.08 0.08
              specularColor 0.2 0.2 0.2
              shininess 0.2
            }
          }
          geometry Box { size 102.5 1.9 6.5 }
        }
      ]
    },
    # Gold Contact Springs inside the slot (visible rows)
    Transform {
      translation 0 0.88 11.0
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }
          }
          geometry Box { size 99.06 0.15 6.0 }
        }
      ]
    },
    Transform {
      translation 0 -0.88 11.0
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }
          }
          geometry Box { size 99.06 0.15 6.0 }
        }
      ]
    },
    # Solder Pins extending down through the PCB (at Y = -2.54 and Y = +2.54)
    Transform {
      translation 0 -2.54 -1.75
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.85 0.85 0.80
              specularColor 0.9 0.9 0.9
              shininess 0.8
            }
          }
          geometry Box { size 99.06 0.64 3.5 }
        }
      ]
    },
    Transform {
      translation 0 2.54 -1.75
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.85 0.85 0.80
              specularColor 0.9 0.9 0.9
              shininess 0.8
            }
          }
          geometry Box { size 99.06 0.64 3.5 }
        }
      ]
    }
  ]
}
"""
    with open(WRL_SOCKET, "w") as f:
        f.write(wrl)
    print(f"Generated Socket 3D WRL: {WRL_SOCKET}")

# =========================================================================
# 2. Generate 3D Model of the Daughtercard Blade Plugged Vertically into Socket
# =========================================================================
def generate_blade_wrl():
    # Daughtercard PCB blade: 102mm wide x 1.6mm thick x 100mm high.
    # The slot floor is at Z = 6.5mm, so the bottom of the card is at Z = 6.5mm.
    # Center of card in Z = 6.5 + 50.0 = 56.5mm.
    wrl = """#VRML V2.0 utf8
# Daughtercard Blade standing vertically in Edge Connector Slot
Transform {
  children [
    # Green FR4 PCB Blade
    Transform {
      translation 0 0 56.5
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.08 0.32 0.18
              specularColor 0.3 0.4 0.3
              shininess 0.5
            }
          }
          geometry Box { size 102.0 1.6 100.0 }
        }
      ]
    },
    # White Silkscreen Banner on Daughtercard
    Transform {
      translation 0 0.82 70.0
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.9 0.9 0.9
              specularColor 0.5 0.5 0.5
              shininess 0.2
            }
          }
          geometry Box { size 90.0 0.05 18.0 }
        }
      ]
    },
    # Gold Contact Fingers (Front Row wiping inside the socket contacts)
    Transform {
      translation 0 0.81 10.25
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }
          }
          geometry Box { size 99.06 0.05 7.5 }
        }
      ]
    },
    # Gold Contact Fingers (Back Row wiping inside the socket contacts)
    Transform {
      translation 0 -0.81 10.25
      children [
        Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.85 0.70 0.20
              specularColor 0.95 0.90 0.60
              shininess 0.9
            }
          }
          geometry Box { size 99.06 0.05 7.5 }
        }
      ]
    }
  ]
}
"""
    with open(WRL_BLADE, "w") as f:
        f.write(wrl)
    print(f"Generated Blade 3D WRL: {WRL_BLADE}")

# =========================================================================
# 3. Build Motherboard with 80P Edge Card Connector Slot
# =========================================================================
def build_motherboard():
    b = pcbnew.BOARD()
    
    # Board Outline: 130 x 80 mm
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(130), mm(80)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    # Mounting Holes (M3)
    for hx, hy in [(5, 5), (125, 5), (5, 75), (125, 75)]:
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
    txt.SetText("MOTHERBOARD: 80-PIN 2.54mm STRAIGHT EDGE CONNECTOR")
    txt.SetPosition(pcbnew.VECTOR2I(mm(65), mm(12)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.8), mm(1.8)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    txt2 = pcbnew.PCB_TEXT(b)
    txt2.SetText("Vertical Insertion Slot (Daughtercard Blade Slides Straight Down)")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(65), mm(18)))
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt2.SetLayer(pcbnew.F_SilkS)
    b.Add(txt2)

    # 80P Edge Card Footprint: 2 rows of 40 pins, pitch 2.54mm, row spacing 5.08mm
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference("J_SLOT1")
    fp.SetValue("EdgeCard_80P_2.54mm_Straight")
    fx = 65.0
    fy = 45.0
    fp.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(fy)))

    pitch = 2.54
    x_start = - (19.5 * pitch) # 40 pins: 39 * 2.54 = 99.06mm span

    for i in range(40):
        px = x_start + i * pitch
        # Row A (Y = -2.54)
        pad_a = pcbnew.PAD(fp)
        pad_a.SetNumber(f"A{i+1}")
        pad_a.SetShape(pcbnew.PAD_SHAPE_CIRCLE if i > 0 else pcbnew.PAD_SHAPE_RECT)
        pad_a.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad_a.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy - 2.54)))
        pad_a.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        pad_a.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        pad_a.SetLayerSet(pcbnew.LSET.AllCuMask())
        fp.Add(pad_a)

        # Row B (Y = +2.54)
        pad_b = pcbnew.PAD(fp)
        pad_b.SetNumber(f"B{i+1}")
        pad_b.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad_b.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad_b.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy + 2.54)))
        pad_b.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
        pad_b.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        pad_b.SetLayerSet(pcbnew.LSET.AllCuMask())
        fp.Add(pad_b)

    # Footprint Courtyard / Silk Outline
    fp_line = pcbnew.PCB_SHAPE(fp)
    fp_line.SetShape(pcbnew.SHAPE_T_RECT)
    fp_line.SetStart(pcbnew.VECTOR2I(mm(fx - 53.75), mm(fy - 4.6)))
    fp_line.SetEnd(pcbnew.VECTOR2I(mm(fx + 53.75), mm(fy + 4.6)))
    fp_line.SetLayer(pcbnew.F_SilkS)
    fp_line.SetWidth(mm(0.15))
    fp.Add(fp_line)

    # Attach 3D Model of the Socket with proper 1/2.54 scale
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = WRL_SOCKET
    m.m_Scale = pcbnew.VECTOR3D(1.0/2.54, 1.0/2.54, 1.0/2.54)
    fp.Add3DModel(m)

    b.Add(fp)
    b.Save(MB_PATH)
    print(f"Saved Motherboard: {MB_PATH}")

# =========================================================================
# 4. Build Daughtercard Blade with 80 Gold Fingers (PCB Edge Connector)
# =========================================================================
def build_daughtercard():
    b = pcbnew.BOARD()

    # Board Outline: 102 x 100 mm (Standard Eurocard height 100mm)
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(102), mm(100)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)

    # M3 Mounting / Pull Holes at top corners
    for hx, hy in [(5, 5), (97, 5)]:
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
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("DAUGHTERCARD BLADE (NO SOLDERED CONNECTOR)")
    txt.SetPosition(pcbnew.VECTOR2I(mm(51), mm(25)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(2.0), mm(2.0)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    txt2 = pcbnew.PCB_TEXT(b)
    txt2.SetText("Direct PCB Edge Gold Fingers (80 Contacts: 40 Front + 40 Back)")
    txt2.SetPosition(pcbnew.VECTOR2I(mm(51), mm(34)))
    txt2.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt2.SetLayer(pcbnew.F_SilkS)
    b.Add(txt2)

    txt3 = pcbnew.PCB_TEXT(b)
    txt3.SetText("Slides Straight Down into Motherboard 80P Edge Card Slot")
    txt3.SetPosition(pcbnew.VECTOR2I(mm(51), mm(42)))
    txt3.SetTextSize(pcbnew.VECTOR2I(mm(1.4), mm(1.4)))
    txt3.SetLayer(pcbnew.F_SilkS)
    b.Add(txt3)

    txt4 = pcbnew.PCB_TEXT(b)
    txt4.SetText("<< INSERTION STOP LINE (9mm Socket Depth) >>")
    txt4.SetPosition(pcbnew.VECTOR2I(mm(51), mm(89.5)))
    txt4.SetTextSize(pcbnew.VECTOR2I(mm(1.1), mm(1.1)))
    txt4.SetLayer(pcbnew.F_SilkS)
    b.Add(txt4)

    # Gold Fingers Footprint:
    # 40 fingers on F.Cu and 40 fingers on B.Cu along Y = 100mm bottom edge!
    # Pitch: 2.54mm, Pad size: 1.5mm wide x 7.5mm high
    fp_fingers = pcbnew.FOOTPRINT(b)
    fp_fingers.SetReference("J_EDGE_FINGERS")
    fp_fingers.SetValue("80P_Gold_Fingers")
    fx = 51.0
    fy = 96.25 # Center at X=51, Y=96.25 (fingers reach exactly to Y=100.0mm edge)
    fp_fingers.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(fy)))

    pitch = 2.54
    x_start = - (19.5 * pitch)

    for i in range(40):
        px = x_start + i * pitch
        # Front Finger (F.Cu + F.Mask)
        pad_f = pcbnew.PAD(fp_fingers)
        pad_f.SetNumber(f"A{i+1}")
        pad_f.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        pad_f.SetRoundRectRadiusRatio(0.2)
        pad_f.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad_f.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy)))
        pad_f.SetSize(pcbnew.VECTOR2I(mm(1.5), mm(7.5)))
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
        pad_b.SetPosition(pcbnew.VECTOR2I(mm(fx + px), mm(fy)))
        pad_b.SetSize(pcbnew.VECTOR2I(mm(1.5), mm(7.5)))
        lset_b = pcbnew.LSET()
        lset_b.AddLayer(pcbnew.B_Cu)
        lset_b.AddLayer(pcbnew.B_Mask) # Fully exposed gold plating!
        pad_b.SetLayerSet(lset_b)
        fp_fingers.Add(pad_b)

    # Insertion guideline line on silkscreen (marking the 9mm socket lip)
    silk_line = pcbnew.PCB_SHAPE(fp_fingers)
    silk_line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    silk_line.SetStart(pcbnew.VECTOR2I(mm(fx + x_start - 1.0), mm(fy - 5.25)))
    silk_line.SetEnd(pcbnew.VECTOR2I(mm(fx - x_start + 1.0), mm(fy - 5.25)))
    silk_line.SetLayer(pcbnew.F_SilkS)
    silk_line.SetWidth(mm(0.2))
    fp_fingers.Add(silk_line)

    b.Add(fp_fingers)
    b.Save(DC_PATH)
    print(f"Saved Daughtercard: {DC_PATH}")

# =========================================================================
# 5. Build Assembled Design (Motherboard with Daughtercard Blade Plugged In)
# =========================================================================
def build_assembly():
    b = pcbnew.BOARD()
    
    # Board Outline: 130 x 80 mm
    gr = pcbnew.PCB_SHAPE(b)
    gr.SetShape(pcbnew.SHAPE_T_RECT)
    gr.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
    gr.SetEnd(pcbnew.VECTOR2I(mm(130), mm(80)))
    gr.SetLayer(pcbnew.Edge_Cuts)
    gr.SetWidth(mm(0.15))
    b.Add(gr)
    
    # Mounting Holes (M3)
    for hx, hy in [(5, 5), (125, 5), (5, 75), (125, 75)]:
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
    txt.SetText("COMPLETE MECHANICAL ASSEMBLY: MOTHERBOARD + VERTICAL BLADE")
    txt.SetPosition(pcbnew.VECTOR2I(mm(65), mm(10)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
    txt.SetLayer(pcbnew.F_SilkS)
    b.Add(txt)

    # 80P Edge Card Footprint with BOTH socket and daughtercard blade plugged in!
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference("J_SLOT1")
    fp.SetValue("EdgeCard_80P_Assembly")
    fx = 65.0
    fy = 45.0
    fp.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(fy)))

    pitch = 2.54
    x_start = - (19.5 * pitch)

    for i in range(40):
        px = x_start + i * pitch
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
    print(f"Saved Assembly: {ASM_PATH}")

if __name__ == "__main__":
    generate_socket_wrl()
    generate_blade_wrl()
    build_motherboard()
    build_daughtercard()
    build_assembly()
