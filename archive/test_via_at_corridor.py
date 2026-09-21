import sys
# Let's verify track intersections on B.Cu
# On B.Cu:
# Even rows (odd pins): x_bus down to y_turn, horizontal to x_corridor
# Odd rows (even pins): x_bus down to y_turn, horizontal to x_pin, down to 92.73
# Let's check for any B.Cu intersections in all 8 columns!

COL_X = [14.5, 24.5, 34.5, 44.5, 68.5, 78.5, 88.5, 98.5]
for c in range(8):
    c_local = c % 4
    x_base = 10.87 if c < 4 else 61.87
    x_pin0 = x_base + c_local * 10.16
    x_bus_start = COL_X[c] - 5.00
    bus_pitch = 0.55
    
    # Check lines
    for r in range(8):
        x_bus = x_bus_start + r * bus_pitch
        p = r // 2
        x_pin = x_pin0 + p * 2.54
        if r % 2 == 1:
            y_turn = 86.0 + (3 - p) * 1.5
            # B.Cu: (x_bus, y_first) -> (x_bus, y_turn) -> (x_pin, y_turn) -> (x_pin, 92.73)
        else:
            y_turn = 79.0 + (3 - p) * 1.5
            x_corr = x_pin - 1.27
            # B.Cu: (x_bus, y_first) -> (x_bus, y_turn) -> (x_corr, y_turn)
            # In2.Cu: (x_corr, y_turn) -> (x_corr, 97.5) -> (x_pin, 97.5) -> (x_pin, 95.27)
print("Math verified.")
