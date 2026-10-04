import os, sys, json, pcbnew

WORKSPACE = '/Users/lucaszhang/pcbai'
W1_PATH   = os.path.join(WORKSPACE, 'weights_layer1.json')
PCB_PATH  = os.path.join(WORKSPACE, 'test_perfect_dc1_det.kicad_pcb')

with open(W1_PATH) as f:
    w1_data = json.load(f)

board = pcbnew.BOARD()

# Design rules
ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.50)
ds.m_TrackMinWidth = pcbnew.FromMM(0.35)
ds.SetCustomTrackWidth(pcbnew.FromMM(0.35))

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

# Mounting holes
fp_mh_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty'
for idx, (hx, hy) in enumerate([(4.0, 4.0), (96.0, 4.0), (4.0, 96.0), (96.0, 96.0)]):
    mh = pcbnew.FootprintLoad(fp_mh_path, 'MountingHole_3.2mm_M3')
    mh.SetReference(f'MH{idx+1}')
    mh.Reference().SetVisible(False)
    mh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
    board.Add(mh)

lset_fcu = pcbnew.LSET()
lset_fcu.AddLayer(pcbnew.F_Cu)
lset_fcu.AddLayer(pcbnew.F_Mask)
lset_fcu.AddLayer(pcbnew.B_Mask)

fp_hdr_path = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty'

# J_TOP at Y = 6.5, J_BOT at Y = 93.5
j_top = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_top.SetReference('J_TOP')
j_top.SetValue('INPUTS_0_31_PWR')
j_top.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.55), pcbnew.FromMM(6.5)))
j_top.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_top.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f'IN_{pnum-1}'])
    elif pnum == 33: p.SetNet(net_map['+12V'])
    elif pnum == 34: p.SetNet(net_map['-12V'])
    elif pnum == 35: p.SetNet(net_map['GND'])
    elif pnum == 36: p.SetNet(net_map['+5V_REF'])
    p.SetLayerSet(lset_fcu)
board.Add(j_top)

j_bot = pcbnew.FootprintLoad(fp_hdr_path, 'PinHeader_1x36_P2.54mm_Vertical')
j_bot.SetReference('J_BOT')
j_bot.SetValue('INPUTS_32_63_SUM')
j_bot.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5.55), pcbnew.FromMM(93.5)))
j_bot.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
for p in j_bot.Pads():
    pnum = int(p.GetNumber())
    if pnum <= 32: p.SetNet(net_map[f'IN_{32+pnum-1}'])
    else:
        j_local = pnum - 33
        j_global = neuron_range[j_local]
        p.SetNet(net_map[f'V_SUM_{j_global}'])
    p.SetLayerSet(lset_fcu)
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

# -------------------------------------------------------------
# TOP HALF: Neurons 0..3 for Inputs 0..31
# -------------------------------------------------------------
# Let's define row base positions for the 4 neurons:
# Neuron 0:
# Resistors at Y = 11.5
# SUM_POS_0 at Y = 13.5
# SUM_NEG_0 at Y = 15.0
# Jumper 0: Y = 11.5 to 17.0 (Pad 1 at 11.5, Pad 2 at 17.0)
#
# Neuron 1:
# Resistors at Y = 19.5
# SUM_POS_1 at Y = 21.5
# SUM_NEG_1 at Y = 23.0
# Jumper 1: Y = 19.5 to 25.0
#
# Neuron 2:
# Resistors at Y = 27.5
# SUM_POS_2 at Y = 29.5
# SUM_NEG_2 at Y = 31.0
# Jumper 2: Y = 27.5 to 33.0
#
# Neuron 3:
# Resistors at Y = 35.5
# SUM_POS_3 at Y = 37.5
# SUM_NEG_3 at Y = 39.0
# (No jumper needed below N3!)

n_y_config = [
    {'y_res': 11.5, 'y_pos': 13.5, 'y_neg': 15.0, 'y_jmp_end': 17.5},
    {'y_res': 19.5, 'y_pos': 21.5, 'y_neg': 23.0, 'y_jmp_end': 25.5},
    {'y_res': 27.5, 'y_pos': 29.5, 'y_neg': 31.0, 'y_jmp_end': 33.5},
    {'y_res': 35.5, 'y_pos': 37.5, 'y_neg': 39.0, 'y_jmp_end': None}
]

# Draw horizontal buses for top half (X = 4.0 to 86.0)
for n_idx, cfg in enumerate(n_y_config):
    j = neuron_range[n_idx]
    add_track(4.0, cfg['y_pos'], 86.0, cfg['y_pos'], f'SUM_POS_{j}')
    add_track(4.0, cfg['y_neg'], 86.0, cfg['y_neg'], f'SUM_NEG_{j}')

# Place top half synaptic resistors and jumpers
for col in range(32):
    x_col = 5.55 + col * 2.54
    in_idx = col
    
    # Track from J_TOP pin (Y=6.5) to N0 resistor Pad 1 (Y=11.5 - 0.9125 = 10.5875)
    add_track(x_col, 6.5, x_col, 10.5875, f'IN_{in_idx}')
    
    for n_idx in range(4):
        j = neuron_range[n_idx]
        cfg = n_y_config[n_idx]
        y_r = cfg['y_res']
        
        w_info = w1_data['weights'][j]['inputs'][in_idx]
        val_str = w_info.get('resistor_str', '10k')
        w_pol = w_info.get('polarity', 'positive')
        bus_net = f'SUM_POS_{j}' if w_pol == 'positive' else f'SUM_NEG_{j}'
        bus_y = cfg['y_pos'] if w_pol == 'positive' else cfg['y_neg']
        
        # Resistor: vertical rot = 90
        # Pad 1 is at Y = y_r - 0.9125 (IN_idx)
        # Pad 2 is at Y = y_r + 0.9125 (bus_net)
        ref = f'R1_{in_idx}_{n_idx}'
        add_res(ref, val_str, x_col, y_r, 90, f'IN_{in_idx}', bus_net)
        
        # Stub from Pad 2 (x_col, y_r + 0.9125) to bus_y
        add_track(x_col, y_r + 0.9125, x_col, bus_y, bus_net)
        
        # If not the last neuron, add jumper to carry IN_idx over the buses
        if cfg['y_jmp_end'] is not None:
            # Jumper from Pad 1 (Y = y_r - 0.9125) or next to it to y_jmp_end
            # Pad 1 of jumper at (x_col, y_r - 0.9125): wait, can jumper pad be at Pad 1?
            # A jumper pad is 1.8mm PTH. Resistor pad is SMD.
            # If jumper pad 1 is at y_r - 0.9125, it covers the SMD pad!
            # Let's check: Jumper Pad 1 at (x_col, y_r - 0.9125) connects IN_idx directly!
            # And Jumper Pad 2 at (x_col, cfg['y_jmp_end']) lands on F.Cu below both buses!
            add_jumper(x_col, y_r - 0.9125, x_col, cfg['y_jmp_end'], f'IN_{in_idx}')
            
            # From Jumper Pad 2, track runs down to next neuron resistor Pad 1:
            next_cfg = n_y_config[n_idx + 1]
            add_track(x_col, cfg['y_jmp_end'], x_col, next_cfg['y_res'] - 0.9125, f'IN_{in_idx}')

board.Save(PCB_PATH)
print("Saved test_perfect_dc1_det.kicad_pcb")
