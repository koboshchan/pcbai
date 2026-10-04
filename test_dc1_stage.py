import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_stage.kicad_pcb')
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))

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

fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for idx, (hx, hy) in enumerate([(4.0, 4.0), (96.0, 4.0), (4.0, 96.0), (96.0, 96.0)]):
    mh = pcbnew.FootprintLoad(fp_mh_path, 'MountingHole_3.2mm_M3')
    mh.SetReference(f'MH{idx+1}')
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
    board.Add(mh)

lset = pcbnew.LSET.AllCuMask()
lset.AddLayer(pcbnew.F_Mask)
lset.AddLayer(pcbnew.B_Mask)

fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'
j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_top.SetReference('J_TOP')
j_top.SetValue('INPUTS_0_31_PWR')
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(6.5), pcbnew.FromMM(10.0)))
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
    line.SetLayer(pcbnew.F_SilkS)
    fp.Add(line)
    
    board.Add(fp)
    return fp

def add_track(x1, y1, x2, y2, net_name, width=0.40):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(width))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(net_map[net_name])
    board.Add(t)
    return t

# Let's test routing Neuron 0 (inputs 0..31):
# J_TOP pins are at (6.5 + col*2.54, 8.0)
# Summing buses:
add_track(5.0, 15.5, 87.0, 15.5, 'SUM_POS_0')
add_track(5.0, 17.5, 87.0, 17.5, 'SUM_NEG_0')

for col in range(32):
    xc = 6.5 + col * 2.54
    in_idx = col
    
    w_info = w1_data['weights'][0]['inputs'][in_idx]
    val_str = w_info.get('resistor_str', '10k')
    w_pol = w_info.get('polarity', 'positive')
    
    # Track from J_TOP pin to Jumper Pad 1 at Y = 10.5
    add_track(xc, 10.0, xc, 11.5, f'IN_{in_idx}')
    
    # Jumper over the buses: from Y = 10.5 to Y = 20.5
    add_jumper(xc, 11.5, xc, 23.5, f'IN_{in_idx}')
    
    if w_pol == 'positive':
        # Resistor above SUM_POS_0 at Y = 12.5 (vertical, rot=90)
        # Pad 1 is at Y = 12.5 - 0.9125 = 11.5875 (net: IN_idx)
        # Pad 2 is at Y = 12.5 + 0.9125 = 13.4125 (net: SUM_POS_0)
        ref = f'R1_{in_idx}_0'
        add_res(ref, val_str, xc, 13.0, -90, f'IN_{in_idx}', 'SUM_POS_0')
        # Track from Jumper Pad 1 (10.5) to Pad 1 (11.5875)
        add_track(xc, 11.5, xc, 12.0875, f'IN_{in_idx}')
        # Track from Pad 2 (13.4125) to SUM_POS_0 (14.5)
        add_track(xc, 13.9125, xc, 15.5, 'SUM_POS_0')
    else:
        # Resistor below SUM_NEG_0 at Y = 18.5 (vertical, rot=270, so Pad 2 is at top, Pad 1 is at bottom)
        # With rot=270: Pad 1 is at Y = 18.5 + 0.9125 = 19.4125 (net: IN_idx)
        # Pad 2 is at Y = 18.5 - 0.9125 = 17.5875 (net: SUM_NEG_0)
        ref = f'R1_{in_idx}_0'
        add_res(ref, val_str, xc, 20.0, 90, f'IN_{in_idx}', 'SUM_NEG_0')
        # Track from Pad 2 (17.5875) to SUM_NEG_0 (16.5)
        add_track(xc, 19.0875, xc, 17.5, 'SUM_NEG_0')
        # Track from Pad 1 (19.4125) to Jumper Pad 2 (20.5)
        add_track(xc, 20.9125, xc, 23.5, f'IN_{in_idx}')

board.Save(PCB_PATH)
print("Saved test_dc1_stage.kicad_pcb")
