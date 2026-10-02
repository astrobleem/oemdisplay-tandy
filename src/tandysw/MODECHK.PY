#!/usr/bin/env python3
"""Independent raw-VRAM oracle for MODETEST.EXE; no BIOS pixel-read oracle.

Build: copy MODETEST.C/DEF/RSP, MODEBLD.BAT and PROBEASM.ASM into a fresh
DOS build directory. Mount the repository/toolchain as C:, stage as D:,
then run D:\\MODEBLD.BAT in a headless DOSBox-X 8086_prefetch instance.
Run only in an isolated own-media Windows 3.0 guest after RESERVE.COM.
C:\\MODETEST.INI [mode] defaults: width=640, colors=4, bios=10, phases=31.
The 640x200x4 default uses palette=1 (black/red/green/white), hardware
[0,12,10,15]. Use palette=0 and --profile 640x200x4-cga for prior CGA data.
Set metadata to a listed profile; phase bits are core=1, imports=2,
exports/readback=4, text/cursor=8, raw aliases=16 (2/4-color). The checker requires all phases by default.

This checker imports no renderer, quantizer, or encoder implementation.
Each captured frame is decoded and every visible pixel compared against
independently synthesized expectations, including right/bottom edges.
Unused physical-bank bytes are checked for unintended changes. Text glyph
shape uses a separately rendered memory-DDB reference (relational oracle),
while its colors and screen placement are checked independently. Cursor
shape is checked for visible change/locality and exact full-frame restore.
Raw VRAM cannot prove RGB palette-register programming; [0,11,13,15] is the
historical 640x200x4-cga hardware-palette contract, not an emulator palette readback.

Examples:
  python3 MODECHK.PY /isolated/guest --profile 640x200x4 --out result.json
  python3 MODECHK.PY /isolated/control --profile 320x200x16 --phases 1
  python3 MODECHK.PY --selftest
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

BASE = [(0,0,0),(0,0,128),(0,128,0),(0,128,128),
        (128,0,0),(128,0,128),(128,128,0),(128,128,128),
        (64,64,64),(0,0,255),(0,255,0),(0,255,255),
        (255,0,0),(255,0,255),(255,255,0),(255,255,255)]
TIES = [(0,127,128),(0,128,127),(127,127,255),
        (128,128,255),(255,127,128),(255,128,127)]
FOUR = [(0,0,0),(0,255,255),(255,0,255),(255,255,255)]
REDGREEN = [(0,0,0),(255,0,0),(0,255,0),(255,255,255)]
PROFILES = {
    '640x200x4': dict(width=640, colors=4, bios=10, banks=4, pitch=160,
                       storage=32768, palette=REDGREEN, hardware=[0,12,10,15],dpi=[96,48],font_height=8,pens=20,palette_kind=1),
    '640x200x4-cga': dict(width=640, colors=4, bios=10, banks=4, pitch=160,
                       storage=32768, palette=FOUR, hardware=[0,11,13,15],dpi=[96,48],font_height=8,pens=20,palette_kind=0),
    '320x200x16': dict(width=320, colors=16, bios=9, banks=4, pitch=160,
                        storage=32768, palette=BASE, hardware=list(range(16))),
    '160x200x16': dict(width=160, colors=16, bios=8, banks=2, pitch=80,
                        storage=16384, palette=BASE, hardware=list(range(16)),dpi=[96,48],font_height=8,pens=80,palette_kind=0),
    '320x200x4': dict(width=320, colors=4, bios=4, banks=2, pitch=80,
                       storage=16384, palette=FOUR, hardware=[0,11,13,15],dpi=[96,48],font_height=8,pens=20,palette_kind=0),
    '640x200x2': dict(width=640, colors=2, bios=6, banks=2, pitch=80,
                       storage=16384, palette=[(0,0,0),(255,255,255)], hardware=[0,15],dpi=[96,48],font_height=8,pens=10,palette_kind=0),
}


def nearest(rgb, p):
    # min on (distance,index) explicitly enforces each declared palette order.
    return min(range(len(p['palette'])),
               key=lambda i: (sum((rgb[j]-p['palette'][i][j])**2
                                  for j in range(3)),i))


def logical_rgb(n, p):
    return p['palette'][nearest((BASE+TIES)[n],p)]


def colorref(rgb):
    return rgb[0] | rgb[1]<<8 | rgb[2]<<16


def loc(p,x,y):
    row=(y%p['banks'])*8192+(y//p['banks'])*p['pitch']
    if p['bios']==10:
        return row+2*(x//8),7-x%8
    bits={2:1,4:2,16:4}[p['colors']]
    return row+x//(8//bits),(8//bits-1-x%(8//bits))*bits


def decode(raw,p):
    if len(raw)!=32768:
        raise ValueError('Frame must contain the complete 32768-byte B800 window')
    out=[]
    for y in range(200):
        for x in range(p['width']):
            a,s=loc(p,x,y)
            if p['bios']==10:
                out.append((raw[a]>>s&1)|((raw[a+1]>>s&1)<<1))
            else:
                out.append(raw[a]>>s&(p['colors']-1))
    return out


def used_bytes(p):
    used=set()
    for y in range(200):
        start=(y%p['banks'])*8192+(y//p['banks'])*p['pitch']
        used.update(range(start,start+p['pitch']))
    return used


def strips(p, grid=False):
    w=p['width'];unit=w//16
    return [nearest(BASE[(x//unit+(y//20)*3 if grid else x//unit)&15],p)
            for y in range(200) for x in range(w)]


def solid(p,n):
    return [nearest(BASE[n],p)]*(p['width']*200)


def pattern(p,x,y,bpp=4):
    n=(x*3+y*5)&15
    if bpp==1:n=15 if n<7 else 0
    return nearest(BASE[n],p)


def draw_copy(dst,p,c,source,srcw,srch,xor=False,band=False):
    w=p['width']
    for oy in range(c['HEIGHT']):
        sy=(11-c['SY']-c['HEIGHT'] if band else c['SY'])+oy
        dy=c['DY']+oy
        if not (0<=sy<srch and 0<=dy<200):continue
        if band and not c['START']<=10-sy<c['START']+c['SCANS']:continue
        for ox in range(c['WIDTH']):
            sx=c['SX']+ox;dx=c['DX']+ox
            if not (0<=sx<srcw and 0<=dx<w):continue
            if c['CLIP'] and not (85<=dx<103 and 62<=dy<68):continue
            v=source[sy*srcw+sx]
            dst[dy*w+dx]=dst[dy*w+dx]^v if xor else v


def readlog(path):
    all_values={};cases=[];active=None
    for s in path.read_text().splitlines():
        if '=' not in s:continue
        k,v=s.split('=',1);v=int(v);all_values.setdefault(k,[]).append(v)
        if k=='CASE':active={'CASE':v,'events':[]};cases.append(active)
        elif active is not None:
            active['events'].append((k,v));active[k]=v
            if k=='ENDCASE':active=None
    return all_values,cases


def ddb_pixels(raw,w,h,stride,p):
    out=[];indices=[]
    for y in range(h):
        for x in range(w):
            index=sum(((raw[y*stride*4+plane*stride+x//8]>>(7-x%8))&1)<<plane
                      for plane in range(4))
            indices.append(index)
            if p['colors']==4:out.append(index&3)
            elif p['colors']==2:out.append(index&1)
            else:out.append((index&10)|((index&1)<<2)|((index&4)>>2))
    return out,indices


def differences(expected,actual,w,limit=16):
    count=0;first=[]
    for i,(e,a) in enumerate(zip(expected,actual)):
        if e!=a:
            count+=1
            if len(first)<limit:first.append([i%w,i//w,e,a])
    if len(expected)!=len(actual):count+=abs(len(expected)-len(actual))
    return dict(mismatch_count=count,first_mismatches=first)


def dib_pixels(info,bits,rows=11,start=0):
    h=struct.unpack_from('<IiiHHIIIIII',info)
    if h[:6]!=(40,37,11,1,4,0):
        raise ValueError('Export must be uncompressed 37x11 4bpp DIB: '+str(h))
    palette=[tuple(reversed(info[40+4*i:43+4*i])) for i in range(16)]
    out=[]
    for row in range(rows):
        for x in range(37):out.append(palette[(bits[row*20+x//2]>>(0 if x&1 else 4))&15])
    return out,palette,h


def expected_cases(phases):
    ids=[]
    if phases&1:ids += [0,1,2]+list(range(10,22))+list(range(30,36))
    if phases&2:ids += list(range(40,96))
    if phases&4:ids += list(range(100,109))
    if phases&8:ids += [110]+list(range(120,125))
    if phases&16:ids += [130,131]
    return ids


def analyze(guest,profile,phases):
    p=PROFILES[profile];w=p['width'];vals,cases=readlog(guest/'MODETEST.LOG')
    assertions=[];results=[];files={};pixels=0;bytes_compared=0
    def check(name,ok,actual=None,expected=None):
        item={'name':name,'pass':bool(ok)}
        if actual is not None:item['actual']=actual
        if expected is not None:item['expected']=expected
        assertions.append(item)
    def read(name):
        path=guest/name;b=path.read_bytes();files[name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
    check('metadata.VERSION',vals.get('VERSION') in ([1],[2]),vals.get('VERSION'),[1,2])
    if vals.get('VERSION')==[2]:
        check('metadata.PALETTE_KIND',vals.get('PALETTE_KIND')==[p.get('palette_kind',0)],vals.get('PALETTE_KIND'),[p.get('palette_kind',0)])
    elif p.get('palette_kind')==1:
        check('metadata.palette_v2_required',False,1,2)
    for k,v in [('PHASES',phases),('HORZRES',w),('VERTRES',200),
                ('BITSPIXEL',1),('PLANES',4),('NUMCOLORS',p['colors']),('BIOS',p['bios']),('COMPLETE',1)]:
        check('metadata.'+k,vals.get(k)==[v],vals.get(k),[v])
    if 'dpi' in p:
        for k,v in zip(['LOGPIXELSX','LOGPIXELSY'],p['dpi']):check(k,vals.get(k)==[v],vals.get(k),[v])
        check('SYSTEM_FONT_HEIGHT',vals.get('SYSTEM_FONT_HEIGHT')==[p['font_height']],vals.get('SYSTEM_FONT_HEIGHT'),[p['font_height']])
        # Five enumerated line styles per real palette color; NUMPENS is not NUMCOLORS.
        check('NUMPENS',vals.get('NUMPENS')==[p['pens']],vals.get('NUMPENS'),[p['pens']])
    check('complete_case_sequence',[c['CASE'] for c in cases]==expected_cases(phases),
          [c['CASE'] for c in cases],expected_cases(phases))
    for k in ['WRONG_DISPLAY','DUMP_ERROR','BRUSH_ERROR','ALIASES_WRONG_PROFILE']:
        check('no.'+k,k not in vals,vals.get(k,[]),[])
    for k in ['CCDC','FULL_DDB','SMALL_DDB','READ_CCDC','READ_CCBM','TEXT_CCDC','TEXT_CCBM',
              'SETDIB_BITMAP','CREATEDIB_BITMAP','CURSOR_LOADED','ALIAS_DCS','ALIAS_BITMAPS']:
        if k in vals:check(k,all(vals[k]),vals[k])
    if phases&1:
        for k,v in [('FULL_WIDTH',w),('FULL_HEIGHT',200),('FULL_STRIDE',w//8),
                    ('FULL_PLANES',4),('FULL_BPP',1),('FULL_BYTES',w//8*4*200)]:
            check(k,vals.get(k)==[v],vals.get(k),[v])
        for indexkey,keys in [('INPUT',['SET','GET','EDGE_SET','EDGE_GET']),
                              ('MEM_INPUT',['MEM_SET','MEM_GET'])]:
            count=16 if p['colors']==16 else 22
            check(indexkey,vals.get(indexkey)==list(range(count)),vals.get(indexkey),list(range(count)))
            expected=[colorref(logical_rgb(i,p)) for i in range(count)]
            for k in keys:check(k,vals.get(k)==expected,vals.get(k),expected)
    textpixels=None;textindices=None
    if phases&8 and (guest/'MDTEXT.BIN').exists():
        textpixels,textindices=ddb_pixels(read('MDTEXT.BIN'),128,32,16,p)
        if 'font_height' in p:check('font.profile_height',vals.get('FONT_HEIGHT')==[p['font_height']],vals.get('FONT_HEIGHT'),[p['font_height']])
        check('text.palette',set(textpixels)=={nearest(BASE[0 if p['colors']==2 else 11],p),nearest(BASE[15],p)},sorted(set(textpixels)))
        check('text.has_glyphs',sum(v!=nearest(BASE[15],p) for v in textpixels)>=20)
        for k,v in [('TEXT_BITS',2048),('MEM_TEXT_RETURN',1),('FONT_HEIGHT',None),('FONT_WIDTH',None)]:
            check(k,vals.get(k)==[v] if v is not None else bool(vals.get(k) and vals[k][0]>0),vals.get(k),v)
    padding=sorted(set(range(p['storage']))-used_bytes(p))
    for c in cases:
        n=c['CASE'];kind=c.get('KIND');r={'case':n,'kind':kind,'pass':False}
        try:
            before=read('MB%03d.BIN'%n);after=read('MD%03d.BIN'%n);actual=decode(after,p)
            expected=None;extra=[]
            if kind==0:expected=strips(p)
            elif kind==1:
                expected=solid(p,15)
                count=16 if p['colors']==16 else 22
                for i,rgb in enumerate((BASE+TIES)[:count]):
                    expected[i]=nearest(rgb,p);expected[199*w+w-count+i]=nearest(rgb,p)
            elif kind==2:expected=strips(p,True)
            elif kind==3:
                expected=solid(p,13);src=[pattern(p,x,y) for y in range(32) for x in range(64)]
                draw_copy(expected,p,c,src,64,32,xor=bool(c['XOR']))
            elif kind==4:
                expected=strips(p,True);draw_copy(expected,p,c,list(expected),w,200)
            elif kind==5:
                expected=solid(p,8)
                if not c['COMPRESSION']:
                    src=[pattern(p,x,y,c['BPP']) for y in range(11) for x in range(37)]
                    draw_copy(expected,p,c,src,37,11,band=True)
                extra += [('input_unchanged',c.get('INPUT_CHANGED')==0),
                          ('return_value',c.get('RETURN',-1)==0 if c['COMPRESSION'] else c.get('RETURN',0)>0)]
            elif kind in (6,7,8):
                expected=solid(p,8)
                for y in range(11):
                    for x in range(37):expected[(189+y)*w+w-37+x]=pattern(p,x,y,c.get('BPP',4))
                if kind==7:extra.append(('setdib_scans',c.get('SETDIB_RETURN')==11))
            elif kind in (11,12):
                expected=solid(p,8)
                for y in range(11):
                    for x in range(37):
                        v=(x+y)&(p['colors']-1) if kind==11 else (0 if p['colors']==2 else 3) if x in (0,36) or y in (0,10) else 1
                        expected[(189+y)*w+w-37+x]=v
            elif kind==9:
                if textpixels is None:raise ValueError('Missing memory text reference')
                expected=solid(p,0)
                for y in range(32):
                    for x in range(128):
                        expected[(40+y)*w+x]=textpixels[y*128+x]
                        expected[(100+y)*w+w-128+x]=textpixels[y*128+x]
                extra += [('text_blt',c.get('TEXT_BLT')==1),('textout',c.get('SCREEN_TEXT_RETURN')==1)]
            elif kind==10:
                expected=strips(p,True);visible=read('MV%03d.BIN'%n);vp=decode(visible,p)
                changed=[i for i,(a,b) in enumerate(zip(actual,vp)) if a!=b]
                cx=max(0,min(w-1,c['CURSOR_REQ_X']));cy=max(0,min(199,c['CURSOR_REQ_Y']))
                extra += [('cursor_position',(c['CURSOR_X'],c['CURSOR_Y'])==(cx,cy)),
                          ('cursor_visible',bool(changed) if (cx,cy)!=(w-1,199) else vp==expected[:-1]+[0]),('cursor_restore',before==after),
                          ('cursor_locality',all(cx<=i%w<cx+32 and cy<=i//w<cy+32 for i in changed))]
                r['visible_changed_pixels']=len(changed)
                if (cx,cy)==(w-1,199):r['clipped_arrow_tip_expected_index']=0
            else:raise ValueError('Unknown case kind '+str(kind))
            pixels+=w*200;bytes_compared+=p['storage']
            r.update(differences(expected,actual,w));r['pixels_compared']=w*200
            padbad=[i for i in padding if before[i]!=after[i]]
            r['padding_bytes_compared']=len(padding);r['padding_mismatches']=padbad[:16]
            r['padding_mismatch_count']=len(padbad)
            if kind in (2,3,4,6,7,8,11,12):extra.append(('return_value',c.get('RETURN',0)>0))
            extra.append(('case_completed',c.get('ENDCASE')==n))
            r['checks']={k:bool(v) for k,v in extra}
            r['pass']=r['mismatch_count']==0 and not padbad and all(v for k,v in extra)
        except (OSError,ValueError,KeyError,IndexError) as e:r['error']=str(e)
        results.append(r)
    if phases&4:
        try:
            db=read('MDBITS.BIN');dbpixels,dbindices=ddb_pixels(db,37,11,6,p)
            wanted=[pattern(p,x,y) for y in range(11) for x in range(37)]
            check('DDB.full_pixel_readback',dbpixels==wanted,differences(wanted,dbpixels,37))
            if p['colors'] in (2,4):
                canonical=[0,15] if p['colors']==2 else [0,5,10,15]
                check('DDB.canonical_indices',all(a==canonical[b] for a,b in zip(dbindices,wanted)))
            check('DDB.guard',db[264:]==bytes([0xa5])*(4096-264))
            check('READ_BITS',vals.get('READ_BITS')==[264],vals.get('READ_BITS'),[264])
            check('READ_STRIDE',vals.get('READ_STRIDE')==[6],vals.get('READ_STRIDE'),[6])
            for name,bitsfile,infofile,rows,start in [('export','MDEXPORT.BIN','MDINFO.BIN',11,0),
                                                   ('partial','MDPART.BIN','MDPINFO.BIN',5,3)]:
                b=read(bitsfile);ip=read(infofile);got,palette,h=dib_pixels(ip,b,rows,start)
                expected=[logical_rgb((x*3+(10-start-row)*5)&15,p) for row in range(rows) for x in range(37)]
                check(name+'.RGB_pixels',got==expected,differences(expected,got,37))
                check(name+'.guard',b[rows*20:]==bytes([0xa5])*(4096-rows*20))
            for k,v in [('EXPORT_RETURN',11),('PARTIAL_RETURN',5),('QUERY_PLANES',1)]:
                check(k,vals.get(k)==[v],vals.get(k),[v])
            if vals.get('QUERY_RETURN')==[0]:
                check('query.unsupported_unchanged',vals.get('QUERY_BPP')==[0] and vals.get('QUERY_SIZE')==[0])
            else:
                check('query.supported_header',bool(vals.get('QUERY_RETURN') and vals['QUERY_RETURN'][0]>0) and vals.get('QUERY_BPP')==[4] and vals.get('QUERY_SIZE')==[220])
            check('READ_INPUT_CHANGED',vals.get('READ_INPUT_CHANGED')==[0,0,0,0],vals.get('READ_INPUT_CHANGED'))
        except (OSError,ValueError,IndexError) as e:check('readback.files',False,str(e))
    if phases&16:
        check('aliases.reduced_color_profile',p['colors'] in (2,4),p['colors'],[2,4])
        mask=p['colors']-1; alias_palette=p['palette']; bg_count=p['colors']
        for k,v in [('ALIAS_SETBITS',264),('ALIAS_GETBITS',264),('FLOOD_SETBITS',264),
                    ('FLOOD_RETURN',1),('FLOOD_GETBITS',264)]:
            check(k,vals.get(k)==[v],vals.get(k),[v])
        check('ALIAS_INDEX',vals.get('ALIAS_INDEX')==list(range(16)),vals.get('ALIAS_INDEX'))
        wanted=[colorref(alias_palette[i&mask]) for i in range(16)]
        check('ALIAS_GETPIXEL',vals.get('ALIAS_GETPIXEL')==wanted,vals.get('ALIAS_GETPIXEL'),wanted)
        for k,v in [('ALIAS_EXPORT_BPP',[1,4,8,24]),('ALIAS_EXPORT_RETURN',[11]*4),
                    ('ALIAS_MONO_BG',list(range(bg_count))),('ALIAS_MONO_RETURN',[1]*bg_count),('ALIAS_MONO_GETBITS',[66]*bg_count)]:
            check(k,vals.get(k)==v,vals.get(k),v)
        try:
            b=read('MALIAS.BIN');pix,indices=ddb_pixels(b,37,11,6,p)
            wanted=[(x+y)&15 for y in range(11) for x in range(37)]
            check('aliases.raw_indices_preserved',indices==wanted,differences(wanted,indices,37))
            check('aliases.raw_guard',b[264:]==bytes([0xa5])*(4096-264))
            expected_raw=bytearray(264)
            for y in range(11):
                for x in range(37):
                    for plane in range(4):
                        if ((x+y)&15)&(1<<plane):expected_raw[y*24+plane*6+x//8]|=128>>(x%8)
            check('aliases.raw_all_bytes',b[:264]==bytes(expected_raw))
            for bpp in [1,4,8,24]:
                b=read('MAE%d.BIN'%bpp);inf=read('MAI%d.BIN'%bpp)
                h=struct.unpack_from('<IiiHHIIIIII',inf)
                check('aliases.export%d.header'%bpp,h[:6]==(40,37,11,1,bpp,0),list(h[:6]))
                palette=[tuple(reversed(inf[40+4*i:43+4*i])) for i in range(256)]
                stride=((37*bpp+31)//32)*4;actual=[];wanted=[]
                for y in range(11):
                    for x in range(37):
                        off=(10-y)*stride;i=(x+y)&mask
                        if bpp==24:rgb=tuple(reversed(b[off+x*3:off+x*3+3]))
                        elif bpp==8:rgb=palette[b[off+x]]
                        elif bpp==4:rgb=palette[(b[off+x//2]>>(0 if x&1 else 4))&15]
                        else:rgb=palette[(b[off+x//8]>>(7-x%8))&1]
                        actual.append(rgb)
                        if bpp==1:
                            color=alias_palette[i]
                            wanted.append((255,255,255) if sum((v-255)**2 for v in color)<sum(v*v for v in color) else (0,0,0))
                        else:wanted.append(alias_palette[i])
                check('aliases.export%d.pixels'%bpp,actual==wanted,differences(wanted,actual,37))
                check('aliases.export%d.guard'%bpp,b[stride*11:]==bytes([0xa5])*(4096-stride*11))
            for bg in range(bg_count):
                b=read('MAM%d.BIN'%bg)
                actual=[(b[y*6+x//8]>>(7-x%8))&1 for y in range(11) for x in range(37)]
                wanted=[int(((x+y)&mask)==bg) for y in range(11) for x in range(37)]
                check('aliases.mono_bg%d.pixels'%bg,actual==wanted,differences(wanted,actual,37))
                check('aliases.mono_bg%d.guard'%bg,b[66:]==bytes([0xa5])*(4096-66))
            b=read('MAFLOOD.BIN');actual,indices=ddb_pixels(b,37,11,6,p)
            wanted=[(0 if p['colors']==2 else 3) if x in (0,36) or y in (0,10) else 1 for y in range(11) for x in range(37)]
            check('aliases.floodfill.pixels',actual==wanted,differences(wanted,actual,37))
            wanted_indices=[(((x+y)&7)<<1) if x in (0,36) or y in (0,10) else 15 for y in range(11) for x in range(37)] if p['colors']==2 else [3+(((x+y)&3)<<2) if x in (0,36) or y in (0,10) else 5 for y in range(11) for x in range(37)]
            check('aliases.floodfill.canonical_interior',indices==wanted_indices,differences(wanted_indices,indices,37))
        except (OSError,ValueError,IndexError) as e:check('aliases.files',False,str(e))
    driver_names={10:'TNDY6404.DRV',9:'TANDY88.DRV',8:'TNDY160.DRV',4:'TNDY3204.DRV',6:'TNDY6402.DRV'}
    for f in [guest/'WINDOWS/MODETEST.EXE',guest/'WINDOWS/SYSTEM'/driver_names.get(p['bios'],'TANDY.DRV')]:
        if f.exists():files[str(f.relative_to(guest))]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
    return {'profile':profile,'guest':str(guest),'phase_mask':phases,'profile_contract':p,
            'complete':vals.get('COMPLETE')==[1],'case_count':len(results),
            'getdibits_null_buffer_query_supported':bool(vals.get('QUERY_RETURN',[0])[0]),
            'pixels_compared':pixels,'physical_bytes_checked':bytes_compared,
            'assertions':assertions,'results':results,'files':files,
            'limits':['Text shape uses memory-DDB reference, not an independent font parser',
                      'Raw VRAM does not verify hardware palette register RGB values',
                      'Future profiles have codec support, not a driver acceptance claim',
                      'No physical Tandy hardware validation'],
            'pass':all(a['pass'] for a in assertions) and all(r['pass'] for r in results)}


def selftest():
    # Golden examples plus an independent arithmetic write loop detect wrong
    # bank, pair, bit order, end-column/end-row and future-codec regressions.
    for name,p in PROFILES.items():
        raw=bytearray([0xa5]*32768);w=p['width'];wanted=[]
        for y in range(200):
            for x in range(w):
                value=(x*3+y*5)&(p['colors']-1);wanted.append(value)
                row=(y%p['banks'])*8192+(y//p['banks'])*p['pitch']
                if p['bios']==10:
                    a=row+((x&~7)//4);mask=128>>(x&7)
                    raw[a]=(raw[a]&~mask)|(mask if value&1 else 0)
                    raw[a+1]=(raw[a+1]&~mask)|(mask if value&2 else 0)
                else:
                    bpp={2:1,4:2,16:4}[p['colors']];bit=x*bpp
                    a=row+bit//8;shift=8-bpp-bit%8;mask=(p['colors']-1)<<shift
                    raw[a]=(raw[a]&~mask)|(value<<shift)
        assert decode(raw,p)==wanted,name
        assert len(used_bytes(p))==p['pitch']*200
        assert all(raw[a]==0xa5 for a in set(range(p['storage']))-used_bytes(p))
    p=PROFILES['640x200x4-cga'];raw=bytearray(32768)
    raw[0]=0x80;raw[1]=0x40;raw[2]=0x80;raw[3]=0x80
    raw[32574]=1;raw[32575]=1
    got=decode(raw,p)
    assert got[0:2]==[1,2] and got[8]==3 and got[-1]==3
    assert [nearest(c,p) for c in BASE]==[0,0,0,1,0,2,0,3,0,0,0,1,0,2,3,3]
    assert [nearest(c,p) for c in TIES]==[0,0,1,3,2,3]
    rg=PROFILES['640x200x4'];bw=PROFILES['640x200x2']
    assert [nearest(c,rg) for c in BASE]==[0,0,2,2,1,1,1,3,0,0,2,2,1,1,1,3]
    assert [nearest(c,rg) for c in TIES]==[0,2,3,3,1,1]
    assert [nearest(c,bw) for c in BASE]==[0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,1]
    assert [nearest(c,bw) for c in REDGREEN]==[0,0,0,1]
    aliasraw=bytes([0x55,0x55,0x33,0x33,0x0f,0x0f,0x00,0xff])
    mono,indices=ddb_pixels(aliasraw,16,1,2,bw)
    assert indices==list(range(16)) and mono==[i&1 for i in range(16)]
    assert expected_cases(15)==[0,1,2]+list(range(10,22))+list(range(30,36))+list(range(40,96))+list(range(100,109))+[110]+list(range(120,125))
    print(json.dumps({'selftest':'PASS','profiles':list(PROFILES),'640x200x4_pixels':128000,
                      'cases_in_complete_run':len(expected_cases(31))},indent=2))


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('guest',type=Path,nargs='?');ap.add_argument('--profile',choices=PROFILES,default='640x200x4')
    ap.add_argument('--phases',type=int,default=31);ap.add_argument('--out',type=Path)
    ap.add_argument('--selftest',action='store_true');a=ap.parse_args()
    if a.selftest:selftest();return 0
    if a.guest is None:ap.error('guest directory is required unless --selftest is used')
    if not 0<a.phases<32:ap.error('--phases must be a bit mask from 1 through 31')
    try:report=analyze(a.guest,a.profile,a.phases)
    except (OSError,ValueError) as e:report={'pass':False,'error':str(e),'profile':a.profile,'guest':str(a.guest)}
    out=a.out or a.guest/'MODECHK.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'pass':report['pass'],'report':str(out),'cases':report.get('case_count'),
                      'pixels_compared':report.get('pixels_compared'),
                      'failed_assertions':[x for x in report.get('assertions',[]) if not x['pass']],
                      'failed_cases':[x for x in report.get('results',[]) if not x['pass']],
                      'error':report.get('error')},indent=2))
    return int(not report['pass'])


if __name__=='__main__':raise SystemExit(main())
