#!/usr/bin/env python3
"""Full 32KiB framebuffer oracle for ROUND4 clipped/banded DIB screen tests."""
import argparse, hashlib, json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('guest',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--mode',choices=['tandy','cga'],default='tandy');ap.add_argument('--source-origin',choices=['top','bottom'],default='bottom');a=ap.parse_args();cases=[];complete=False
 for line in (a.guest/'ROUND4.LOG').read_text().splitlines():
  k,v=line.split('=',1)
  if k=='CASE':cases.append({'CASE':int(v)})
  elif k=='COMPLETE':complete=int(v)==1
  elif cases:cases[-1][k]=int(v)
 results=[]
 for c in cases:
  i=c['CASE'];before=(a.guest/('R4B%02d.BIN'%i)).read_bytes();after=(a.guest/('R4D%02d.BIN'%i)).read_bytes();expected=bytearray(before)
  assert len(before)==len(after)==32768
  if c['COMPRESSION']==0:
   for oy in range(c['HEIGHT']):
    sy=(c['SY'] if a.source_origin=='top' else 11-c['SY']-c['HEIGHT'])+oy;dy=c['DY']+oy;scan=10-sy
    if not(0<=sy<11 and 0<=dy<200 and c['START']<=scan<c['START']+c['SCANS']):continue
    for ox in range(c['WIDTH']):
     sx=c['SX']+ox;dx=c['DX']+ox
     if not(0<=sx<37 and 0<=dx<(640 if a.mode=='cga' else 320)):continue
     if c['CLIP'] and not(85<=dx<103 and 62<=dy<68):continue
     value=(15 if ((sx*3+sy*5)&15)<7 else 0) if c['BPP']==1 else (sx*3+sy*5)&15
     if a.mode=='cga':
      offset=(dy%2)*8192+(dy//2)*80+dx//8;mask=128>>(dx%8)
      expected[offset]=(expected[offset]|mask) if value else (expected[offset]&(~mask&255))
      expected[offset+16384]=expected[offset]
     else:
      offset=(dy%4)*8192+(dy//4)*160+dx//2
      expected[offset]=(expected[offset]&0xf0)|value if dx&1 else (expected[offset]&0x0f)|(value<<4)
  bad=[(i,expected[i],after[i]) for i in range(32768) if expected[i]!=after[i]]
  okret=c['RETURN']==0 if c['COMPRESSION'] else c['RETURN']>0
  results.append({'parameters':c,'framebuffer_bytes_compared':32768,'mismatch_count':len(bad),'first_mismatches':bad[:16],'return_valid':okret,'input_unchanged':c['INPUT_CHANGED_BYTES']==0,'pass':not bad and okret and c['INPUT_CHANGED_BYTES']==0})
 report={'guest':str(a.guest),'mode':a.mode,'source_origin':a.source_origin,'driver_sha256':hashlib.sha256((a.guest/'WINDOWS/SYSTEM'/('CGA.DRV' if a.mode=='cga' else 'TANDY88.DRV')).read_bytes()).hexdigest(),'round4_exe_sha256':hashlib.sha256((a.guest/'WINDOWS/ROUND4.EXE').read_bytes()).hexdigest(),'complete':complete,'case_count':len(results),'framebuffer_bytes_compared':len(results)*32768,'results':results,'pass':complete and all(r['pass'] for r in results)}
 out=a.out or a.guest/'ROUND4';Path(str(out)+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'pass':report['pass'],'case_count':len(results),'failures':[r for r in results if not r['pass']]},indent=2));return int(not report['pass'])
if __name__=='__main__':raise SystemExit(main())
