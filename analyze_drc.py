import json
from collections import Counter

with open("drc_dc1a.json") as f:
    drc = json.load(f)

violations = drc.get("violations", [])
unconnected = drc.get("unconnected_items", [])

v_types = Counter(v.get("type", "unknown") for v in violations)
print("Violations summary:", len(violations))
for k, v in v_types.items():
    print(f"  {k}: {v}")

print("\nSample violations:")
for v in violations[:10]:
    print(f"  Type: {v.get('type')}, Description: {v.get('description')}")
    for item in v.get("items", []):
        print(f"    Item: {item}")

print("\nUnconnected items summary:", len(unconnected))
u_nets = Counter(u.get("net", u.get("description", "unknown")) for u in unconnected)
for k, v in u_nets.most_common(10):
    print(f"  {k}: {v}")
