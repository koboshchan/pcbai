import os, sys, json, subprocess, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
PCB_PATH  = os.path.join(WORKSPACE, 'test_matrix.kicad_pcb')
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')
KICAD_CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))

neuron_range = range(0, 4)
nets = ['GND', '+12V', '-12V', '+5V_REF', '-5V_REF']
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

# Mounting holes: placed at (3.0, 50.0), (97.5, 50.0) in the central corridor with 0 clearance conflicts
fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for idx, (hx, hy) in enumerate([(3.0, 50.0), (97.5, 50.0)]):
    mh = pcbnew.FootprintLoad(fp_mh_path, 'MountingHole_3.2mm_M3')
    mh.SetReference(f'MH{idx+1}')
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
    board.Add(mh)

lset = pcbnew.LSET.AllCuMask()
lset.AddLayer(pcbnew.F_Mask)
lset.AddLayer(pcbnew.B_Mask)

fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'
fp_res_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty'

# Column 0 starts at X = 7.0 mm (Pitch = 2.54 mm, col 31 is at 7.0 + 31*2.54 = 85.74 mm)
# Connectors: J_TOP at Y = 5.0 mm, J_BOT at Y = 95.0 mm
j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_top.SetReference('J_TOP')
j_top.SetValue('INPUTS_0_31_PWR')
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(7.0), pcbnew.FromMM(5.0)))
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

j_bot = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_bot.SetReference('J_BOT')
j_bot.SetValue('INPUTS_32_63_SUM')
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(7.0), pcbnew.FromMM(95.0)))
j_bot.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_bot.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f'IN_{32+pnum-1}'])
    else:
        j_local = pnum - 33
        j_global = neuron_range[j_local]
        p.SetNet(net_map[f'V_SUM_{j_global}'])
    p.SetLayerSet(lset)
board.Add(j_bot)

def add_res(ref, val, x, y, rot, n1, n2, pol=None):
    fp = pcbnew.FootprintLoad(fp_res_path, 'R_0805_2012Metric')
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    if pol:
        fp.SetLibDescription(f'polarity={pol}')
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
    ref = f'W{jumper_count}'
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue('JUMPER')
    fp.SetKeywords('net tie')
    fp.SetFPID(pcbnew.LIB_ID('', 'Jumper_Wire'))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    
    for pnum, (px, py) in [('1', (x1, y1)), ('1', (x2, y2))]:
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

# TOP HALF (Inputs 0..31): 4 stages (Neurons 0..3)
# Base Y = 9.0 mm. Period = 10.0 mm. (yt to next yt is 10.0 mm, yb = yt + 8.8, gap = 1.2 mm)
top_stages = []
base_y_top = 9.0
for s_idx in range(4):
    yt = base_y_top + s_idx * 10.0
    yb = yt + 8.8
    top_stages.append({
        'neuron': s_idx,
        'y_top': yt, 'y_bot': yb,
        'yr_pos': yt + 2.6,
        'y_pos': yt + 3.8,
        'y_neg': yt + 5.0,
        'yr_neg': yt + 6.2
    })

# Draw top horizontal buses
for s_idx in range(4):
    j = top_stages[s_idx]['neuron']
    cfg = top_stages[s_idx]
    add_track(6.0, cfg['y_pos'], 86.5, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(6.0, cfg['y_neg'], 86.5, cfg['y_neg'], f'SUM_NEG_{j}')

# Populate top half
for col in range(32):
    xc = 7.0 + col * 2.54
    in_idx = col
    add_track(xc, 5.0, xc, top_stages[0]['y_top'], f'IN_{in_idx}')
    
    for s_idx in range(4):
        j = top_stages[s_idx]['neuron']
        cfg = top_stages[s_idx]
        w_info = w1_data['weights'][j]['inputs'][in_idx]
        val_str = w_info.get('resistor_str', '10k')
        w_pol = w_info.get('polarity', 'positive')
        
        add_jumper(xc, cfg['y_top'], xc, cfg['y_bot'], f'IN_{in_idx}')
        
        ref = f'R1_{in_idx}_{j}'
        if w_pol == 'positive':
            add_res(ref, val_str, xc, cfg['yr_pos'], -90, f'IN_{in_idx}', f'SUM_POS_{j}', pol='positive')
            add_track(xc, cfg['y_top'], xc, cfg['yr_pos'] - 0.9125, f'IN_{in_idx}')
            add_track(xc, cfg['yr_pos'] + 0.9125, xc, cfg['y_pos'], f'SUM_POS_{j}')
        else:
            add_res(ref, val_str, xc, cfg['yr_neg'], 90, f'IN_{in_idx}', f'SUM_NEG_{j}', pol='negative')
            add_track(xc, cfg['yr_neg'] - 0.9125, xc, cfg['y_neg'], f'SUM_NEG_{j}')
            add_track(xc, cfg['yr_neg'] + 0.9125, xc, cfg['y_bot'], f'IN_{in_idx}')
            
        if s_idx < 3:
            next_yt = top_stages[s_idx + 1]['y_top']
            add_track(xc, cfg['y_bot'], xc, next_yt, f'IN_{in_idx}')

# BOTTOM HALF (Inputs 32..63): 4 stages (Neurons 3, 2, 1, 0)
# Base Y = 52.2 mm. Period = 10.0 mm.
# Stage 0: 52.2..61.0 (N3)
# Stage 1: 62.2..71.0 (N2)
# Stage 2: 72.2..81.0 (N1)
# Stage 3: 82.2..91.0 (N0)
# J_BOT is at 95.0 mm (distance from 91.0 is 4.0 mm, zero overlap!)
bot_stages = []
base_y_bot = 52.2
for s_idx in range(4):
    yt = base_y_bot + s_idx * 10.0
    yb = yt + 8.8
    j_assigned = 3 - s_idx # N3, N2, N1, N0
    bot_stages.append({
        'neuron': j_assigned,
        'y_top': yt, 'y_bot': yb,
        'yr_neg': yt + 2.6,
        'y_neg': yt + 3.8,
        'y_pos': yt + 5.0,
        'yr_pos': yt + 6.2
    })

# Draw bottom horizontal buses
for s_idx in range(4):
    j = bot_stages[s_idx]['neuron']
    cfg = bot_stages[s_idx]
    add_track(6.0, cfg['y_pos'], 86.5, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(6.0, cfg['y_neg'], 86.5, cfg['y_neg'], f'SUM_NEG_{j}')

# Populate bottom half
for col in range(32):
    xc = 7.0 + col * 2.54
    in_idx = 32 + col
    # Track from J_BOT (xc, 95.0) to bot_stages[3]['y_bot'] (91.0)
    add_track(xc, 95.0, xc, bot_stages[3]['y_bot'], f'IN_{in_idx}')
    
    # Inputs flow UP from stage 3 to stage 0
    for s_idx in range(4):
        j = bot_stages[s_idx]['neuron']
        cfg = bot_stages[s_idx]
        w_info = w1_data['weights'][j]['inputs'][in_idx]
        val_str = w_info.get('resistor_str', '10k')
        w_pol = w_info.get('polarity', 'positive')
        
        add_jumper(xc, cfg['y_top'], xc, cfg['y_bot'], f'IN_{in_idx}')
        
        ref = f'R1_{in_idx}_{j}'
        if w_pol == 'negative':
            add_res(ref, val_str, xc, cfg['yr_neg'], -90, f'IN_{in_idx}', f'SUM_NEG_{j}', pol='negative')
            add_track(xc, cfg['y_top'], xc, cfg['yr_neg'] - 0.9125, f'IN_{in_idx}')
            add_track(xc, cfg['yr_neg'] + 0.9125, xc, cfg['y_neg'], f'SUM_NEG_{j}')
        else:
            add_res(ref, val_str, xc, cfg['yr_pos'], 90, f'IN_{in_idx}', f'SUM_POS_{j}', pol='positive')
            add_track(xc, cfg['yr_pos'] - 0.9125, xc, cfg['y_pos'], f'SUM_POS_{j}')
            add_track(xc, cfg['yr_pos'] + 0.9125, xc, cfg['y_bot'], f'IN_{in_idx}')
            
        if s_idx > 0:
            prev_yb = bot_stages[s_idx - 1]['y_bot']
            add_track(xc, prev_yb, xc, cfg['y_top'], f'IN_{in_idx}')

# CONCENTRIC PLANAR CORRIDOR ROUTING (NON-CROSSING NESTED U-BENDS)
x_bus_map = {
    3: (87.5, 88.5), # N3 (inner pair): x_neg = 87.5, x_pos = 88.5
    2: (89.5, 90.5), # N2: x_neg = 89.5, x_pos = 90.5
    1: (91.5, 92.5), # N1: x_neg = 91.5, x_pos = 92.5
    0: (93.5, 94.5)  # N0 (outer pair): x_neg = 93.5, x_pos = 94.5
}

top_cfg_by_n = {cfg['neuron']: cfg for cfg in top_stages}
bot_cfg_by_n = {cfg['neuron']: cfg for cfg in bot_stages}

for j in [3, 2, 1, 0]:
    x_neg, x_pos = x_bus_map[j]
    t_cfg = top_cfg_by_n[j]
    b_cfg = bot_cfg_by_n[j]
    
    # 1. SUM_NEG (Inner U-bend):
    add_track(86.5, t_cfg['y_neg'], x_neg, t_cfg['y_neg'], f'SUM_NEG_{j}')
    add_track(x_neg, t_cfg['y_neg'], x_neg, b_cfg['y_neg'], f'SUM_NEG_{j}')
    add_track(86.5, b_cfg['y_neg'], x_neg, b_cfg['y_neg'], f'SUM_NEG_{j}')
    
    # 2. SUM_POS (Outer U-bend):
    add_track(86.5, t_cfg['y_pos'], x_pos, t_cfg['y_pos'], f'SUM_POS_{j}')
    add_track(x_pos, t_cfg['y_pos'], x_pos, b_cfg['y_pos'], f'SUM_POS_{j}')
    add_track(86.5, b_cfg['y_pos'], x_pos, b_cfg['y_pos'], f'SUM_POS_{j}')

board.Save(PCB_PATH)
print("Saved complete concentric matrix to", PCB_PATH)
