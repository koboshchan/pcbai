import json

with open("weights_layer1.json") as f:
    w = json.load(f)

for j in range(16):
    b = w["weights"][j]["bias_float"]
    b_str = w["weights"][j].get("bias_resistor_str", "10k")
    rail = "-5V_REF" if b >= 0 else "+5V_REF"
    print(f"Neuron {j}: bias={b:+.4f}, R={b_str}, rail={rail}")
