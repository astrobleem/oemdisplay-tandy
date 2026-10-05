from PIL import Image,ImageDraw
from pathlib import Path
import math,struct
P=Path(__file__).resolve().parent
(P/"assets").mkdir(exist_ok=True)
PAL=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
def build(w):
 im=Image.new('P',(w,200),9); im.putpalette(sum((list(c) for c in PAL),[])+[0]*720)
 pix=im.load()
 # Original pixel-designed landscape, geometry evaluated at target resolution.
 # No runtime scaling: pixels represent a 4:3 display (wide 160-mode pixels).
 for y in range(200):
  for x in range(w):
   X=x*320/w
   # Thin ordered horizon haze; keep quiet blue sky behind application windows.
   if y>63 and [[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]][y%4][x%4] < min(6,(y-63)//9): pix[x,y]=11
   rear=120+10*math.sin((X+20)/61)
   main=132-31*math.exp(-((X-112)/115)**2)+13*(X/320)
   front=177+17*math.sin((X-110)/92)
   if y>=rear: pix[x,y]=2
   if y>=main:
    pix[x,y]=10
    # Shade follows the hill's slope, using a sparse coarse ordered dither.
    depth=(y-main)/(200-main)
    if depth>.40 and (x%4==y%4): pix[x,y]=2
    if depth>.76 and (x+y)%2==0: pix[x,y]=2
   if y>=front:
    pix[x,y]=2
    if y<front+5 and (x+y)%2==0:pix[x,y]=10
 # Clouds are purpose-drawn in pixel runs, with restrained gray-blue shadows.
 d=ImageDraw.Draw(im)
 def cloud(cx,cy,scale):
  spans=[(-19,19,8,12),(-28,26,5,9),(-22,21,1,6),(-15,11,-5,4),(-10,6,-9,2),(8,20,-2,5)]
  for l,r,t,b in spans:d.rectangle((round((cx+l*scale)*w/320),round(cy+t*scale),round((cx+r*scale)*w/320),round(cy+b*scale)),fill=15)
  for l,r,t,b in [(-25,20,9,11),(-17,26,7,9)]:d.rectangle((round((cx+l*scale)*w/320),round(cy+t*scale),round((cx+r*scale)*w/320),round(cy+b*scale)),fill=7)
 cloud(69,37,.85);cloud(255,57,.6);cloud(218,25,.38)
 return im

def bmp4(im,path):
 w,h=im.size;stride=((w+1)//2+3)&~3;rows=[]
 for y in range(h-1,-1,-1):
  row=bytes((im.getpixel((x,y))<<4)|(im.getpixel((x+1,y)) if x+1<w else 0) for x in range(0,w,2));rows.append(row+b'\0'*(stride-len(row)))
 body=b''.join(rows);offset=14+40+64
 path.write_bytes(struct.pack('<2sIHHI',b'BM',offset+len(body),0,0,offset)+struct.pack('<IiiHHIIiiII',40,w,h,1,4,0,len(body),0,0,16,16)+b''.join(bytes((b,g,r,0)) for r,g,b in PAL)+body)
for w in (160,320):
 im=build(w);bmp4(im,P/'assets'/f'HILL{w}.BMP');im.resize((800,600),Image.Resampling.NEAREST).save(P/'assets'/f'HILL{w}.PNG')
 # Verify on-disk packed 4-bit round trip, RGBI palette and exact pixel identity.
 check=Image.open(P/'assets'/f'HILL{w}.BMP');assert list(check.getdata())==list(im.getdata());assert check.size==(w,200)
print('4-bit BMPs verified: 16,118 / 32,118 bytes; no runtime conversion.')
