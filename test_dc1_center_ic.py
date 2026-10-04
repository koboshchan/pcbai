import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_center_ic.kicad_pcb')

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))

neuron_range = range(0, 4)
nets = ['GND', '+12V', '-12V', '+5V_REF']
for i in range(64):
    nets.append(f'IN_{i}')
for j in neuron_range:
    nets.extend([f'SUM_POS_{j}', f'SUM_NEG_{j}', f'V_INV_{j}', f'V_SUM_{j}'])
    
net_map = {}
for n in nets:
    netinfo = pcbnew.NETINFO_ITEM(board, n)
    board.Add(netinfo)
    net_map[n] = board.FindNet(n)

# Board outline
corners = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
    seg.SetWidth(pcbnew.FromMM(0.15))
    seg.SetLayer(pcbnew.Edge_Cuts)
    board.Add(seg)

# Mounting holes
fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for idx, (hx, hy) in enumerate([(4.0, 4.0), (96.0, 4.0), (4.0, 96.0), (96.0, 96.0)]):
    mh = pcbnew.FootprintLoad(fp_mh_path, 'MountingHole_3.2mm_M3')
    mh.SetReference(f'MH{idx+1}')
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
    board.Add(mh)

fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'

# Connectors: J_TOP at Y = 11.0, J_BOT at Y = 89.0
j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_top.SetReference('J_TOP')
j_top.SetValue('INPUTS_0_31_PWR')
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.55), pcbnew.FromMM(11.0)))
j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_top.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f'IN_{pnum-1}'])
    elif pnum == 33: p.SetNet(net_map['+12V'])
    elif pnum == 34: p.SetNet(net_map['-12V'])
    elif pnum == 35: p.SetNet(net_map['GND'])
    elif pnum == 36: p.SetNet(net_map['+5V_REF'])
board.Add(j_top)

j_bot = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_bot.SetReference('J_BOT')
j_bot.SetValue('INPUTS_32_63_SUM')
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.55), pcbnew.FromMM(89.0)))
j_bot.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_bot.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f'IN_{32+pnum-1}'])
    else:
        j_local = pnum - 33
        j_global = neuron_range[j_local]
        p.SetNet(net_map[f'V_SUM_{j_global}'])
board.Add(j_bot)

fp_res_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty'
fp_ic_path  = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_SO.pretty'
fp_cap_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Capacitor_SMD.pretty'

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

def add_cap(ref, val, x, y, rot, n1, n2):
    fp = pcbnew.FootprintLoad(fp_cap_path, 'C_0805_2012Metric')
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

# Center Corridor ICs: U1 at (35, 49), U2 at (65, 49)
u1 = pcbnew.FootprintLoad(fp_ic_path, 'SOIC-14_3.9x8.7mm_P1.27mm')
u1.SetReference('U1')
u1.SetValue("TL074_INV")
u1.Reference().SetVisible(False)
u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(35.0), pcbnew.FromMM(49.0)))
n0, n1, n2, n3 = neuron_range[0], neuron_range[1], neuron_range[2], neuron_range[3]
u1_pdict = {
    '1': f'V_INV_{n0}', '2': f'SUM_NEG_{n0}', '3': 'GND',
    '4': '+12V',
    '5': 'GND', '6': f'SUM_NEG_{n1}', '7': f'V_INV_{n1}',
    '8': f'V_INV_{n2}', '9': f'SUM_NEG_{n2}', '10': 'GND',
    '11': '-12V',
    '12': 'GND', '13': f'SUM_NEG_{n3}', '14': f'V_INV_{n3}'
}
for pad in u1.Pads():
    pnum = pad.GetNumber()
    if pnum in u1_pdict: pad.SetNet(net_map[u1_pdict[pnum]])
board.Add(u1)

u2 = pcbnew.FootprintLoad(fp_ic_path, 'SOIC-14_3.9x8.7mm_P1.27mm')
u2.SetReference('U2')
u2.SetValue("TL074_SUM")
u2.Reference().SetVisible(False)
u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(65.0), pcbnew.FromMM(49.0)))
u2_pdict = {
    '1': f'V_SUM_{n0}', '2': f'SUM_POS_{n0}', '3': 'GND',
    '4': '+12V',
    '5': 'GND', '6': f'SUM_POS_{n1}', '7': f'V_SUM_{n1}',
    '8': f'V_SUM_{n2}', '9': f'SUM_POS_{n2}', '10': 'GND',
    '11': '-12V',
    '12': 'GND', '13': f'SUM_POS_{n3}', '14': f'V_SUM_{n3}'
}
for pad in u2.Pads():
    pnum = pad.GetNumber()
    if pnum in u2_pdict: pad.SetNet(net_map[u2_pdict[pnum]])
board.Add(u2)

# Decoupling Caps
add_cap("C_U1_POS", "100n", 35.0, 43.0, 0, "+12V", "GND")
add_cap("C_U1_NEG", "100n", 35.0, 55.0, 0, "-12V", "GND")
add_cap("C_U2_POS", "100n", 65.0, 43.0, 0, "+12V", "GND")
add_cap("C_U2_NEG", "100n", 65.0, 55.0, 0, "-12V", "GND")

# Feedback & Coupling Resistors at X = 48..52, Y = 45..53
for local_idx, j in enumerate(neuron_range):
    y_row = 45.0 + local_idx * 2.5
    add_res(f'Rf1_N{j}', '10k', 47.0, y_row, 0, f'V_INV_{j}', f'SUM_NEG_{j}')
    add_res(f'Rc_N{j}',  '10k', 50.5, y_row, 0, f'V_INV_{j}', f'SUM_POS_{j}')
    add_res(f'Rf2_N{j}', '10k', 54.0, y_row, 0, f'V_SUM_{j}', f'SUM_POS_{j}')
    
    b_val = w1_data['weights'][j]['bias_float']
    b_str = w1_data['weights'][j].get('bias_resistor_str', '10k')
    bus_net = f'SUM_POS_{j}' if b_val >= 0 else f'SUM_NEG_{j}'
    add_res(f'Rb_N{j}', b_str, 78.0, y_row, 0, '+5V_REF', bus_net)

# Synaptic Resistor Matrix
top_neuron_y = [15.0, 22.0, 29.0, 36.0]
bot_neuron_y = [59.0, 66.0, 73.0, 80.0]

for col in range(32):
    cx = 5.55 + col * 2.54
    in_top = col
    y_offset = 0.0 if (col % 2 == 0) else 3.2
    for local_n in range(4):
        j = neuron_range[local_n]
        cy = top_neuron_y[local_n] + y_offset
        w_info = w1_data['weights'][j]['inputs'][in_top]
        val_str = w_info.get('resistor_str', 'OPEN')
        w_pol = w_info.get('polarity', 'positive')
        bus_net = f'SUM_POS_{j}' if w_pol == 'positive' else f'SUM_NEG_{j}'
        ref = f'R1_{in_top}_{local_n}'
        add_res(ref, val_str, cx + 0.95, cy, 0, f'IN_{in_top}', bus_net)

    in_bot = 32 + col
    for local_n in range(4):
        j = neuron_range[local_n]
        cy = bot_neuron_y[local_n] + y_offset
        w_info = w1_data['weights'][j]['inputs'][in_bot]
        val_str = w_info.get('resistor_str', 'OPEN')
        w_pol = w_info.get('polarity', 'positive')
        bus_net = f'SUM_POS_{j}' if w_pol == 'positive' else f'SUM_NEG_{j}'
        ref = f'R1_{in_bot}_{local_n}'
        add_res(ref, val_str, cx + 0.95, cy, 0, f'IN_{in_bot}', bus_net)

board.Save(PCB_PATH)
print("Saved", PCB_PATH)
