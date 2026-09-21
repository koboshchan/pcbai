#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
import os, subprocess, pcbnew, time, json
import build_motherboard as bm

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_PATH = os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb")
DSN_PATH = os.path.join(WORKSPACE_DIR, "motherboard.dsn")
SES_PATH = os.path.join(WORKSPACE_DIR, "motherboard.ses")
DRC_PATH = os.path.join(WORKSPACE_DIR, "drc_motherboard.json")

# Build skeleton WITHOUT any bad pre-routed tracks
b = pcbnew.LoadBoard(BOARD_PATH)

# Remove all tracks and vias
for trk in list(b.GetTracks()):
    b.Remove(trk)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(BOARD_PATH)

pcbnew.ExportSpecctraDSN(b, DSN_PATH)
print(f"Exported clean DSN: {DSN_PATH}")

cmd = [
    "/usr/bin/java", "-jar", JAR_PATH,
    "-de", DSN_PATH,
    "-do", SES_PATH,
    "--gui.enabled=false",
    "-mp", "150",
    "-mt", "1"
]
t0 = time.time()
res = subprocess.run(cmd, capture_output=True, text=True)
print(f"Freerouting finished in {time.time()-t0:.1f}s, exit code: {res.returncode}")

if os.path.exists(SES_PATH):
    b = pcbnew.LoadBoard(BOARD_PATH)
    pcbnew.ImportSpecctraSES(b, SES_PATH)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(BOARD_PATH)

    cmd_drc = f"{KICAD_CLI} pcb drc --severity-error --output {DRC_PATH} --format json {BOARD_PATH}"
    subprocess.run(cmd_drc, shell=True)
    with open(DRC_PATH) as f:
        d = json.load(f)
    uncon = len(d.get("unconnected_items", []))
    viols = len(d.get("violations", []))
    print(f"[Clean Motherboard] DRC Result: {uncon} unconnected, {viols} errors")
