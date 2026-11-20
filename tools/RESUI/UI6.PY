"""Original six-ink-row System face for compact 200-line graphics UI.

Separate from released CG1/CG2 and PPCUI; no proprietary font input.
"""
from pathlib import Path
import importlib.machinery as M,sys
ROOT=Path(__file__).resolve().parents[2]
C=M.SourceFileLoader('ui6_cga',str(ROOT/'src/cga/CGAFONT.PY')).load_module()
B=C.B
# One deliberate blank advance column, with full counters and a visible
# baseline. Narrow i/l retain two-pixel advances; m/w gain five ink columns.
FORMS={
 'P':'##./#.#/#.#/##./#../#..',
 'a':'.../.##/..#/.##/#.#/.##',
 'b':'#../#../##./#.#/#.#/##.',
 'c':'.../.##/#../#../#../.##',
 'd':'..#/..#/.##/#.#/#.#/.##',
 'e':'.../.#./#.#/###/#../.##',
 'f':'.##/.#./###/.#./.#./.#.',
 'h':'#../#../##./#.#/#.#/#.#',
 'i':'#/./#/#/#/#', 'l':'#/#/#/#/#/#',
 'j':'.#/../.#/.#/.#/#.',
 'n':'.../##./#.#/#.#/#.#/#.#',
 'o':'.../.#./#.#/#.#/#.#/.#.',
 'r':'.../#.#/##./#../#../#..',
 's':'.../.##/#../.#./..#/##.',
 't':'.#./###/.#./.#./.#./..#',
 'u':'.../#.#/#.#/#.#/#.#/.##',
 'v':'.../#.#/#.#/#.#/#.#/.#.',
 'm':'...../##.#./#.#.#/#.#.#/#.#.#/#.#.#',
 'w':'...../#...#/#...#/#.#.#/#.#.#/.#.#.',
 'M':'#...#/##.##/#.#.#/#...#/#...#/#...#',
 'W':'#...#/#...#/#...#/#.#.#/#.#.#/.#.#.',
 'U':'#.#/#.#/#.#/#.#/#.#/.#.',
 'I':'###/.#./.#./.#./.#./###',
 'T':'###/.#./.#./.#./.#./.#.',
 '0':'.#./#.#/#.#/#.#/#.#/.#.',
 '8':'.#./#.#/.#./#.#/#.#/.#.',
 '(':'..#/.#./#../#../.#./..#',
 ')':'#../.#./..#/..#/.#./#..',
}

def width(char):
 if char is None:return 4
 if char in 'MWmw':return 6
 if char in " il.,:;'|!":return 2
 return 4

def drawing(char,w,h,fixed=False):
 rows=FORMS.get(char)
 if rows:rows=rows.split('/')
 else:
  rows=list(C.G.get(char,C.G['\u25a1']))
  # Existing capital outlines have five ink rows plus a blank sixth.
  # Extend their vertical stems once, retaining the bottom outline.
  if char and (char.isupper() or char.isdigit()):rows=rows[:4]+[rows[3],rows[4]]
 return [[int(x<len(rows[y]) and rows[y][x]=='#') for x in range(w)] for y in range(h)]

def build():
 B.glyph=drawing
 widths=[width(B.decode_code(c,0)) for c in range(32,256)]
 contract=dict(type=0,points=11,vert_res=40,horiz_res=48,ascent=6,internal=0,external=0,
  italic=0,underline=0,strikeout=0,weight=700,charset=0,pix_width=0,height=6,
  pitch_family=0x21,avg_width=4,max_width=6,first=32,last=255,default=31,
  widths=widths,face='System',**{'break':0})
 raw,_=B.fnt(contract)
 return B.fon(raw,'FONTS',27,'Original compact six-row proportional System')
if __name__=='__main__':Path(sys.argv[1]).write_bytes(build())
