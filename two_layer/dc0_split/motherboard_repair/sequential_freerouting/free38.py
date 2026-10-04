from run import *
b=p.LoadBoard(str(D/'restore_last_two.kicad_pcb'));ids={'2bd8fb38-b3fe-4851-a580-e6938b103222','8e0d1ade-69a8-4799-b6b3-846fa5edcca7','fbec8156-a903-403b-aa13-df3814466bdb','d096a433-f487-4cd5-8bd3-df7f0d4dd94b'};base=json.load(open(D/'baseline_copper.json'));ret=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ids:ret.append(t);b.Remove(t)
j=json.load(open(D/'LAST_LOCAL_BLOCKERS.json'));j['released_items'].update({k:base[k] for k in ids});j['extra_endpoint_release_reason']='JS2 B7 IN38 PTH endpoint access, release only attached 1.6mm original stub after fixed endpoint failed';write('LAST_LOCAL_BLOCKERS.json',j);p.SaveBoard(str(D/'free38.kicad_pcb'),b)
