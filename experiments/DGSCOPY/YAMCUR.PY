#!/usr/bin/env python3
"""Original compact monochrome OEM cursors, drawn from geometric primitives.
No stock/ROM glyph or third-party cursor bitmap is copied. Legacy 32x32 storage;
active marks fit 12x12 after the standard 1x2 cursor compression.
"""
from pathlib import Path
import hashlib, struct

def line(points,a,b):
    x,y=a;X,Y=b;dx=abs(X-x);sx=1 if x<X else -1
    dy=-abs(Y-y);sy=1 if y<Y else -1;err=dx+dy
    while True:
        points.add((x,y))
        if (x,y)==(X,Y):break
        e=2*err
        if e>=dy:err+=dy;x+=sx
        if e<=dx:err+=dx;y+=sy

def arrow(points,a,b):
    line(points,a,b)
    x,y=b;dx=0 if b[0]==a[0] else (1 if b[0]>a[0] else -1)
    dy=0 if b[1]==a[1] else (1 if b[1]>a[1] else -1)
    for k in (-1,1):
        line(points,b,(x-2*dx+k*2*dy,y-2*dy-k*2*dx))

def designs():
    result={}
    p=set()
    # Compact slanted pointer, intentionally drawn independently.
    for y in range(2,11):
        for x in range(2,3+(y-2)//2):p.add((x,y))
    line(p,(5,8),(7,12));result['NORMAL.CUR']=(p,(2,2))
    p=set();line(p,(6,2),(6,12));line(p,(4,2),(8,2));line(p,(4,12),(8,12))
    result['IBEAM.CUR']=(p,(6,7))
    p=set();line(p,(2,7),(12,7));line(p,(7,2),(7,12));result['CROSS.CUR']=(p,(7,7))
    p=set()
    for a,b in [((3,2),(11,2)),((3,12),(11,12)),((3,3),(11,11)),((11,3),(3,11))]:line(p,a,b)
    result['WAIT.CUR']=(p,(7,7))
    p=set();arrow(p,(7,12),(7,2));result['UP.CUR']=(p,(7,2))
    for name,a,b in [('SIZEWE.CUR',(2,7),(12,7)),('SIZENS.CUR',(7,2),(7,12)),
                     ('SIZENWSE.CUR',(3,3),(11,11)),('SIZENESW.CUR',(3,11),(11,3))]:
        p=set();arrow(p,a,b);arrow(p,b,a);result[name]=(p,(7,7))
    p=set()
    for a,b in [((7,7),(2,7)),((7,7),(12,7)),((7,7),(7,2)),((7,7),(7,12))]:arrow(p,a,b)
    result['SIZE.CUR']=(p,(7,7))
    p=set()
    for a,b in [((3,3),(11,3)),((11,3),(11,11)),((11,11),(3,11)),((3,11),(3,3))]:line(p,a,b)
    result['ICON.CUR']=(p,(7,7))
    return result

def encode(points,hot):
    assert all(0<x<15 and 0<y<15 for x,y in points)
    halo={(x+dx,y+dy) for x,y in points for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))}-points
    # Windows 3.0 OEM loader expects the legacy 32x32 resource container.
    # Double vertical source pixels so stock CGA 1x2 compression preserves
    # the independently drawn small shape. Right-hand canvas remains clear.
    points={(x,2*y+k) for x,y in points for k in (0,1)}
    halo={(x,2*y+k) for x,y in halo for k in (0,1)}
    xor=bytearray();mask=bytearray()
    for y in range(31,-1,-1):
        xb=ab=0
        for x in range(32):
            if (x,y) in halo:xb|=1<<(31-x)
            if (x,y) not in points and (x,y) not in halo:ab|=1<<(31-x)
        xor.extend(struct.pack('>I',xb));mask.extend(struct.pack('>I',ab))
    dib=struct.pack('<IiiHHIIiiII',40,32,64,1,1,0,256,0,0,2,0)
    dib+=bytes((0,0,0,0,255,255,255,0))+xor+mask
    return struct.pack('<HHHBBBBHHII',0,2,1,32,32,0,0,hot[0],2*hot[1],len(dib),22)+dib

def stage(resources):
    resources=Path(resources);report={}
    for name,(points,hot) in designs().items():
        data=encode(points,hot);(resources/name).write_bytes(data)
        report[name]=dict(bytes=len(data),hotspot=list(hot),sha256=hashlib.sha256(data).hexdigest())
    return dict(source='independently generated geometric cursors',canvas=[32,32],
                active_shape_limit=[12,12],compression=[1,2],runtime='NOT_TESTED',resources=report)
