import os
import subprocess
import pcbnew
import time

board_path = "/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb"
dsn_path = "/Users/lucaszhang/pcbai/test_dc1a.dsn"
ses_path = "/Users/lucaszhang/pcbai/test_dc1a.ses"
jar_path = "/Users/lucaszhang/.kicad-mcp/freerouting.jar"

# 1. Prepare clean skeleton board with GND vias
os.system(f"/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 /Users/lucaszhang/pcbai/generate_clean_dc1_board.py")

# 2. Export to DSN
b = pcbnew.LoadBoard(board_path)
pcbnew.ExportSpecctraFile(board_path, dsn_path)
print(f"Exported DSN to {dsn_path}")

# 3. Run Freerouting CLI directly with -mp 60 -mt 1
cmd = [
    "/usr/bin/java", "-jar", jar_path,
    "-de", dsn_path,
    "-do", ses_path,
    "--gui.enabled=false",
    "-mp", "60",
    "-mt", "1"
]
print("Running Freerouting CLI:", " ".join(cmd))
t0 = time.time()
res = subprocess.run(cmd, capture_output=True, text=True)
print(f"Freerouting completed in {time.time()-t0:.1f}s, exit code: {res.returncode}")

# 4. Import SES
if os.path.exists(ses_path):
    pcbnew.ImportSpecctraSES(b, ses_path)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(board_path)
    print(f"Imported SES and saved to {board_path}")
    
    # 5. Run DRC
    os.system(f"/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --output drc_dc1a_direct.json --format json {board_path}")
else:
    print("SES not generated!")
