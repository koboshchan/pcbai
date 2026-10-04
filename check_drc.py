import json
import sys

def main():
    report_file = sys.argv[1] if len(sys.argv) > 1 else "drc_dc1a.json"
    with open(report_file) as f:
        data = json.load(f)
    
    violations = data.get("violations", [])
    unconnected = data.get("unconnected_items", [])
    print(f"Total violations: {len(violations)}, Unconnected: {len(unconnected)}")
    
    types = {}
    for v in violations:
        t = v.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    
    for t, c in types.items():
        print(f"  {t}: {c}")
        
    print("\nDetailed violations:")
    for i, v in enumerate(violations):
        print(f"[{i+1}] Type: {v.get('type')}, Description: {v.get('description')}")
        for item in v.get("items", []):
            print(f"     Item: {item.get('description')} at ({item.get('pos', {}).get('x', '?')}, {item.get('pos', {}).get('y', '?')})")

if __name__ == "__main__":
    main()
