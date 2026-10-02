#!/usr/bin/env python3
"""
Generate publication-quality 1920x1080 raytraced 3D renders of the complete
6-blade modular analog neural network cube assembly with 76-pin straddle headers.
"""
import subprocess
import os

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
ASM_PCB = os.path.join(WORKSPACE_DIR, "full_system_assembly.kicad_pcb")
RENDERS_DIR = os.path.join(WORKSPACE_DIR, "renders")
os.makedirs(RENDERS_DIR, exist_ok=True)

views = [
    {
        "name": "render_straddle_cube_assembly_iso.png",
        "desc": "Hero Isometric View 1: Input Side (MCU SPI, Shift Registers, DC1A 256 Weights, 6 Blades)",
        "args": ["--rotate", "-35,0,135", "--pivot", "0,0,5.8", "--zoom", "0.20", "--perspective", "--floor"]
    },
    {
        "name": "render_straddle_cube_assembly_wta.png",
        "desc": "Hero Isometric View 2: Output Side (10-Way Winner-Take-All Active Digit Classification)",
        "args": ["--rotate", "-28,-25,20", "--pivot", "0,0,5.8", "--zoom", "0.18", "--perspective", "--floor"]
    },
    {
        "name": "render_straddle_cube_assembly_side.png",
        "desc": "Card-Cage Side Profile: 6 Parallel Blades at 11mm Pitch in Motherboard Straddle Sockets",
        "args": ["--side", "right", "--pivot", "0,0,5.8", "--zoom", "0.17", "--perspective", "--floor"]
    },
    {
        "name": "render_straddle_cube_assembly_cardcage.png",
        "desc": "Card-Cage Perspective: Dynamic View of Parallel Blade Spacing and Straddle Headers",
        "args": ["--rotate", "-20,-45,15", "--pivot", "0,0,5.8", "--zoom", "0.18", "--perspective", "--floor"]
    },
    {
        "name": "render_straddle_cube_assembly_front.png",
        "desc": "Front Elevation View: DC1A Synaptic Board and Motherboard Backplane",
        "args": ["--rotate", "-8,0,180", "--pivot", "0,0,5.8", "--zoom", "0.20", "--perspective", "--floor"]
    }
]

for v in views:
    out_path = os.path.join(RENDERS_DIR, v["name"])
    print(f"Rendering {v['name']} ({v['desc']})...")
    cmd = [
        KICAD_CLI, "pcb", "render",
        "--output", out_path,
        "--width", "1920", "--height", "1080",
        "--quality", "high"
    ] + v["args"] + [ASM_PCB]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  -> SUCCESS: {out_path}")
    else:
        print(f"  -> FAILED: {res.stderr}")

print("All assembly renders completed!")
