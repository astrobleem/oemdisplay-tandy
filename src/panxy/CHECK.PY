"""Independent full-frame software viewport oracle from raw adapter VRAM."""
from pathlib import Path
import argparse,importlib.machinery,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--driver',type=Path,required=True);p.add_argument('--adapter',choices=('pcjr','colorplus'),default='pcjr');a=p.parse_args()
IRGB=[0,4,2,6,1,5,3,7,8,12,10,14,9,13,11,15]
def decode(raw):
 assert len(raw)==32768
 if a.adapter=='pcjr':return [(raw[(y%4)*8192+(y//4)*160+x//2]>>(4 if not x%2 else 0))&15 for y in range(200) for x in range(320)]
 out=[]
 for y in range(200):
  for x in range(320):
   at=(y%2)*8192+(y//2)*80+x//4;shift=6-2*(x%4);rg=(raw[at]>>shift)&3;bi=(raw[at+16384]>>shift)&3
   out.append(((rg&2)<<1)|((rg&1)<<1)|((bi&2)>>1)|((bi&1)<<3))
 return out
positions=[(0,0),(8,0),(320,0),(320,4),(320,200),(0,200),(160,100),(0,0)]+[(304,192)]*3
reader=importlib.machinery.SourceFileLoader('panxy_arrow',str(ROOT/'src/xtpan/PANCHK.PY')).load_module();hx,hy,glyph=reader.arrow(a.driver.read_bytes())
results=[]
for i,(left,top) in enumerate(positions):
 raw=(a.folder/('PX%03d.BIN'%i)).read_bytes();actual=decode(raw)
 if i<8:expected=[IRGB[(((y+top)>>3)+((x+left)>>5))&15] for y in range(200) for x in range(320)]
 else:expected=[15 if 300<=x+left<350 and 190<=y+top<220 else 0 for y in range(200) for x in range(320)]
 if i==9:
  for dx,dy,andbit,xorbit in glyph:
   x=16-hx+dx;y=8-hy+dy
   if 0<=x<320 and 0<=y<200:
    at=y*320+x;expected[at]=(expected[at] if andbit else 0)^(15 if xorbit else 0)
 bad=[(n%320,n//320,v,expected[n]) for n,v in enumerate(actual) if v!=expected[n]]
 results.append(dict(shot=i,viewport=[left,top],pixels=64000,mismatches=len(bad),first=bad[:4],vram_sha256=hashlib.sha256(raw).hexdigest()))
driver_bytes=a.driver.read_bytes()
report=dict(driver=dict(bytes=len(driver_bytes),sha256=hashlib.sha256(driver_bytes).hexdigest()),outcome='PASS' if not any(r['mismatches'] for r in results) else 'FAIL',adapter=a.adapter,frames=results,pixels_checked=64000*len(results),physical_hardware=False)
(a.folder.parent/'PIXELS.JSN').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['outcome']=='PASS'
