"""Extract nominal resistor networks and selectable geometry from KiCad sources."""
import csv, hashlib, json, math, re
from pathlib import Path
import sexpdata
ROOT=Path(__file__).resolve().parent
def children(n,k): return [x for x in n if isinstance(x,list) and x and str(x[0])==k]
def child(n,k,default=None):
    a=children(n,k)
    return a[0] if a else default
def val(n,k,default=''):
    a=child(n,k)
    return str(a[1]) if a and len(a)>1 else default
def ohms(s):
    s=s.strip().replace('Ω','').replace('ohm','').replace('*','').strip()
    if s.upper() in ('','DNP','DNP+','NC','N/A'): return None
    m=re.fullmatch(r'(\d+(?:\.\d+)?)([RrKkMm]?)(\d*)',s)
    if not m:return None
    a,u,b=m.groups()
    return float(a+('.'+b if b else ''))*{'':1,'r':1,'k':1e3,'m':1e6}[u.lower()]
def extract(path,name,overlay=None):
    root=sexpdata.loads(path.read_text())
    nets={}
    for n in children(root,'net'): nets[str(n[1])]=str(n[2])
    pads=[]; edges=[]; tracks=[]; labels=[]; outlines=[]; warnings=[]
    def net(p):
        n=child(p,'net')
        if not n:return ''
        if len(n)>2:return str(n[2])
        return nets.get(str(n[1]),str(n[1]) if not isinstance(n[1],int) else '')
    def xy(n,k):
        p=child(n,k,[k,0,0]);return [float(p[1]),float(p[2])]
    def transform(p,at):
        a=math.radians(float(at[3]) if len(at)>3 else 0)
        return [float(at[1])+p[0]*math.cos(a)+p[1]*math.sin(a),float(at[2])-p[0]*math.sin(a)+p[1]*math.cos(a)]
    for f in children(root,'footprint'):
        props={str(p[1]):str(p[2]) for p in children(f,'property')}
        ref=props.get('Reference',''); value=props.get('Value','')
        at=child(f,'at',['at',0,0]); layer=val(f,'layer')
        local=[]
        for p in children(f,'pad'):
            pn=net(p); pos=transform(xy(p,'at'),at)
            size=xy(p,'size'); layers=[str(x) for x in child(p,'layers',['layers'])[1:]]
            point={'x':pos[0],'y':pos[1],'w':size[0],'h':size[1],'angle':(float(at[3]) if len(at)>3 else 0)+(float(child(p,'at',['at',0,0,0])[3]) if len(child(p,'at',[]))>3 else 0),'net':pn,'ref':ref,'pin':str(p[1]),'layers':layers,'shape':str(p[3])}
            pads.append(point);local.append(point)
        for p in children(f,'property'):
            if str(p[1])!='Reference' or val(p,'layer') not in ('F.SilkS','B.SilkS'):continue
            pos=transform(xy(p,'at'),at)
            labels.append({'x':pos[0],'y':pos[1],'text':ref,'layer':val(p,'layer')})
        value=(overlay or {}).get(ref,value)
        attr=child(f,'attr',[])
        excluded=any(str(x)=='dnp' for x in attr)
        if ref.startswith('R') and not excluded:
            r=ohms(value)
            if r is not None:
                bypin={p['pin']:p['net'] for p in local}
                if bypin.get('1') and bypin.get('2'):
                    edges.append({'a':bypin['1'],'b':bypin['2'],'r':r,'ref':ref,'value':value})
                else:warnings.append(ref+' missing connected terminals')
            elif value.upper() not in ('','DNP','DNP+'):warnings.append(ref+' unparsed '+value)
    for t in children(root,'segment'):
        tracks.append({'a':xy(t,'start'),'b':xy(t,'end'),'w':float(val(t,'width',0.2)),'net':net(t),'layer':val(t,'layer')})
    for v in children(root,'via'):
        p=xy(v,'at');pads.append({'x':p[0],'y':p[1],'w':float(val(v,'size',0.6)),'h':float(val(v,'size',0.6)),'angle':0,'net':net(v),'ref':'via','pin':'','layers':['*.Cu'],'shape':'circle'})
    for kind in ('gr_line','gr_rect','gr_arc','gr_circle'):
        for g in children(root,kind):
            if val(g,'layer')!='Edge.Cuts':continue
            outlines.append({'kind':kind,'a':xy(g,'start'),'b':xy(g,'end'),'mid':xy(g,'mid'),'center':xy(g,'center')})
    xs=[p['x'] for p in pads];ys=[p['y'] for p in pads]
    return dict(name=name,source=str(path.relative_to(ROOT.parent)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pads=pads,edges=edges,tracks=tracks,labels=labels,outlines=outlines,bounds=[min(xs)-4,min(ys)-4,max(xs)+4,max(ys)+4],warnings=warnings)
def main():
    boards=[]
    for p in sorted((ROOT.parent/'boards').rglob('*.kicad_pcb')):
        name={'dc1':'DC1 universal','dc0':'DC0','dc2':'DC2','dc3':'DC3','motherboard':'Motherboard','ads_carrier':'ADS carrier'}.get(p.parent.name,p.parent.name)
        boards.append(extract(p,name))
        if p.parent.name=='dc1':
            for letter in 'abcd':
                with (p.parent/('DC1'+letter+'.csv')).open() as f:
                    overlay={r['Reference']:r['Value'] for r in csv.DictReader(f)}
                b=extract(p,'DC1'+letter.upper(),overlay)
                b['population']='boards/dc1/DC1'+letter+'.csv'
                boards.append(b)
    (ROOT/'data'/'boards.json').write_text(json.dumps(boards,separators=(',',':')))
    print([(b['name'],len(b['pads']),len(b['edges']),len(b['warnings'])) for b in boards])
if __name__=='__main__':main()

