#!/usr/bin/env python3
"""Check real compact resource identity, renderer preservation and refusals."""
import argparse,json,struct,zipfile
from pathlib import Path
import CMPRSC as C
from STAGECGA import write

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 a.out.mkdir(parents=True,exist_ok=False)
 with zipfile.ZipFile(a.repo/'docs/QUAL/CGACMP/BASE.ZIP') as z:
  files={Path(n).name:z.read(n) for n in z.namelist() if not n.endswith('/')}
 donor=files['CGA100.DRV'];_,_,rr=C.resources(donor)
 expected={(r['type'],r['id']):r['data'] for r in rr if r['type']==0x8002 or (r['type']==0xf006 and r['id'] in (0x8001,0x8003))}
 reports={};refusals=0
 for base in ('CGA320.DRV','CGA640.DRV'):
  original=files[base];b,proof=C.compact(original,donor);assert C.compact(original,donor)[0]==b
  actual={(r['type'],r['id']):r['data'] for r in C.resources(b)[2]}
  before={(r['type'],r['id']):r['data'] for r in C.resources(original)[2]}
  for key,value in expected.items():assert actual[key]==value
  for key,value in before.items():
   if key not in expected:assert actual[key]==value
  assert actual[0xf006,0x8002]==before[0xf006,0x8002] # palette remains mode-specific
  assert len(proof['segments'])==10 and proof['header_growth']==48
  # Header offsets, bounds and resource identities must fail closed.
  ne=struct.unpack_from('<I',original,60)[0];table=ne+struct.unpack_from('<H',original,ne+36)[0]
  variants=[b'',b'MZ'+bytes(62),original[:100],original[:table+2]]
  for off,value in ((60,0xffffffff),(ne+36,0xffff),(ne+38,0),(table,0),(table+10,0xffff)):
   bad=bytearray(original);struct.pack_into('<I' if off==60 else '<H',bad,off,value);variants.append(bytes(bad))
  for bad in variants:
   try:C.compact(bad,donor)
   except (ValueError,struct.error,AssertionError):refusals+=1
   else:raise AssertionError('Corrupt NE accepted')
  reports[base]=proof
 write(a.out/'CMPTEST.JSN',json.dumps(dict(host='PASS',windows='NOT_RUN',resource_profiles=reports,corruption_refusals=refusals),indent=2)+'\n')
 print('Compact resource identity/unchanged renderer PASS; corruption refusals',refusals)
if __name__=='__main__':main()
