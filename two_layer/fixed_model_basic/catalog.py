"""Snapshot and individually verify every in-stock JLC Basic 0805 resistor."""
import concurrent.futures,datetime,json,re,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
URL='https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList/v2'
def query(keyword):
 p={'currentPage':1,'pageSize':100,'presaleType':'stock','searchType':2,'keyword':keyword,'stockFlag':False,'searchSource':'search','componentLibraryType':'base'}
 for trial in range(4):
  try:
   return json.load(urllib.request.urlopen(urllib.request.Request(URL,data=json.dumps(p).encode(),headers={'Content-Type':'application/json'}),timeout=90))
  except Exception:
   if trial==3:raise
   time.sleep(2)
def resistance(s):
 m=re.fullmatch(r'([\d.]+)([kM]?)(?:Ω|ohm)?',s)
 if not m:raise ValueError(s)
 return float(m[1])*{'':1,'k':1000,'M':1000000}[m[2]]
def extract(c):
 a={x.get('attribute_name_en'):x.get('attribute_value_name') for x in c.get('attributes',[])}
 if c.get('componentLibraryType')!='base' or c.get('componentSpecificationEn')!='0805' or 'Resistance' not in a or int(c.get('stockCount') or 0)<=0:return None
 return {'ohms':resistance(a['Resistance']),'lcsc':c['componentCode'],'library':'Basic','stock':c['stockCount'],'tolerance':a.get('Tolerance'),'package':'0805','model':c.get('componentModelEn'),'attributes':a,'url':'https://jlcpcb.com/partdetail/'+c['componentCode'],'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if __name__=='__main__':
 raw=query('0805'); page=raw['data']['componentPageInfo'];assert page['total']<=100
 candidates=[r for c in page['list'] if (r:=extract(c))]
 def verify(r):
  cs=query(r['lcsc'])['data']['componentPageInfo']['list'];cs=[c for c in cs if c['componentCode']==r['lcsc']];assert len(cs)==1
  v=extract(cs[0]);assert v and v['ohms']==r['ohms'];return v
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:parts=list(pool.map(verify,candidates))
 parts.sort(key=lambda x:x['ohms']);out={'endpoint':URL,'query':'0805, componentLibraryType=base, presaleType=stock','total_catalog_records':page['total'],'individually_verified':True,'parts':parts}
 (H/'basic_catalog.json').write_text(json.dumps(out,indent=2));print([(p['ohms'],p['lcsc'],p['stock'],p['tolerance']) for p in parts],flush=True)
