#!/usr/bin/env python3
"""Decode an exact 32 KiB mode-09 B800 dump and compare every screen pixel."""
import argparse, collections, hashlib, json
from pathlib import Path
from PIL import Image
PALETTE=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]

def decode(data):
    assert len(data)==32768, f'Expected32768bytes,got{len(data)}'
    return [[(data[(y%4)*8192+(y//4)*160+x//2]>>(4 if x%2==0 else 0))&15 for x in range(320)] for y in range(200)]

def fill(screen,l,t,r,b,c):
    for y in range(t,b):
        for x in range(l,r):screen[y][x]=c

def draw_oracle():
    a=[[0]*320 for _ in range(200)]
    for i in range(16):fill(a,i*20,32,(i+1)*20,168,i)
    fill(a,0,0,320,1,15);fill(a,0,199,320,200,15)
    fill(a,0,0,1,200,15);fill(a,319,0,320,200,15)
    fill(a,1,1,9,9,12);fill(a,311,1,319,9,10)
    fill(a,1,191,9,199,9);fill(a,311,191,319,199,14)
    return a

BLT_CASES=[(16,16,0,0,32,16),(65,16,1,0,31,16),(114,16,2,0,29,16),(163,16,3,0,27,16),(212,16,7,0,25,16),(261,16,15,0,17,16),(17,64,0,1,31,15),(66,64,1,2,30,14),(115,64,3,3,29,13),(164,64,4,4,28,12),(213,64,6,5,26,11),(262,64,7,6,25,10)]
def blt_oracle():
    a=[[8]*320 for _ in range(200)]
    for dx,dy,sx,sy,w,h in BLT_CASES:
        for y in range(h):
            for x in range(w):a[dy+y][dx+x]=((sx+x)*3+(sy+y)*5)&15
    return a

def main():
    ap=argparse.ArgumentParser();ap.add_argument('dump',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--test',choices=['draw','blt'],default='draw');args=ap.parse_args()
    data=args.dump.read_bytes();actual=decode(data);expected=draw_oracle() if args.test=='draw' else blt_oracle()
    mismatches=[(x,y,expected[y][x],actual[y][x]) for y in range(200) for x in range(320) if actual[y][x]!=expected[y][x]]
    counts=dict(sorted(collections.Counter(c for row in actual for c in row).items()))
    report={'test':args.test,'dump':str(args.dump),'sha256':hashlib.sha256(data).hexdigest(),'mode':'09','dimensions':[320,200],'banking':'offset=(y%4)*8192+(y//4)*160+x//2,even_x_high_nibble','pixels_compared':64000,'mismatch_count':len(mismatches),'first_mismatches':mismatches[:40],'all16colors':set(counts)==set(range(16)),'color_counts':counts,'pass':not mismatches}
    out=args.out or args.dump.with_suffix('')
    im=Image.new('RGB',(320,200));im.putdata([PALETTE[v] for row in actual for v in row]);im.save(str(out)+'.png')
    Path(str(out)+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return int(bool(mismatches))
if __name__=='__main__':raise SystemExit(main())
