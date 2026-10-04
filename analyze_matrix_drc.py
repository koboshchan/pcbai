import json
from collections import Counter

with open("test_matrix_drc.json") as f:
    d = json.load(f)

v_list = d.get("violations", [])
print(f"Total violations: {len(v_list)}")
type_counts = Counter(v["type"] for v in v_list)
print("Violation types:", type_counts)

for v_type, count in type_counts.items():
    print(f"\n--- Examples of {v_type} ---")
    examples = [v for v in v_list if v["type"] == v_type][:3]
    for ex in examples:
        print(ex.get("description"))
        print([it.get("item") for it in ex.get("items", [])])
