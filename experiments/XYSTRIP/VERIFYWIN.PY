"""Independently compare Windows shadow and real cursor VRAM snapshots."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT.parent/'tandy-pan-integration'
def pixel(s,x,y):
    bit=128>>(x&7);off=y*320+x//8
    return sum(w for p,w in enumerate((4,2,1,8)) if s[off+p*80]&bit)
def verify(name,tag=''):
    out=OUT/('windows-'+name+tag);log=(out/'PANQA.LOG').read_text()
    shadows={i:(out/('S%03d.BIN'%i)).read_bytes() for i in (0,1)}
    assert all(len(s)==81920 for s in shadows.values())
    rows=[];total=cursor_pixels=0
    for line in log.splitlines():
        if not line.startswith('FRAME '):continue
        d={k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
        raw=(out/('V%03d.BIN'%d['id'])).read_bytes();assert len(raw)==32768
        shadow=shadows[d['shadow']];bad=[];cursor_changed=0
        for vy in range(200):
            y=d['y']+vy
            for vx in range(0,320,2):
                expected=0
                for q in range(2):
                    x=d['x']+vx+q;c=pixel(shadow,x,y)
                    if d['cursor'] and 0<=x-d['cx']<8 and 0<=y-d['cy']<8:
                        c=15 if x-d['cx']==y-d['cy'] else 0
                        cursor_changed+=1
                    expected=expected*16+c
                address=(vy&3)*8192+((vy//4*160+d['head']*2+vx//2)&8191)
                if raw[address]!=expected and len(bad)<8:bad.append([vx,vy,address,raw[address],expected])
        rows.append(dict(frame=d['id'],cursor=d['cursor'],cursor_pixels=cursor_changed,
                         result='PASS' if not bad else 'FAIL',first_mismatches=bad))
        total+=32000;cursor_pixels+=cursor_changed
    moves=[{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
           for line in log.splitlines() if line.startswith('MOVE ')]
    memory=[dict(label=m[1],free=int(m[2]),largest=int(m[3]))
            for m in re.finditer(r'MEM (\w+) free=(\d+) largest=(\d+)',log)]
    # Check controlled GDI interiors, away from text and diagonal strokes.
    semantic=[('black',20,100,0),('red',100,100,4),('green',500,220,2),
              ('bright_blue_after_draw',50,70,9)]
    checks=[]
    for label,x,y,want in semantic:
        s=shadows[1] if label=='bright_blue_after_draw' else shadows[0]
        actual=pixel(s,x,y);checks.append(dict(label=label,x=x,y=y,expected=want,actual=actual,pass_=actual==want))
    result=dict(status='PASS' if all(r['result']=='PASS' for r in rows) and all(r['pass_'] for r in checks) else 'FAIL',
        frames=len(rows),compared_bytes=total,visible_cursor_pixels_checked=cursor_pixels,
        frame_results=rows,gdi_checks=checks,moves=moves,memory=memory,
        normal_dos_return=json.loads((out/'RESULT.JSN').read_text())['normal_dos_return'],
        scope='Actual Windows driver/cursor/GDI VRAM equivalence, not physical EX scanout')
    (out/'VERIFIED.JSN').write_text(json.dumps(result,indent=2)+'\n')
    print(name,result['status'],'frames',len(rows),'bytes',total,'GDI',checks,
          'failed_frames',[r for r in rows if r['result']!='PASS'][:3],flush=True)
    return result
if __name__=='__main__':verify(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '')
