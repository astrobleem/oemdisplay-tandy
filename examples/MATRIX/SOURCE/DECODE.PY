from pathlib import Path
from PIL import Image
import argparse
p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('out',type=Path);p.add_argument('--mode',choices=['160','baseline','3204','6404','6402'],default='160');a=p.parse_args()
w,col,banks,pal={'160':(160,16,2,list(range(16))),'baseline':(320,16,4,list(range(16))),'3204':(320,4,2,[0,11,13,15]),'6404':(640,4,4,[0,12,10,15]),'6402':(640,2,2,[0,15])}[a.mode]
raw=a.raw.read_bytes();pitch=160 if banks==4 else 80
rgb=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
im=Image.new('RGB',(w,200));pix=[]
for y in range(200):
 for x in range(w):
  off=(y%banks)*8192+(y//banks)*pitch
  if a.mode=='6404':
   off+=2*(x//8);s=7-x%8;v=(raw[off]>>s&1)|((raw[off+1]>>s&1)<<1)
  else:
   bits={16:4,4:2,2:1}[col];per=8//bits;off+=x//per;s=(per-1-x%per)*bits;v=(raw[off]>>s)&(col-1)
  pix.append(rgb[pal[v]])
im.putdata(pix);im.save(a.out)
