#!/usr/bin/env python3
"""CGA640 proportional Helv spacing over the existing XT Pixels 8-row strike.

No glyph resampling or new font engine: preserve every ink pixel, remove
blank side bearings and assign advances for ordinary proportional dialogs.
TEXT80's fixed-cell faces and its producer remain unchanged.
"""
import hashlib
import importlib.machinery
import struct
from pathlib import Path
import CGAFONT

def build(repo,support):
    t80=importlib.machinery.SourceFileLoader('cga640_t80font',str(repo/'src/text80/T80FONT.PY')).load_module()
    origin=(support/'distributions/WINXT/XTTSYS.FON').read_bytes()
    if hashlib.sha256(origin).hexdigest()!=t80.XTTSYS_SHA:
        raise ValueError('Wrong original XT Pixels 8-row strike')
    source,rid=t80.strike(origin);first,last=source[95:97];height=8
    rows={};widths=[]
    B=CGAFONT.B
    for code in range(first,last+1):
        char=B.decode_code(code,source[85]);width,off=struct.unpack_from('<HH',source,118+4*(code-first))
        if width!=8:raise ValueError('Expected retained fixed-cell XT Pixels source')
        bitmap=[[int(bool(source[off+y]&(128>>x))) for x in range(8)] for y in range(height)]
        ink=[x for x in range(8) if any(row[x] for row in bitmap)]
        left=min(ink) if ink else 0;inkwidth=max(ink)-left+1 if ink else 0
        if char and char.isascii():
            advance=9 if char in 'MWmw' else 5 if char=='I' else 3 if char in 'il.,:;\'!|' else 5 if char in 'fjrt' else 6 if char=='k' else 7 if char.islower() else 4 if char==' ' else 8
            advance=max(advance,inkwidth+1)
            rows[char]=[row[left:left+inkwidth] for row in bitmap]
        else:
            advance=8;rows[char]=bitmap
        widths.append(advance)
    contract={key:struct.unpack_from('<H',source,at)[0] for at,key in
        ((66,'type'),(68,'points'),(70,'vert_res'),(72,'horiz_res'),(74,'ascent'),(76,'internal'),(78,'external'))}
    contract.update(italic=0,underline=0,strikeout=0,weight=700,charset=source[85],pix_width=0,
                    height=height,pitch_family=0x21,avg_width=7,max_width=max(widths),
                    first=first,last=last,default=source[97],**{'break':source[98]},widths=widths,face='Helv')
    old=B.glyph
    def glyph(char,width,height,fixed=False):
        bitmap=rows.get(char,rows['?'])
        return [row[:width]+[0]*max(0,width-len(row)) for row in bitmap]
    try:
        B.glyph=glyph;fnt,_=B.fnt(contract)
    finally:B.glyph=old
    data=B.fon(fnt,'CG6HELV',rid,'CGA640 proportional Helv; original XT Pixels ink, 96x48')
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    advances={chr(c):widths[c-first] for c in range(first,last+1)}
    average=sum(advances[c] for c in alphabet)/52
    # The real Open template reserves35 horizontal dialog units for labels.
    limit=35*int(average)//4
    for text in ('Filename:','Directory:'):
        if sum(advances[c] for c in text)>limit:raise ValueError('CGA640 label exceeds conservative native template: '+text)
    return data,dict(source_sha256=t80.XTTSYS_SHA,contract=contract,
                     alphabet_average=average,label_limit=limit,
                     label_widths={s:sum(advances[c] for c in s) for s in ('Filename:','Directory:')},
                     ink='Exact existing XT Pixels glyphs; horizontal blank bearings removed, no resampling')
