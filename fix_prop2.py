with open('test_full_dc1_generation.py') as f:
    code = f.read()

code = code.replace("if pol:\n        fp.SetDescription(f'polarity={pol}')", "")

with open('test_full_dc1_generation.py', 'w') as f:
    f.write(code)

