#!/usr/bin/env python3
"""
audit_pin_coordinates.py
------------------------
Performs a rigorous geometric and electrical alignment audit across all 6 daughtercards
and the 6 motherboard socket slots:
- Slot 0: DC1A (L1 Neurons 0..3)
- Slot 1: DC1B (L1 Neurons 4..7)
- Slot 2: DC1C (L1 Neurons 8..11)
- Slot 3: DC1D (L1 Neurons 12..15)
- Slot 4: DC2 (16x Active Precision ReLU)
- Slot 5: DC3 (L2 Synaptic Weights + Winner-Take-All)

Verifies:
1. Relative header-to-header spacing (J_SLOT_A to J_SLOT_B) on daughtercards vs motherboard sockets.
2. Pin-by-pin pitch, row offset, and pad center-to-center delta (< 0.001 mm).
3. Netlist mating compatibility across all 480 slot pins.
"""

import os
import sys
import pcbnew

WORKSPACE = "/Users/lucaszhang/pcbai"

DAUGHTERCARD_FILES = [
    ("DC1A", "daughtercard1a_weights_l1.kicad_pcb", 0),
    ("DC1B", "daughtercard1b_weights_l1.kicad_pcb", 1),
    ("DC1C", "daughtercard1c_weights_l1.kicad_pcb", 2),
    ("DC1D", "daughtercard1d_weights_l1.kicad_pcb", 3),
    ("DC2",  "daughtercard2_relu_l1.kicad_pcb",     4),
    ("DC3",  "daughtercard3_weights_l2_wta.kicad_pcb", 5),
]

def run_audit():
    print("=" * 85)
    print("           MODULAR HARDWARE MATING & PIN-LEVEL ALIGNMENT AUDIT REPORT")
    print("=" * 85)
    
    mb_path = os.path.join(WORKSPACE, "motherboard.kicad_pcb")
    if not os.path.exists(mb_path):
        print("ERROR: motherboard.kicad_pcb not found!")
        return False
    
    mb = pcbnew.LoadBoard(mb_path)
    all_passed = True
    total_pins_audited = 0
    total_pin_errors = 0
    total_net_discrepancies = 0
    
    for dc_name, dc_filename, slot_idx in DAUGHTERCARD_FILES:
        dc_path = os.path.join(WORKSPACE, dc_filename)
        if not os.path.exists(dc_path):
            print(f"[FAIL] {dc_name}: file {dc_filename} missing!")
            all_passed = False
            continue
            
        dc = pcbnew.LoadBoard(dc_path)
        
        # Check Daughtercard Header Footprints
        dc_ha = dc.FindFootprintByReference("J_SLOT_A")
        dc_hb = dc.FindFootprintByReference("J_SLOT_B")
        if not dc_ha or not dc_hb:
            print(f"[FAIL] {dc_name}: Missing J_SLOT_A or J_SLOT_B headers!")
            all_passed = False
            continue
            
        # Check Motherboard Socket Footprints
        mb_sa = mb.FindFootprintByReference(f"J_SLOT{slot_idx}_A")
        mb_sb = mb.FindFootprintByReference(f"J_SLOT{slot_idx}_B")
        if not mb_sa or not mb_sb:
            print(f"[FAIL] Motherboard: Missing J_SLOT{slot_idx}_A or J_SLOT{slot_idx}_B sockets!")
            all_passed = False
            continue
            
        # Header Spacing on Daughtercard
        dc_ha_pos = dc_ha.GetPosition()
        dc_hb_pos = dc_hb.GetPosition()
        dc_delta_x = (dc_hb_pos.x - dc_ha_pos.x) / 1e6
        dc_delta_y = (dc_hb_pos.y - dc_ha_pos.y) / 1e6
        
        # Socket Spacing on Motherboard
        mb_sa_pos = mb_sa.GetPosition()
        mb_sb_pos = mb_sb.GetPosition()
        mb_delta_x = (mb_sb_pos.x - mb_sa_pos.x) / 1e6
        mb_delta_y = (mb_sb_pos.y - mb_sa_pos.y) / 1e6
        
        spacing_match = abs(dc_delta_x - mb_delta_x) < 0.001 and abs(dc_delta_y - mb_delta_y) < 0.001
        
        # Pin-by-pin audit
        pin_errors = 0
        net_mismatches = 0
        
        # J_SLOT_A and J_SLOT_B Pins 1..40 (total 80 pins per card)
        for header_suffix, dc_h, mb_s in [("A", dc_ha, mb_sa), ("B", dc_hb, mb_sb)]:
            h_pos = dc_h.GetPosition()
            s_pos = mb_s.GetPosition()
            for p in range(1, 41):
                total_pins_audited += 1
                p_str = str(p)
                dc_pad = dc_h.FindPadByNumber(p_str)
                mb_pad = mb_s.FindPadByNumber(p_str)
                
                if not dc_pad or not mb_pad:
                    pin_errors += 1
                    continue
                
                # Check relative pin positions within header vs socket
                rel_dc_x = (dc_pad.GetPosition().x - h_pos.x) / 1e6
                rel_dc_y = (dc_pad.GetPosition().y - h_pos.y) / 1e6
                rel_mb_x = (mb_pad.GetPosition().x - s_pos.x) / 1e6
                rel_mb_y = (mb_pad.GetPosition().y - s_pos.y) / 1e6
                
                dx = abs(rel_dc_x - rel_mb_x)
                dy = abs(rel_dc_y - rel_mb_y)
                if dx > 0.001 or dy > 0.001:
                    pin_errors += 1
                    
                # Check net name consistency
                dc_net = dc_pad.GetNet().GetNetname()
                mb_net = mb_pad.GetNet().GetNetname()
                if dc_net and mb_net and dc_net != mb_net:
                    net_mismatches += 1
                    
        total_pin_errors += pin_errors
        total_net_discrepancies += net_mismatches
        status_str = "PASS" if (spacing_match and pin_errors == 0 and net_mismatches == 0) else "WARN/FAIL"
        if status_str != "PASS":
            all_passed = False
            
        print(f"[{status_str}] Slot {slot_idx} <-> {dc_name}:")
        print(f"       Header Spacing: DC ΔX={dc_delta_x:.3f} mm, MB ΔX={mb_delta_x:.3f} mm (diff: {abs(dc_delta_x - mb_delta_x):.4f} mm)")
        print(f"       Pin Geometry:  {80 - pin_errors}/80 pins strictly aligned (Δ < 0.001 mm)")
        print(f"       Net Mating:    {80 - net_mismatches}/80 signals perfectly matched ({net_mismatches} mismatches)")
        
    print("=" * 85)
    print(f"SUMMARY:")
    print(f"  Total Mating Pins Audited:     {total_pins_audited}")
    print(f"  Total Geometric Pin Errors:    {total_pin_errors}")
    print(f"  Total Net Discrepancies:       {total_net_discrepancies}")
    print(f"  Overall Verification:          {'100% PERFECT PHYSICAL & ELECTRICAL MATING' if all_passed else 'MISMATCH DETECTED'}")
    print("=" * 85)
    return all_passed

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
