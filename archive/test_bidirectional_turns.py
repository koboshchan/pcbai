def test_turns():
    # Let's test Column 4 with COL_X[4] = 68.5, x_bus_start = 63.50
    # x_pin = [61.87, 64.41, 66.95, 69.49]
    # x_bus = [63.50, 64.05, 64.60, 65.15, 65.70, 66.25, 66.80, 67.35]
    for p in range(4):
        x_pin = 61.87 + p * 2.54
        # even pin (r = 2*p + 1)
        r_even = 2 * p + 1
        x_bus_even = 63.50 + r_even * 0.55
        dx_even = x_pin - x_bus_even
        y_turn_even = (86.0 + (3 - p) * 1.5) if dx_even > 0 else (86.0 + p * 1.5)

        # odd pin (r = 2*p)
        r_odd = 2 * p
        x_bus_odd = 63.50 + r_odd * 0.55
        dx_odd = x_pin - x_bus_odd
        y_turn_odd = (79.0 + (3 - p) * 1.5) if dx_odd > 0 else (79.0 + p * 1.5)
        x_corr = (x_pin - 1.27) if dx_odd > 0 else (x_pin + 1.27)
        print(f"p={p}: x_pin={x_pin:.2f}")
        print(f"   odd  (r={r_odd}): x_bus={x_bus_odd:.2f} -> y_turn={y_turn_odd:.2f} -> x_corr={x_corr:.2f} (dx={dx_odd:+.2f})")
        print(f"   even (r={r_even}): x_bus={x_bus_even:.2f} -> y_turn={y_turn_even:.2f} -> x_pin={x_pin:.2f} (dx={dx_even:+.2f})")

test_turns()
