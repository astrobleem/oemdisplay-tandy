#!/usr/bin/env python3
"""Encode a 640x200 two-color binary PBM (P4) to Windows 3.0 CGA RLE."""
from pathlib import Path
import argparse,runpy
mod=runpy.run_path(str(Path(__file__).with_name('BUILD.PY')))
def load_pbm(data):
 pos=0
 def token():
  nonlocal pos
  while pos<len(data):
   if data[pos:pos+1]==b'#':
    end=data.find(b'\n',pos)
    if end<0:raise ValueError('Truncated PBM comment')
    pos=end+1
   elif data[pos] in b' \t\r\n':pos+=1
   else:break
  start=pos
  while pos<len(data) and data[pos] not in b' \t\r\n':pos+=1
  return data[start:pos]
 if (token(),token(),token())!=(b'P4',b'640',b'200'):raise ValueError('Expected binary PBM P4, 640x200')
 if pos>=len(data) or data[pos] not in b' \t\r\n':raise ValueError('Missing raster separator')
 pos+=2 if data[pos:pos+2]==b'\r\n' else 1
 raw=data[pos:]
 if len(raw)!=16000:raise ValueError('Expected exactly 16000 packed monochrome pixel bytes')
 return [[1-((raw[y*80+x//8]>>(7-x%8))&1) for x in range(640)] for y in range(200)]
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('pbm',type=Path);p.add_argument('rle',type=Path);a=p.parse_args()
 rows=load_pbm(a.pbm.read_bytes());data=mod['encode'](rows);out,report=mod['decode'](data);assert out==rows
 a.rle.write_bytes(data);print(report)
