import subprocess
import pcbnew
import json

b = pcbnew.LoadBoard("/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb")

# Clear all tracks
for t in list(b.GetTracks()):
    b.Delete(t)

def mm(v): return int(v * 1000000)

def add_track(x1, y1, x2, y2, layer, net, width=0.20):
    if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4: return
    trk = pcbnew.PCB_TRACK(b)
    trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    trk.SetWidth(mm(width))
    trk.SetLayer(layer)
    trk.SetNet(net)
    b.Add(trk)

def add_via(x, y, net, size=0.50, drill=0.30):
    via = pcbnew.PCB_VIA(b)
    via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    via.SetWidth(mm(size))
    via.SetDrill(mm(drill))
    via.SetNet(net)
    b.Add(via)

nets = {b.FindNet(i).GetNetname(): b.FindNet(i) for i in range(b.GetNetCount()) if b.FindNet(i)}

COL_X = [14.5, 24.5, 34.5, 44.5, 65.5, 75.5, 85.5, 95.5]
NEURON_Y = [18.0, 34.0, 50.0, 66.0]

for c in range(8):
    c_local = c % 4
    x_base = 9.87 if c < 4 else 61.87
    # Determine bus start
    # Let's check pins for this column:
    pins = [x_base + (c_local * 4 + p) * 2.54 for p in range(4)]
    min_pin = pins[0]
    max_pin = pins[3]

    # Place buses strictly to the left of min_pin, OR strictly to the right of max_pin
    # For c=0..3: min_pin is 9.87, 20.03, 30.19, 40.35. Resistor is at COL_X[c] (14.5, 24.5, 34.5, 44.5).
    # If bus is at COL_X[c] - 5.5, for c=0 that is 9.0 (left of 9.87!).
    # For all c, let's put bus strictly to the left of min_pin:
    # X_bus(r) = min_pin - 5.0 + r * 0.55
    # Then max X_bus is min_pin - 5.0 + 7 * 0.55 = min_pin - 1.15 < min_pin!
    # ALWAYS strictly to the left!
    x_bus_start = min_pin - 4.5

    for r in range(8):
        i = c * 8 + r
        net_in = nets[f"IN_{i}"]
        x_bus = x_bus_start + r * 0.50
        x_pad1 = COL_X[c] - 0.95
        y_first = NEURON_Y[0] + r * 1.5

        # Connect 4 neuron resistor Pad 1s on F.Cu to the via on the vertical bus
        for idx in range(4):
            y_res = NEURON_Y[idx] + r * 1.5
            add_track(x_pad1, y_res, x_bus, y_res, pcbnew.F_Cu, net_in, width=0.20)
            add_via(x_bus, y_res, net_in, size=0.50, drill=0.30)

        # All jog RIGHT: turn order r = 7 down to 0
        p = r // 2
        x_pin = pins[p]
        y_turn = 76.0 + (7 - r) * 1.8

        if r % 2 == 1:
            # ODD r -> EVEN pin at (x_pin, 92.73) on B.Cu
            add_track(x_bus, y_first, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
            add_track(x_bus, y_turn, x_pin, y_turn, pcbnew.B_Cu, net_in, width=0.20)
            add_track(x_pin, y_turn, x_pin, 92.73, pcbnew.B_Cu, net_in, width=0.20)
        else:
            # EVEN r -> ODD pin at (x_pin, 95.27) on In2.Cu
            x_corridor = x_pin + 1.27
            add_track(x_bus, y_first, x_bus, y_turn, pcbnew.B_Cu, net_in, width=0.20)
            add_via(x_bus, y_turn, net_in, size=0.50, drill=0.30)
            add_track(x_bus, y_turn, x_corridor, y_turn, pcbnew.In2_Cu, net_in, width=0.20)
            add_track(x_corridor, y_turn, x_corridor, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
            add_track(x_corridor, 97.5, x_pin, 97.5, pcbnew.In2_Cu, net_in, width=0.20)
            add_track(x_pin, 97.5, x_pin, 95.27, pcbnew.In2_Cu, net_in, width=0.20)

b.Save("/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb")
print("Saved inputs!")
