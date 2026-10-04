with open('test_7mm_block.py') as f:
    code = f.read()

# Change line layer from F_SilkS to F_Fab
code = code.replace("line.SetLayer(pcbnew.F_SilkS)", "line.SetLayer(pcbnew.F_Fab)")

# Update spacing:
# y_top = 9.5
# y_r_pos = 9.5 + 2.6 = 12.1
# y_pos = 12.1 + 1.2 = 13.3
# y_neg = 13.3 + 1.2 = 14.5
# y_r_neg = 14.5 + 1.2 = 15.7
# y_bot = 15.7 + 2.6 = 18.3
code = code.replace("""y_top = 9.5
y_pos = 12.2
y_neg = 13.8
y_bot = 16.5""",
"""y_top = 9.5
y_pos = 13.3
y_neg = 14.5
y_bot = 18.3""")

code = code.replace("y_r = y_top + 1.8", "y_r = 12.1")
code = code.replace("y_r = y_bot - 1.8", "y_r = 15.7")

with open('test_7mm_block.py', 'w') as f:
    f.write(code)

