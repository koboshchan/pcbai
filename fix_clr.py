with open('test_full_dc1_generation.py') as f:
    code = f.read()

# Fix bus X positions:
# Space by 1.0mm starting at X = 85.5
old_bus = """# Connect top and bottom summing buses in the right margin corridor
for s_idx in range(4):
    j = neuron_range[s_idx]
    x_pos_bus = 84.5 + s_idx * 1.5
    x_neg_bus = x_pos_bus + 0.75
    # Connect top y_pos to bot y_pos
    add_track(x_pos_bus, top_stages[s_idx]['y_pos'], x_pos_bus, bot_stages[s_idx]['y_pos'], f'SUM_POS_{j}')
    # Connect top y_neg to bot y_neg
    add_track(x_neg_bus, top_stages[s_idx]['y_neg'], x_neg_bus, bot_stages[s_idx]['y_neg'], f'SUM_NEG_{j}')"""

new_bus = """# Connect top and bottom summing buses in the right margin corridor
for s_idx in range(4):
    j = neuron_range[s_idx]
    x_pos_bus = 85.5 + s_idx * 2.0
    x_neg_bus = x_pos_bus + 1.0
    # Connect top y_pos to bot y_pos
    add_track(x_pos_bus, top_stages[s_idx]['y_pos'], x_pos_bus, bot_stages[s_idx]['y_pos'], f'SUM_POS_{j}')
    # Connect top y_neg to bot y_neg
    add_track(x_neg_bus, top_stages[s_idx]['y_neg'], x_neg_bus, bot_stages[s_idx]['y_neg'], f'SUM_NEG_{j}')"""

assert old_bus in code
code = code.replace(old_bus, new_bus)

# Fix horizontal bus end X to match x_neg_bus
code = code.replace("84.5 + s_idx * 1.5", "85.5 + s_idx * 2.0 + 1.0")

# Fix mounting holes: (3.0, 50.0), (97.0, 50.0), (50.0, 3.0), (50.0, 97.0) or corners
code = code.replace("[(4.0, 4.0), (BOARD_W - 4.0, 4.0), (4.0, BOARD_H - 4.0), (BOARD_W - 4.0, BOARD_H - 4.0)]",
                    "[(3.5, 50.0), (BOARD_W - 3.5, 50.0), (50.0, 3.0), (50.0, BOARD_H - 3.0)]")

with open('test_full_dc1_generation.py', 'w') as f:
    f.write(code)

