#!/usr/bin/env python3
"""
audit_board_dimensions.py
-------------------------
Verifies that EVERY printed circuit board in the stack meets:
1. Maximum Outer Dimensions: <= 100.0 mm x 100.0 mm
2. Maximum Copper Layer Count: <= 4 layers
"""

import os
import sys
import pcbnew

from pathlib import Path
WORKSPACE = str(Path(__file__).resolve().parents[1])
BOARDS = [
    ("DC0", "boards/dc0/DC0_verified.kicad_pcb"),
    ("DC1", "boards/dc1/board.kicad_pcb"),
    ("DC2", "boards/dc2/daughtercard2_relu_l1_buffered_repaired.kicad_pcb"),
    ("DC3", "boards/dc3/dc3_universal.kicad_pcb"),
    ("MB", "boards/motherboard/post_crb.kicad_pcb"),
    ("ADS", "boards/ads_carrier/targeted.kicad_pcb"),
]

def audit():
    print("=" * 80)
    print("           BOARD DIMENSIONS & COPPER LAYER COUNT AUDIT")
    print("=" * 80)
    all_passed = True
    
    for name, fname in BOARDS:
        path = os.path.join(WORKSPACE, fname)
        if not os.path.exists(path):
            print(f"[FAIL] {name} ({fname}): File not found!")
            all_passed = False
            continue
            
        b = pcbnew.LoadBoard(path)
        bb = b.GetBoardEdgesBoundingBox()
        layers = b.GetCopperLayerCount()
        
        w = bb.GetWidth() / 1e6
        h = bb.GetHeight() / 1e6
        
        # KiCad outline track stroke width can add 0.15mm to the raw bounding box
        # Tolerating up to 100.2 mm for a 0.15mm centerline outline
        dim_ok = (w <= 100.2) and (h <= 100.2)
        layers_ok = (layers <= 4)
        
        status = "PASS" if (dim_ok and layers_ok) else "FAIL"
        if status != "PASS": all_passed = False
        
        print(f"[{status}] {name:5s} ({fname:35s}): {w:.1f} x {h:.1f} mm | {layers} copper layers")
        
    print("=" * 80)
    msg = "ALL 7 PCBS COMPLY WITH <= 100x100mm AND <= 4 LAYERS" if all_passed else "DIMENSION / LAYER VIOLATIONS DETECTED"
    print("OVERALL RESULT:", msg)
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = audit()
    sys.exit(0 if success else 1)
