import os
import subprocess
import pcbnew
import time

board_path = "/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb"
dsn_path = "/Users/lucaszhang/pcbai/test_dc1a_fr_clean.dsn"
ses_path = "/Users/lucaszhang/pcbai/test_dc1a_fr_clean.ses"
jar_path = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"

# 1. Start with fresh skeleton board
import build_perfect_dc1_v14
build_perfect_dc1_v14.generate_dc1_board("daughtercard1a_weights_l1.kicad_pcb", "Daughtercard 1A - L1 Neurons 0..3", range(0, 4))

# 2. Load board and route ONLY the 64 inputs and GND vias
b = pcbnew.LoadBoard(board_path)
for t in list(b.GetTracks()):
    b.Delete(t)

def mm(v): return int(v * 1000000)
def add_track(x1, y1, x2, y2, layer, net, width=0.20):
    if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4: return
    trk = pcbnew.PCB_TRACK(b)
    trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    trk.SetWidth(mm(width))
    trk.SetLayer(layer)
    trk.SetNet(net)
    b.Add(trk)

def add_via(x, y, net, size=0.50, drill=0.30):
    via = pcbnew.PCB_VIA(b)
    via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    via.SetWidth(mm(size))
    via.SetDrill(mm(drill))
    via.SetNet(net)
    b.Add(via)

nets = {b.FindNet(i).GetNetname(): b.FindNet(i) for i in range(b.GetNetCount()) if b.FindNet(i)}
net_gnd = nets["GND"]

# Route 64 inputs
COL_X = [14.5, 24.5, 34.5, 44.5, 65.5, 75.5, 85.5, 95.5]
NEURON_Y = [18.0, 34.0, 50.0, 66.0]
bus_pitch = 0.55
for c in range(8):
    c_local = c % 4
    x_base = 10.87 if c < 4 else 61.87
    x_pin0 = x_base + c_local * 10.16
    x_bus_start = COL_X[c] - 5.00

    for r in range(8):
        i = c * 8 + r
        net_in = nets[f"IN_{i}"]
        x_bus = x_bus_start + r * bus_pitch
        x_pad1 = COL_X[c] - 0.95
        y_first = NEURON_Y[0] + r * 1.5

        for idx in range(4):
            y_res = NEURON_Y[idx] + r * 1.5
            add_track(x_pad1, y_res, x_bus, y_res, pcbnew.F_Cu, net_in, width=0.20)
            add_via(x_bus, y_res, net_in, size=0.50, drill=0.30)

        p = r // 2
        x_pin = x_pin0 + p * 2.54

        if r % 2 == 1:
            y_turn = 86.0 + (3 - p) * 1.5
            add_track(x_bus, y_first, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
            add_track(x_bus, y_turn, x_pin, y_turn, pcbnew.B_Cu, net_in, width=0.20)
            add_track(x_pin, y_turn, x_pin, 92.73, pcbnew.B_Cu, net_in, width=0.20)
        else:
            y_turn = 79.0 + (3 - p) * 1.5
            x_corridor = x_pin - 1.27
            add_track(x_bus, y_first, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
            add_via(x_bus, y_turn, net_in, size=0.50, drill=0.30)
            add_track(x_bus, y_turn, x_corridor, y_turn, pcbnew.In2_Cu, net_in, width=0.20)
            add_track(x_corridor, y_turn, x_corridor, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
            add_track(x_corridor, 97.5, x_pin, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
            add_track(x_pin, 97.5, x_pin, 95.27, pcbnew.In2_Cu, net_in, width=0.20)

# Outward GND vias for U1 and Caps
add_via(50.5, 48.73, net_gnd)
add_track(52.3, 48.73, 50.5, 48.73, pcbnew.F_Cu, net_gnd)
add_via(50.5, 51.27, net_gnd)
add_track(52.3, 51.27, 50.5, 51.27, pcbnew.F_Cu, net_gnd)
add_via(59.5, 51.27, net_gnd)
add_track(57.7, 51.27, 59.5, 51.27, pcbnew.F_Cu, net_gnd)
add_via(59.5, 48.73, net_gnd)
add_track(57.7, 48.73, 59.5, 48.73, pcbnew.F_Cu, net_gnd)

# Caps GND - C_U1P is at (52.0, 42.0), Pad 2 (GND) is at (52.95, 42.0)
add_via(52.95, 40.5, net_gnd)
add_track(52.95, 42.0, 52.95, 40.5, pcbnew.F_Cu, net_gnd)

# C_U1N is at (52.0, 58.0), Pad 2 (GND) is at (52.95, 58.0)
add_via(52.95, 59.5, net_gnd)
add_track(52.95, 58.0, 52.95, 59.5, pcbnew.F_Cu, net_gnd)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(board_path)

# 3. Export DSN
pcbnew.ExportSpecctraDSN(b, dsn_path)
print(f"Exported clean DSN to {dsn_path}")

# 4. Run Freerouting CLI with 100 passes
cmd = [
    "/usr/bin/java", "-jar", jar_path,
    "-de", dsn_path,
    "-do", ses_path,
    "--gui.enabled=false",
    "-mp", "100",
    "-mt", "1"
]
print("Running Freerouting CLI...")
t0 = time.time()
res = subprocess.run(cmd, capture_output=True, text=True)
print(f"Freerouting finished in {time.time()-t0:.1f}s, exit code: {res.returncode}")

# 5. Import SES
if os.path.exists(ses_path):
    b = pcbnew.LoadBoard(board_path)
    pcbnew.ImportSpecctraSES(b, ses_path)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(board_path)
    print("Imported SES and saved board.")
    
    # 6. Run DRC
    os.system(f"/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --severity-error --output drc_dc1a_fr_clean.json --format json {board_path}")
