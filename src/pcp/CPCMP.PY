#!/usr/bin/env python3
"""Compare complete CPBENCH runs, including every32768-byte ColorPlus capture."""
from pathlib import Path
import argparse,importlib.machinery,json,sys
RR=importlib.machinery.SourceFileLoader('cp_rrcmp',str(Path(__file__).resolve().parent.parent/'rrect/RRCMP.PY')).load_module()
NAMES=RR.BATCHES+('full_width','scan_full','scan_narrow','cursor_overlap','visible_steps','marker_steps','polylines')+RR.APPS

def pixels(raw):
    if len(raw)!=32768:raise ValueError('ColorPlus frame must contain 32768 bytes')
    out=bytearray(64000)
    for y in range(200):
        at=(y&1)*8192+(y//2)*80
        for x in range(320):
            shift=6-2*(x&3);a=(raw[at+x//4]>>shift)&3;b=(raw[at+16384+x//4]>>shift)&3
            out[y*320+x]=((a&2)<<1)|((a&1)<<1)|((b&2)>>1)|((b&1)<<3)
    return out

def validate(directory):
    log=(directory/'RRBENCH.LOG').read_text()
    head,rows=RR.parse(log);bad=[]
    def number(d,key):
        v=d.get(key,[])
        if len(v)!=1 or not v[0].isdigit():
            bad.append('missing/nonnegative integer '+key);return None
        return int(v[0])
    multiplier=number(head,'MULTIPLIER')
    if multiplier not in range(1,10):bad.append('invalid multiplier')
    free=number(head,'FREE_BEFORE_PROBE')
    if free is None or free<=0:bad.append('invalid free-memory observation')
    if not log.rstrip().endswith('COMPLETE=1') or log.count('COMPLETE=')!=1:bad.append('incomplete log')
    for key,val in [('VERSION','9'),('COLORPLUS_PLANES','2'),('SCREEN_WIDTH','320'),('SCREEN_HEIGHT','200'),('LOGICAL_WIDTH','320'),('LOGICAL_HEIGHT','200'),('NUMCOLORS','16'),('REAL_MODE','1'),('SHOTS','0')]:
        if head.get(key)!=[val]:bad.append('invalid header '+key)
    if tuple(r.get('NAME',['?'])[0] for r in rows)!=NAMES:bad.append('wrong stage sequence')
    if [r.get('STAGE') for r in rows]!=[[str(i+1)] for i in range(len(NAMES))]:bad.append('wrong stage numbers')
    captures={}
    clears=head.get('CLEAR_SUCCESS',[])+[v for r in rows for v in r.get('CLEAR_SUCCESS',[])]
    if len(clears)<len(NAMES) or any(v!='1' for v in clears):bad.append('missing/failed clear')
    for r in rows:
        name=r.get('NAME',['?'])[0];n=int(r['STAGE'][0])
        if 'KIND' in r:
            count=number(r,'COUNT');api=number(r,'API_SUCCESSES');elapsed=number(r,'ELAPSED_MS')
            expected={'roundrect_large':6,'ellipse_12':4,'scan_full':20000,'scan_narrow':20000,'visible_steps':17,'marker_steps':9,'polylines':3}.get(name,20)
            if name not in ('visible_steps','marker_steps','polylines'):expected*=multiplier or 0
            if count is None or count<=0 or count!=expected:bad.append(name+': call count')
            if name in ('scan_full','scan_narrow'):
                # The inherited SCANLINE renderer leaves scratch AX on exit.
                # Aligned black scans return zero; this is a raw nonzero-
                # return count, compared exactly between drivers below.
                if api is None or count is None or not 0<=api<=count:bad.append(name+': raw return count')
                if r.get('RAW_OUTPUT_FOUND')!=['1']:bad.append(name+': raw Output missing')
                if elapsed is None or elapsed<=0:bad.append(name+': missing measurable raw timing')
            elif api!=count:bad.append(name+': GDI API count')
        else:
            number(r,'LAUNCH_TO_PAINTED_MS')
            if r.get('APP_FOUND')!=['1'] or len(r.get('TITLE',[]))!=1 or not r['TITLE'][0] or len(r.get('REPAINT_MS',[]))!=3 or not all(v.isdigit() for v in r['REPAINT_MS']):bad.append(name+': app incomplete')
        made,size=r.get('DUMP_CREATED',[]),r.get('DUMP_BYTES',[])
        if made!=['1']*(2 if name=='cursor_overlap' else 1) or len(made)!=len(size) or any(v!='32768' for v in size):bad.append(name+': capture incomplete')
        captures['RB%02d.BIN'%n]=None
        steps={'visible_steps':17,'marker_steps':9,'polylines':3}.get(name,0)
        if steps:
            if r.get('COUNT')!=[str(steps)] or r.get('STEP_DUMPS')!=[str(steps)] or r.get('STEP_DUMP_CREATED')!=['1']*steps or r.get('STEP_DUMP_BYTES')!=['32768']*steps:bad.append(name+': per-call capture incomplete')
            prefix={'visible_steps':'RV','marker_steps':'RM','polylines':'RP'}[name]
            captures.update({prefix+'%02d.BIN'%k:None for k in range(1,steps+1)})
        if r.get('BANK_STATE')!=['15']*(len(made)+steps):bad.append(name+': ColorPlus bank calibration failed')
        if r.get('CAPTURE_BANKS')!=['15']*(len(made)+steps):bad.append(name+': capture did not copy four distinct banks')
        if name=='marker_steps':
            for key in ['FIRST_ROW_ON_RETURN','SECOND_ROW_ON_RETURN','ROWS_VISIBLE_BEFORE_SETTLE']:
                if r.get(key)!=['1']*9:bad.append(name+': '+key)
            for key in ['IDLE_VRAM_NOW','IDLE_VRAM_LATER']:
                if r.get(key)!=['1']:bad.append(name+': '+key)
            if int(r.get('IDLE_BIOS_TICKS',['0'])[0])<9:bad.append('idle observation too short')
        if name=='polylines' and r.get('POLY_VISIBLE_ON_RETURN')!=['1']*3:bad.append('polyline visibility')
        if name in ('scan_full','scan_narrow') and r.get('SCAN_VISIBLE_ON_RETURN')!=['1']:bad.append(name+': scan visibility')
        if name in ('marker_steps','polylines') and r.get('RAW_OUTPUT_FOUND')!=['1']:bad.append('raw Output missing')
    for name in captures:
        p=directory/name
        if not p.is_file() or p.stat().st_size!=32768:bad.append('missing/truncated '+name)
        else:
            captures[name]=p.read_bytes()
            if any(captures[name][bank*8192+8000]!=(1<<bank) for bank in range(4)):
                bad.append('missing/aliased bank calibration '+name)
    # A separate expected image catches equally wrong captures/drivers.
    for k in range(1,10):
        raw=captures.get('RM%02d.BIN'%k)
        if raw is None:continue
        want=bytearray([15])*64000
        for y in range(144,147 if k==7 else 146):
            for x in range(4,45):want[y*320+x]=0
        if k==3:want[144*320+100]=0
        if pixels(raw)!=want:bad.append('marker pixel oracle %d'%k)
    for name,left,right in [('scan_full',0,320),('scan_narrow',144,160)]:
        raw=captures.get('RB%02d.BIN'%(NAMES.index(name)+1))
        if raw is None:continue
        want=bytearray([15])*64000
        for y in range(100,120):want[y*320+left:y*320+right]=bytes(right-left)
        if pixels(raw)!=want:bad.append(name+': independent scan pixel oracle')
    try:summary=RR.stages(log)
    except ValueError:
        summary={};bad.append('malformed stage summary')
    return head,summary,captures,bad

def compare(a,b):
    ha,sa,ca,ba=validate(a);hb,sb,cb,bb=validate(b)
    problems={'baseline':ba,'candidate':bb}
    if {k:v for k,v in ha.items() if k!='FREE_BEFORE_PROBE'}!={k:v for k,v in hb.items() if k!='FREE_BEFORE_PROBE'}:problems['setup']=['headers differ']
    frames=[]
    for name in sorted(set(ca)|set(cb)):
        x,y=ca.get(name),cb.get(name)
        equal=x is not None and x==y
        frames.append({'file':name,'equal':equal,'differing_pixels':0 if equal else (sum(i!=j for i,j in zip(pixels(x),pixels(y))) if x is not None and y is not None else None)})
    times=[]
    for i in sorted(set(sa)|set(sb)):
        x,y=sa.get(i,{}),sb.get(i,{})
        times.append({'stage':x.get('name'),'baseline_ms':x.get('elapsed_ms',x.get('repaint_ms')),'candidate_ms':y.get('elapsed_ms',y.get('repaint_ms'))})
        for key in ['name','count','api_successes','app_found','title','step_dumps']:
            if x.get(key)!=y.get(key):problems.setdefault('metadata',[]).append(str(i)+' '+key)
    ok=not any(problems.values()) and all(f['equal'] for f in frames)
    return {'pass':ok,'problems':problems,'frames':frames,'timings':times,'frame_bytes':32768,'pixels_per_frame':64000,'free_before_probe':{'baseline':ha.get('FREE_BEFORE_PROBE'),'candidate':hb.get('FREE_BEFORE_PROBE')}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    r=compare(a.baseline,a.candidate);a.json.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 0 if r['pass'] else 1

if __name__=='__main__':sys.exit(main())
