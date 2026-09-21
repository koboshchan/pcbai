import sys
sys.path.append("/Users/lucaszhang/pcbai")

# Let's verify coordinates
COL_X = [14.5, 24.5, 34.5, 44.5, 65.5, 75.5, 85.5, 95.5]
for c in range(8):
    c_local = c % 4
    x_base = 10.87 if c < 4 else 61.87
    x_pin0 = x_base + c_local * 10.16
    x_bus_start = COL_X[c] - 5.00
    p3_pin = x_pin0 + 3 * 2.54
    p3_bus = x_bus_start + 7 * 0.55
    print(f"Col {c}: pin0={x_pin0:.2f}, bus_start={x_bus_start:.2f}, p3_pin={p3_pin:.2f}, p3_bus={p3_bus:.2f}")
    assert x_bus_start < x_pin0, f"Col {c} bus must start before pin0!"
    assert p3_bus < p3_pin, f"Col {c} last bus must be before last pin!"
print("All 8 columns satisfy strictly planar east-turning geometry!")
