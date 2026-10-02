#!/usr/bin/env python3
"""Reproducible Tandy CGA splash: vector layout -> 640x200 PBM -> RLE4 BMP.
No external modules or fonts required. Pillow is used only for optional PNGs.
The source geometry lives here; ASSETS/TANDY.SVG is the editable generated vector.
"""
from pathlib import Path
import struct, hashlib, json
W,H=640,200
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'
FONT={
' ':['00000']*7,
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['111','010','010','010','010','010','111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['010','110','010','010','010','010','111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'/':['00001','00001','00010','00100','01000','10000','10000'],
'.':['0','0','0','0','0','1','1'],
}
# Scene in native 640x200 coordinates. SVG's viewBox uses the same coordinates.
scene=[]
def poly(points,c=1):scene.append((points,c))
def rect(x,y,w,h,c=1):poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],c)
def text_width(s,sx=2,gap=2):return sum(len(FONT[c][0])*sx+gap for c in s)-gap
def text(s,x,y,sx=2,sy=1,gap=2):
 for c in s:
  glyph=FONT[c]
  for yy,row in enumerate(glyph):
   for xx,val in enumerate(row):
    if val=='1':rect(x+xx*sx,y+yy*sy,sx,sy)
  x+=len(glyph[0])*sx+gap

def center(s,y,sx=2,sy=1,gap=2):text(s,(W-text_width(s,sx,gap))//2,y,sx,sy,gap)
# Quiet frame, offset stripe accents, and generous empty space.
rect(38,20,564,1);rect(38,179,564,1)
for x in (38,601):rect(x,20,1,12);rect(x,168,1,12)
center('PERSONAL COMPUTER SYSTEM',31,2,1,3)
# Custom geometric italic wordmark. The strokes are vector polygons, no fonts.
base_x,base_y,gw,gh,gap=107,55,76,43,10
shapes={
'T': [([(0,0),(76,0),(76,10),(46,10),(46,43),(30,43),(30,10),(0,10)],1)],
'A': [([(26,0),(50,0),(76,43),(59,43),(53,32),(23,32),(17,43),(0,43)],1), ([(37,11),(39,11),(47,22),(29,22)],0)],
'N': [([(0,0),(17,0),(59,29),(59,0),(76,0),(76,43),(59,43),(17,14),(17,43),(0,43)],1)],
'D': [([(0,0),(50,0),(68,6),(76,14),(76,29),(68,37),(50,43),(0,43)],1), ([(17,10),(46,10),(59,15),(59,28),(46,33),(17,33)],0)],
'Y': [([(0,0),(20,0),(38,17),(56,0),(76,0),(46,29),(46,43),(30,43),(30,29)],1)],
}
for idx,c in enumerate('TANDY'):
 for points,color in shapes[c]:
  poly([(base_x+idx*(gw+gap)+x+(gh-y)*0.20,base_y+y) for x,y in points],color)
# Fine white divider echoes period OEM packaging.
rect(108,108,424,1)
center('MICROSOFT WINDOWS',122,2,1,3)
center('VERSION 3.0',135,2,1,2)
text('1000 EX / HX',52,163,2,1,2)
s='STARTING WINDOWS';text(s,588-text_width(s,2,2),163,2,1,2)
# Exact binary raster from polygon centres. No anti-aliasing or dithering.
pixels=[[0]*W for _ in range(H)]
for points,color in scene:
 for y in range(max(0,int(min(p[1] for p in points))),min(H,int(max(p[1] for p in points))+1)):
  py=y+0.5;cross=[]
  for a,b in zip(points,points[1:]+points[:1]):
   if min(a[1],b[1])<=py<max(a[1],b[1]):cross.append(a[0]+(py-a[1])*(b[0]-a[0])/(b[1]-a[1]))
  cross.sort()
  for left,right in zip(cross[0::2],cross[1::2]):
   for x in range(max(0,int(left)),min(W,int(right)+1)):
    if left<=x+0.5<right:pixels[y][x]=color

def encode(rows):
 assert len(rows)==H and all(len(row)==W for row in rows)
 assert all(p in (0,1) for row in rows for p in row)
 payload=bytearray()
 for row in reversed(rows):
  x=0
  while x<W:
   c=row[x];n=1
   while n<254 and x+n<W and row[x+n]==c:n+=1
   payload+=bytes((n,c*17));x+=n
  payload+=b'\0\0'
 payload+=b'\0\1'
 if 4336+62+len(payload)>65280:
  raise ValueError('Image is too complex for the stock 64 KiB COM loader; simplify the artwork')
 # Encode a self-consistent BMP header; no ignored trailing bytes are needed.
 header=struct.pack('<2sIHHI',b'BM',62+len(payload),0,0,62)
 header+=struct.pack('<IiiHHIIiiII',40,W,H,1,1,2,len(payload),0,0,2,0)
 return header+b'\0\0\0\0\xff\xff\xff\0'+payload

def decode(data):
 if 4336+len(data)>65280:
  raise ValueError('RLE exceeds the stock 64 KiB COM loader limit')
 assert data[:2]==b'BM'
 declared,off=struct.unpack_from('<I4xI',data,2)
 size,w,h,planes,bpp,compression,imglen=struct.unpack_from('<IiiHHII',data,14)
 assert (size,w,h,planes,bpp,compression,off)==(40,W,H,1,1,2,62)
 assert data[54:62]==b'\0\0\0\0\xff\xff\xff\0'
 rows=[[0]*w for _ in range(h)]; x=y=0;i=off;runs=eols=0
 while True:
  n,v=data[i:i+2];i+=2
  if n:
   assert y<h and x+n<=w
   for j in range(n):
    value=(v>>(4 if not j%2 else 0))&15;assert value<2
    rows[h-1-y][x]=value;x+=1
   runs+=1
  elif v==0:assert x==w;x=0;y+=1;eols+=1
  elif v==1:break
  else:raise ValueError('Non-run command outside custom safe encoding subset')
 assert y==h and x==0 and eols==h
 assert i-off==imglen and declared==i
 assert data[i:]==b''
 return rows,{'width':w,'height':h,'bpp':bpp,'compression':compression,'palette_entries':2,'encoded_runs':runs,'eol_commands':eols,'file_bytes':len(data),'image_bytes':imglen,'end_of_bitmap_offset':i}

def build():
 OUT.mkdir(exist_ok=True)
 rle=encode(pixels);restored,report=decode(rle);assert restored==pixels
 (OUT/'TNDYLOGO.RLE').write_bytes(rle)
 # PBM uses 1=black, hence invert visual white bits.
 (OUT/'TANDY.PBM').write_bytes(b'P4\n640 200\n'+bytes(sum((1-pixels[y][x+k])<<(7-k) for k in range(8)) for y in range(H) for x in range(0,W,8)))
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 200" preserveAspectRatio="none">','<title>Tandy Windows 3.0 startup splash</title>','<desc>640 by 200 two-color native CGA artwork; intended 4:3 display. Generated by tools/BUILD.PY.</desc>','<rect width="640" height="200" fill="black"/>']
 for points,color in scene:svg.append('<polygon points="'+' '.join(f'{x:g},{y:g}' for x,y in points)+'" fill="'+('white' if color else 'black')+'"/>')
 svg.append('</svg>');(OUT/'TANDY.SVG').write_text('\n'.join(svg)+'\n')
 try:
  from PIL import Image
  im=Image.new('1',(W,H));im.putdata([p*255 for row in pixels for p in row]);im.save(OUT/'PREVIEW.PNG');im.resize((640,480),Image.Resampling.NEAREST).save(OUT/'ASPECT.PNG')
 except ImportError:pass
 report['sha256']=hashlib.sha256(rle).hexdigest();report['round_trip_pixels_match']=True
 (OUT/'FORMAT.JSON').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=="__main__":
 build()
