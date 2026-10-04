import json

with open("test_matrix_drc.json") as f:
    d = json.load(f)

for v in d.get("violations", []):
    if v["type"] in ["pth_inside_courtyard", "courtyards_overlap", "tracks_crossing"]:
        print(v["type"], v.get("description"), [it.get("pos") for it in v.get("items", [])])
