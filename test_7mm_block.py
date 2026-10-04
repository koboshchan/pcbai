import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_7mm_block.kicad_pcb')
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))

neuron_range = range(0, 4)
nets = ['GND', '+12V', '-12V', '+5V_REF']
for i in range(64): nets.append(f'IN_{i}')
for j in neuron_range: nets.extend([f'SUM_POS_{j}', f'SUM_NEG_{j}', f'V_INV_{j}', f'V_SUM_{j}'])
    
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

lset = pcbnew.LSET.AllCuMask()
lset.AddLayer(pcbnew.F_Mask)
lset.AddLayer(pcbnew.B_Mask)

fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'
j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_top.SetReference('J_TOP')
j_top.SetValue('INPUTS_0_31_PWR')
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.0), pcbnew.FromMM(6.0)))
j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_top.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f'IN_{pnum-1}'])
    elif pnum == 33: p.SetNet(net_map['+12V'])
    elif pnum == 34: p.SetNet(net_map['-12V'])
    elif pnum == 35: p.SetNet(net_map['GND'])
    elif pnum == 36: p.SetNet(net_map['+5V_REF'])
    p.SetLayerSet(lset)
board.Add(j_top)

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

jumper_count = 0
def add_jumper(x1, y1, x2, y2, net_name):
    global jumper_count
    jumper_count += 1
    ref = f"W{jumper_count}"
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
        pad.SetLayerSet(lset)
        pad.SetNet(net_map[net_name])
        fp.Add(pad)
        
    line = pcbnew.PCB_SHAPE(fp)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    line.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    line.SetWidth(pcbnew.FromMM(0.2))
    line.SetLayer(pcbnew.F_Fab)
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

# Test Neuron 0 block:
# Y_top = 9.5 mm, Y_bot = 16.5 mm
# SUM_POS_0 at Y = 12.2 mm
# SUM_NEG_0 at Y = 13.8 mm
y_top = 9.5
y_pos = 13.3
y_neg = 14.5
y_bot = 18.3

add_track(4.0, y_pos, 86.0, y_pos, 'SUM_POS_0')
add_track(4.0, y_neg, 86.0, y_neg, 'SUM_NEG_0')

for col in range(32):
    xc = 5.0 + col * 2.54
    in_idx = col
    
    w_info = w1_data['weights'][0]['inputs'][in_idx]
    val_str = w_info.get('resistor_str', '10k')
    w_pol = w_info.get('polarity', 'positive')
    
    # Track from J_TOP pin (5.0 + col*2.54, 6.0) to Jumper Pad 1 (xc, y_top)
    add_track(xc, 6.0, xc, y_top, f'IN_{in_idx}')
    
    # Jumper across the block
    add_jumper(xc, y_top, xc, y_bot, f'IN_{in_idx}')
    
    if w_pol == 'positive':
        y_r = 12.1
        ref = f'R1_{in_idx}_0'
        add_res(ref, val_str, xc, y_r, -90, f'IN_{in_idx}', 'SUM_POS_0')
        # Track from Jumper Pad 1 to Pad 1 (y_r - 0.9125)
        add_track(xc, y_top, xc, y_r - 0.9125, f'IN_{in_idx}')
        # Track from Pad 2 (y_r + 0.9125) to SUM_POS_0
        add_track(xc, y_r + 0.9125, xc, y_pos, 'SUM_POS_0')
    else:
        y_r = 15.7
        ref = f'R1_{in_idx}_0'
        add_res(ref, val_str, xc, y_r, 90, f'IN_{in_idx}', 'SUM_NEG_0')
        # Track from Pad 2 (y_r - 0.9125) to SUM_NEG_0
        add_track(xc, y_r - 0.9125, xc, y_neg, 'SUM_NEG_0')
        # Track from Pad 1 (y_r + 0.9125) to Jumper Pad 2
        add_track(xc, y_r + 0.9125, xc, y_bot, f'IN_{in_idx}')

board.Save(PCB_PATH)
print("Saved test_7mm_block.kicad_pcb")
