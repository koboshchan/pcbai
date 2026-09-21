# Test bus routing for 8 columns to 2x20 headers
x_base_A = 7.87
x_base_B = 63.87
COL_X = [14.5, 24.5, 34.5, 44.5, 72.5, 82.5, 92.5, 102.5]

for c in range(8):
    base = x_base_A if c < 4 else x_base_B
    c_local = c % 4
    pins = [base + (c_local * 4 + p) * 2.54 for p in range(4)]
    print(f"Col {c}: COL_X={COL_X[c]}, Pins X: {[round(p, 2) for p in pins]}")
