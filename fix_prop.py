with open('test_full_dc1_generation.py') as f:
    code = f.read()

code = code.replace("fp.SetProperty('Description', f'polarity={pol}')",
                    "fp.SetDescription(f'polarity={pol}')")

with open('test_full_dc1_generation.py', 'w') as f:
    f.write(code)

