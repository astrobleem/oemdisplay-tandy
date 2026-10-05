#!/usr/bin/env python3
"""Regression tests for the font-free image source, encoder and decoder."""
from pathlib import Path
import runpy,tempfile,hashlib,struct
ROOT=Path(__file__).resolve().parents[1]
m=runpy.run_path(str(ROOT/'tools'/'BUILD.PY'));enc,dec=m['encode'],m['decode']
def rejected(fn):
 try:fn()
 except (AssertionError,ValueError,IndexError):return
 raise AssertionError('Invalid input was accepted')
for rows in (
 [[0]*640 for _ in range(200)],
 [[1]*640 for _ in range(200)],
 [[(x//32+y//20)%2 for x in range(640)] for y in range(200)],
 m['pixels'],
):
 data=enc(rows);back,report=dec(data);assert back==rows
 assert report['eol_commands']==200
rejected(lambda:enc([[0]*640]*199))
rejected(lambda:enc([[0]*639]*200))
rejected(lambda:enc([[2]*640]*200))
rejected(lambda:enc([[(x+y)%2 for x in range(640)] for y in range(200)]))
data=enc(m['pixels'])
huge=(b'\x01\x00'*640+b'\x00\x00')*200+b'\x00\x01'
header=bytearray(data[:62]);struct.pack_into('<I',header,2,62+len(huge));struct.pack_into('<I',header,34,len(huge))
rejected(lambda:dec(bytes(header)+huge))
for bad in (data[:-2],data[:62]+bytes((255,0))*3+data[68:],data[:62]+b'\x01\x22'+data[64:]):rejected(lambda bad=bad:dec(bad))
assert data==(ROOT/'assets'/'WXTSPL01.RLE').read_bytes()
pm=runpy.run_path(str(ROOT/'tools'/'ENCODE.PY'))
assert pm['load_pbm']((ROOT/'assets'/'WINDOWSXT.PBM').read_bytes())==m['pixels']
rejected(lambda:pm['load_pbm'](b'P4\n320 200\n'))
print('PASS: 4 pixel round trips; 4 rejected invalid/oversized rasters; 3 rejected malformed streams plus oversized decoder input; exact checked-in RLE; PBM round trip and size rejection')
print('RLE SHA256 '+hashlib.sha256(data).hexdigest())

