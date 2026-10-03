#!/usr/bin/env python3
"""Validate ROUND2 Win3.0 DIB regression outputs without relying on screenshots."""
import argparse, hashlib, json, struct
from pathlib import Path
from PIL import Image
COLORS=[(0,0,0),(0,0,128),(0,128,0),(0,128,128),(128,0,0),(128,0,128),(128,128,0),(128,128,128),(64,64,64),(0,0,255),(0,255,0),(0,255,255),(255,0,0),(255,0,255),(255,255,0),(255,255,255)]
HW=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('guest',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args()
 text=(a.guest/'ROUND2.LOG').read_text();items=[line.split('=',1) for line in text.splitlines() if '=' in line]
 vals={k:int(v) for k,v in items};info=(a.guest/'ROUND2IN.BIN').read_bytes();bits=(a.guest/'ROUND2DI.BIN').read_bytes();part=(a.guest/'ROUND2PT.BIN').read_bytes()
 palette=[tuple(reversed(info[40+i*4:43+i*4])) for i in range(16)]
 w,h=37,11;stride=20
 def pixel(buf,x,row):return palette[(buf[row*stride+x//2]>>(0 if x&1 else 4))&15]
 failures=[(x,y,COLORS[(x*3+y*5)&15],pixel(bits,x,h-1-y)) for y in range(h) for x in range(w) if COLORS[(x*3+y*5)&15]!=pixel(bits,x,h-1-y)]
 pf=[(x,s,COLORS[(x*3+(h-1-(3+s))*5)&15],pixel(part,x,s)) for s in range(5) for x in range(w) if COLORS[(x*3+(h-1-(3+s))*5)&15]!=pixel(part,x,s)]
 negative=[]
 for k,v in items:
  if k=='NEG_COMPRESSION':negative.append({'compression':int(v)})
  elif k=='NEG_SET_RETURN':negative[-1]['return']=int(v)
  elif k=='NEG_CHANGED_BYTES':negative[-1]['changed_bytes']=int(v)
 raw=(a.guest/'ROUND2VR.BIN').read_bytes()
 screen=[[raw[(y%4)*8192+(y//4)*160+x//2]>>(4 if x%2==0 else 0)&15 for x in range(320)] for y in range(200)]
 paths={}
 for name,top in [('source_ddb',8),('saved_dib_to_screen',40),('synthetic_dib_to_screen',72),('setdib_to_ddb',104),('createdib_to_ddb',136)]:
  bad=[(x,y,(x*3+y*5)&15,screen[top+y][16+x]) for y in range(h) for x in range(w) if screen[top+y][16+x]!=(x*3+y*5)&15]
  paths[name]={'mismatch_count':len(bad),'first_mismatches':bad[:10]}
 im=Image.new('RGB',(320,200));im.putdata([HW[v] for row in screen for v in row])
 out=a.out or a.guest/'ROUND2';im.save(str(out)+'.png')
 report={'guest':str(a.guest),'driver_sha256':hashlib.sha256((a.guest/'WINDOWS/SYSTEM/TANDY88.DRV').read_bytes()).hexdigest(),'round2_exe_sha256':hashlib.sha256((a.guest/'WINDOWS/ROUND2.EXE').read_bytes()).hexdigest(),'complete':vals.get('COMPLETE')==1,'width':w,'height':h,'ddb_stride':vals['BM_WIDTHBYTES'],'ddb_planes':vals['BM_PLANES'],'ddb_bpp':vals['BM_BITSPIXEL'],'dib_palette':palette,'getdib_mismatch_count':len(failures),'getdib_first_mismatches':failures[:10],'partial_get_mismatch_count':len(pf),'partial_first_mismatches':pf[:10],'partial_guard_untouched':part[100:]==bytes([0xa5])*3996,'setdib_gdi_mismatches':vals.get('SETDIB_MISMATCHES'),'createdib_gdi_mismatches':vals.get('CREATEDIB_MISMATCHES'),'negative_compression':negative,'screen_paths':paths}
 report['pass']=report['complete'] and not failures and not pf and report['partial_guard_untouched'] and not vals.get('SETDIB_MISMATCHES') and not vals.get('CREATEDIB_MISMATCHES') and all(n['return']==0 and n['changed_bytes']==0 for n in negative) and all(p['mismatch_count']==0 for p in paths.values())
 Path(str(out)+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
