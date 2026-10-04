with open('test_full_dc1_generation.py') as f:
    code = f.read()

# Exact planar bus formula:
# Neuron 0: x_pos = 92.0, x_neg = 91.0
# Neuron 1: x_pos = 90.0, x_neg = 89.0
# Neuron 2: x_pos = 88.0, x_neg = 87.0
# Neuron 3: x_pos = 86.0, x_neg = 85.0
# x_pos = 92.0 - s_idx * 2.0
# x_neg = 91.0 - s_idx * 2.0

old_connect = """# Connect top and bottom summing buses in the right margin corridor
# Monotonic planar river router: X increases with Y
for s_idx in range(4):
    j = neuron_range[s_idx]
    x_pos_bus = 85.0 + s_idx * 2.0
    x_neg_bus = x_pos_bus + 1.0
    # Connect top y_pos to bot y_pos
    add_track(x_pos_bus, top_stages[s_idx]['y_pos'], x_pos_bus, bot_stages[s_idx]['y_pos'], f'SUM_POS_{j}')
    # Connect top y_neg to bot y_neg
    add_track(x_neg_bus, top_stages[s_idx]['y_neg'], x_neg_bus, bot_stages[s_idx]['y_neg'], f'SUM_NEG_{j}')"""

new_connect = """# Connect top and bottom summing buses in the right margin corridor
# Planar non-crossing river router:
for s_idx in range(4):
    j = neuron_range[s_idx]
    x_pos_bus = 92.0 - s_idx * 2.0
    x_neg_bus = 91.0 - s_idx * 2.0
    # Connect top y_pos to bot y_pos
    add_track(x_pos_bus, top_stages[s_idx]['y_pos'], x_pos_bus, bot_stages[s_idx]['y_pos'], f'SUM_POS_{j}')
    # Connect top y_neg to bot y_neg
    add_track(x_neg_bus, top_stages[s_idx]['y_neg'], x_neg_bus, bot_stages[s_idx]['y_neg'], f'SUM_NEG_{j}')"""

assert old_connect in code
code = code.replace(old_connect, new_connect)

# Fix horizontal bus end points in top and bottom halves:
old_top_bus = """for s_idx in range(4):
    j = neuron_range[s_idx]
    cfg = top_stages[s_idx]
    x_p = 85.0 + s_idx * 2.0
    x_n = x_p + 1.0
    add_track(4.0, cfg['y_pos'], x_p, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(4.0, cfg['y_neg'], x_n, cfg['y_neg'], f'SUM_NEG_{j}')"""

new_top_bus = """for s_idx in range(4):
    j = neuron_range[s_idx]
    cfg = top_stages[s_idx]
    x_p = 92.0 - s_idx * 2.0
    x_n = 91.0 - s_idx * 2.0
    add_track(4.0, cfg['y_pos'], x_p, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(4.0, cfg['y_neg'], x_n, cfg['y_neg'], f'SUM_NEG_{j}')"""

assert old_top_bus in code
code = code.replace(old_top_bus, new_top_bus)

old_bot_bus = """for s_idx in range(4):
    j = neuron_range[s_idx]
    cfg = bot_stages[s_idx]
    x_p = 85.0 + s_idx * 2.0
    x_n = x_p + 1.0
    add_track(4.0, cfg['y_pos'], x_p, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(4.0, cfg['y_neg'], x_n, cfg['y_neg'], f'SUM_NEG_{j}')"""

new_bot_bus = """for s_idx in range(4):
    j = neuron_range[s_idx]
    cfg = bot_stages[s_idx]
    x_p = 92.0 - s_idx * 2.0
    x_n = 91.0 - s_idx * 2.0
    add_track(4.0, cfg['y_pos'], x_p, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(4.0, cfg['y_neg'], x_n, cfg['y_neg'], f'SUM_NEG_{j}')"""

assert old_bot_bus in code
code = code.replace(old_bot_bus, new_bot_bus)

with open('test_full_dc1_generation.py', 'w') as f:
    f.write(code)

