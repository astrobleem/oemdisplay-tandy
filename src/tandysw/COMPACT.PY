#!/usr/bin/env python3
"""Opt-in low-resolution OEM chrome. Changes staged sources only.

Windows 3.0 derives caption size/hit testing from the OEM bitmap dimensions.
OBM_CLOSE contains two system-menu halves; it is deliberately not a close X.
No USER binary, installed-font list, package pins or installer is changed.
"""
from pathlib import Path
import re, struct

PROFILES = {'compact320': (16, 8), 'compact160': (8, 8), 'textgrid': (16, 8), 'compact160narrow': (8, 8)}
SCROLL = {'compact320': (12, 8), 'compact160': (8, 8), 'textgrid': (8, 8), 'compact160narrow': (8, 8)}


def bitmap(rows):
    """Monochrome OS/2 core BMP, the same encoding as the CGA OEM controls."""
    h, w = len(rows), len(rows[0])
    assert all(len(r) == w and set(r) <= {0, 1} for r in rows)
    stride = (w + 31) // 32 * 4
    bits = bytearray()
    for row in reversed(rows):
        packed = bytearray(stride)
        for x, value in enumerate(row):
            packed[x // 8] |= value << (7 - x % 8)
        bits.extend(packed)
    offset = 14 + 12 + 6
    return (struct.pack('<2sIHHI', b'BM', offset + len(bits), 0, 0, offset) +
            struct.pack('<I4H', 12, w, h, 1, 1) + b'\0\0\0\xff\xff\xff' + bits)


def control(w, h, kind, pressed=False):
    rows = [[1] * w for _ in range(h)]
    # Full bitmap footprint includes the border, not padding around a 27x14 box.
    for x in range(w):
        rows[0][x] = rows[-1][x] = 0
    for y in range(h):
        rows[y][0] = rows[y][-1] = 0
    c = w // 2
    if kind == 'min':
        for x in range(c - 2, c + 2): rows[5][x] = 0
    elif kind == 'max':
        for x in range(c - 2, c + 2): rows[2][x] = rows[5][x] = 0
        for y in range(2, 6): rows[y][c - 2] = rows[y][c + 1] = 0
        for x in range(c - 2, c + 2): rows[3][x] = 0
    elif kind == 'restore':
        for x in range(c - 1, c + 3): rows[2][x] = rows[4][x] = 0
        for y in range(2, 5): rows[y][c - 1] = rows[y][c + 2] = 0
        for x in range(c - 3, c + 1): rows[3][x] = rows[6][x] = 0
        for y in range(3, 7): rows[y][c - 3] = rows[y][c] = 0
    elif kind == 'system':
        # Conventional Windows system-menu dash, never an X.
        for y in (3, 4):
            for x in range(c - 2, c + 2): rows[y][x] = 0
    else:
        raise ValueError(kind)
    return [[1 - v for v in r] for r in rows] if pressed else rows


def arrow(w, h, direction, state='normal'):
    """Original six-pixel arrow with a full compact button footprint."""
    rows = [[1] * w for _ in range(h)]
    for x in range(w): rows[0][x] = rows[-1][x] = 0
    for y in range(h): rows[y][0] = rows[y][-1] = 0
    pixels = [(x,y) for y in range(3) for x in range(2-y,4+y)]
    for x,y in pixels:
        if direction == 'up': x,y=x+(w-6)//2,y+2
        elif direction == 'down': x,y=x+(w-6)//2,h-3-y
        elif direction == 'left': x,y=y+(w-4)//2,x+1
        elif direction == 'right': x,y=w-1-y-(w-4)//2,x+1
        else: raise ValueError(direction)
        if state != 'disabled' or (x+y)%2 == 0: rows[y][x]=0
    if state == 'pressed': rows=[[1-v for v in r] for r in rows]
    elif state not in ('normal','disabled'): raise ValueError(state)
    return rows


def stage(renderer, resources, repo, key, mode):
    if key not in PROFILES: raise ValueError('Unknown compact profile: ' + key)
    if key in ('compact160','compact160narrow') and mode != '160x200x16':
        raise ValueError('compact160 requires the distinct 160-wide mode')
    if key in ('compact320', 'textgrid') and mode not in ('320x200x16', '320x200x4'):
        raise ValueError('320/text profiles require a 320-wide mode')
    w, h = PROFILES[key]
    for kind, normal, down, old in (
            ('min', 'MIN.BMP', 'MIND.BMP', 'ORED.BMP'),
            ('max', 'MAX.BMP', 'MAXD.BMP', 'OZOOM.BMP'),
            ('restore', 'RESTORE.BMP', 'RESTORED.BMP', 'OREST.BMP')):
        for name, pressed in ((normal, False), (down, True), (old, False)):
            (resources / name).write_bytes(bitmap(control(w, h, kind, pressed)))
    normal, down = control(w, h, 'system'), control(w, h, 'system', True)
    (resources / 'SYSMENU.BMP').write_bytes(bitmap([a + b for a, b in zip(normal, down)]))
    (resources / 'OCLOSE.BMP').write_bytes(bitmap([a + b for a, b in zip(normal, down)]))
    sw,sh = SCROLL[key]
    # These are supported OEM configuration words, not USER patches.
    config=resources/'CONFIG.ASM';data=config.read_bytes()
    for old,value,label in [(11,sh,b'Height of vertical thumb'),(23,sw,b'Width of horizontal thumb')]:
        expression=rb'dw[ \t]+'+str(old).encode()+rb'([ \t]+;'+label+rb')'
        data,count=re.subn(expression,lambda m:b'dw      '+str(value).encode()+m.group(1),data)
        assert count==1, label
    config.write_bytes(data)
    for direction,leaf,old,ident in [('up','UP','OUP','UPARROWI'),
            ('down','DOWN','ODOWN','DNARROWI'),('left','LEFT','OLEFT','LFARROWI'),
            ('right','RIGHT','ORIGHT','RGARROWI')]:
        for name,state in [(leaf,'normal'),(leaf+'D','pressed'),(old,'normal'),(leaf+'I','disabled')]:
            (resources/(name+'.BMP')).write_bytes(bitmap(arrow(sw,sh,direction,state)))
        rc=resources/'RC_LOW.RC';data=rc.read_bytes()
        marker=b'1               oembin'
        assert data.count(marker)==1
        line=('OBM_'+ident+'     bitmap         '+leaf.lower()+'i.bmp\r\n').encode('ascii')
        rc.write_bytes(data.replace(marker,line+marker))
    # Driver font descriptions must match the selected 8-row CGA System strike.
    low = repo / 'DDK/286/DISPLAY/1PLANE/RC_LOW'
    (resources / 'FONTS.ASM').write_bytes((low / 'FONTS.ASM').read_bytes().replace(b'\x1a', b''))
    if mode == '320x200x16':
        p = renderer / 'EGA/TSOFT.ASM'
        data = p.read_bytes()
        old = b'dw 96,72,DC_IgnoreDFNP'
        assert data.count(old) == 1
        p.write_bytes(data.replace(old, b'dw 96,48,DC_IgnoreDFNP'))
        p = renderer / 'EGA/TSOFT.DEF'
        data = p.read_bytes()
        assert data.count(b'133,96,72') == 1
        p.write_bytes(data.replace(b'133,96,72', b'200,96,48'))
    if key=='compact160narrow':
        font=resources/'FONTS.ASM';data=font.read_bytes()
        old=b'dw\t9\t\t;lfwidth';assert data.count(old)==2
        font.write_bytes(data.replace(old,b'dw\t6\t\t;lfwidth'))
        p=renderer/'EGA/TSOFT.DEF';data=p.read_bytes()
        assert data.count(b'200,96,48')==1
        p.write_bytes(data.replace(b'200,96,48',b'0160,96,48'))
    return dict(profile=key, button_pixels=[w, h], system_menu_bitmap=[2*w, h],
                revision='R2 compact scroll arrows',scroll_arrow_pixels=[sw,sh],
                scroll_thumb_pixels=[sw,sh],
                system_font=('Original XTS6SYS/XTS6FIX, eight rows; graphics160 only' if key=='compact160narrow'
                             else 'CGA 8-row strike; installed font list preserved'),
                configuration='WIN.INI [windows] BorderWidth=1; optional fixture only',
                user_patch=False, runtime='NOT_TESTED')
