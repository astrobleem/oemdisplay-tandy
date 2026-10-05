#!/usr/bin/env python3
"""Stage all five Trial5 source pipelines and test exact inputs/inverse scope.
This is source verification only. Use BUILD88, TSTWIDE and Windows tests too.
"""
from pathlib import Path
import argparse,hashlib,json,tempfile,importlib.machinery
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=HERE.parents[1]);a=p.parse_args();repo=a.repo.resolve()
 load=lambda n:importlib.machinery.SourceFileLoader('trial5_'+n,str(HERE/(n+('.py' if n=='build' else '.PY')))).load_module()
 mods={n:load(n) for n in ['build','PORT8086','PORTDIB','MODEPROF','REPCOPY88','BYTECOL','CURKEEP','OUTROWS','WIDESCAN']}
 baseline=json.loads((repo/'docs/TRIAL4/BUILDS.JSN').read_text());wanted=json.loads((repo/'docs/TRIAL5/BUILDS.JSN').read_text());rows=[]
 for rel,digest in baseline['source_files'].items():
  target=repo/rel
  if rel=='src/tandysw/BUILD88.PY':target=HERE/'BLDTR4.PY'
  assert hashlib.sha256(target.read_bytes()).hexdigest()==digest,rel
 with tempfile.TemporaryDirectory(prefix='trial5-src-') as temp:
  for mode,pin in baseline['profiles'].items():
   renderer,res=mods['build'].prepare(repo,Path(temp)/mode)
   for n in ['PORT8086','PORTDIB']:mods[n].port(renderer,repo)
   mods['MODEPROF'].port(renderer,res,repo,mode)
   for n in ['REPCOPY88','BYTECOL']:mods[n].port(renderer,mode)
   mods['CURKEEP'].port(renderer,mode,combined=True);mods['OUTROWS'].port(renderer,mode)
   before={str(x.relative_to(renderer)):x.read_bytes() for x in renderer.rglob('*') if x.is_file()}
   for name,digest in pin['staged_source_sha256'].items():assert hashlib.sha256(before['EGA/'+name]).hexdigest()==digest
   report=mods['WIDESCAN'].port(renderer,mode)
   for rel,data in before.items():
    if rel!='EGA/TSOFT.ASM':assert (renderer/rel).read_bytes()==data,rel
   out=(renderer/'EGA/TSOFT.ASM').read_bytes();assert hashlib.sha256(out).hexdigest()==wanted['profiles'][mode]['staged_source_sha256']
   for data in [out,before['EGA/TSOFT.ASM']+b'; changed\r\n']:
    (renderer/'EGA/TSOFT.ASM').write_bytes(data)
    try:mods['WIDESCAN'].port(renderer,mode)
    except RuntimeError:pass
    else:raise AssertionError('Invalid input accepted')
    assert (renderer/'EGA/TSOFT.ASM').read_bytes()==data
   rows.append({'mode':mode,'exact_staging':'PASS','only_changed_staged_source':'EGA/TSOFT.ASM','invalid_inputs':'rejected without writes','inverse_scope':report['inverse_scope']})
 print(json.dumps({'status':'PASS','scope':'static source only','profiles':rows},indent=2))
if __name__=='__main__':main()
