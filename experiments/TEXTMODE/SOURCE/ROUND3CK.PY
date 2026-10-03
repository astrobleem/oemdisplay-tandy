#!/usr/bin/env python3
"""Check color-accurate Win3.0 DIB output at1,4,8and24bits per pixel."""
import argparse, json, struct
from pathlib import Path
COLORS=[(0,0,0),(0,0,128),(0,128,0),(0,128,128),(128,0,0),(128,0,128),(128,128,0),(128,128,128),(64,64,64),(0,0,255),(0,255,0),(0,255,255),(255,0,0),(255,0,255),(255,255,0),(255,255,255)]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('guest',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args();reports=[]
 logs={};current=None
 for line in (a.guest/'ROUND3.LOG').read_text().splitlines():
  k,v=line.split('=',1)
  if k=='BPP':current={};logs[int(v)]=current
  elif current is not None:current[k]=int(v)
 for bpp in [1,4,8,24]:
  data=(a.guest/('R3G%d.BIN'%bpp)).read_bytes();info=(a.guest/('R3I%d.BIN'%bpp)).read_bytes();stride=((37*bpp+31)//32)*4
  palette=[tuple(reversed(info[40+i*4:43+i*4])) for i in range(256)]
  def rgb(x,y):
   row=10-y;off=row*stride
   if bpp==24:return tuple(reversed(data[off+x*3:off+x*3+3]))
   if bpp==8:return palette[data[off+x]]
   if bpp==4:return palette[data[off+x//2]>>(0 if x&1 else 4)&15]
   return palette[data[off+x//8]>>(7-x%8)&1]
  def expected(x,y):return COLORS[(15 if (x+y)&1 else 0) if bpp==1 else (x*3+y*5)&15]
  bad=[(x,y,expected(x,y),rgb(x,y)) for y in range(11) for x in range(37) if expected(x,y)!=rgb(x,y)]
  reports.append({'bpp':bpp,'getdib_mismatch_count':len(bad),'first_mismatches':bad[:10],'buffer_guard_untouched':data[stride*11:]==bytes([0xa5])*(4096-stride*11),'runtime':logs[bpp]})
 report={'guest':str(a.guest),'bit_depth_matrix':reports,'pass':all(not r['getdib_mismatch_count'] and r['buffer_guard_untouched'] and not r['runtime']['SETDIB_MISMATCHES'] and not r['runtime']['CREATEDIB_MISMATCHES'] and not r['runtime']['DIRECTDIB_MISMATCHES'] for r in reports)}
 out=a.out or a.guest/'ROUND3';Path(str(out)+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return int(not report['pass'])
if __name__=='__main__':raise SystemExit(main())
