"""Decode actual captured video memory to native logical pixels; never synthesize UI."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--adapter',choices=('pcjr','cga100'),required=True)
for n in ('vram','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();raw=a.vram.read_bytes();assert len(raw)==32768
if a.adapter=='pcjr':
 size=(320,200);pixels=bytes((raw[(y%4)*8192+(y//4)*160+x//2]>>(4 if not x%2 else 0))&15 for y in range(200) for x in range(320))
else:
 assert set(raw[:16000:2])=={0xde},'Not a captured160x100 CGA half-block video page'
 size=(160,100);pixels=bytes((raw[y*160+(x//2)*2+1]>>(4 if x%2==0 else 0))&15 for y in range(100) for x in range(160))
from PIL import Image
im=Image.frombytes('P',size,pixels);palette=[]
for i in range(16):
 r=170 if i&4 else 0;g=170 if i&2 else 0;b=170 if i&1 else 0
 if i==6:g=85
 if i&8:r+=85;g+=85;b+=85
 palette.extend((r,g,b))
im.putpalette(palette+[0]*(768-len(palette)));im.save(a.out)
print('Decoded captured',a.adapter,'video memory at',size,'pixels')
