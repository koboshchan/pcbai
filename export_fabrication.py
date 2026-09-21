#!/usr/bin/env python3
"""
export_fabrication.py
---------------------
Automates generation of full manufacturing and assembly deliverables for JLCPCB:
- 4-layer Gerbers (F.Cu, In1.Cu, In2.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, F.Paste, B.Paste, Edge.Cuts)
- Excellon Drill files (.drl, PTH & NPTH separated)
- Component Placement List (CPL / POS CSV)
- Bill of Materials (BOM CSV) formatted for JLCPCB SMT assembly
- Consolidated System BOM across all 7 PCBs
- Production ZIP packages
"""

import os
import sys
import csv
import subprocess
import zipfile
from collections import defaultdict

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
FAB_DIR = os.path.join(WORKSPACE_DIR, "fabrication")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

import pcbnew

BOARDS = [
    {
        "name": "daughtercard1a_weights_l1",
        "pcb": os.path.join(WORKSPACE_DIR, "daughtercard1a_weights_l1.kicad_pcb"),
        "title": "Daughtercard 1A: Layer 1 Synaptic Weights (Neurons 0..3)"
    },
    {
        "name": "daughtercard1b_weights_l1",
        "pcb": os.path.join(WORKSPACE_DIR, "daughtercard1b_weights_l1.kicad_pcb"),
        "title": "Daughtercard 1B: Layer 1 Synaptic Weights (Neurons 4..7)"
    },
    {
        "name": "daughtercard1c_weights_l1",
        "pcb": os.path.join(WORKSPACE_DIR, "daughtercard1c_weights_l1.kicad_pcb"),
        "title": "Daughtercard 1C: Layer 1 Synaptic Weights (Neurons 8..11)"
    },
    {
        "name": "daughtercard1d_weights_l1",
        "pcb": os.path.join(WORKSPACE_DIR, "daughtercard1d_weights_l1.kicad_pcb"),
        "title": "Daughtercard 1D: Layer 1 Synaptic Weights (Neurons 12..15)"
    },
    {
        "name": "daughtercard2_relu_l1",
        "pcb": os.path.join(WORKSPACE_DIR, "daughtercard2_relu_l1.kicad_pcb"),
        "title": "Daughtercard 2: Layer 1 Active Precision ReLU Rectifiers"
    },
    {
        "name": "daughtercard3_weights_l2_wta",
        "pcb": os.path.join(WORKSPACE_DIR, "daughtercard3_weights_l2_wta.kicad_pcb"),
        "title": "Daughtercard 3: Layer 2 Weights & Winner-Take-All Argmax"
    },
    {
        "name": "motherboard",
        "pcb": os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb"),
        "title": "Motherboard: 6-Slot Backplane Interconnect"
    }
]

LCSC_MAPPING = {
    "TL074": "C6982",
    "LM339": "C2684873",
    "1N4148": "C81598",
    "1N4148W": "C81598",
    "0.1uF": "C49678",
    "10uF": "C15850",
    "Green": "C2290",
    "10k": "C17414",
    "1k": "C17513",
    "47k": "C17713",
    "100k": "C17407",
    "20k": "C17441",
    "PinHeader_2x20_P2.54mm_Vertical": "C2938830",
    "PinSocket_2x20_P2.54mm_Vertical": "C2897389",
    "PinHeader_2x05_P2.54mm_Vertical": "C2938827",
}

def get_lcsc_code(val, fp_name):
    for k, code in LCSC_MAPPING.items():
        if k in val or k in fp_name:
            return code
    if "Resistor" in fp_name or "R_0805" in fp_name:
        return f"C_0805_1%_{val}"
    if "Capacitor" in fp_name or "C_0805" in fp_name:
        return "C49678"
    if "LED" in fp_name:
        return "C2290"
    return "N/A"

def run_cmd(cmd, desc):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Warning in {desc}: code {res.returncode}")
        if res.stderr:
            print(f"  {res.stderr.strip()[:200]}")
    return res

def export_all():
    os.makedirs(FAB_DIR, exist_ok=True)
    print("=" * 85)
    print("      GENERATING COMPLETE JLCPCB MANUFACTURING & ASSEMBLY DELIVERABLES")
    print("=" * 85)
    
    consolidated_bom = defaultdict(lambda: {"qty": 0, "designators": [], "boards": set(), "lcsc": "N/A"})

    for b in BOARDS:
        b_name = b["name"]
        b_title = b["title"]
        b_pcb = b["pcb"]
        print(f"\nProcessing [{b_name}]: {b_title}")
        
        b_dir = os.path.join(FAB_DIR, b_name)
        gerber_dir = os.path.join(b_dir, "gerbers")
        os.makedirs(gerber_dir, exist_ok=True)
        
        # 1. Export 4-layer Gerbers
        run_cmd([
            KICAD_CLI, "pcb", "export", "gerbers",
            "--output", gerber_dir,
            "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts",
            "--subtract-soldermask",
            b_pcb
        ], f"Gerbers: {b_name}")
        
        # 2. Export Drill Files (PTH + NPTH separate)
        run_cmd([
            KICAD_CLI, "pcb", "export", "drill",
            "--output", gerber_dir,
            "--format", "excellon",
            "--excellon-units", "mm",
            "--excellon-separate-th",
            "--generate-map",
            b_pcb
        ], f"Drill: {b_name}")
        
        # 3. Create Production Gerber ZIP
        zip_path = os.path.join(FAB_DIR, f"{b_name}_gerbers.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(gerber_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    zipf.write(full_p, arcname=f)
        print(f"  -> Gerbers & Drills zipped: {os.path.basename(zip_path)}")
        
        # 4. Export Pick and Place (CPL / POS) CSV
        pos_path = os.path.join(b_dir, f"{b_name}_cpl.csv")
        run_cmd([
            KICAD_CLI, "pcb", "export", "pos",
            "--format", "csv",
            "--units", "mm",
            "--side", "both",
            "--output", pos_path,
            b_pcb
        ], f"CPL / POS: {b_name}")
        print(f"  -> CPL (Pick & Place) CSV: {os.path.basename(pos_path)}")
        
        # 5. Extract Board BOM directly from PCB
        board_obj = pcbnew.LoadBoard(b_pcb)
        board_bom = defaultdict(list)
        
        for fp in board_obj.GetFootprints():
            ref = fp.GetReference()
            val = fp.GetValue()
            fp_id = str(fp.GetFPID().GetLibItemName())
            if ref.startswith("H") and "MountingHole" in fp_id:
                continue # Skip mounting holes from SMT assembly BOM
            board_bom[(val, fp_id)].append(ref)
            
            # Consolidated
            lcsc = get_lcsc_code(val, fp_id)
            key = (val, fp_id)
            consolidated_bom[key]["qty"] += 1
            consolidated_bom[key]["designators"].append(f"{b_name}:{ref}")
            consolidated_bom[key]["boards"].add(b_name)
            consolidated_bom[key]["lcsc"] = lcsc
            
        # Write board BOM CSV
        bom_path = os.path.join(b_dir, f"{b_name}_bom.csv")
        with open(bom_path, "w", newline="") as f_bom:
            writer = csv.writer(f_bom)
            writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Quantity"])
            for (val, fp_id), refs in sorted(board_bom.items(), key=lambda x: x[0][0]):
                refs_sorted = sorted(refs)
                lcsc = get_lcsc_code(val, fp_id)
                writer.writerow([val, " ".join(refs_sorted), fp_id, lcsc, len(refs_sorted)])
        print(f"  -> Board BOM CSV: {os.path.basename(bom_path)} ({len(board_bom)} unique part lines)")
        
    # Write Master Consolidated System BOM
    consolidated_path = os.path.join(FAB_DIR, "consolidated_system_bom.csv")
    with open(consolidated_path, "w", newline="") as f_con:
        writer = csv.writer(f_con)
        writer.writerow(["Comment / Value", "Footprint / Package", "Total Qty", "LCSC Part #", "Used On Boards", "Designators Summary"])
        total_components = 0
        for (val, fp_id), data in sorted(consolidated_bom.items(), key=lambda x: (x[0][1], x[0][0])):
            qty = data["qty"]
            total_components += qty
            boards_str = ", ".join(sorted(data["boards"]))
            des_sample = ", ".join(data["designators"][:10]) + ("..." if len(data["designators"]) > 10 else "")
            writer.writerow([val, fp_id, qty, data["lcsc"], boards_str, des_sample])
            
    print("\n" + "=" * 85)
    print("FABRICATION EXPORT COMPLETE!")
    print(f"  Total System Components in BOM: {total_components}")
    print(f"  Master Consolidated BOM:        {consolidated_path}")
    print(f"  Output Directory:               {FAB_DIR}")
    print("=" * 85)

if __name__ == "__main__":
    export_all()
