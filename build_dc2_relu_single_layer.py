#!/usr/bin/env python3
"""
build_dc2_relu_single_layer.py
------------------------------
Generates daughtercard2_relu_l1.kicad_pcb as a strictly SINGLE LAYER (F.Cu)
home-etchable board (100x100mm, 0 B.Cu, 0 inner layers, 0 vias).
16-channel Active Precision Half-Wave Rectifier (ReLU):
- 4x TL074 quad op-amps (SOIC-14)
- 16x Rin 10k 0805, 16x Rfb 10k 0805
- 32x 1N4148 diodes (SOD-123)
- 4x 100nF decoupling capacitors (0805)
- J_IN 1x16 2.54mm pin header (V_SUM_0..15)
- J_OUT 1x16 2.54mm pin header (ACT_0..15)
- J_PWR 1x4 2.54mm pin header (+12V, -12V, GND, NC)
- 4x M3 mounting holes (3.2mm)
- Trace width: 0.4mm (signals), 0.6mm (power/GND)
- Clearance >= 0.5mm everywhere
"""

import os
import sys
import uuid
import subprocess

def make_uuid():
    return str(uuid.uuid4())

BOARD_W = 100.0
BOARD_H = 100.0

def generate_dc2_board(output_path="daughtercard2_relu_l1.kicad_pcb"):
    nets = {
        0: "",
        1: "GND",
        2: "+12V",
        3: "-12V"
    }
    net_id = 10
    for ch in range(16):
        nets[net_id] = f"V_SUM_{ch}"
        nets[net_id + 1] = f"ACT_{ch}"
        nets[net_id + 2] = f"INV_IN_{ch}"
        nets[net_id + 3] = f"OP_OUT_{ch}"
        net_id += 4

    net_map = {name: nid for nid, name in nets.items() if name}

    # S-Expression Elements
    footprints = []
    tracks = []
    shapes = []

    # 1. Edge.Cuts Outline
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)]
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[i+1]
        shapes.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type default)) (layer "Edge.Cuts") (uuid "{make_uuid()}"))')

    # 2. Mounting Holes (M3, 4mm inset)
    for idx, (hx, hy) in enumerate([(4.0, 4.0), (BOARD_W - 4.0, 4.0), (4.0, BOARD_H - 4.0), (BOARD_W - 4.0, BOARD_H - 4.0)]):
        footprints.append(f"""  (footprint "MountingHole:MountingHole_3.2mm_M3" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {hx:.2f} {hy:.2f})
    (property "Reference" "MH{idx+1}" (at 0 -2.5 0) (layer "F.SilkS") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "MountingHole_3.2mm" (at 0 2.5 0) (layer "F.Fab") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.12))))
    (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask"))
  )""")

    # 3. Connectors:
    # J_IN: 1x16 Header at Left (X = 6.5mm, Y = 18..56.1mm)
    jin_pads = []
    for i in range(16):
        py = 18.0 + i * 2.54
        nname = f"V_SUM_{i}"
        nid = net_map[nname]
        shape = "rect" if i == 0 else "circle"
        jin_pads.append(f'    (pad "{i+1}" thru_hole {shape} (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net {nid} "{nname}") (uuid "{make_uuid()}"))')
    jin_pads_str = "\n".join(jin_pads)
    footprints.append(f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x16_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at 6.5 18.0)
    (descr "1x16 2.54mm pin header for V_SUM inputs")
    (property "Reference" "J_IN" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "V_SUM_IN" (at 0 41.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{jin_pads_str}
  )""")

    # J_OUT: 1x16 Header at Right (X = 93.5mm, Y = 18..56.1mm)
    jout_pads = []
    for i in range(16):
        py = 18.0 + i * 2.54
        nname = f"ACT_{i}"
        nid = net_map[nname]
        shape = "rect" if i == 0 else "circle"
        jout_pads.append(f'    (pad "{i+1}" thru_hole {shape} (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net {nid} "{nname}") (uuid "{make_uuid()}"))')
    jout_pads_str = "\n".join(jout_pads)
    footprints.append(f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x16_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at 93.5 18.0)
    (descr "1x16 2.54mm pin header for ACT outputs")
    (property "Reference" "J_OUT" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "ACT_OUT" (at 0 41.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{jout_pads_str}
  )""")

    # J_PWR: 1x4 Header at Bottom Center (X = 50.0, Y = 92.0)
    jpwr_pads = []
    pwr_list = [("+12V", 2), ("-12V", 3), ("GND", 1), ("GND", 1)]
    for i, (pname, pid) in enumerate(pwr_list):
        shape = "rect" if i == 0 else "circle"
        jpwr_pads.append(f'    (pad "{i+1}" thru_hole {shape} (at {i*2.54:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net {pid} "{pname}") (uuid "{make_uuid()}"))')
    jpwr_pads_str = "\n".join(jpwr_pads)
    footprints.append(f"""  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at 46.19 92.0)
    (descr "1x04 2.54mm pin header for Power (+12V, -12V, GND)")
    (property "Reference" "J_PWR" (at 3.81 -2.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "POWER" (at 3.81 2.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{jpwr_pads_str}
  )""")

    # 4. Rectifier Channels: 16 channels arranged in 4 vertical groups (one quad TL074 per 4 channels)
    # TL074 pinout:
    # Op1: Out=1, In-=2, In+=3
    # VCC+: 4 (+12V)
    # Op2: In+=5, In-=6, Out=7
    # Op3: Out=8, In-=9, In+=10
    # VCC-: 11 (-12V)
    # Op4: In+=12, In-=13, Out=14

    tl074_units = [
        (1, 2, 3),   # Op 1: Out, In-, In+
        (7, 6, 5),   # Op 2: Out, In-, In+
        (8, 9, 10),  # Op 3: Out, In-, In+
        (14, 13, 12) # Op 4: Out, In-, In+
    ]

    # Helper: add resistor 0805
    def add_resistor(ref, val, x, y, rot, net1_name, net2_name):
        n1 = net_map[net1_name]
        n2 = net_map[net2_name]
        footprints.append(f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.2f} {y:.2f} {rot})
    (descr "Resistor SMD 0805 (2012 Metric)")
    (property "Reference" "{ref}" (at 0 -1.5 0) (layer "F.SilkS") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 0) (layer "F.Fab") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -0.9125 0) (size 1.025 1.4) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net {n1} "{net1_name}") (uuid "{make_uuid()}"))
    (pad "2" smd roundrect (at 0.9125 0) (size 1.025 1.4) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net {n2} "{net2_name}") (uuid "{make_uuid()}"))
  )""")

    # Helper: add diode SOD-123 (Pad 1=Cathode, Pad 2=Anode)
    def add_diode(ref, val, x, y, rot, net_k_name, net_a_name):
        nk = net_map[net_k_name]
        na = net_map[net_a_name]
        footprints.append(f"""  (footprint "Diode_SMD:D_SOD-123" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.2f} {y:.2f} {rot})
    (descr "Diode SOD-123")
    (property "Reference" "{ref}" (at 0 -1.5 0) (layer "F.SilkS") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (property "Value" "{val}" (at 0 1.5 0) (layer "F.Fab") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" smd roundrect (at -1.65 0) (size 0.9 1.2) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net {nk} "{net_k_name}") (uuid "{make_uuid()}"))
    (pad "2" smd roundrect (at 1.65 0) (size 0.9 1.2) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net {na} "{net_a_name}") (uuid "{make_uuid()}"))
  )""")

    # Helper: add jumper wire
    def add_jumper(ref, val, x, y, length_mm, rot, net_name):
        nid = net_map[net_name]
        hl = length_mm / 2.0
        footprints.append(f"""  (footprint "Jumper_Wire" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.2f} {y:.2f} {rot})
    (property "Reference" "{ref}" (at 2.0 0 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "{val}" (at 0 2.0 0) (layer "F.Fab") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Keywords" "net tie" (layer "F.Fab") (hide yes) (effects (font (size 0.5 0.5) (thickness 0.05))))
    (net_tie_pad_groups "1,2")
    (pad "1" thru_hole circle (at 0 -{hl:.2f}) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net {nid} "{net_name}") (uuid "{make_uuid()}"))
    (pad "2" thru_hole circle (at 0 {hl:.2f}) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net {nid} "{net_name}") (uuid "{make_uuid()}"))
    (fp_line (start 0 -{hl - 1.2:.2f}) (end 0 {hl - 1.2:.2f}) (stroke (width 0.2) (type solid)) (layer "F.SilkS"))
  )""")

    # Helper: add SOIC-14 TL074
    def add_tl074(ref, x, y, rot, pin_net_dict):
        pads = []
        y_starts = [-3.81, -2.54, -1.27, 0.0, 1.27, 2.54, 3.81]
        # Left pins 1..7
        for i in range(7):
            pnum = str(i + 1)
            py = y_starts[i]
            nname = pin_net_dict.get(pnum, "GND")
            nid = net_map.get(nname, 1)
            pads.append(f'    (pad "{pnum}" smd roundrect (at -2.70 {py:.3f}) (size 1.55 0.6) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net {nid} "{nname}") (uuid "{make_uuid()}"))')
        # Right pins 14..8
        for i in range(7):
            pnum = str(14 - i)
            py = y_starts[i]
            nname = pin_net_dict.get(pnum, "GND")
            nid = net_map.get(nname, 1)
            pads.append(f'    (pad "{pnum}" smd roundrect (at 2.70 {py:.3f}) (size 1.55 0.6) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net {nid} "{nname}") (uuid "{make_uuid()}"))')
        pads_str = "\n".join(pads)
        footprints.append(f"""  (footprint "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm" (layer "F.Cu")
    (uuid "{make_uuid()}")
    (at {x:.2f} {y:.2f} {rot})
    (property "Reference" "{ref}" (at 0 -5.2 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "TL074" (at 0 5.2 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
{pads_str}
  )""")

    # 4 Quad TL074 locations:
    # Group 0 (Ch 0..3):   Y center ~ 20.0
    # Group 1 (Ch 4..7):   Y center ~ 38.0
    # Group 2 (Ch 8..11):  Y center ~ 56.0
    # Group 3 (Ch 12..15): Y center ~ 74.0
    group_y = [20.0, 38.0, 56.0, 74.0]

    for g, cy in enumerate(group_y):
        u_ref = f"U{g+1}"
        tl_x = 50.0
        tl_y = cy
        
        # Build pin net dictionary for this TL074
        # Ch 4*g + 0 -> unit 0 (pins 1,2,3)
        # Ch 4*g + 1 -> unit 1 (pins 7,6,5)
        # Ch 4*g + 2 -> unit 2 (pins 8,9,10)
        # Ch 4*g + 3 -> unit 3 (pins 14,13,12)
        ch0 = 4 * g
        ch1 = 4 * g + 1
        ch2 = 4 * g + 2
        ch3 = 4 * g + 3

        pdict = {
            "1": f"OP_OUT_{ch0}",
            "2": f"INV_IN_{ch0}",
            "3": "GND",
            "4": "+12V",
            "5": "GND",
            "6": f"INV_IN_{ch1}",
            "7": f"OP_OUT_{ch1}",
            "8": f"OP_OUT_{ch2}",
            "9": f"INV_IN_{ch2}",
            "10": "GND",
            "11": "-12V",
            "12": "GND",
            "13": f"INV_IN_{ch3}",
            "14": f"OP_OUT_{ch3}"
        }
        add_tl074(u_ref, tl_x, tl_y, 0, pdict)

        # Decoupling Caps for this IC (at X = 50.0, Y = cy - 6.5 and cy + 6.5)
        add_resistor(f"C_{g+1}_POS", "100n", tl_x - 5.5, cy - 6.0, 90, "+12V", "GND")
        add_resistor(f"C_{g+1}_NEG", "100n", tl_x + 5.5, cy + 6.0, 90, "-12V", "GND")

        # Place the 4 channels around the IC:
        # Each channel has:
        # Rin: V_SUM_ch -> INV_IN_ch
        # D_fb: Cathode=OP_OUT_ch, Anode=INV_IN_ch
        # D_out: Anode=OP_OUT_ch, Cathode=ACT_ch
        # Rfb: INV_IN_ch -> ACT_ch

        channels = [
            (ch0, cy - 3.81, -1), # Left top
            (ch1, cy + 2.54, -1), # Left bottom
            (ch2, cy + 2.54, +1), # Right bottom
            (ch3, cy - 3.81, +1), # Right top
        ]

        for ch_idx, py, side in channels:
            # Side -1 = West (pins 1,2 or 6,7), Side +1 = East (pins 8,9 or 13,14)
            rx_in = tl_x + side * 18.0
            rx_fb = tl_x + side * 24.0
            dx_fb = tl_x + side * 12.0
            dx_out = tl_x + side * 30.0

            add_resistor(f"R_IN_{ch_idx}", "10k", rx_in, py, 0, f"V_SUM_{ch_idx}", f"INV_IN_{ch_idx}")
            add_resistor(f"R_FB_{ch_idx}", "10k", rx_fb, py, 0, f"INV_IN_{ch_idx}", f"ACT_{ch_idx}")
            # D_fb: K=OP_OUT, A=INV_IN
            add_diode(f"D_FB_{ch_idx}", "1N4148", dx_fb, py, 0 if side < 0 else 180, f"OP_OUT_{ch_idx}", f"INV_IN_{ch_idx}")
            # D_out: A=OP_OUT, K=ACT
            add_diode(f"D_OUT_{ch_idx}", "1N4148", dx_out, py, 180 if side < 0 else 0, f"ACT_{ch_idx}", f"OP_OUT_{ch_idx}")

    # Build Header and Net Definitions
    net_defs = "\n".join([f'  (net {nid} "{name}")' for nid, name in sorted(nets.items()) if name])

    footprints_str = "\n".join(footprints)
    shapes_str = "\n".join(shapes)

    content = f"""(kicad_pcb
  (version 20240108)
  (generator "pcbnew")
  (generator_version "10.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "USLetter")
  (title_block
    (title "Daughtercard 2: Layer 1 Precision Half-Wave Active Rectifiers (16x ReLU)")
    (date "2026-10-03")
    (rev "v2.0-SingleLayer")
    (company "Discrete Analog MNIST System")
  )
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "B.Paste" user)
    (41 "F.Paste" user)
    (44 "Edge.Cuts" user)
  )
  (setup
    (pad_to_mask_clearance 0)
    (pcbplotparams
      (layerselection 0x00000000_00000000_55555555_5755f5ff)
      (plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (pdf_front_fp_property_popups yes)
      (pdf_back_fp_property_popups yes)
      (dxfpadmode 1)
      (dxfqualifier 1)
      (dxftolabelwidth 0)
      (dxfpttolerance 0.001000)
      (dxfsubparts yes)
    )
  )
{net_defs}

{footprints_str}

{shapes_str}
)"""

    with open(output_path, "w") as f:
        f.write(content)
    print(f"Generated {output_path}")
    return output_path

if __name__ == "__main__":
    generate_dc2_board()
