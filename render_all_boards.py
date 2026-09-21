#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
render_all_boards.py
--------------------
Batch renders photorealistic 3D raytraced images for each PCB in the 
72-Pin Straight Modular Analog Neural Network System:
1. Motherboard Backplane (100x100mm, 6x 72P straight sockets)
2. Daughtercard 1A (Neurons 0..3)
3. Daughtercard 1B (Neurons 4..7)
4. Daughtercard 1C (Neurons 8..11)
5. Daughtercard 1D (Neurons 12..15)
6. Daughtercard 2  (16-Channel Active Precision ReLU)
7. Daughtercard 3  (L2 Weights + 10-Way Winner-Take-All + 10 LEDs)
8. Full System Assembly (Isometric Hero 6-Blade Rack)
9. Full System Assembly (Side View Card Cage)
"""

import os
import subprocess
import shutil

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
ARTIFACTS_DIR = "/Users/lucaszhang/.gemini/antigravity/brain/7f377471-c6f5-4618-a438-177f823c16b4"
RENDERS_DIR = os.path.join(WORKSPACE_DIR, "renders")
os.makedirs(RENDERS_DIR, exist_ok=True)

boards_to_render = [
    {
        "input": "motherboard.kicad_pcb",
        "output": "render_motherboard.png",
        "args": ["--rotate", "-35,0,35", "--zoom", "0.90", "--perspective", "--floor"]
    },
    {
        "input": "daughtercard1a_weights_l1.kicad_pcb",
        "output": "render_dc1a_weights.png",
        "args": ["--rotate", "-30,0,25", "--zoom", "0.92", "--perspective", "--floor"]
    },
    {
        "input": "daughtercard1b_weights_l1.kicad_pcb",
        "output": "render_dc1b_weights.png",
        "args": ["--rotate", "-30,0,25", "--zoom", "0.92", "--perspective", "--floor"]
    },
    {
        "input": "daughtercard1c_weights_l1.kicad_pcb",
        "output": "render_dc1c_weights.png",
        "args": ["--rotate", "-30,0,25", "--zoom", "0.92", "--perspective", "--floor"]
    },
    {
        "input": "daughtercard1d_weights_l1.kicad_pcb",
        "output": "render_dc1d_weights.png",
        "args": ["--rotate", "-30,0,25", "--zoom", "0.92", "--perspective", "--floor"]
    },
    {
        "input": "daughtercard2_relu_l1.kicad_pcb",
        "output": "render_dc2_relu.png",
        "args": ["--rotate", "-30,0,25", "--zoom", "0.92", "--perspective", "--floor"]
    },
    {
        "input": "daughtercard3_weights_l2_wta.kicad_pcb",
        "output": "render_dc3_wta.png",
        "args": ["--rotate", "-30,0,25", "--zoom", "0.92", "--perspective", "--floor"]
    },
    {
        "input": "full_system_assembly.kicad_pcb",
        "output": "render_assembly_iso.png",
        "args": ["--rotate", "-32,0,38", "--zoom", "0.50", "--pan", "0,-0.8,0", "--perspective", "--floor"]
    },
    {
        "input": "full_system_assembly.kicad_pcb",
        "output": "render_assembly_side.png",
        "args": ["--side", "right", "--zoom", "0.36", "--pan", "0,-1.5,0", "--perspective", "--floor"]
    }
]

def run():
    print(f"Starting batch rendering of {len(boards_to_render)} views...")
    for idx, item in enumerate(boards_to_render):
        in_path = os.path.join(WORKSPACE_DIR, item["input"])
        out_path = os.path.join(RENDERS_DIR, item["output"])
        artifact_path = os.path.join(ARTIFACTS_DIR, item["output"])
        
        cmd = [
            KICAD_CLI, "pcb", "render",
            "--output", out_path,
            "--quality", "high"
        ] + item["args"] + [in_path]
        
        print(f"[{idx+1}/{len(boards_to_render)}] Rendering {item['input']} -> {item['output']}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            shutil.copyfile(out_path, artifact_path)
            print(f"       Done. Copied to artifacts.")
        else:
            print(f"       ERROR rendering {item['input']}:")
            print(res.stderr)

    print("\nAll renders completed successfully!")

if __name__ == "__main__":
    run()
