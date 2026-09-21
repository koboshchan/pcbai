#!/usr/bin/env python3
"""
update_pcb_weights.py
---------------------
Updates all synaptic and bias resistor values in the KiCad PCB board files
directly from weights_layer1.json and weights_layer2.json.
Also sets footprint Description field to record polarity metadata.
"""

import os
import sys
import json
import pcbnew
import subprocess

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def update_dc1_board(filename, neuron_range, l1_data):
    board_path = os.path.join(WORKSPACE_DIR, filename)
    print(f"\nUpdating {filename} for neurons {list(neuron_range)}...")
    board = pcbnew.LoadBoard(board_path)
    
    updated_count = 0
    dnp_count = 0
    
    # 1. Update 256 matrix resistors R1_<in_idx>_<local_neuron>
    for local_idx, n_idx in enumerate(neuron_range):
        n_info = l1_data["weights"][n_idx]
        for inp in n_info["inputs"]:
            i = inp["input_idx"]
            ref = f"R1_{i}_{local_idx}"
            fp = board.FindFootprintByReference(ref)
            if fp:
                val_str = inp["resistor_str"]
                pol = inp["polarity"]
                fp.SetValue(val_str)
                for f in fp.GetFields():
                    if f.GetName() == "Description":
                        f.SetText(f"polarity={pol}")
                if val_str == "DNP":
                    dnp_count += 1
                else:
                    updated_count += 1
            else:
                print(f"Warning: footprint {ref} not found on {filename}!")
                
        # 2. Update Bias Resistor Rb_N<n_idx>
        rb_ref = f"Rb_N{n_idx}"
        rb_fp = board.FindFootprintByReference(rb_ref)
        if rb_fp:
            rb_val = n_info["bias_resistor_str"]
            rb_fp.SetValue(rb_val)
            for f in rb_fp.GetFields():
                if f.GetName() == "Description":
                    f.SetText(f"rail={n_info['bias_rail']}")
            print(f"  {rb_ref}: {rb_val} (rail: {n_info['bias_rail']})")
        else:
            print(f"Warning: bias resistor {rb_ref} not found!")

    board.Save(board_path)
    print(f"Successfully saved {filename}: {updated_count} active resistors, {dnp_count} DNP.")

def update_dc3_board(filename, l2_data):
    board_path = os.path.join(WORKSPACE_DIR, filename)
    print(f"\nUpdating {filename} for 10 classes...")
    board = pcbnew.LoadBoard(board_path)
    
    updated_count = 0
    dnp_count = 0
    
    # 1. Update 160 matrix resistors R2_<hidden_idx>_<class_idx>
    for c in range(10):
        c_info = l2_data["weights"][c]
        for inp in c_info["inputs"]:
            j = inp["hidden_idx"]
            ref = f"R2_{j}_{c}"
            fp = board.FindFootprintByReference(ref)
            if fp:
                val_str = inp["resistor_str"]
                pol = inp["polarity"]
                fp.SetValue(val_str)
                for f in fp.GetFields():
                    if f.GetName() == "Description":
                        f.SetText(f"polarity={pol}")
                if val_str == "DNP":
                    dnp_count += 1
                else:
                    updated_count += 1
            else:
                print(f"Warning: footprint {ref} not found on {filename}!")
                
        # 2. Update Bias Resistor Rb_L2_<c>
        rb_ref = f"Rb_L2_{c}"
        rb_fp = board.FindFootprintByReference(rb_ref)
        if rb_fp:
            rb_val = c_info["bias_resistor_str"]
            rb_fp.SetValue(rb_val)
            for f in rb_fp.GetFields():
                if f.GetName() == "Description":
                    f.SetText(f"rail={c_info['bias_rail']}")
            print(f"  {rb_ref}: {rb_val} (rail: {c_info['bias_rail']})")
        else:
            print(f"Warning: bias resistor {rb_ref} not found!")

    board.Save(board_path)
    print(f"Successfully saved {filename}: {updated_count} active resistors, {dnp_count} DNP.")

def main():
    print("=================================================================")
    print("UPDATING ALL PCB BOARD FILES WITH 60-VALUE KIT WEIGHTS")
    print("=================================================================")
    
    with open(os.path.join(WORKSPACE_DIR, "weights_layer1.json")) as f:
        l1_data = json.load(f)
    with open(os.path.join(WORKSPACE_DIR, "weights_layer2.json")) as f:
        l2_data = json.load(f)
        
    update_dc1_board("daughtercard1a_weights_l1.kicad_pcb", range(0, 4), l1_data)
    update_dc1_board("daughtercard1b_weights_l1.kicad_pcb", range(4, 8), l1_data)
    update_dc1_board("daughtercard1c_weights_l1.kicad_pcb", range(8, 12), l1_data)
    update_dc1_board("daughtercard1d_weights_l1.kicad_pcb", range(12, 16), l1_data)
    update_dc3_board("daughtercard3_weights_l2_wta.kicad_pcb", l2_data)

    print("\n=================================================================")
    print("RUNNING DRC VERIFICATION ON ALL BOARDS VIA KICAD-CLI")
    print("=================================================================")
    kicad_cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    
    boards = [
        "daughtercard1a_weights_l1.kicad_pcb",
        "daughtercard1b_weights_l1.kicad_pcb",
        "daughtercard1c_weights_l1.kicad_pcb",
        "daughtercard1d_weights_l1.kicad_pcb",
        "daughtercard2_relu_l1.kicad_pcb",
        "daughtercard3_weights_l2_wta.kicad_pcb",
        "motherboard.kicad_pcb"
    ]
    
    all_passed = True
    for b in boards:
        b_path = os.path.join(WORKSPACE_DIR, b)
        rpt_path = os.path.join(WORKSPACE_DIR, f"drc_check_{b}.rpt")
        cmd = [kicad_cli, "pcb", "drc", "--severity-all", "--output", rpt_path, b_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # Parse report
        with open(rpt_path) as rf:
            rpt_text = rf.read()
        err_count = 0
        warn_count = 0
        for line in rpt_text.splitlines():
            if "total violations:" in line.lower():
                pass
            if "[error]" in line.lower():
                err_count += 1
            elif "[warning]" in line.lower() and "unconnected" in line.lower():
                warn_count += 1
        print(f"{b:<40} -> Errors: {err_count}, Unconnected: {warn_count}")
        if err_count > 0 or warn_count > 0:
            all_passed = False
            
    if all_passed:
        print("\nALL 7 BOARDS MAINTAIN 0 DRC ERRORS AND 0 UNCONNECTED ITEMS!")
    else:
        print("\nWarning: Some boards have DRC issues. Check individual reports.")

if __name__ == "__main__":
    main()
