#!/usr/bin/env python3
"""Host reference for CGA100 VRAM capture validation; no hardware I/O.

This model checks memory/encoding, not scanout, snow, CRTC compatibility,
Windows execution or performance. Planes are the retained DDK R/G/B/I order.
"""
WIDTH, HEIGHT, STRIDE, SHADOW = 160, 100, 20, 8000


def attribute_offset(x,y):
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT): raise ValueError('Outside CGA100')
    return y*160+(x//2)*2+1


def shadow_pixel(shadow,x,y):
    p = y*80+x//8
    mask = 0x80 >> (x%8)
    return sum(bit for offset,bit in ((0,4),(20,2),(40,1),(60,8)) if shadow[p+offset]&mask)


def present(shadow,vram,rect):
    if len(shadow) != SHADOW or len(vram) != 16384: raise ValueError('Wrong buffer size')
    x0,y0,x1,y1 = rect
    x0,x1 = max(0,x0),min(WIDTH,x1)
    y0,y1 = max(0,y0),min(HEIGHT,y1)
    if x0 >= x1 or y0 >= y1: return 0
    first,last = x0//8,(x1+7)//8
    writes = 0
    for y in range(y0,y1):
        for x in range(first*8,last*8,2):
            off = attribute_offset(x,y)
            vram[off-1] = 0xde
            vram[off] = (shadow_pixel(shadow,x,y)<<4)|shadow_pixel(shadow,x+1,y)
            writes += 2
    return writes


def decode(vram):
    if len(vram) != 16384: raise ValueError('Capture must contain all 16 KB of CGA VRAM')
    if any(vram[off] != 0xde for off in range(0,16000,2)):
        raise ValueError('Capture contains damaged/non-DEh character bytes')
    return [[(vram[attribute_offset(x,y)] >> (4 if x%2 == 0 else 0)) & 15
             for x in range(WIDTH)] for y in range(HEIGHT)]


def cursor_rectangle(x,y,w,h):
    if not (0 <= w <= 32 and 0 <= h <= 32): raise ValueError('Cursor shape outside retained contract')
    left,right,top,bottom = max(0,x),min(WIDTH,x+w),max(0,y),min(HEIGHT,y+h)
    if left >= right or top >= bottom: return []
    first,last = (left//2)*2,((right-1)//2)*2+2
    return [row*160+column for row in range(top,bottom) for column in range(first,last)]
