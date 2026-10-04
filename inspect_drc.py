import json
from collections import Counter

with open("drc_dc1a.json") as f:
    d = json.load(f)

violations = d.get("violations", [])
unconnected = d.get("unconnected_items", [])

print(f"Total violations: {len(violations)}")
print(f"Total unconnected items: {len(unconnected)}")

v_types = Counter(v.get("type") for v in violations)
print("\nViolation types:")
for t, c in v_types.items():
    print(f"  {t}: {c}")

print("\nSample violations:")
for t in v_types:
    print(f"\n=== VIOLATIONS: {t} ===")
    items_t = [v for v in violations if v.get("type") == t]
    for v in items_t[:10]:
        print(" ", v.get("description"), [item.get("description") for item in v.get("items", [])])

net_unconnected = Counter()
for u in unconnected:
    desc = u.get("description", "")
    items_desc = [item.get("description", "") for item in u.get("items", [])]
    for idesc in items_desc:
        if "[" in idesc and "]" in idesc:
            net = idesc.split("[")[1].split("]")[0]
            net_unconnected[net] += 1
print("\nSample unconnected IN_0 items:")
for u in unconnected:
    items_desc = [item.get("description", "") for item in u.get("items", [])]
    if any("IN_0" in s for s in items_desc):
        print(" ", u.get("description"), items_desc)


