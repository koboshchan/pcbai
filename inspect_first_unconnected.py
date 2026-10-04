import json

with open("drc_dc1a.json") as f:
    d = json.load(f)

unconnected = d.get("unconnected_items", [])
if unconnected:
    print(json.dumps(unconnected[0], indent=2))
