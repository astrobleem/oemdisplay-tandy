"""Decode unedited Tandy B800 framebuffer samples from native Windows QA."""
from pathlib import Path
import argparse,json,hashlib
from PIL import Image
PAL=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
def decode(src,mode,dst):
 b=src.read_bytes();assert len(b)==(32768 if mode in ('baseline','6404') else 16384)
 w={'160':160,'baseline':320,'3204':320,'6404':640,'6402':640}[mode]
 px=[]
 for y in range(200):
  for x in range(w):
   if mode in ['160','baseline']:
    k=2 if mode=='160' else 4;v=(b[(y%k)*8192+(y//k)*(w//2)+x//2]>>(4 if x%2==0 else 0))&15
   elif mode=='3204':v=[0,11,13,15][(b[(y%2)*8192+(y//2)*80+x//4]>>(6-2*(x%4)))&3]
   elif mode=='6402':v=[0,15][(b[(y%2)*8192+(y//2)*80+x//8]>>(7-x%8))&1]
   else:
    a=(y%4)*8192+(y//4)*160+(x//8)*2;bit=7-x%8;v=[0,12,10,15][((b[a]>>bit)&1)|(((b[a+1]>>bit)&1)<<1)]
   px.append(PAL[v])
 im=Image.new('RGB',(w,200));im.putdata(px);im.save(dst)
 if mode=='160':im.resize((320,200),Image.Resampling.NEAREST).save(dst.with_name(dst.stem+'-DISPLAY.PNG'))
 return {'raw':src.name,'mode':mode,'logical_dimensions':[w,200],'sha256_raw':hashlib.sha256(b).hexdigest(),'png':dst.name,'pixel_changes':'none; hardware layout decoding only; 160 DISPLAY duplicates horizontal pixels'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('mode',choices=['160','baseline','3204','6404','6402']);p.add_argument('png',type=Path);a=p.parse_args();print(json.dumps(decode(a.raw,a.mode,a.png),indent=2))
