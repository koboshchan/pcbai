import os
import subprocess
import pcbnew
import time

board_path = "/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb"
dsn_path = "/Users/lucaszhang/pcbai/test_dc1a_fr.dsn"
ses_path = "/Users/lucaszhang/pcbai/test_dc1a_fr.ses"
jar_path = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"

# 1. Generate board with all 64 inputs pre-routed
# In build_perfect_dc1_v14.py, only inputs were routed and DRC gave 0 errors!
os.system("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 /Users/lucaszhang/pcbai/build_perfect_dc1_v14.py")

# 2. Add GND vias to board so GND plane is connected
b = pcbnew.LoadBoard(board_path)
def mm(v): return int(v * 1000000)
def add_via(x, y, net, size=0.50, drill=0.30):
    via = pcbnew.PCB_VIA(b)
    via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    via.SetWidth(mm(size))
    via.SetDrill(mm(drill))
    via.SetNet(net)
    b.Add(via)
def add_track(x1, y1, x2, y2, layer, net, width=0.25):
    trk = pcbnew.PCB_TRACK(b)
    trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    trk.SetWidth(mm(width))
    trk.SetLayer(layer)
    trk.SetNet(net)
    b.Add(trk)

net_gnd = b.FindNet("GND")
# Pin 3, 5, 10, 12 GND
add_via(50.5, 48.73, net_gnd)
add_track(52.3, 48.73, 50.5, 48.73, pcbnew.F_Cu, net_gnd)
add_via(50.5, 51.27, net_gnd)
add_track(52.3, 51.27, 50.5, 51.27, pcbnew.F_Cu, net_gnd)
add_via(59.5, 51.27, net_gnd)
add_track(57.7, 51.27, 59.5, 51.27, pcbnew.F_Cu, net_gnd)
add_via(59.5, 48.73, net_gnd)
add_track(57.7, 48.73, 59.5, 48.73, pcbnew.F_Cu, net_gnd)
# Caps GND
add_via(52.95, 33.5, net_gnd)
add_track(52.95, 35.0, 52.95, 33.5, pcbnew.F_Cu, net_gnd)
add_via(52.95, 66.5, net_gnd)
add_track(52.95, 65.0, 52.95, 66.5, pcbnew.F_Cu, net_gnd)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(board_path)

# 3. Export DSN
pcbnew.ExportSpecctraDSN(b, dsn_path)
print(f"Exported DSN to {dsn_path}")

# 4. Run Freerouting
cmd = [
    "/usr/bin/java", "-jar", jar_path,
    "-de", dsn_path,
    "-do", ses_path,
    "--gui.enabled=false",
    "-mp", "50",
    "-mt", "1"
]
print("Running Freerouting on remaining nets...")
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
    os.system(f"/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --severity-error --output drc_dc1a_fr_spine.json --format json {board_path}")
