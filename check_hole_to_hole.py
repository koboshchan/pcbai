import json

with open("test_matrix_drc.json") as f:
    d = json.load(f)

for v in d.get("violations", []):
    if v["type"] in ["pth_inside_courtyard", "hole_to_hole"]:
        print(v["type"], v.get("description"), [it.get("pos") for it in v.get("items", [])])
        break
