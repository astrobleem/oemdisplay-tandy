"""Independent pinned-phase GDI frame checker for the new five oval scenes."""
from pathlib import Path
import argparse,hashlib,itertools,json,re,runpy,struct
HERE=Path(__file__).resolve().parent
# Keep the independent reference primitives local to this saver test suite.
S=[0, 13, 25, 37, 49, 60, 71, 81, 90, 99, 106, 113, 118, 123, 126, 127, 128, 127, 126, 123, 118, 113, 106, 99, 90, 81, 71, 60, 49, 37, 25, 13, 0, -13, -25, -37, -49, -60, -71, -81, -90, -99, -106, -113, -118, -123, -126, -127, -128, -127, -126, -123, -118, -113, -106, -99, -90, -81, -71, -60, -49, -37, -25, -13]
RGB=[(85,255,255),(255,85,255),(255,255,85),(85,255,85),(85,85,255),(255,85,85),(255,255,255),(170,170,170)]
def rgb(index):return [64]*3 if index==8 else [(255 if index&8 else 128) if index&(1<<p) else 0 for p in range(3)]
def supported(p):
 index=p[3]&15;return index>0 and list(p[:3])==rgb(index) and (index==15 or p[3]&240==[32,0,0,0,0,0,0,0,0,0,16,16,0,16,16,48][index])
def frames(data,total):
 at=0
 for case in range(total):
  for phase in range(4):
   if at+4>len(data) or struct.unpack_from('<2H',data,at)!=(case,phase):raise ValueError('Missing/reordered frame header')
   at+=4;frame=bytearray()
   while len(frame)<32768:
    if at+3>len(data):raise ValueError('Truncated frame run')
    n,value=struct.unpack_from('<HB',data,at);at+=3
    if not n or len(frame)+n>32768:raise ValueError('Invalid full-frame RLE run')
    frame.extend(bytes([value])*n)
   yield frame
 if at!=len(data):raise ValueError('Trailing frame data')
C={"supported":supported,"frames":frames,"rgb":rgb}
def trunc(a,b):return abs(a)//abs(b)*(-1 if (a<0)!=(b<0) else 1)
def scale(a,b,d):return trunc(a*b,d)
def slots(effect,density):return density*2 if effect in (0,2) else min(density+2,8) if effect==4 else density
def shape(effect,phase,index,count=8,w=320,h=200):
 p=phase&63;cx=w//2;cy=h//2;rx=w//4;ry=h//4;angle=0;color=index&7
 if effect==0:
  q=(p+index*64//count)&63;cx+=scale(S[q],w,1024);cy+=scale(S[(q*2)&63],h,1024);rx=w//4+scale(S[(q+16)&63],w,2048);ry=h//6;angle=(p+index*3)&63;color=5 if index*3//count==0 else 2 if index*3//count==1 else 3
 elif effect==1:
  r=count//2
  if index<r:
   lat=(index+1)*32//(r+1)-16;cy+=scale(S[lat&63],h,384);rx=scale(S[(lat+16)&63],w,384);ry=h//30
  else:q=(p+(index-r)*32//(count-r))&63;rx=scale(abs(S[q]),w,384);ry=h//3
  dy=cy-h//2;cx=w//2-scale(scale(dy,S[6],128),w,h);cy=h//2+scale(dy,S[22],128);angle=6
 elif effect==2:
  q=(p+index*5)&63;r=count-index+2;rx=w*r//(3*(count+3));ry=h*r//(5*(count+3));cx+=scale(S[q],w,1536);cy+=scale(S[(q+16)&63],h,1536);angle=(p+index*2)&63;color=index&1
 elif effect==3:
  q=(index*64//count+p)&63;r=q+8;rx=scale(w,r,160);ry=scale(h,r,160);cx+=scale(scale(S[p],72-r,128),w,512);cy+=scale(scale(S[(p+16)&63],72-r,128),h,512);color=3 if r<24 else 2 if r<48 else 5
 else:
  if index<3:cy=h*7//8+index*max(h//36,3);rx=w*3//8-index*w//32;ry=1;color=6
  else:
   q=(p-(index-3)*2)&31;r=min(q,32-q);rx=w//20;ry=h//14
   if r<3:rx=rx*(11-r)//8;ry=ry*(5+r)//8
   cx=w//2+scale(S[(p-(index-3)*2)&63],w,384);cy=h*7//8-ry-scale(q*(32-q),h,512);color=1-((index-3)&1)

 return cx,cy,max(rx,2),(1 if effect==4 and index<3 else max(ry,2)),angle,color,w,h

def vertices(o):
 cx,cy,rx,ry,angle,color,w,h=o
 for n in range(33):
  p=(n*2)&63;a=scale(S[(p+16)&63],rx,128);b=scale(S[p],ry,128)
  yield cx+scale(a,S[(angle+16)&63],128)-scale(scale(b,S[angle],128),w,h),cy+scale(scale(a,S[angle],128),h,w)+scale(b,S[(angle+16)&63],128)
def vertex_hash(o):
 h=0
 for x,y in vertices(o):h=((h*33+x)*33+y)&65535
 return h

def records(quick):
 for effect in range(5):
  count=slots(effect,16)
  indices=([0,1,2,3,count-1] if effect==4 else [0,count//2,count-1]) if quick else list(range(count))
  for p in range(4 if quick else 8):
   for index in indices:yield effect,p*(16 if quick else 8),index,count

def read(folder,candidate):
 lines=(folder/'FXPRO.LOG').read_text().splitlines();m=re.fullmatch(r'VERSION=2 EFFECTS=5 DENSITY=16 PHASES=(4|8) GRID=(Q|FULL) CAPS=8 FRAME_BYTES=32768 FRAMES_PER_CASE=4',lines[0]) if lines else None
 if not m:raise ValueError('Unknown revised effect header')
 phases,grid=m.groups();quick=grid=='Q'
 if (int(phases),grid) not in [(4,'Q'),(8,'FULL')]:raise ValueError('Unsupported phase grid')
 expected_records=list(records(quick));total=len(expected_records)
 if len(lines)!=total+3 or lines[-2:]!=['CASES=%d FAILURES=0'%total,'COMPLETE=1']:raise ValueError('Incomplete effect probe')
 rows=[]
 for case,line in enumerate(lines[1:-2]):
  effect,phase,index,count=expected_records[case];o=shape(effect,phase,index,count);color=o[5]
  pattern=r'CASE=%d EFFECT=%d PHASE=%d INDEX=%d COUNT=%d CX=%d CY=%d RX=%d RY=%d ANGLE=%d COLOR=%d AX=%d AY=%d HASH=%d RGB=(\d+) PREFIX=([0-9a-f]{32}) RET=1 ERASE_RET=1 ACCEPTED=([01]) ERASE_ACCEPTED=([01]) RESYNC_ACCEPTED=0 RESYNC2_ACCEPTED=0 RESYNC=1 RESYNC2=1'%((case,effect,phase,index,count)+o+(vertex_hash(o),))
  m=re.fullmatch(pattern,line)
  if not m:raise ValueError('Unexpected geometry/order/return CASE=%d'%case)
  value,prefix,admitted,erased=m.groups();p=bytes.fromhex(prefix)
  if int(value)!=RGB[color][0]+(RGB[color][1]<<8)+(RGB[color][2]<<16) or struct.unpack('<6H',p[4:])!=(0,0xe117,1,0,0,0x3cc3):raise ValueError('Factory tag/logical RGB mismatch')
  expected=o[4]==0 and (C['supported'](p) if candidate else p[:3]==b'\xff'*3 and p[3]&15==15)
  if int(admitted)!=int(expected) or int(erased)!=int(expected):raise ValueError('Unexpected actual curve admission')
  rows.append({'case':case,'effect':effect,'phase':phase,'index':index,'shape':o,'prefix':prefix,'physical_index':p[3]&15,'accepted':int(admitted)})
 return rows,(folder/'FXPRO.RLE').read_bytes()
def check(a,b):
 ar,av=read(a,False);br,bv=read(b,True)
 if len(ar)!=len(br) or any({k:v for k,v in x.items() if k!='accepted'}!={k:v for k,v in y.items() if k!='accepted'} for x,y in zip(ar,br)):raise ValueError('Independent geometry/prefix identities differ')
 digest=hashlib.sha256();count=0;prior=draw=background=None
 for i,pair in enumerate(itertools.zip_longest(C['frames'](av,len(ar)),C['frames'](bv,len(br)))):
  x,y=pair
  if x is None or y is None or x!=y:raise ValueError('Independent full VRAM mismatch CASE=%d PHASE=%d'%(i//4,i%4))
  if i%4 in (1,3) and x!=prior:raise ValueError('Shadow resync changed pixels')
  if i%4==0:draw=x
  if i%4==2:
   if br[i//4]['physical_index']>0 and draw==x:raise ValueError('Visible oval produced no pixel change')
   if br[i//4]['physical_index']==0 and draw!=x:raise ValueError('Black XOR changed background')
   if background is None:background=x
   elif x!=background:raise ValueError('XOR did not restore common background')
  prior=x;count+=1;digest.update(x)
 if count!=len(ar)*4:raise ValueError('Incomplete frames')
 if not any(r['accepted'] and r['physical_index']!=15 for r in br):raise ValueError('No new nonwhite native ellipse admitted')
 if not any(r['shape'][4]!=0 and not r['accepted'] for r in br):raise ValueError('No application Polyline fallback observed')
 return {'pass':True,'scenes':len(ar),'frames':count,'VRAM_bytes_compared':count*32768,'common_decoded_SHA256':digest.hexdigest(),'native_ellipse_admissions':sum(r['accepted'] for r in br),'polyline_cases':sum(r['shape'][4]!=0 for r in br),'scope':'native input words+16-bit vertex hash and independent full GDI VRAM comparison; not timing, cursor or actual saver lifecycle. Vertex hash is not collision-free geometry proof.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args();print(json.dumps(check(a.baseline,a.candidate),indent=2))
