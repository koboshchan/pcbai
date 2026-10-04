import json

with open("test_matrix_drc.json") as f:
    d = json.load(f)

for v in d.get("violations", []):
    if v["type"] == "hole_clearance":
        print(v.get("description"), [it.get("pos") for it in v.get("items", [])])
