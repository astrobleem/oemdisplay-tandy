#!/usr/bin/env python3
"""Independent Pillow pixel oracle plus grammar/LZW corruption tests."""
import argparse, json, random, struct, subprocess, tempfile
from pathlib import Path
from PIL import Image
ap=argparse.ArgumentParser();ap.add_argument('--exe',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
BASE=[(0,0,0),(0,0,128),(0,128,0),(0,128,128),(128,0,0),(128,0,128),(128,128,0),(128,128,128),(64,64,64),(0,0,255),(0,255,0),(0,255,255),(255,0,0),(255,0,255),(255,255,0),(255,255,255)]
PAL={16:BASE,2:[BASE[0],BASE[15]],4:[BASE[x] for x in (0,11,13,15)],5:[BASE[x] for x in (0,12,10,15)]}
checks=[]
def run(name,data,valid,im=None):
 src=a.out/(name+'.GIF');src.write_bytes(data)
 for mode in ([2,4,5,16] if valid else [16]):
  dst=a.out/(name+str(mode)+'.BMP');dst.unlink(missing_ok=True)
  r=subprocess.run([a.exe,str(src),str(dst),str(mode)],capture_output=True,timeout=10)
  assert (r.returncode==0)==valid,(name,mode,r.stderr)
  assert src.read_bytes()==data
  if valid:
   got=Image.open(dst).convert('RGB');oracle=im or Image.open(src).convert('RGB');pal=PAL[mode]
   want=[pal[min(range(len(pal)),key=lambda i:sum((rgb[k]-pal[i][k])**2 for k in range(3)))] for rgb in oracle.getdata()]
   assert list(got.getdata())==want,(name,mode,'pixels')
   old=dst.read_bytes();r2=subprocess.run([a.exe,str(src),str(dst),str(mode)],capture_output=True);assert r2.returncode and dst.read_bytes()==old
  else:assert not dst.exists(),(name,'partial file retained')
  checks.append({'name':name,'mode':mode,'valid':valid,'diagnostic':r.stderr.decode().strip()})
# A clear before each literal makes tiny deterministic hand-built GIFs.
def literal(w,h,idx,interlace=False,local=False,mincode=2):
 clear=1<<mincode;codes=[]
 for x in idx:codes.extend([clear,x])
 codes.append(clear+1);bits=0;n=0;out=bytearray()
 for c in codes:
  bits|=c<<n;n+=mincode+1
  while n>=8:out.append(bits&255);bits>>=8;n-=8
 if n:out.append(bits&255)
 blocks=b''.join(bytes([len(out[i:i+255])])+out[i:i+255] for i in range(0,len(out),255))+b'\0'
 pal=b'\0\0\0\xff\xff\xff\xff\0\0\0\xff\0'
 return b'GIF87a'+struct.pack('<HHBBB',w,h,0 if local else 0x81,0,0)+(b'' if local else pal)+b','+struct.pack('<HHHHB',0,0,w,h,(0x81 if local else 0)|(64 if interlace else 0))+(pal if local else b'')+bytes([mincode])+blocks+b';'
for h in [1,2,3,4,7,8,9,17,200]:
 w=13;px=[(x+y)%4 for y in range(h) for x in range(w)]
 order=list(range(0,h,8))+list(range(4,h,8))+list(range(2,h,4))+list(range(1,h,2));inter=[px[y*w+x] for y in order for x in range(w)]
 for local in [False,True]:
  for il in [False,True]:run('I%d%d%d'%(h,local,il),literal(w,h,inter if il else px,il,local),True)
# Real encoder creates dictionary additions, width growth and full dictionary clears.
random.seed(1729)
for n,wh in enumerate([(1,1),(37,19),(320,200)]):
 im=Image.new('P',wh);im.putpalette([v for rgb in [(i,(i*31)%256,(i*17)%256) for i in range(256)] for v in rgb]);im.putdata([random.randrange(256) for _ in range(wh[0]*wh[1])]);path=a.out/('RAND%d.GIF'%n);im.save(path,interlace=True);run('RAND%d'%n,path.read_bytes(),True)
# Full dictionary with deferred clear: legal literal stream after table fills.
def deferred():
 w,h=320,200;px=[(x+y)%4 for y in range(h) for x in range(w)]
 codes=[4]+px+[5];size=3;nextcode=6;have=False;bits=n=0;out=bytearray()
 for c in codes:
  bits|=c<<n;n+=size
  while n>=8:out.append(bits&255);bits>>=8;n-=8
  if c==4:size=3;nextcode=6;have=False
  elif c!=5:
   if have and nextcode<4096:
    nextcode+=1
    if nextcode==(1<<size) and size<12:size+=1
   have=True
 if n:out.append(bits&255)
 base=literal(w,h,[])
 return base[:36]+b''.join(bytes([len(out[i:i+255])])+out[i:i+255] for i in range(0,len(out),255))+b'\0;'
run('DEFER',deferred(),True)
for color in [0,1,255]:
 im=Image.new('P',(320,200),color);im.putpalette([v for i in range(256) for v in (i,i,i)]);im.save(a.out/'SOLID.GIF');run('SOLID%d'%color,(a.out/'SOLID.GIF').read_bytes(),True)
# Attractive native proof, deliberately small enough for low-resolution Paintbrush.
im=Image.new('P',(96,64));im.putpalette([v for rgb in BASE for v in rgb]+[0]*720)
im.putdata([((x//12)+(y//8)*2)%16 for y in range(64) for x in range(96)]);im.save(a.out/'TEST.GIF',optimize=False);run('TEST',(a.out/'TEST.GIF').read_bytes(),True)
base=literal(3,2,[0,1,2,3,2,1]);run('COMMENT',base[:-1]+b'!\xfe\x03abc\0;',True)
run('GCE',base[:6].replace(b'87a',b'89a')+base[6:25]+b'!\xf9\x04\0\0\0\0\0'+base[25:],True)
for i in range(len(base)):run('TR%03d'%i,base[:i],False)
run('TRAIL',base+b'x',False)
run('ANIM',base[:-1]+base[25:],False)
run('TRANS',base[:25]+b'!\xf9\x04\x01\0\0\0\0'+base[25:],False)
run('APP',base[:25]+b'!\xff\x0bNETSCAPE2.0\x03\x01\0\0\0'+base[25:],False)
run('SUBRECT',base[:26]+b'\x01'+base[27:],False)
run('WIDTH',base[:6]+struct.pack('<H',321)+base[8:],False)
run('ZERO',base[:6]+b'\0\0'+base[8:],False)
run('MIN1',base[:35]+b'\x01'+base[36:],False)
run('MIN9',base[:35]+b'\x09'+base[36:],False)
run('NOCLR',base[:37]+bytes([(base[37]&~7)|1])+base[38:],False)
run('BADCODE',base[:37]+bytes([(base[37]&7)|(7<<3)])+base[38:],False)
run('SHORTPIX',literal(3,2,[0,1,2]),False)
run('LONGPIX',literal(3,2,[0]*7),False)
run('BADPAL',literal(3,2,[0,1,2,3,4,1],mincode=3),False)
run('CAP',base+b'\0'*262144,False)
(a.out/'RESULT.JSON').write_text(json.dumps({'passed':len(checks),'checks':checks},indent=2));print('PASS',len(checks))
