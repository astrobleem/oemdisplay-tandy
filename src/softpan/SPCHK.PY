"""Independent full-frame oracle for SPTEST's raw PCjr/ColorPlus video dumps.

Text shape is compared to the separately rendered memory bitmap. Other
drawing geometry, colors, scroll and cursor composition are modeled here.
"""
from pathlib import Path
import argparse
import importlib.machinery
import json
import hashlib

HERE = Path(__file__).resolve().parent
IRGB = [0, 4, 2, 6, 1, 5, 3, 7, 8, 12, 10, 14, 9, 13, 11, 15]
PAL = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
       (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]


def decode(raw, adapter='pcjr'):
    if len(raw) != 32768:
        raise ValueError('video dump must be exactly 32768 bytes')
    if adapter == 'pcjr':
        return [((raw[(y%4)*8192+(y//4)*160+x//2] >> (4 if x%2==0 else 0)) & 15)
                for y in range(200) for x in range(320)]
    # ColorPlus stores R,G in plane 0; B,I in plane 1, each CGA even/odd.
    out=[]
    for y in range(200):
        for x in range(320):
            at=(y%2)*8192+(y//2)*80+x//4
            shift=6-2*(x%4)
            a=(raw[at]>>shift)&3; b=(raw[at+16384]>>shift)&3
            out.append(((a&2)<<1)|((a&1)<<1)|((b&2)>>1)|((b&1)<<3))
    return out


def ddb(raw):
    return [sum(((raw[y*64+p*16+x//8]>>(7-x%8))&1)<<b
                for p,b in enumerate((2,1,0,3))) for y in range(32) for x in range(128)]


def fill(p, l,t,r,b,c):
    for y in range(max(0,t),min(400,b)):
        for x in range(max(0,l),min(320,r)):
            p[y*320+x]=IRGB[c]


def fixtures(p,text):
    p=p.copy()
    fill(p,17,95,83,108,9)
    fill(p,40,102,100,205,12)
    for top in (94,294):
        for y in range(32):
            p[(top+y)*320+150:(top+y)*320+278]=text[y*128:(y+1)*128]
        for y in range(16):
            for x in range(32):
                p[(top+y)*320+5+x]=IRGB[(x//4+3*(y//4))&15]
    for top in (193,393):
        for y in range(min(11,400-top)):
            for x in range(37):
                p[(top+y)*320+270+x]=IRGB[(x+3*y)&15]
    fill(p,0,200,320,201,15)
    old=p.copy()
    for y in range(60):
        p[(220+y)*320+100:(220+y)*320+196]=old[(180+y)*320:(180+y)*320+96]
    return p


def parse(log):
    vals={}; shots=[]; current=None
    for row in log.splitlines():
        k,sep,v=row.partition('=')
        if not sep:
            continue
        v=int(v); vals.setdefault(k,[]).append(v)
        if k=='SHOT':
            current={'SHOT':v}; shots.append(current)
        elif k in ('TOP','X','Y','VISIBLE') and current is not None:
            current[k]=v
    return vals,shots


def check(guest, driver, adapter='pcjr', write_images=True):
    vals,shots=parse((guest/'SPTEST.LOG').read_text())
    pan=importlib.machinery.SourceFileLoader('sp_arrow',str(HERE.parent/'xtpan/PANCHK.PY')).load_module()
    hx,hy,glyph=pan.arrow(driver.read_bytes())
    text=ddb((guest/'TEXT.BIN').read_bytes())
    plain=[IRGB[12+((y>>7)&3) if x>=288 else ((y>>3)+(x>>5))&15]
           for y in range(400) for x in range(320)]
    drawn=fixtures(plain,text)
    scrolled=drawn[17*320:]+[IRGB[6]]*(17*320)
    retained=scrolled.copy();fill(retained,75,196,110,210,10)
    wanted_tops=[0,1,99,100,199,200,0,200,200,100,0,200,200,0,100]+[100]*12+[100,199,200,200,0]
    assertions={
        'complete':vals.get('COMPLETE')==[1],
        'no_failed_calls':'FAILED' not in vals and 'WRONG_DISPLAY' not in vals,
        'geometry':vals.get('HORZRES')==[320] and vals.get('VERTRES')==[400] and vals.get('NUMCOLORS')==[16],
        'initial_top':vals.get('START_TOP')==[0],
        'video_segment':vals.get('VIDEO_SEG')==[0x1800 if adapter=='pcjr' else 0xb800],
        'pan_sequence':[s.get('TOP') for s in shots]==wanted_tops,
        'frame_sequence':[s['SHOT'] for s in shots]==list(range(32)),
        'text_reference':set(text)=={IRGB[11],IRGB[15]} and text.count(IRGB[11])>=20,
        'text_bytes':vals.get('TEXT_BYTES')==[2048],
        'dib_scans':vals.get('DIB_MIDDLE')==[11] and vals.get('DIB_LOGICAL_EDGE')==[7],
        'cursor_show_counts':vals.get('CURSOR_SHOW')==[0]*6 and vals.get('CURSOR_HIDE')==[-1]*6,
        'stable_pan_memory':vals.get('FREE_BEFORE_PANS')==vals.get('FREE_AFTER'),
        'helper_and_config':all(vals.get(k)==[1] for k in ('CONFIG_LAUNCH','CONFIG_PRESERVED','HELPER_RUNNING',
                               'HELPER_DOWN','HELPER_UP','CONFIG_OFF_LAUNCH','CONFIG_REMOVED','HELPER_STOPPED')),
    }
    for key in ('CONFIG_REENABLED', 'HELPER_RESET_SYNC'):
        if key in vals:
            assertions[key.lower()] = vals[key] == [1]
    active={((y%4)*8192+(y//4)*160+x) if adapter=='pcjr' else
            ((y%2)*8192+(y//2)*80+x)+plane*16384
            for y in range(200) for x in range(160 if adapter=='pcjr' else 80)
            for plane in range(1 if adapter=='pcjr' else 2)}
    padding=set(range(32768))-active
    initial=(guest/'SP000.BIN').read_bytes()
    results=[]
    for s in shots:
        n=s['SHOT'];raw=(guest/('SP%03d.BIN'%n)).read_bytes();got=decode(raw,adapter)
        surface=plain if n<9 else drawn if n<12 else scrolled if n<27 else retained
        top=s['TOP'];want=surface[top*320:(top+200)*320].copy()
        if s['VISIBLE']:
            for dx,dy,a,xr in glyph:
                x,y=s['X']-hx+dx,s['Y']-top-hy+dy
                if 0<=x<320 and 0<=y<200:
                    i=y*320+x;want[i]=(want[i] if a else 0)^(15 if xr else 0)
        bad=[i for i,(a,b) in enumerate(zip(got,want)) if a!=b]
        pad=[i for i in padding if raw[i]!=initial[i]]
        results.append({'frame':n,'top':top,'cursor_visible':s['VISIBLE'],
                        'mismatches':len(bad),'padding_mismatches':len(pad),
                        'first':[[i%320,i//320,got[i],want[i]] for i in bad[:8]],
                        'pass':not bad and not pad})
        if write_images and n in (0,9,12,27,29):
            from PIL import Image
            im=Image.new('P',(320,200));im.putpalette([v for c in PAL for v in c]+[0]*(768-48))
            im.putdata(got);im.resize((640,400),Image.Resampling.NEAREST).save(guest/('FRAME%03d.PNG'%n))
    return {'pass':all(assertions.values()) and all(r['pass'] for r in results),
            'driver_sha256':hashlib.sha256(driver.read_bytes()).hexdigest(),
            'adapter':adapter,'assertions':assertions,'frames':len(results),'pixels_compared':len(results)*64000,
            'padding_bytes_per_frame':len(padding),'results':results,
            'free_start':vals.get('FREE_START'),'free_after':vals.get('FREE_AFTER'),'free_delta':vals.get('FREE_DELTA'),
            'free_clean':vals.get('FREE_CLEAN'),
            'limits':['raw VRAM screenshots are decoded captures, not host window grabs',
                      'text glyph uses separately rendered memory bitmap reference',
                      'no physical hardware qualification or performance claim']}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('guest',type=Path);ap.add_argument('--driver',type=Path,required=True)
    ap.add_argument('--adapter',choices=('pcjr','colorplus'),default='pcjr')
    a=ap.parse_args();r=check(a.guest,a.driver,a.adapter)
    (a.guest/'SPCHK.JSON').write_bytes((json.dumps(r,indent=2)+'\r\n').encode())
    print(json.dumps({k:v for k,v in r.items() if k!='results'},indent=2))
    print(json.dumps([x for x in r['results'] if not x['pass']],indent=2))
    return int(not r['pass'])


if __name__=='__main__':
    raise SystemExit(main())
