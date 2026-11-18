"""Build metric-compatible System candidates; never overwrite accepted assets.

Only glyph bitmap bytes change. FNT/NE headers, advances, offsets, fixed
fonts and the approved PR219 M/W and I/J/C/E/S glyphs remain exact.
"""
import argparse
import importlib.machinery as M
from pathlib import Path
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]
I = M.SourceFileLoader('sysfont_inspect', str(ROOT/'tools/XTFONTS/INSPECT.PY')).load_module()
G = M.SourceFileLoader('sysfont_glyphs', str(ROOT/'tools/XTFONTS/GLYPHS.PY')).load_module().G

# Hand-drawn compact forms. Their advances are unchanged; do not squeeze a
# five-column M into three columns or fill its counters with solid strokes.
SMALL = {
 'M':'#.#/###/#.#/#.#/#.#', 'N':'#.#/###/###/#.#/#.#',
 'W':'#.#/#.#/#.#/###/#.#', '0':'###/#.#/#.#/#.#/###',
 '8':'.#./#.#/.#./#.#/.#.', 'e':'.../.##/###/#../.##',
 's':'.../.##/#../..#/##.', 'x':'.../#.#/.#./.#./#.#',
}
MEDIUM = {
 '0':'###/#.#/#.#/#.#/###/...',
 '8':'.#./#.#/.#./#.#/.#./...',
 'e':'.../.#./#.#/###/.##/...',
 's':'.../.##/##./..#/##./...',
 'N':'#.#/###/#.#/###/#.#/...',
}

def source(name):
    if name == 'XTCSYS.FON':
        return (ROOT/'tools/XTFONTS/COMPAT'/name).read_bytes()
    if name == 'XTESYS.FON':
        return (ROOT/'distributions/WINXT'/name).read_bytes()
    with zipfile.ZipFile(ROOT/'downloads/FRESH/CGA.ZIP') as z:
        return z.read('CGA/'+name)

def strike(data):
    entries=[r for r in I.resources(data)[1] if r[0]==0x8008]
    if len(entries)!=1:raise ValueError('Expected one bitmap strike')
    base=entries[0][3]
    raw=data[base:base+I.dword(data,base+2)]
    if I.word(raw,0)!=0x200 or raw[85]!=0 or I.word(raw,86):
        raise ValueError('Expected FNT2 ANSI proportional System')
    return raw,base

def bitmap(raw,code):
    width,off=struct.unpack_from('<HH',raw,118+4*(code-raw[95]))
    height=I.word(raw,88)
    return [[(raw[off+x//8*height+y]>>(7-x%8))&1 for x in range(width)] for y in range(height)]

def improve(name,data):
    raw,base=strike(data);height=I.word(raw,88);out=bytearray(data)
    for code in range(33,127):
        char=chr(code);old=bitmap(raw,code);width=len(old[0])
        if height in (5,6):
            grid=(SMALL if height==5 else MEDIUM).get(char)
            if grid is None:continue
            rows=grid.split('/')
            # Keep a spacing column whenever the existing cell permits it.
            rows=[[int(x<len(row) and row[x]=='#') for x in range(width)] for row in rows]
        else:
            if name=='XTCSYS.FON' and char in 'MWIJCES':continue
            grid=G.get(char)
            if grid is None:continue
            ink=len(grid[0])
            # Preserve narrow glyphs rather than lose pixels through sampling.
            if ink>width-1:continue
            left=(width-ink)//2
            if height==8:ymap=range(8)
            elif height==12:ymap=[None,0,1,2,2,3,4,4,5,6,7,None]
            else:raise ValueError('Unexpected System height')
            rows=[[int(sy is not None and left<=x<left+ink and grid[sy][x-left]=='#')
                   for x in range(width)] for sy in ymap]
        _,off=struct.unpack_from('<HH',raw,118+4*(code-raw[95]))
        for x in range(width):
            for y in range(height):
                at=base+off+x//8*height+y;mask=128>>(x%8)
                out[at]=(out[at]|mask) if rows[y][x] else (out[at]&~mask)
    return bytes(out)

def build(out):
    out.mkdir(parents=True,exist_ok=False)
    for name in ('CG1SYS.FON','CG2SYS.FON','XTCSYS.FON','XTESYS.FON'):
        (out/name).write_bytes(improve(name,source(name)))
        print(name)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    build(p.parse_args().out)
