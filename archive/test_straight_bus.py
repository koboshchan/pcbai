import sys

x_base_A = 7.87
x_base_B = 63.87
for c in range(8):
    base = x_base_A if c < 4 else x_base_B
    c_local = c % 4
    print(f"--- Column {c} ---")
    for r in range(8):
        p = r // 2
        x_pin = base + (c_local * 4 + p) * 2.54
        if r % 2 == 1:
            # Even pin (Pin 2, 4, 6, 8) at (x_pin, 92.73)
            x_bus = x_pin
            print(f"  r={r} (Even pin {2*p+2}): x_bus = {x_bus:.3f} (straight to pin)")
        else:
            # Odd pin (Pin 1, 3, 5, 7) at (x_pin, 95.27)
            # Corridor at x_pin + 1.27
            x_bus = x_pin + 1.27
            print(f"  r={r} (Odd pin {2*p+1}):  x_bus = {x_bus:.3f} (corridor to 97.5, jog 1.27 to pin)")
