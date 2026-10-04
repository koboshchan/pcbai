import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_n0.kicad_pcb')

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))

# Nets
nets = ['GND', '+12V', '-12V', '+5V_REF', 'SUM_POS_0', 'SUM_NEG_0']
for i in range(32):
    nets.append(f'IN_{i}')
net_map = {}
for n in nets:
    netinfo = pcbnew.NETINFO_ITEM(board, n)
    board.Add(netinfo)
    net_map[n] = board.FindNet(n)

# Board outline 100 x 100 mm
corners = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
    seg.SetWidth(pcbnew.FromMM(0.15))
    seg.SetLayer(pcbnew.Edge_Cuts)
    board.Add(seg)

lset_fcu = pcbnew.LSET()
lset_fcu.AddLayer(pcbnew.F_Cu)
lset_fcu.AddLayer(pcbnew.F_Mask)
lset_fcu.AddLayer(pcbnew.B_Mask)

fp_res_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty'

def add_res(ref, val, x, y, rot, n1, n2):
    fp = pcbnew.FootprintLoad(fp_res_path, 'R_0805_2012Metric')
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    for pad in fp.Pads():
        if pad.GetNumber() == '1': pad.SetNet(net_map[n1])
        elif pad.GetNumber() == '2': pad.SetNet(net_map[n2])
    board.Add(fp)
    return fp

jumper_idx = 0
def add_jumper(x1, y1, x2, y2, net_name):
    global jumper_idx
    jumper_idx += 1
    ref = f"W{jumper_idx}"
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue("JUMPER")
    fp.SetKeywords("net tie")
    fp.SetFPID(pcbnew.LIB_ID("", "Jumper_Wire"))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    
    for pnum, (px, py) in [("1", (x1, y1)), ("1", (x2, y2))]:
        pad = pcbnew.PAD(fp)
        pad.SetNumber(pnum)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
        pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        pad.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
        pad.SetLayerSet(lset_fcu)
        pad.SetNet(net_map[net_name])
        fp.Add(pad)
        
    line = pcbnew.PCB_SHAPE(fp)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    line.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    line.SetWidth(pcbnew.FromMM(0.2))
    line.SetLayer(pcbnew.F_SilkS)
    fp.Add(line)
    
    board.Add(fp)
    return fp

def add_track(x1, y1, x2, y2, net_name, width=0.35):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(width))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(net_map[net_name])
    board.Add(t)
    return t

# 1. Horizontal buses for N0
# SUM_POS_0 at Y = 20.80 mm
# SUM_NEG_0 at Y = 22.20 mm
add_track(4.0, 20.80, 86.0, 20.80, 'SUM_POS_0')
add_track(4.0, 22.20, 86.0, 22.20, 'SUM_NEG_0')

# 2. Resistors for N0 (top half: inputs 0..31)
# Even columns at Y = 12.0 mm
# Odd columns at Y = 15.0 mm
# Pad 1 at cx - 0.95. If cx_res = X_col + 0.95, Pad 1 is at X_col!
# Pad 2 at cx_res + 0.95 = X_col + 1.90!
for col in range(32):
    x_col = 5.55 + col * 2.54
    y_res = 12.0 if (col % 2 == 0) else 15.0
    
    w_info = w1_data['weights'][0]['inputs'][col]
    val_str = w_info.get('resistor_str', '10k')
    w_pol = w_info.get('polarity', 'positive')
    bus_net = 'SUM_POS_0' if w_pol == 'positive' else 'SUM_NEG_0'
    bus_y = 20.80 if w_pol == 'positive' else 22.20
    
    # Resistor footprint
    ref = f'R1_{col}_0'
    add_res(ref, val_str, x_col + 0.95, y_res, 0, f'IN_{col}', bus_net)
    
    # Input track: comes from header (Y=7.0) to Pad 1 (x_col, y_res)
    add_track(x_col, 7.0, x_col, y_res, f'IN_{col}')
    
    # Track from Pad 1 (x_col, y_res) down to Jumper Pad 1 (x_col, 19.0)
    add_track(x_col, y_res, x_col, 19.0, f'IN_{col}')
    
    # Jumper across both buses from Y = 19.0 to Y = 24.0
    add_jumper(x_col, 19.0, x_col, 24.0, f'IN_{col}')
    
    # Track from Jumper Pad 2 (x_col, 24.0) down to next row (Y=26.0)
    add_track(x_col, 24.0, x_col, 26.0, f'IN_{col}')
    
    # Bus connection stub: from Pad 2 (x_col + 1.90, y_res) down to bus_y
    # Pad 2 X is x_col + 1.90
    # Next column is at x_col + 2.54
    # The gap between x_col + 1.90 and x_col + 2.54 is 0.64 mm.
    # A vertical stub down from x_col + 1.90 to bus_y:
    add_track(x_col + 1.90, y_res, x_col + 1.90, bus_y, bus_net)

board.Save(PCB_PATH)
print("Saved test_dc1_n0.kicad_pcb")
