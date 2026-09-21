#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
import os, subprocess, pcbnew, time, json

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
JAR_PATH = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

BOARD_PATH = os.path.join(WORKSPACE_DIR, "motherboard.kicad_pcb")
DSN_PATH = os.path.join(WORKSPACE_DIR, "motherboard.dsn")
SES_PATH = os.path.join(WORKSPACE_DIR, "motherboard.ses")
DRC_PATH = os.path.join(WORKSPACE_DIR, "drc_motherboard.json")

# Re-create motherboard from build_motherboard logic or load existing and strip tracks
b = pcbnew.LoadBoard(BOARD_PATH)
for trk in list(b.GetTracks()):
    b.Remove(trk)

# Set netclass rules
ns = b.GetDesignSettings().m_NetSettings
nc = ns.GetDefaultNetclass()
nc.SetTrackWidth(200000)   # 0.20 mm
nc.SetClearance(150000)    # 0.15 mm (enforces > 0.127 mm)
b.GetDesignSettings().m_TrackMinWidth = 150000

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(BOARD_PATH)

pcbnew.ExportSpecctraDSN(b, DSN_PATH)
print(f"Exported DSN with width=200um, clearance=150um: {DSN_PATH}")
