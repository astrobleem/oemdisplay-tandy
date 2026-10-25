#!/usr/bin/env python3
"""Original six-row CGA100 OEM chrome, using the existing BMP serializer.

The checkbox/radio atlas keeps the Windows 3.0 4-column/3-row layout.
No USER patch or per-application replacement is used. Native hit testing
and metrics are mandatory acceptance gates (README.MD).
"""
import importlib.machinery
import re
from pathlib import Path
from STAGECGA import read, write, once

COMPACT = importlib.machinery.SourceFileLoader('cga_compact', str(
    Path(__file__).resolve().parent.parent / 'tandysw' / 'COMPACT.PY')).load_module()


def box(kind, pressed=False, w=8, h=6):
    rows = [[int(0 < x < w-1 and 0 < y < h-1) for x in range(w)] for y in range(h)]
    c = w // 2
    if kind == 'system':
        for x in range(c-2,c+2): rows[2][x] = 0
    elif kind == 'min':
        for x in range(c-2,c+2): rows[4][x] = 0
    elif kind == 'max':
        for y in range(1,5): rows[y][c-2] = rows[y][c+1] = 0
        for x in range(c-2,c+2): rows[1][x] = rows[4][x] = 0
    elif kind == 'restore':
        for x,y in ((3,1),(4,1),(5,1),(5,2),(2,2),(3,2),(4,2),(2,3),(4,3),(2,4),(3,4),(4,4)):
            rows[y][x] = 0
    else:
        raise ValueError(kind)
    return [[1-v for v in row] for row in rows] if pressed else rows


def arrow(direction, state='normal'):
    rows = [[int(0 < x < 5 and 0 < y < 5) for x in range(6)] for y in range(6)]
    for x,y in ((2,1),(1,2),(2,2),(3,2),(2,3)):
        if direction == 'down': y = 5-y
        elif direction == 'left': x,y = y,x
        elif direction == 'right': x,y = 5-y,x
        elif direction != 'up': raise ValueError(direction)
        if state != 'disabled' or (x+y)%2 == 0: rows[y][x] = 0
    return [[1-v for v in r] for r in rows] if state == 'pressed' else rows


def stage(resources):
    images = {}
    for kind, normal, down, old in (('min','MIN','MIND','ORED'), ('max','MAX','MAXD','OZOOM'),
                                   ('restore','RESTORE','RESTORED','OREST')):
        for name, state in ((normal,False),(down,True),(old,False)):
            images[name+'.BMP'] = box(kind, state)
    system = [a+b for a,b in zip(box('system'), box('system',True))]
    images.update({'SYSMENU.BMP':system, 'OCLOSE.BMP':system})
    rc = read(resources / 'RC_LOW.RC')
    for direction,leaf,old,ident in (('up','UP','OUP','UPARROWI'), ('down','DOWN','ODOWN','DNARROWI'),
                                    ('left','LEFT','OLEFT','LFARROWI'), ('right','RIGHT','ORIGHT','RGARROWI')):
        for name,state in ((leaf,'normal'),(leaf+'D','pressed'),(old,'normal'),(leaf+'I','disabled')):
            images[name+'.BMP'] = arrow(direction,state)
        rc = once(rc,'1               oembin', 'OBM_'+ident+'     bitmap         '+leaf.lower()+'i.bmp\n1               oembin')
    # Menu check and submenu arrow have a six-row footprint as well.
    images['OCHECK.BMP'] = [[1]*6 for _ in range(6)]
    for x,y in ((1,3),(2,4),(3,3),(4,2)): images['OCHECK.BMP'][y][x] = 0
    images['MNARROW.BMP'] = [[1]*4 for _ in range(6)]
    for x,y in ((1,1),(1,2),(2,2),(1,3)): images['MNARROW.BMP'][y][x] = 0
    images['COMBO.BMP'] = arrow('down')
    # Four variants per row: unchecked/checked, then pressed versions.
    # Rows: checkbox, radio, disabled checkbox, matching the existing atlas.
    atlas = [[1]*24 for _ in range(18)]
    for row in range(3):
        for column in range(4):
            tile = [[1]*6 for _ in range(6)]
            for y in range(6):
                for x in range(6):
                    border = (x in (0,5) or y in (0,5)) if row != 1 else (
                        ((y in (0,5) and 1 <= x <= 4) or (x in (0,5) and 1 <= y <= 4)))
                    if border and (row != 2 or (x+y)%2 == 0): tile[y][x] = 0
            if column%2:
                points = ((2,2),(3,2),(2,3),(3,3)) if row == 1 else ((1,1),(4,1),(2,2),(3,2),(2,3),(3,3),(1,4),(4,4))
                for x,y in points:
                    if row != 2 or (x+y)%2 == 0: tile[y][x] = 0
            if column >= 2: tile = [[1-p for p in r] for r in tile]
            for y in range(6): atlas[row*6+y][column*6:column*6+6] = tile[y]
    images['OBUTTON.BMP'] = atlas
    config = read(resources / 'CONFIG.ASM')
    for old,value,label in ((11,6,'Height of vertical thumb'),(23,6,'Width of horizontal thumb'),
                            (2,4,'Icon horiz compression factor'),(4,8,'Icon vert compression factor'),
                            (1,2,'Cursor horz compression factor'),(2,4,'Cursor vert compression factor')):
        pattern = r'dw[ \t]+'+str(old)+r'([ \t]+;'+label+r')'
        config,n = re.subn(pattern, lambda m:'dw      '+str(value)+m[1],config)
        if n != 1: raise ValueError('CGAUI config: '+label)
    fonts = read(resources / 'FONTS.ASM')
    fonts,n = re.subn(r'dw\t8(\t+;lfheight)',r'dw\t6\1',fonts)
    if n != 3: raise ValueError('CGAUI font heights')
    fonts,n = re.subn(r'dw\t[89](\t+;lfwidth)',r'dw\t4\1',fonts)
    if n != 3: raise ValueError('CGAUI font widths')
    for name,rows in images.items():
        (resources/name).write_bytes(COMPACT.bitmap(rows))
    write(resources/'CONFIG.ASM',config)
    write(resources/'FONTS.ASM',fonts)
    write(resources/'RC_LOW.RC',rc)
    return images
