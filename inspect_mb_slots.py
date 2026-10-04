with open("generate_motherboard_v8_mcu.py") as f:
    text = f.read()

import re
matches = re.findall(r"slot_names.*?(?=def |\Z)", text, re.DOTALL)
if matches:
    print(matches[0][:2000])
