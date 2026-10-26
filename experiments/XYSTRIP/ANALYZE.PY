"""Summarize receipts and model bounded target walks; no native execution."""
from pathlib import Path
import collections, csv, hashlib, json, re, subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def cost(dx,dy):return 100*dx+160*dy-dx*dy//2
def walk(budget,tx,ty,legacy=False):
    best={(0,0):(0,0,[])}
    moves=[(x,y) for x in range(0,min(tx,48)+1,8) for y in range(0,min(ty,32)+1,4)
           if (x or y) and cost(x,y)<=budget and (not legacy or (x<=8 and y<=4))]
    for y in range(0,ty+1,4):
        for x in range(0,tx+1,8):
            if (x,y)==(0,0):continue
            choices=[]
            for dx,dy in moves:
                if (x-dx,y-dy) in best:
                    n,b,p=best[x-dx,y-dy]
                    choices.append((n+1,b+cost(dx,dy),p+[(dx,dy)]))
            if choices:best[x,y]=min(choices)
    n,b,p=best[tx,ty]
    return dict(target=[tx,ty],transactions=n,total_staged_bytes=b,
                repeated_moves={str(k):v for k,v in collections.Counter(p).items()},
                model_seconds_at_60hz=n/60,
                caveat='Address/step-count model, not measured travel time or a helper implementation')

result={'baseline_commit':(ROOT/'.git/refs/heads/main').read_text().strip(),
        'host':json.loads((HERE/'MODEL.JSN').read_text()),'native':{},'chunks':{},'memory':{}}
for name,budget in [('base',1440),('2816',2816),('5504',5504)]:
    d=HERE/('native-base-05' if name=='base' else f'native-{name}-05')
    r=json.loads((d/'NATIVE.JSN').read_text());result['native'][name]=r
    listing=(d/'PAN.LST').read_text(errors='replace')
    lengths={}
    for symbol in ('HP_SET','XY_RECTANGLES'):
        match=re.search(r'^'+symbol+r' .*Length = ([0-9A-F]+)',listing,re.M)
        assert match,symbol
        lengths[symbol]=int(match[1],16)
    result['memory'][name]=dict(stage=budget,scratch_delta=budget-1440,procedure_bytes=lengths)
    result['chunks'][name]=[walk(budget,x,y,name=='base') for x,y in [(32,16),(320,56)]]
base=result['memory']['base']['procedure_bytes']
for name in ('2816','5504'):
    row=result['memory'][name]
    row['code_delta']=sum(row['procedure_bytes'].values())-sum(base.values())
    row['code_plus_scratch_delta']=row['code_delta']+row['scratch_delta']
rows=[]
for n in range(len(result['native']['base']['cases'])):
    row={}
    for name in ('base','2816','5504'):
        c=result['native'][name]['cases'][n]
        row.update(dx=c['dx'],dy=c['dy'])
        for key,value in c['mean'].items():row[name+'_'+key]=value
        row[name+'_bytes']=c['bytes']
        row[name+'_x_pixels_second']=1000*c['dx']/c['mean']['total_ms']
        row[name+'_y_pixels_second']=1000*c['dy']/c['mean']['total_ms']
    rows.append(row)
with (HERE/'COMPARISON.CSV').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
result['source_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (ROOT/'experiments/XYPAN').glob('*') if p.is_file()}
(HERE/'SUMMARY.JSN').write_text(json.dumps(result,indent=2)+'\n')
# Exact tracked-source diff; independent model/harness sources remain separate.
diff=subprocess.check_output(['git','--git-dir='+str(ROOT/'.git'),'--work-tree='+str(ROOT),
                              'diff','--',':(top)experiments/XYPAN',
                              ':(top)experiments/XYRRECT/XRBUILD.PY'])
(HERE/'PROTOTYPE.PATCH').write_bytes(diff)
for name in ('2816','5504'):print(name,result['memory'][name],result['chunks'][name])
