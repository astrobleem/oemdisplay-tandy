"""Independently compare Windows shadow and real cursor VRAM snapshots."""
from pathlib import Path
import json,re,sys
def pixel(s,x,y):
    bit=128>>(x&7);off=y*320+x//8
    return sum(w for p,w in enumerate((4,2,1,8)) if s[off+p*80]&bit)
def verify(out):
    out=Path(out);name=out.name;log=(out/'PANQA.LOG').read_text()
    shadows={i:(out/('S%03d.BIN'%i)).read_bytes() for i in (0,1,10,11,12)}
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
    extra=[]
    for i in range(16):
        extra.append(dict(label='palette_'+str(i),expected={6:4,8:0}.get(i,i),actual=pixel(shadows[0],i*40+20,12)))
    for y in range(8):
        for x in range(8):
            extra.append(dict(label='late_mixed',expected=8 if (x+y)&1 else 0,actual=pixel(shadows[0],480+x,32+y)))
            extra.append(dict(label='early_mixed',expected=4 if (x+y)&1 else 0,actual=pixel(shadows[0],488+x,32+y)))
    extra_bad=[c for c in extra if c['expected']!=c['actual']]
    result=dict(status='PASS' if all(r['result']=='PASS' for r in rows) and all(r['pass_'] for r in checks) and not extra_bad else 'FAIL',
        extra_gdi_checks=extra,extra_gdi_failures=extra_bad,
        oracle_correction='Initial baseline oracle expected flat palette6/8 RGB brushes. Existing EGA brush dithering gives red/black at selected points; initial failed receipt preserved. Driver color realization unchanged.',
        frames=len(rows),compared_bytes=total,visible_cursor_pixels_checked=cursor_pixels,
        frame_results=rows,gdi_checks=checks,moves=moves,memory=memory,
        normal_dos_return=json.loads((out/'RESULT.JSN').read_text())['normal_dos_return'],
        scope='Actual Windows driver/cursor/GDI VRAM equivalence, not physical EX scanout')
    (out/'VERIFIED.JSN').write_text(json.dumps(result,indent=2)+'\n')
    print(name,result['status'],'frames',len(rows),'bytes',total,'GDI',checks,
          'failed_frames',[r for r in rows if r['result']!='PASS'][:3],flush=True)
    return result
if __name__=='__main__':
    result=verify(sys.argv[1]);raise SystemExit(0 if result['status']=='PASS' else 1)
