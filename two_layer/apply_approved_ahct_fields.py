#!/usr/bin/python3
"""Router-owner-only post-route metadata application. Never autoroutes.
Use INPUT OUTPUT (different paths). Final model/CPL audits must follow.
Only changes quoted metadata strings, leaving pad/net/route bytes untouched.
"""
import re,sys,hashlib
from pathlib import Path

def transform(text):
 # Metadata-only exact replacements; values are distinct from footprint identifiers.
 old=[('"74AHCT595D"','"74AHCT595S16-13"'),('Nexperia 74AHCT595D,112','Diodes 74AHCT595S16-13'),('C554704','C126402')]
 # Require eight register footprint blocks, each with original/new approved value.
 from motherboard_refs import MAP,canonical
 for i in range(1,9):
  legacy=f'U_SR{i}';actual=canonical(legacy) if MAP.exists() else legacy
  count=sum(len(re.findall(r'\(property "Reference" "'+re.escape(ref)+r'"',text)) for ref in {legacy,actual})
  assert count==1, f'Missing/duplicate register role {legacy}'
 assert text.count('(property "Value" "74AHCT595D"')+text.count('(property "Value" "74AHCT595S16-13"')==8
 for a,b in old:text=text.replace(a,b)
 assert text.count('(property "Value" "74AHCT595S16-13"')==8
 return text

def main():
 source,dest=map(Path,sys.argv[1:]);assert source.resolve()!=dest.resolve(),'Never overwrite active board'
 raw=source.read_text();out=transform(raw)
 # Normalize allowed metadata edits and prove every remaining byte unchanged.
 normalized=out.replace('"74AHCT595S16-13"','"74AHCT595D"').replace('Diodes 74AHCT595S16-13','Nexperia 74AHCT595D,112').replace('C126402','C554704')
 assert normalized==raw,'Unexpected nonmetadata edit'
 dest.write_text(out)
 print('Metadata only. Original SHA256 '+hashlib.sha256(source.read_bytes()).hexdigest())
if __name__=='__main__':main()
