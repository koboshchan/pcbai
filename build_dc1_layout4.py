
import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')
PCB_PATH  = os.path.join(WORKSPACE, 'test_dc1_layout4.kicad_pcb')

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

# 1. Rules
ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.40))

# 2. Add Nets
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

# 3. Outline (100 x 100 mm)
corners = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i][0]), pcbnew.FromMM(corners[i][1])))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(corners[i+1][0]), pcbnew.FromMM(corners[i+1][1])))
    seg.SetWidth(pcbnew.FromMM(0.15))
    seg.SetLayer(pcbnew.Edge_Cuts)
    board.Add(seg)

# 4. Mounting Holes M3 (4mm inset)
fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for idx, (hx, hy) in enumerate([(4.0, 4.0), (96.0, 4.0), (4.0, 96.0), (96.0, 96.0)]):
    mh = pcbnew.FootprintLoad(fp_mh_path, 'MountingHole_3.2mm_M3')
    mh.SetReference(f'MH{idx+1}')
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
    board.Add(mh)

# 5. Connectors:
# J_TOP: 1x18 at Y = 10.0, X = 28.4..71.6 (rot = 90 degrees points positive X)
fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'

j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x18_P2.54mm_Vertical')
j_top.SetReference('J_TOP')
j_top.SetValue('INPUTS_0_15_PWR')
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(28.4), pcbnew.FromMM(10.0)))
j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T)) # Points +X
for p in j_top.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 16: p.SetNet(net_map[f'IN_{pnum-1}'])
    elif pnum == 17: p.SetNet(net_map['+12V'])
    elif pnum == 18: p.SetNet(net_map['-12V'])
board.Add(j_top)

# J_BOT: 1x18 at Y = 90.0mm, X = 28.4..71.6 (rot = 90 degrees points positive X)
j_bot = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x18_P2.54mm_Vertical')
j_bot.SetReference('J_BOT')
j_bot.SetValue('INPUTS_16_31_PWR')
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(28.4), pcbnew.FromMM(90.0)))
j_bot.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T)) # Points +X
for p in j_bot.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 16: p.SetNet(net_map[f'IN_{16+pnum-1}'])
    elif pnum == 17: p.SetNet(net_map['GND'])
    elif pnum == 18: p.SetNet(net_map['+5V_REF'])
board.Add(j_bot)

# J_LEFT: 1x18 at X = 8.0mm, Y = 28.4..71.6 (rot = 0 points positive Y)
j_left = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x18_P2.54mm_Vertical')
j_left.SetReference('J_LEFT')
j_left.SetValue('INPUTS_32_47')
j_left.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(8.0), pcbnew.FromMM(28.4)))
for p in j_left.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 16: p.SetNet(net_map[f'IN_{32+pnum-1}'])
    else: p.SetNet(net_map['GND'])
board.Add(j_left)

# J_RIGHT: 1x20 at X = 92.0mm, Y = 25.87..74.13 (rot = 0 points positive Y)
j_right = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x20_P2.54mm_Vertical')
j_right.SetReference('J_RIGHT')
j_right.SetValue('INPUTS_48_63_SUM')
j_right.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(92.0), pcbnew.FromMM(25.87)))
for p in j_right.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 16: p.SetNet(net_map[f'IN_{48+pnum-1}'])
    else:
        j_local = pnum - 17
        j_global = neuron_range[j_local]
        p.SetNet(net_map[f'V_SUM_{j_global}'])
board.Add(j_right)

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

# 7. Op-Amps: U1 at (83, 30), U2 at (83, 70)
u1 = pcbnew.FootprintLoad(fp_ic_path, 'SOIC-14_3.9x8.7mm_P1.27mm')
u1.SetReference('U1')
u1.SetValue('TL074_INV')
u1.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(83.0), pcbnew.FromMM(30.0)))
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
    if pnum in u1_pdict:
        pad.SetNet(net_map[u1_pdict[pnum]])
board.Add(u1)

u2 = pcbnew.FootprintLoad(fp_ic_path, 'SOIC-14_3.9x8.7mm_P1.27mm')
u2.SetReference('U2')
u2.SetValue('TL074_SUM')
u2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(83.0), pcbnew.FromMM(70.0)))
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
    if pnum in u2_pdict:
        pad.SetNet(net_map[u2_pdict[pnum]])
board.Add(u2)

# Decoupling Caps at X = 83.0, Y = 23, 37, 63, 77
add_cap('C_U1_POS', '100n', 83.0, 23.0, 0, '+12V', 'GND')
add_cap('C_U1_NEG', '100n', 83.0, 37.0, 0, '-12V', 'GND')
add_cap('C_U2_POS', '100n', 83.0, 63.0, 0, '+12V', 'GND')
add_cap('C_U2_NEG', '100n', 83.0, 77.0, 0, '-12V', 'GND')

# Feedback & Coupling Resistors at X = 73, 78, 83, Y = 45..55
for local_idx, j in enumerate(neuron_range):
    y_row = 45.0 + local_idx * 3.0
    add_res(f'Rf1_N{j}', '10k', 73.0, y_row, 0, f'V_INV_{j}', f'SUM_NEG_{j}')
    add_res(f'Rc_N{j}',  '10k', 78.0, y_row, 0, f'V_INV_{j}', f'SUM_POS_{j}')
    add_res(f'Rf2_N{j}', '10k', 83.0, y_row, 0, f'V_SUM_{j}', f'SUM_POS_{j}')
    
    # Bias at Y = 16.0..25.0, X = 75.0
    b_val = w1_data['weights'][j]['bias_float']
    b_str = w1_data['weights'][j].get('bias_resistor_str', '10k')
    bus_net = f'SUM_POS_{j}' if b_val >= 0 else f'SUM_NEG_{j}'
    add_res(f'Rb_N{j}', b_str, 75.0, 16.0 + local_idx * 3.0, 0, '+5V_REF', bus_net)

# 8. Synaptic Resistor Matrix (16 cols x 16 rows)
# Step X = 3.6mm (X = 13.0 to 67.0)
# Step Y = 2.6mm (Y = 30.0 to 69.0)
for col in range(16):
    cx = 13.0 + col * 3.6
    for row in range(16):
        cy = 30.0 + row * 2.5
        res_idx = row * 16 + col
        in_idx = res_idx % 64
        local_n = res_idx // 64
        j = neuron_range[local_n]
        
        w_info = w1_data['weights'][j]['inputs'][in_idx]
        val_str = w_info.get('resistor_str', 'OPEN')
        w_pol = w_info.get('polarity', 'positive')
        bus_net = f'SUM_POS_{j}' if w_pol == 'positive' else f'SUM_NEG_{j}'
        
        ref = f'R1_{in_idx}_{local_n}'
        add_res(ref, val_str, cx, cy, 0, f'IN_{in_idx}', bus_net)

board.Save(PCB_PATH)
print('Board saved. Running unrouted DRC...')
import subprocess
res = subprocess.run(['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli', 'pcb', 'drc', '--format', 'json', '--output', 'test_dc1_drc4.json', PCB_PATH], capture_output=True, text=True)
with open('test_dc1_drc4.json') as f:
    d = json.load(f)
v_counts = {}
for v in d.get('violations', []):
    t = v.get('type', 'unknown')
    v_counts[t] = v_counts.get(t, 0) + 1
print('Violations count:', len(d.get('violations', [])))
print('Violation types:', v_counts)
if d.get('violations'):
    for v in d['violations']:
        print(' ', v['type'], v['description'])
