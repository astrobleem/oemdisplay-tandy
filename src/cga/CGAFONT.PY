#!/usr/bin/env python3
"""Original 4x6 CGA100 System/Fixed/OEM and dialog faces; developer tool.

ASCII grids are drawn here, not sampled from ROM, installed or Windows
fonts. CP437 box/block primitives reuse XT Pixels' original algorithm.
Unsupported extended glyphs deliberately use a visible fallback box.
The existing XT Pixels FNT/FON serializer is reused unchanged.
"""
import argparse
import hashlib
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1] / 'tools' / 'XTFONTS'
sys.path.insert(0, str(KIT))
sys.modules['GLYPHS'] = importlib.machinery.SourceFileLoader('GLYPHS', str(KIT/'GLYPHS.PY')).load_module()
B = importlib.machinery.SourceFileLoader('cga_font_writer', str(KIT/'BUILD.PY')).load_module()
G = {}


def put(char, grid):
    rows = grid.split('/')
    if len(rows) != 6 or any(len(row) != 3 or set(row)-set('.#') for row in rows):
        raise ValueError('Bad 3x6 grid: '+char)
    G[char] = rows


# Three ink columns plus one spacing column. Lower-case has its own
# x-height; row six is available for descenders, underlines and commas.
DATA = {
 ' ':'.../.../.../.../.../...', '!':'.#./.#./.#./.../.#./...',
 '"':'#.#/#.#/.../.../.../...', '#':'#.#/###/#.#/###/#.#/...',
 '$':'.#./.##/##./.##/##./.#.', '%':'#.#/..#/.#./#../#.#/...',
 '&':'.#./#.#/.#./#.#/.##/...', "'":'.#./.#./.../.../.../...',
 '(':'..#/.#./.#./.#./..#/...', ')':'#../.#./.#./.#./#../...',
 '*':'.../#.#/.#./#.#/.../...', '+':'.../.#./###/.#./.../...',
 ',':'.../.../.../.../.#./#..', '-':'.../.../###/.../.../...',
 '.':'.../.../.../.../.#./...', '/':'..#/..#/.#./#../#../...',
 '0':'###/#.#/###/#.#/###/...', '1':'.#./##./.#./.#./###/...',
 '2':'##./..#/.#./#../###/...', '3':'##./..#/.#./..#/##./...',
 '4':'#.#/#.#/###/..#/..#/...', '5':'###/#../##./..#/##./...',
 '6':'.##/#../###/#.#/###/...', '7':'###/..#/.#./.#./.#./...',
 '8':'###/#.#/###/#.#/###/...', '9':'###/#.#/###/..#/##./...',
 ':':'.../.#./.../.#./.../...', ';':'.../.#./.../.#./.#./#..',
 '<':'..#/.#./#../.#./..#/...', '=':'.../###/.../###/.../...',
 '>':'#../.#./..#/.#./#../...', '?':'##./..#/.#./.../.#./...',
 '@':'.#./#.#/#.#/#../.##/...',
 'A':'.#./#.#/###/#.#/#.#/...', 'B':'##./#.#/##./#.#/##./...',
 'C':'.##/#../#../#../.##/...', 'D':'##./#.#/#.#/#.#/##./...',
 'E':'###/#../##./#../###/...', 'F':'###/#../##./#../#../...',
 'G':'.##/#../#.#/#.#/.##/...', 'H':'#.#/#.#/###/#.#/#.#/...',
 'I':'###/.#./.#./.#./###/...', 'J':'..#/..#/..#/#.#/.#./...',
 'K':'#.#/#.#/##./#.#/#.#/...', 'L':'#../#../#../#../###/...',
 'M':'#.#/###/###/#.#/#.#/...', 'N':'#.#/###/###/###/#.#/...',
 'O':'.#./#.#/#.#/#.#/.#./...', 'P':'##./#.#/##./#../#../...',
 'Q':'.#./#.#/#.#/###/.##/...', 'R':'##./#.#/##./#.#/#.#/...',
 'S':'.##/#../.#./..#/##./...', 'T':'###/.#./.#./.#./.#./...',
 'U':'#.#/#.#/#.#/#.#/###/...', 'V':'#.#/#.#/#.#/#.#/.#./...',
 'W':'#.#/#.#/###/###/#.#/...', 'X':'#.#/#.#/.#./#.#/#.#/...',
 'Y':'#.#/#.#/.#./.#./.#./...', 'Z':'###/..#/.#./#../###/...',
 '[':'.##/.#./.#./.#./.##/...', '\\':'#../#../.#./..#/..#/...',
 ']':'##./.#./.#./.#./##./...', '^':'.#./#.#/.../.../.../...',
 '_':'.../.../.../.../.../###', '`':'#../.#./.../.../.../...',
 'a':'.../.##/#.#/#.#/.##/...', 'b':'#../#../##./#.#/##./...',
 'c':'.../.##/#../#../.##/...', 'd':'..#/..#/.##/#.#/.##/...',
 'e':'.../.#./#.#/##./.##/...', 'f':'.##/.#./###/.#./.#./...',
 'g':'.../.##/#.#/.##/..#/##.', 'h':'#../#../##./#.#/#.#/...',
 'i':'.#./.../.#./.#./.#./...', 'j':'..#/.../..#/..#/#.#/.#.',
 'k':'#../#.#/##./#.#/#.#/...', 'l':'##./.#./.#./.#./..#/...',
 'm':'.../###/###/#.#/#.#/...', 'n':'.../##./#.#/#.#/#.#/...',
 'o':'.../.#./#.#/#.#/.#./...', 'p':'.../##./#.#/##./#../#..',
 'q':'.../.##/#.#/.##/..#/..#', 'r':'.../#.#/##./#../#../...',
 's':'.../.##/##./.##/##./...', 't':'.#./###/.#./.#./..#/...',
 'u':'.../#.#/#.#/#.#/.##/...', 'v':'.../#.#/#.#/#.#/.#./...',
 'w':'.../#.#/#.#/###/###/...', 'x':'.../#.#/.#./.#./#.#/...',
 'y':'.../#.#/#.#/.##/..#/##.', 'z':'.../###/..#/#../###/...',
 '{':'.##/.#./#../.#./.##/...', '|':'.#./.#./.#./.#./.#./...',
 '}':'##./.#./..#/.#./##./...', '~':'.../.##/##./.../.../...',
 '\u25a1':'###/#.#/#.#/#.#/###/...',
}
for ch, rows in DATA.items(): put(ch, rows)
# Distinguish 0/8 while retaining three columns.
put('0', '.#./#.#/#.#/#.#/.#./.#.')


def drawing(char, width, height, fixed=False):
    if height != 6: raise ValueError('CGA100 strike must have six rows')
    cell = B.cell_glyph(char, width, height) if fixed else None
    if cell is not None: return cell
    if char not in G:
        # No accent squeezing: a visible fallback is more honest than a
        # base letter silently losing the accent at this size.
        char = '\u25a1'
    rows = G[char]
    return [[int(x < 3 and rows[y][x] == '#') for x in range(width)] for y in range(height)]


FACES = {'CG1SYS.FON': ('System','FONTS',27,0,True,700,0x20),
         'CG1FIX.FON': ('Courier','FIXFONTS',27,0,False,400,0x30),
         'CG1OEM.FON': ('Terminal','OEMFONTS',29,255,False,400,0x30),
         'CG1HELV.FON': ('Helv','CG1HELV',27,0,True,700,0x20),
         'CG1COUR.FON': ('Courier','CG1COUR',27,0,False,400,0x30)}


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    B.glyph = drawing
    rec = {'runtime':'NOT_TESTED', 'cell':[4,6], 'dpi':[48,40], 'fonts':{},
           'provenance':'Original CGA100 ASCII grids and XT Pixels box/block algorithm; MIT',
           'limits':'ASCII plus OEM box/block primitives. Other extended bytes show a fallback box.'}
    for filename,(face,mod,rid,charset,variable,weight,family) in FACES.items():
        first,last = (32,255) if charset == 0 else (1,254)
        contract = dict(type=0,points=11,vert_res=40,horiz_res=48,ascent=5,internal=0,external=0,
                        italic=0,underline=0,strikeout=0,weight=weight,charset=charset,
                        pix_width=0 if variable else 4,height=6,pitch_family=family|int(variable),
                        avg_width=4,max_width=8,first=first,last=last,default=ord('?')-first,
                        **{'break':32-first}, widths=[4]*(last-first+1),face=face)
        raw,_ = B.fnt(contract)
        data = B.fon(raw,mod,rid,'CGA100 original 4x6 '+face+'; native unqualified')
        (out/filename).write_bytes(data)
        fallback = []
        for code in range(first,last+1):
            ch = B.decode_code(code,charset)
            if ch not in G and not (charset == 255 and B.cell_glyph(ch,4,6) is not None):
                fallback.append(code)
        rec['fonts'][filename] = dict(face=face,module=mod,rid=rid,contract=contract,
                                     fallback_bytes=fallback,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    B.textfile(out/'CGAFONT.JSN',json.dumps(rec,indent=2)+'\n')
    return rec


def specimen(out):
    from PIL import Image, ImageDraw
    lines = ['HOST FONT SPECIMEN - NOT WINDOWS PROOF',
             'File Edit Search Help', 'Windows 3.0 - CGA 160x100',
             'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz',
             '0123456789  Il1 O08 B6  rn m w', 'OK  Cancel  Save As...  [x] (o)',
             'C:\\WINDOWS>WIN /R  AaBbCcGgPpQqYy', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~']
    im = Image.new('RGB',(160,100),'#aaa')
    for line,text in enumerate(lines):
        for i,ch in enumerate(text[:40]):
            rows = drawing(ch,4,6)
            for y,row in enumerate(rows):
                for x,p in enumerate(row):
                    if p: im.putpixel((i*4+x,6+line*10+y),(0,0,0))
    im.save(out/'CGAFONT.PNG')
    im.resize((640,480),Image.Resampling.NEAREST).save(out/'CGA43.PNG')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args = ap.parse_args()
    if args.out.exists(): raise SystemExit('Choose a fresh --out')
    build(args.out)
    specimen(args.out)
    print('CGA100 original fonts generated; native loading/legibility NOT_TESTED')


if __name__ == '__main__': main()
