#!/usr/bin/env python3
"""Original CGA100 compact UI and 4x6 fixed/OEM faces; developer tool.

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
    if height == 5:
        # The stock Notepad Open template is 192x130 dialog units. A true
        # 3x5 dialog strike targets its layout while desktop text stays 4x6.
        rows = list(G.get(char,G['\u25a1']))
        if char == '0': rows = ['###','#.#','#.#','#.#','###']
        elif char == 'I' and width==2: rows = ['##.','.#.','.#.','.#.','##.']
        elif char == 'i' and width==2: rows = ['#..','...','#..','#..','#..']
        elif char == 'l' and width==2: rows = ['#..','#..','#..','#..','##.']
        elif char == 'j' and width==2: rows = ['.#.','...','.#.','.#.','##.']
        elif char == 'E' and width==3: rows = ['##.','#..','##.','#..','##.']
        elif char == 'F' and width==3: rows = ['##.','#..','##.','#..','#..']
        elif char == 'L' and width==3: rows = ['#..','#..','#..','#..','##.']
        elif char == 'J' and width==3: rows = ['.#.','.#.','.#.','##.','##.']
        elif char == '$': rows = ['.##','##.','.##','##.','.#.']
        elif rows[-1] == '...': rows.pop()
        elif '...' in rows: rows.remove('...')
        else: rows = rows[:5]
        return [[int(x < 3 and rows[y][x] == '#') for x in range(width)] for y in range(5)]
    if height != 6: raise ValueError('CGA100 strike must have five or six rows')
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


def ui_width(char):
    # Preserve a spacing column for capitals, digits and wide lower case.
    # Narrow lower case and punctuation bring the dialog base unit to three
    # pixels without joining every capital in DOS paths and file names.
    if not char:return 4
    if char in " iljI.,:;'|!": return 2
    if char in 'EFJL[]()': return 3
    if char.isascii() and char.islower(): return 4 if char in 'mw' else 3
    return 4


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    B.glyph = drawing
    rec = {'runtime':'NOT_TESTED', 'ui_average':[3,5], 'fixed_cell':[4,6], 'dpi':[48,40], 'fonts':{},
           'provenance':'Original CGA100 ASCII grids and XT Pixels box/block algorithm; MIT',
           'limits':'ASCII plus OEM box/block primitives. Other extended bytes show a fallback box.'}
    for filename,(face,mod,rid,charset,variable,weight,family) in FACES.items():
        ui = filename in ('CG1SYS.FON','CG1HELV.FON')
        small = ui or filename=='CG1COUR.FON'
        width,height = (3 if ui else 4,5) if small else (4,6)
        first,last = (32,255) if charset == 0 else (1,254)
        widths=[ui_width(B.decode_code(c,charset)) if ui else width for c in range(first,last+1)]
        contract = dict(type=0,points=9 if small else 11,vert_res=40,horiz_res=48,ascent=5,internal=0,external=0,
                        italic=0,underline=0,strikeout=0,weight=weight,charset=charset,
                        pix_width=0 if variable else width,height=height,pitch_family=family|int(variable),
                        avg_width=width,max_width=8,first=first,last=last,default=ord('?')-first,
                        **{'break':32-first}, widths=widths,face=face)
        raw,_ = B.fnt(contract)
        data = B.fon(raw,mod,rid,'CGA100 original %dx%d %s; native unqualified'%(width,height,face))
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
        pen=0
        for ch in text:
            width=ui_width(ch)
            if pen+width>160:break
            rows = drawing(ch,width,5)
            for y,row in enumerate(rows):
                for x,p in enumerate(row):
                    if p: im.putpixel((pen+x,6+line*10+y),(0,0,0))
            pen+=width
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
