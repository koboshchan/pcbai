#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
route_shifter_board.py
----------------------
Exports DSN from shifter_board.kicad_pcb, configures single-layer F.Cu rules,
runs FreeRouting, imports SES, verifies single-layer integrity, and runs DRC.
"""

import os
import sys
import re
import time
import json
import subprocess
import pcbnew

WORKSPACE  = "/Users/lucaszhang/pcbai"
BOARD_PATH = os.path.join(WORKSPACE, "shifter_board.kicad_pcb")
DSN_PATH   = os.path.join(WORKSPACE, "shifter_board.dsn")
SES_PATH   = os.path.join(WORKSPACE, "shifter_board.ses")
DRC_JSON   = os.path.join(WORKSPACE, "shifter_board_drc.json")
KICAD_CLI  = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

JAR_PATH   = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
if not os.path.exists(JAR_PATH):
    JAR_PATH = os.path.join(WORKSPACE, "freerouting.jar")

JAVA_BIN   = "/opt/homebrew/opt/openjdk@25/bin/java"
if not os.path.exists(JAVA_BIN):
    JAVA_BIN = "/usr/bin/java"

def export_and_patch_dsn():
    print("1. Loading fresh board and exporting Specctra DSN...")
    import build_shifter_board
    board = build_shifter_board.create_board()
    
    # Ensure design rules on board
    ds = board.GetDesignSettings()
    ds.m_MinClearance  = pcbnew.FromMM(0.5)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.3)
    ds.SetCustomTrackWidth(pcbnew.FromMM(0.5))
    board.Save(BOARD_PATH)

    ok = pcbnew.ExportSpecctraDSN(board, DSN_PATH)
    print(f"   ExportSpecctraDSN: {ok}")

    with open(DSN_PATH, "r") as f:
        dsn = f.read()

    # Rule 1: Set B.Cu to power (disabled for routing signals)
    dsn = re.sub(r'(\(layer\s+"?B\.Cu"?\s+\(type\s+)signal(\))', r'\1power\2', dsn)

    # Rule 2: Set default trace width to 350 (0.35 mm) to allow routing between SMD pads
    dsn = re.sub(r'\(width\s+\d+\)', '(width 350)', dsn)

    # Rule 3: Set clearance to 500 (0.5 mm)
    dsn = re.sub(r'\(clearance\s+\d+\)', '(clearance 500)', dsn)
    dsn = re.sub(r'\(clearance\s+\d+\s+\(type smd_smd\)\)', '(clearance 500 (type smd_smd))', dsn)

    with open(DSN_PATH, "w") as f:
        f.write(dsn)
    print("   [OK] DSN patched: F.Cu single layer, width=350um, clearance=500um")

def run_freerouting():
    print(f"\n2. Launching FreeRouting with Java ({JAVA_BIN})...")
    if os.path.exists(SES_PATH):
        os.remove(SES_PATH)

    cmd = [
        JAVA_BIN, "-jar", JAR_PATH,
        "-de", DSN_PATH,
        "-do", SES_PATH,
        "--gui.enabled=false",
        "-mp", "60",
        "-mt", "1"
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.time() - t0
    print(f"   FreeRouting finished in {dt:.1f}s, exit code: {res.returncode}")
    if res.returncode != 0:
        print("   STDERR:", res.stderr)
        print("   STDOUT:", res.stdout[-500:])

def import_ses_and_verify():
    print("\n3. Importing SES into board...")
    if not os.path.exists(SES_PATH):
        raise FileNotFoundError(f"SES file not found at {SES_PATH}")

    board = pcbnew.LoadBoard(BOARD_PATH)
    ok = pcbnew.ImportSpecctraSES(board, SES_PATH)
    print(f"   ImportSpecctraSES: {ok}")
    board.Save(BOARD_PATH)

    # Reload board cleanly for SWIG track verification
    board = pcbnew.LoadBoard(BOARD_PATH)
    vias_count = 0
    bcu_count = 0
    fcu_count = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            board.Remove(t)
            vias_count += 1
        elif t.GetLayer() == pcbnew.B_Cu:
            board.Remove(t)
            bcu_count += 1
        elif t.GetLayer() == pcbnew.F_Cu:
            fcu_count += 1

    # Ensure perimeter GND tracks exist on board
    gnd_net = board.FindNet("GND")
    pts_gnd = [
        (19.09, 13.5),  # R1_PD Pad 1
        (19.09, 11.5),  # North of CH1
        (3.6, 11.5),    # West top perimeter
        (3.6, 26.16),   # West to J_IN pin 5 level
        (6.5, 26.16),   # J_IN pin 5
        (3.6, 26.16),   # Back to west edge
        (3.6, 61.5),    # Down west edge
        (46.4, 61.5),   # Along south perimeter
        (46.4, 28.7),   # Up east edge
        (43.5, 28.7),   # J_OUT pin 6
    ]
    for i in range(len(pts_gnd) - 1):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(pts_gnd[i][0]), pcbnew.FromMM(pts_gnd[i][1])))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(pts_gnd[i+1][0]), pcbnew.FromMM(pts_gnd[i+1][1])))
        t.SetWidth(pcbnew.FromMM(0.5))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(gnd_net)
        board.Add(t)

    t_tap = pcbnew.PCB_TRACK(board)
    t_tap.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(13.5), pcbnew.FromMM(61.5)))
    t_tap.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(13.5), pcbnew.FromMM(55.81)))
    t_tap.SetWidth(pcbnew.FromMM(0.5))
    t_tap.SetLayer(pcbnew.F_Cu)
    t_tap.SetNet(gnd_net)
    board.Add(t_tap)

    # Straight horizontal route for IN1
    t_in1 = pcbnew.PCB_TRACK(board)
    t_in1.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(16.0)))
    t_in1.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(19.09), pcbnew.FromMM(16.0)))
    t_in1.SetWidth(pcbnew.FromMM(0.4))
    t_in1.SetLayer(pcbnew.F_Cu)
    t_in1.SetNet(board.FindNet("IN1"))
    board.Add(t_in1)

    # Clean guided routes for IN2, IN3, IN4 passing through W4, W5, W6
    input_bus = [
        ("IN2", [(6.5, 18.54), (10.9, 22.94), (10.9, 28.0), (19.09, 28.0)]),
        ("IN3", [(6.5, 21.08), (9.7, 24.28), (9.7, 40.0), (19.09, 40.0)]),
        ("IN4", [(6.5, 23.62), (8.5, 25.62), (8.5, 52.0), (19.09, 52.0)]),
    ]
    for net_name, pts_in in input_bus:
        for i in range(len(pts_in) - 1):
            t_in = pcbnew.PCB_TRACK(board)
            t_in.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(pts_in[i][0]), pcbnew.FromMM(pts_in[i][1])))
            t_in.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(pts_in[i+1][0]), pcbnew.FromMM(pts_in[i+1][1])))
            t_in.SetWidth(pcbnew.FromMM(0.4))
            t_in.SetLayer(pcbnew.F_Cu)
            t_in.SetNet(board.FindNet(net_name))
            board.Add(t_in)

    # Route connecting W4 Pad 1 to R2_PD Pad 1 (GND_CH1) north of IN2
    t_ch1 = pcbnew.PCB_TRACK(board)
    t_ch1.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(13.5), pcbnew.FromMM(24.19)))
    t_ch1.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(17.5), pcbnew.FromMM(24.19)))
    t_ch1.SetWidth(pcbnew.FromMM(0.5))
    t_ch1.SetLayer(pcbnew.F_Cu)
    t_ch1.SetNet(board.FindNet("GND_CH1"))
    board.Add(t_ch1)

    t_ch1_diag = pcbnew.PCB_TRACK(board)
    t_ch1_diag.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(17.5), pcbnew.FromMM(24.19)))
    t_ch1_diag.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(19.09), pcbnew.FromMM(25.5)))
    t_ch1_diag.SetWidth(pcbnew.FromMM(0.5))
    t_ch1_diag.SetLayer(pcbnew.F_Cu)
    t_ch1_diag.SetNet(board.FindNet("GND_CH1"))
    board.Add(t_ch1_diag)

    # Ensure backbone links exist
    backbone_links = [
        ("GND_CH2", 13.5, 31.81, 36.19),
        ("GND_CH3", 13.5, 43.81, 48.19),
        ("+5V_CH2", 33.5, 31.81, 36.19),
        ("+5V_CH3", 33.5, 43.81, 48.19),
    ]
    for n_name, bx, by1, by2 in backbone_links:
        t_bb = pcbnew.PCB_TRACK(board)
        t_bb.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by1)))
        t_bb.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by2)))
        t_bb.SetWidth(pcbnew.FromMM(0.5))
        t_bb.SetLayer(pcbnew.F_Cu)
        t_bb.SetNet(board.FindNet(n_name))
        board.Add(t_bb)

    print(f"   Tracks on board: {fcu_count} F.Cu tracks from SES, {bcu_count} B.Cu tracks removed, {vias_count} vias removed")
    board.Save(BOARD_PATH)

    # Re-inject net_tie_pad_groups for DRC
    with open(BOARD_PATH, "r") as f:
        content = f.read()
    content = content.replace('(tags "net tie")', '(tags "net tie")\n    (net_tie_pad_groups "1,2")')
    with open(BOARD_PATH, "w") as f:
        f.write(content)

    print(f"   Saved routed board to {BOARD_PATH}")

def run_drc():
    print("\n4. Running KiCad DRC...")
    subprocess.run([
        KICAD_CLI, "pcb", "drc",
        "--output", DRC_JSON,
        "--format", "json",
        "--severity-all",
        BOARD_PATH
    ], check=True)

    with open(DRC_JSON) as f:
        drc = json.load(f)

    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])

    print(f"   DRC Violations Count:  {len(violations)}")
    print(f"   DRC Unconnected Count: {len(unconnected)}")

    if violations:
        print("\n   --- Violations Detail ---")
        for v in violations:
            print(f"   [{v.get('severity', 'ERR')}] {v.get('type')}: {v.get('description')}")
    if unconnected:
        print("\n   --- Unconnected Detail ---")
        for u in unconnected:
            print(f"   [UNCONNECTED] {u.get('description')}")

    return len(violations), len(unconnected)

if __name__ == "__main__":
    export_and_patch_dsn()
    run_freerouting()
    import_ses_and_verify()
    v_cnt, u_cnt = run_drc()
    if v_cnt == 0 and u_cnt == 0:
        print("\n" + "="*60)
        print("SUCCESS: 0 DRC VIOLATIONS, 0 UNCONNECTED ITEMS!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print(f"ROUTING RESULT: {v_cnt} violations, {u_cnt} unconnected")
        print("="*60)
