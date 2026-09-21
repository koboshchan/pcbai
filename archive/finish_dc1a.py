import pcbnew

def mm(v): return int(v * 1000000)

board_path = "/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb"
b = pcbnew.LoadBoard(board_path)

nets = {b.FindNet(i).GetNetname(): b.FindNet(i) for i in range(b.GetNetCount()) if b.FindNet(i)}
net_gnd = nets["GND"]
net_s2 = nets["V_SUM_2"]
net_in30 = nets["IN_30"]

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

# 1. GND Connections
add_via(55.0, 48.73, net_gnd, size=0.50, drill=0.30)
add_track(52.3, 48.73, 55.0, 48.73, pcbnew.F_Cu, net_gnd, width=0.25) # pin 3
add_track(57.7, 48.73, 55.0, 48.73, pcbnew.F_Cu, net_gnd, width=0.25) # pin 12

add_via(55.0, 51.27, net_gnd, size=0.50, drill=0.30)
add_track(52.3, 51.27, 55.0, 51.27, pcbnew.F_Cu, net_gnd, width=0.25) # pin 5
add_track(57.7, 51.27, 55.0, 51.27, pcbnew.F_Cu, net_gnd, width=0.25) # pin 10

add_via(52.95, 40.5, net_gnd, size=0.50, drill=0.30)
add_track(52.95, 42.0, 52.95, 40.5, pcbnew.F_Cu, net_gnd, width=0.25)

add_via(58.95, 56.5, net_gnd, size=0.50, drill=0.30)
add_track(58.95, 58.0, 58.95, 56.5, pcbnew.F_Cu, net_gnd, width=0.25)

# 2. IN_30 connection: from (44.50, 43.95) to Pad 1 of R1_30_0 at (43.55, 27.0)
# Route on B.Cu to avoid F.Cu resistors
add_via(44.50, 43.95, net_in30, size=0.50, drill=0.30)
add_track(44.50, 43.95, 44.50, 27.0, pcbnew.B_Cu, net_in30, width=0.20)
add_via(44.50, 27.0, net_in30, size=0.50, drill=0.30)
add_track(44.50, 27.0, 43.55, 27.0, pcbnew.F_Cu, net_in30, width=0.20)

# 3. V_SUM_2: U1 Pin 8 (57.7, 53.81) to Pad 35 of J_SLOT_A at (54.05, 95.27)
add_track(57.7, 53.81, 57.7, 55.5, pcbnew.F_Cu, net_s2, width=0.25)
add_track(57.7, 55.5, 52.78, 55.5, pcbnew.F_Cu, net_s2, width=0.25)
add_via(52.78, 55.5, net_s2, size=0.50, drill=0.30)
add_track(52.78, 55.5, 52.78, 97.5, pcbnew.B_Cu, net_s2, width=0.25)
add_track(52.78, 97.5, 54.05, 97.5, pcbnew.B_Cu, net_s2, width=0.25)
add_track(54.05, 97.5, 54.05, 95.27, pcbnew.B_Cu, net_s2, width=0.25)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())

b.Save(board_path)
print("Finished manual routing and filled zones on DC1A")
