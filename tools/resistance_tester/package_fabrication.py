#!/usr/bin/env python3
"""Package an explicit single-sided manufacturing allowlist and audit exports."""
import csv, hashlib, json, re, zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ["FABRICATION.txt", "fingerprint-B_Cu.gbl", "fingerprint-B_Mask.gbs",
         "fingerprint-F_Mask.gts", "fingerprint-F_Silkscreen.gto",
         "fingerprint-Edge_Cuts.gm1", "fingerprint.drl"]

def package():
    fab = ROOT / "fabrication"
    rows = list(csv.DictReader((ROOT / "BOM.csv").open(newline="")))
    counts = Counter(r["Reference"][0] for r in rows)
    assert counts == {"J": 4, "R": 20, "C": 20}, counts
    assert all(r["Side"] == "Bottom" for r in rows if r["Reference"].startswith("C"))
    copper = (fab / "fingerprint-B_Cu.gbl").read_text()
    assert "Copper,L2,Bot" in copper
    drill = (fab / "fingerprint.drl").read_text()
    active = None
    holes = Counter()
    for line in drill.splitlines():
        if re.fullmatch(r"T[12]", line):
            active = line
        elif re.fullmatch(r"X[-\d.]+Y[-\d.]+", line):
            assert active is not None
            holes[active] += 1
    assert holes == {"T1": 40, "T2": 60}, holes
    edge = (fab / "fingerprint-Edge_Cuts.gm1").read_text()
    vertices = {(int(x)/1e6, int(y)/1e6) for x,y in re.findall(r"X(-?\d+)Y(-?\d+)D0[12]", edge)}
    assert vertices == {(0,0),(100,0),(100,-70),(0,-70)}, vertices
    archive = ROOT / "fingerprint-fabrication.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(fab / name, name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert z.namelist() == FILES
    report = dict(component_counts=dict(counts), drill_holes=dict(holes),
                  outline_mm=[100,70], copper_files=["fingerprint-B_Cu.gbl"],
                  archive_files=FILES, sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    (ROOT / "evidence/fabrication-audit.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    package()
