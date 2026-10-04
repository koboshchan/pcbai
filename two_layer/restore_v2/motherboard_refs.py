#!/usr/bin/python3
"""Reversible motherboard-only reference roles. Daughter references are untouched."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent
MAP=ROOT/'old_to_new_refs.json'
FAMILIES={'R_PWM_':'RP','C_PWM_':'CP','U_SR':'U','C_SR':'C','R_TOP_':'RT','R_BOT_':'RB','R_REF_':'RR','R_ADC_':'RA','D_HI_':'DH','D_LO_':'DL','J_SLOT':'JS'}
SPECIAL={'C_BULK_N':'CBN','C_BULK_P':'CBP','C_RAIL_N':'CRN','C_RAIL_P':'CRP','C_REG_BULK':'CRB','C_REG_IN':'CRI','C_REG_OUT':'CRO','U_REG5':'UR5','R_REF_LINK':'RRL','R_REG_MINLOAD':'RM','J_ADC_REF':'JAR','J_MCU_SCORES':'JAD','J_MCU_SPI':'JSPI','J_PWR_IN':'JP'}
def shortened(old):
    if old in SPECIAL:return SPECIAL[old]
    for prefix,new in FAMILIES.items():
        tail=old.removeprefix(prefix)
        if old.startswith(prefix) and tail.isdigit():return new+tail
    return old

def make_map(board):
    old=sorted(f.GetReference() for f in board.GetFootprints())
    assert len(old)==len(set(old))
    mapping={r:shortened(r) for r in old}
    assert len(set(mapping.values()))==len(old),'Reference collision'
    # Every UUID is retained and gives sourcing a reference-independent anchor.
    uuids={str(f.m_Uuid.AsString()):{'old':f.GetReference(),'new':mapping[f.GetReference()]} for f in board.GetFootprints()}
    assert len(uuids)==len(old)
    return {'schema':1,'board':'motherboard_adc_repaired','old_to_new':mapping,'new_to_old':{n:o for o,n in mapping.items()},'uuid_roles':uuids,'complete_reference_count':len(old),'reference_only':True}

def data():return json.loads(MAP.read_text())
def canonical(old):return data()['old_to_new'].get(old,old)
def legacy(new):return data()['new_to_old'].get(new,new)
def role(fp):
    return data()['uuid_roles'].get(str(fp.m_Uuid.AsString()),{}).get('old',legacy(fp.GetReference()))
def indexed(board):
    """Historical role lookup for audits, never mutates actual reference fields."""
    return {role(f):f for f in board.GetFootprints()}

def physical(board):
    def point(q):return [q.x,q.y]
    rows={}
    for f in board.GetFootprints():
        rows[str(f.m_Uuid.AsString())]={'value':f.GetValue(),'fpid':f.GetFPID().GetUniStringLibId(),'position':point(f.GetPosition()),'angle':f.GetOrientationDegrees(),'layer':f.GetLayer(),'pads':sorted((str(q.m_Uuid.AsString()),q.GetNumber(),q.GetNetname(),point(q.GetPosition()),point(q.GetSize()),point(q.GetDrillSize()),q.GetShape(),q.GetAttribute(),q.GetOrientationDegrees(),q.GetLayerSet().FmtHex()) for q in f.Pads())}
    return rows

def rename(board):
    record=make_map(board);before=physical(board)
    for f in board.GetFootprints():f.SetReference(record['old_to_new'][f.GetReference()])
    assert before==physical(board),'Rename changed physical component identity'
    assert sorted(f.GetReference() for f in board.GetFootprints())==sorted(record['new_to_old'])
    record['physical_identity_sha256']=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
    MAP.write_text(json.dumps(record,indent=2)+'\n')
    return record
