#!/usr/bin/env python3
"""Independently check the native Paintbrush BMP save and exact reopened pixels."""
import argparse, collections, hashlib, json, struct
from pathlib import Path
from PIL import Image
LOGICAL=[(0,0,0),(0,0,128),(0,128,0),(0,128,128),(128,0,0),(128,0,128),(128,128,0),(128,128,128),(64,64,64),(0,0,255),(0,255,0),(0,255,255),(255,0,0),(255,0,255),(255,255,0),(255,255,255)]
RGBI=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input_bmp',type=Path);ap.add_argument('saved_bmp',type=Path);ap.add_argument('native_capture',type=Path);ap.add_argument('--out',type=Path,default=Path('NATIVE05.json'));a=ap.parse_args()
 src=Image.open(a.input_bmp).convert('RGB');saved=Image.open(a.saved_bmp).convert('RGB');capture=Image.open(a.native_capture).convert('RGB');data=a.saved_bmp.read_bytes()
 header=struct.unpack_from('<IiiHHIIIIII',data,14);palette=[tuple(reversed(data[54+i*4:57+i*4])) for i in range(16)]
 mapping=dict(zip(LOGICAL,RGBI));w,h=saved.size
 bars=[(x,y)for y in range(20)for x in range(w)if saved.getpixel((x,y))!=src.getpixel((x,y))]
 below=collections.Counter(saved.getpixel((x,y))for y in range(20,h)for x in range(w));text=[(x,y)for y in range(20,h)for x in range(w)if saved.getpixel((x,y))==(0,255,255)]
 bad=[(x,y,mapping.get(saved.getpixel((x,y))),capture.getpixel((x+36,y+48))) for y in range(h)for x in range(w)if capture.getpixel((x+36,y+48))!=mapping.get(saved.getpixel((x,y)))]
 colors=set(saved.getpixel((x,y))for y in range(h)for x in range(w))
 report={'input_sha256':hashlib.sha256(a.input_bmp.read_bytes()).hexdigest(),'saved_sha256':hashlib.sha256(data).hexdigest(),'capture_sha256':hashlib.sha256(a.native_capture.read_bytes()).hexdigest(),'saved_dimensions':list(saved.size),'bmp_header':{'size':header[0],'width':header[1],'height':header[2],'planes':header[3],'bpp':header[4],'compression':header[5],'image_bytes':header[6],'colors_used':header[9]},'palette_rgb':palette,'saved_color_count':len(colors),'bar_pixels_compared':w*20,'bar_mismatch_count':len(bars),'cyan_text_pixel_count':len(text),'text_bounds':[min(x for x,y in text),min(y for x,y in text),max(x for x,y in text)+1,max(y for x,y in text)+1] if text else None,'below_bar_color_counts':{str(k):v for k,v in below.items()},'capture_dimensions':list(capture.size),'capture_canvas_origin':[36,48],'reopened_pixels_compared':w*h,'reopened_mismatch_count':len(bad),'reopened_first_mismatches':bad[:16]}
 report['pass']=saved.size==(200,120) and capture.size==(320,200) and header[3:6]==(1,4,0) and set(palette)==set(LOGICAL) and colors==set(LOGICAL) and not bars and len(text)==280 and set(below)=={(255,255,255),(0,255,255)} and not bad
 a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return int(not report['pass'])
if __name__=='__main__':raise SystemExit(main())
