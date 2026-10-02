#!/usr/bin/env python3
"""
Generate ultra-photorealistic VRML models for all 6 daughtercard blades
with discrete straddle-mount male pin headers, and assemble the full 6-blade
modular analog neural network cube.
"""
import os
import re

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"

def vrml_material(diffuse=(0.8, 0.8, 0.8), specular=(0.5, 0.5, 0.5), shininess=0.5, emissive=(0.0, 0.0, 0.0)):
    d_str = f"{diffuse[0]:.2f} {diffuse[1]:.2f} {diffuse[2]:.2f}"
    s_str = f"{specular[0]:.2f} {specular[1]:.2f} {specular[2]:.2f}"
    e_str = f"{emissive[0]:.2f} {emissive[1]:.2f} {emissive[2]:.2f}"
    return f"""appearance Appearance {{
            material Material {{
              diffuseColor {d_str}
              specularColor {s_str}
              shininess {shininess:.2f}
              emissiveColor {e_str}
            }}
          }}"""

def vrml_box(x, y, z, sx, sy, sz, mat_str):
    return f"""    Transform {{
      translation {x:.3f} {y:.3f} {z:.3f}
      children [
        Shape {{
          {mat_str}
          geometry Box {{ size {sx:.3f} {sy:.3f} {sz:.3f} }}
        }}
      ]
    }}"""

def vrml_cylinder(x, y, z, radius, height, mat_str, rot_str=None):
    rot = f"\n      rotation {rot_str}" if rot_str else ""
    return f"""    Transform {{
      translation {x:.3f} {y:.3f} {z:.3f}{rot}
      children [
        Shape {{
          {mat_str}
          geometry Cylinder {{ radius {radius:.3f} height {height:.3f} }}
        }}
      ]
    }}"""

# Predefined materials
MAT_PCB_FR4 = vrml_material((0.04, 0.25, 0.12), (0.35, 0.45, 0.35), 0.65)
MAT_SILK_WHITE = vrml_material((0.95, 0.95, 0.95), (0.4, 0.4, 0.4), 0.2)
MAT_COPPER_GOLD = vrml_material((0.85, 0.70, 0.22), (0.95, 0.85, 0.50), 0.85)
MAT_HEADER_BLACK = vrml_material((0.10, 0.10, 0.10), (0.35, 0.35, 0.35), 0.45)
MAT_SOLDER_TIN = vrml_material((0.88, 0.88, 0.90), (0.98, 0.98, 0.98), 0.92)
MAT_GOLD_PIN = vrml_material((0.90, 0.78, 0.28), (0.98, 0.92, 0.60), 0.95)
MAT_IC_BLACK = vrml_material((0.15, 0.15, 0.15), (0.30, 0.30, 0.30), 0.50)
MAT_RES_BODY = vrml_material((0.18, 0.18, 0.20), (0.30, 0.30, 0.30), 0.40)
MAT_CAP_BODY = vrml_material((0.65, 0.52, 0.38), (0.40, 0.35, 0.30), 0.40)
MAT_POT_BLUE = vrml_material((0.05, 0.28, 0.75), (0.40, 0.55, 0.85), 0.70)
MAT_POT_BRASS = vrml_material((0.85, 0.72, 0.25), (0.95, 0.90, 0.55), 0.90)

# Glowing LED materials
MAT_LED_GREEN = vrml_material((0.1, 0.9, 0.2), (0.8, 1.0, 0.8), 0.9, emissive=(0.2, 0.8, 0.2))
MAT_LED_RED   = vrml_material((0.9, 0.1, 0.1), (1.0, 0.8, 0.8), 0.9, emissive=(0.8, 0.1, 0.1))
MAT_LED_AMBER = vrml_material((0.95, 0.65, 0.1), (1.0, 0.9, 0.6), 0.9, emissive=(0.9, 0.55, 0.1))
MAT_LED_BLUE  = vrml_material((0.1, 0.3, 0.95), (0.6, 0.8, 1.0), 0.9, emissive=(0.1, 0.3, 0.9))
MAT_LED_DIM   = vrml_material((0.3, 0.25, 0.15), (0.2, 0.2, 0.2), 0.3, emissive=(0.0, 0.0, 0.0))

def generate_straddle_header_shapes():
    """Generate the 76-pin straddle header clamping the PCB edge."""
    shapes = []
    # 1. Thermoplastic insulator body spanning Z = 8.5 to 11.0mm
    shapes.append(vrml_box(0, 0, 9.75, 97.50, 5.00, 2.50, MAT_HEADER_BLACK))

    # 2. 38 Pairs of discrete solder clamping legs on F.Cu (+Y) and B.Cu (-Y)
    # PCB edge enters down to Z = 10.5mm. Solder clamps run Z = 10.5 to 15.0mm (height 4.5mm)
    for i in range(38):
        px = -46.99 + i * 2.54
        # Front solder clamp (+Y, F.Cu)
        shapes.append(vrml_box(px, 1.02, 12.75, 0.64, 0.44, 4.50, MAT_SOLDER_TIN))
        # Back solder clamp (-Y, B.Cu)
        shapes.append(vrml_box(px, -1.02, 12.75, 0.64, 0.44, 4.50, MAT_SOLDER_TIN))
        # Solder fillets on pads
        shapes.append(vrml_box(px, 0.95, 12.00, 0.90, 0.30, 2.50, MAT_SOLDER_TIN))
        shapes.append(vrml_box(px, -0.95, 12.00, 0.90, 0.30, 2.50, MAT_SOLDER_TIN))

        # 3. Gold mating pins projecting downward into motherboard female socket (Z = 2.5 to 8.5mm)
        # Row B (+Y = +1.27mm)
        shapes.append(vrml_box(px, 1.27, 5.50, 0.64, 0.64, 6.00, MAT_GOLD_PIN))
        # Row A (-Y = -1.27mm)
        shapes.append(vrml_box(px, -1.27, 5.50, 0.64, 0.64, 6.00, MAT_GOLD_PIN))

    return shapes

def add_soic14(shapes, cx, cz, label="LM324", y_face=1):
    """SOIC-14 op-amp on F.Cu (+Y) or B.Cu (-Y)."""
    y_body = 1.60 * y_face
    y_silk = 2.41 * y_face
    y_lead = 1.10 * y_face
    # Plastic molded body: length=8.65 (X), height=1.6 (Y), width=3.9 (Z)
    shapes.append(vrml_box(cx, y_body, cz, 8.65, 1.60, 3.90, MAT_IC_BLACK))
    # Pin 1 indicator dot
    shapes.append(vrml_cylinder(cx - 3.2, y_silk, cz - 1.0, 0.4, 0.02, MAT_SILK_WHITE, "1 0 0 1.5708"))
    # IC white text marking bar
    shapes.append(vrml_box(cx, y_silk, cz, 5.5, 0.02, 1.2, MAT_SILK_WHITE))
    # 14 Gullwing leads
    for p in range(7):
        lx = cx - 3.81 + p * 1.27
        # Top row leads (+Z = cz + 2.5)
        shapes.append(vrml_box(lx, y_lead, cz + 2.4, 0.45, 0.60, 1.10, MAT_SOLDER_TIN))
        # Bottom row leads (-Z = cz - 2.5)
        shapes.append(vrml_box(lx, y_lead, cz - 2.4, 0.45, 0.60, 1.10, MAT_SOLDER_TIN))

def add_trimpot_bourns(shapes, cx, cz, y_face=1):
    """Bourns 3296W multi-turn cermet potentiometer."""
    y_body = 3.20 * y_face
    y_screw = 5.65 * y_face
    y_silk = 5.61 * y_face
    # Blue body: 9.5mm (X) x 4.8mm (Y) x 9.5mm (Z)
    shapes.append(vrml_box(cx, y_body, cz, 9.50, 4.80, 9.50, MAT_POT_BLUE))
    # Brass top adjustment screw
    shapes.append(vrml_cylinder(cx + 2.2, y_screw, cz, 1.20, 0.30, MAT_POT_BRASS, "1 0 0 1.5708"))
    # White adjustment pointer triangle
    shapes.append(vrml_box(cx - 2.0, y_silk, cz, 2.5, 0.02, 0.8, MAT_SILK_WHITE))

def add_resistor_0805(shapes, cx, cz, orient="H", y_face=1):
    """0805 SMD resistor (2.0 x 1.25 x 0.6mm) on PCB."""
    y_body = 1.10 * y_face
    if orient == "H":
        shapes.append(vrml_box(cx, y_body, cz, 1.20, 0.55, 1.25, MAT_RES_BODY))
        shapes.append(vrml_box(cx - 0.80, y_body, cz, 0.40, 0.58, 1.25, MAT_SOLDER_TIN))
        shapes.append(vrml_box(cx + 0.80, y_body, cz, 0.40, 0.58, 1.25, MAT_SOLDER_TIN))
    else:
        shapes.append(vrml_box(cx, y_body, cz, 1.25, 0.55, 1.20, MAT_RES_BODY))
        shapes.append(vrml_box(cx, y_body, cz - 0.80, 1.25, 0.58, 0.40, MAT_SOLDER_TIN))
        shapes.append(vrml_box(cx, y_body, cz + 0.80, 1.25, 0.58, 0.40, MAT_SOLDER_TIN))

def add_capacitor_0805(shapes, cx, cz, orient="H", y_face=1):
    """0805 MLCC ceramic capacitor."""
    y_body = 1.10 * y_face
    if orient == "H":
        shapes.append(vrml_box(cx, y_body, cz, 1.20, 0.60, 1.25, MAT_CAP_BODY))
        shapes.append(vrml_box(cx - 0.80, y_body, cz, 0.40, 0.62, 1.25, MAT_SOLDER_TIN))
        shapes.append(vrml_box(cx + 0.80, y_body, cz, 0.40, 0.62, 1.25, MAT_SOLDER_TIN))
    else:
        shapes.append(vrml_box(cx, y_body, cz, 1.25, 0.60, 1.20, MAT_CAP_BODY))
        shapes.append(vrml_box(cx, y_body, cz - 0.80, 1.25, 0.62, 0.40, MAT_SOLDER_TIN))
        shapes.append(vrml_box(cx, y_body, cz + 0.80, 1.25, 0.62, 0.40, MAT_SOLDER_TIN))

def add_led_0805(shapes, cx, cz, mat_led, y_face=1):
    """0805 SMD LED with clear/glowing lens."""
    y_base = 0.95 * y_face
    y_lens = 1.30 * y_face
    shapes.append(vrml_box(cx, y_base, cz, 1.25, 0.30, 2.00, MAT_RES_BODY))
    shapes.append(vrml_box(cx, y_lens, cz, 1.10, 0.50, 1.40, mat_led))

def add_sod123_diode(shapes, cx, cz, y_face=1):
    """SOD-123 high speed switching diode."""
    y_body = 1.35 * y_face
    y_band = 1.36 * y_face
    y_lead = 1.05 * y_face
    shapes.append(vrml_box(cx, y_body, cz, 1.60, 1.10, 2.60, MAT_IC_BLACK))
    shapes.append(vrml_box(cx, y_band, cz - 0.80, 1.62, 1.12, 0.45, MAT_SILK_WHITE))
    shapes.append(vrml_box(cx, y_lead, cz - 1.50, 0.90, 0.40, 0.50, MAT_SOLDER_TIN))
    shapes.append(vrml_box(cx, y_lead, cz + 1.50, 0.90, 0.40, 0.50, MAT_SOLDER_TIN))


def build_blade_dc1(filename, title_text, neurons_str):
    """Build Layer 1 Synaptic Weight Daughtercard (DC1A..DC1D)."""
    shapes = []
    # 1. Main PCB Substrate: 100mm (X) x 1.6mm (Y) x 100mm (Z), Z = 10.5 to 110.5mm
    shapes.append(vrml_box(0, 0, 60.50, 100.00, 1.60, 100.00, MAT_PCB_FR4))

    # 2. Silkscreen Title Banner on F.Cu at top
    shapes.append(vrml_box(0, 0.81, 106.00, 94.00, 0.02, 5.00, MAT_SILK_WHITE))
    shapes.append(vrml_box(0, 0.81, 101.50, 70.00, 0.02, 2.50, MAT_SILK_WHITE))

    # 3. Straddle-Mount Pin Header Clamping Bottom Edge
    shapes.extend(generate_straddle_header_shapes())

    # 4. Four Precision Summing Op-Amps (LM324 SOIC-14) across X
    ic_xs = [-30.0, -10.0, 10.0, 30.0]
    for x in ic_xs:
        add_soic14(shapes, x, 85.0, "LM324ADR", y_face=1)
        add_capacitor_0805(shapes, x + 6.0, 85.0, "V", y_face=1)
        add_capacitor_0805(shapes, x - 6.0, 85.0, "V", y_face=1)

    # 5. Four Bourns 3296W Precision Bias Trimpots above op-amps
    for x in ic_xs:
        add_trimpot_bourns(shapes, x, 96.0, y_face=1)

    # 6. Dense Matrix of 256 Precision Synaptic Weight Resistors (0805)
    col_xs = [-42.0, -30.0, -18.0, -6.0, 6.0, 18.0, 30.0, 42.0]
    for cx in col_xs:
        for r in range(32):
            cz = 20.0 + r * 1.75
            add_resistor_0805(shapes, cx, cz, "H", y_face=1)

    # 7. Four Diagnostic Power LEDs at top
    add_led_0805(shapes, -40.0, 106.0, MAT_LED_GREEN, y_face=1) # +12V
    add_led_0805(shapes, -36.0, 106.0, MAT_LED_RED, y_face=1)   # -12V
    add_led_0805(shapes, 36.0, 106.0, MAT_LED_AMBER, y_face=1)  # +5V_REF
    add_led_0805(shapes, 40.0, 106.0, MAT_LED_BLUE, y_face=1)   # -5V_REF

    wrl_content = f"""#VRML V2.0 utf8
# =========================================================================
# MODULAR ANALOG BLADE: {title_text}
# Neurons: {neurons_str}
# 76-Pin Straddle-Mount Clamping Male Header
# =========================================================================
Transform {{
  children [
{chr(10).join(shapes)}
  ]
}}
"""
    wrl_path = os.path.join(WORKSPACE_DIR, filename)
    with open(wrl_path, "w") as f:
        f.write(wrl_content)
    print(f"Generated VRML Blade: {wrl_path}")
    return wrl_path


def build_blade_dc2(filename):
    """Build Layer 1 Active Precision ReLU Daughtercard (DC2)."""
    shapes = []
    shapes.append(vrml_box(0, 0, 60.50, 100.00, 1.60, 100.00, MAT_PCB_FR4))

    # Silkscreen Banner
    shapes.append(vrml_box(0, 0.81, 106.00, 94.00, 0.02, 5.00, MAT_SILK_WHITE))
    shapes.append(vrml_box(0, 0.81, 101.50, 80.00, 0.02, 2.50, MAT_SILK_WHITE))

    shapes.extend(generate_straddle_header_shapes())

    row1_z = 52.0
    row2_z = 82.0
    ic_xs = [-33.0, -11.0, 11.0, 33.0]
    for x in ic_xs:
        add_soic14(shapes, x, row1_z, "LM324ADR", y_face=1)
        add_capacitor_0805(shapes, x + 6.0, row1_z, "V", y_face=1)
        add_soic14(shapes, x, row2_z, "LM324ADR", y_face=1)
        add_capacitor_0805(shapes, x + 6.0, row2_z, "V", y_face=1)

    for x in ic_xs:
        for offset_x in [-2.5, 2.5]:
            add_sod123_diode(shapes, x + offset_x, row1_z - 8.0, y_face=1)
            add_sod123_diode(shapes, x + offset_x, row1_z + 8.0, y_face=1)
            add_sod123_diode(shapes, x + offset_x, row2_z - 8.0, y_face=1)
            add_sod123_diode(shapes, x + offset_x, row2_z + 8.0, y_face=1)

    for cx in [-42.0, -22.0, -2.0, 18.0, 38.0]:
        for cz in [25.0, 30.0, 35.0, 40.0, 65.0, 70.0, 95.0]:
            add_resistor_0805(shapes, cx, cz, "H", y_face=1)

    add_led_0805(shapes, -40.0, 106.0, MAT_LED_GREEN, y_face=1)
    add_led_0805(shapes, -36.0, 106.0, MAT_LED_RED, y_face=1)
    add_led_0805(shapes, 36.0, 106.0, MAT_LED_AMBER, y_face=1)
    add_led_0805(shapes, 40.0, 106.0, MAT_LED_BLUE, y_face=1)

    wrl_content = f"""#VRML V2.0 utf8
# =========================================================================
# MODULAR ANALOG BLADE: DC2 16-CHANNEL ACTIVE PRECISION RELU
# 76-Pin Straddle-Mount Clamping Male Header
# =========================================================================
Transform {{
  children [
{chr(10).join(shapes)}
  ]
}}
"""
    wrl_path = os.path.join(WORKSPACE_DIR, filename)
    with open(wrl_path, "w") as f:
        f.write(wrl_content)
    print(f"Generated VRML Blade: {wrl_path}")
    return wrl_path


def build_blade_dc3(filename):
    """Build Layer 2 Synaptic Weights + 10-Way Winner-Take-All Blade (DC3).
    Components face OUTWARD (y_face = -1) so the 10-Way classification display
    is directly visible on the back of the modular rack!
    """
    shapes = []
    # 1. Main PCB Substrate
    shapes.append(vrml_box(0, 0, 60.50, 100.00, 1.60, 100.00, MAT_PCB_FR4))

    # 2. Silkscreen Banner on outward face (Y = -0.81mm)
    shapes.append(vrml_box(0, -0.81, 106.00, 94.00, 0.02, 5.00, MAT_SILK_WHITE))
    shapes.append(vrml_box(0, -0.81, 101.50, 85.00, 0.02, 2.50, MAT_SILK_WHITE))

    # 3. Straddle-Mount Header
    shapes.extend(generate_straddle_header_shapes())

    # 4. 10-WAY WINNER-TAKE-ALL OUTPUT LED BAR along Z = 106mm
    # Digits 0 through 9! Class "7" is brightly lit as the winner!
    for d in range(10):
        lx = -36.0 + d * 8.0
        led_mat = MAT_LED_AMBER if d == 7 else MAT_LED_DIM
        add_led_0805(shapes, lx, 106.0, led_mat, y_face=-1)
        # White digit marker label under each LED
        shapes.append(vrml_box(lx, -0.81, 103.50, 3.5, 0.02, 1.5, MAT_SILK_WHITE))

    # 5. 5 SOIC-14 ICs (LM339 Comparators & LM324 Summer Op-Amps)
    for idx, cx in enumerate([-32.0, -16.0, 0.0, 16.0, 32.0]):
        add_soic14(shapes, cx, 80.0, "LM339DR", y_face=-1)
        add_capacitor_0805(shapes, cx + 6.0, 80.0, "V", y_face=-1)

    # 6. 10 Bourns 3296W WTA Trimpots across X
    for idx in range(10):
        px = -40.5 + idx * 9.0
        add_trimpot_bourns(shapes, px, 92.0, y_face=-1)

    # 7. 160 Precision Synaptic Resistors (16 inputs x 10 output classes)
    for col in range(10):
        cx = -40.5 + col * 9.0
        for r in range(16):
            cz = 20.0 + r * 3.8
            add_resistor_0805(shapes, cx, cz, "H", y_face=-1)

    wrl_content = f"""#VRML V2.0 utf8
# =========================================================================
# MODULAR ANALOG BLADE: DC3 L2 WEIGHTS + 10-WAY WINNER-TAKE-ALL
# Outward-Facing Classification Display Panel
# 76-Pin Straddle-Mount Clamping Male Header
# =========================================================================
Transform {{
  children [
{chr(10).join(shapes)}
  ]
}}
"""
    wrl_path = os.path.join(WORKSPACE_DIR, filename)
    with open(wrl_path, "w") as f:
        f.write(wrl_content)
    print(f"Generated VRML Blade: {wrl_path}")
    return wrl_path


def assemble_full_system():
    """Inject the 6 blade models into full_system_assembly.kicad_pcb."""
    mb_file = os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb")
    asm_file = os.path.join(WORKSPACE_DIR, "full_system_assembly.kicad_pcb")

    with open(mb_file) as f:
        content = f.read()

    blade_files = [
        os.path.join(WORKSPACE_DIR, "blade_dc1a.wrl"),
        os.path.join(WORKSPACE_DIR, "blade_dc1b.wrl"),
        os.path.join(WORKSPACE_DIR, "blade_dc1c.wrl"),
        os.path.join(WORKSPACE_DIR, "blade_dc1d.wrl"),
        os.path.join(WORKSPACE_DIR, "blade_dc2.wrl"),
        os.path.join(WORKSPACE_DIR, "blade_dc3.wrl"),
    ]

    for s_idx, bpath in enumerate(blade_files):
        ref = f"J_SLOT{s_idx}"
        p = f'(property "Reference" "{ref}"'
        idx = content.find(p)
        if idx == -1:
            print(f"ERROR: {ref} not found in motherboard!")
            continue

        close_idx = content.find("\n\t)", idx)
        if close_idx == -1:
            print(f"ERROR: closing tag for {ref} not found!")
            continue

        model_snippet = f"""\t\t(model "{bpath}"
\t\t\t(offset
\t\t\t\t(xyz 0 0 0)
\t\t\t)
\t\t\t(scale
\t\t\t\t(xyz 1 1 1)
\t\t\t)
\t\t\t(rotate
\t\t\t\t(xyz 0 0 0)
\t\t\t)
\t\t)"""

        content = content[:close_idx] + "\n" + model_snippet + content[close_idx:]

    with open(asm_file, "w") as f:
        f.write(content)
    print(f"Successfully assembled complete 6-Blade System: {asm_file}")

if __name__ == "__main__":
    print("Building Photorealistic 76-Pin Straddle-Mount Blades...")
    build_blade_dc1("blade_dc1a.wrl", "DC1A: LAYER 1 SYNAPTIC WEIGHTS", "Neurons 0..3 (256 Weights)")
    build_blade_dc1("blade_dc1b.wrl", "DC1B: LAYER 1 SYNAPTIC WEIGHTS", "Neurons 4..7 (256 Weights)")
    build_blade_dc1("blade_dc1c.wrl", "DC1C: LAYER 1 SYNAPTIC WEIGHTS", "Neurons 8..11 (256 Weights)")
    build_blade_dc1("blade_dc1d.wrl", "DC1D: LAYER 1 SYNAPTIC WEIGHTS", "Neurons 12..15 (256 Weights)")
    build_blade_dc2("blade_dc2.wrl")
    build_blade_dc3("blade_dc3.wrl")
    assemble_full_system()
