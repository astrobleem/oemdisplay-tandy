"""Check real current ZIP inputs and documentation-only package refreshes."""
from pathlib import Path
import argparse,copy,importlib.machinery,json,re,tempfile,zipfile
from unittest import mock
P=importlib.machinery.SourceFileLoader('current_catalog',str(Path(__file__).with_name('BUNDLE.PY'))).load_module()

def check(sound):
 config=P.spec();assets=P.ancillary(sound);checks=[];references=[]
 checks.append('All14 ancillary ZIPs match qualified inputs and deterministic build-input archive')
 assert assets['BUILDIN.ZIP']==P.input_archive(config)
 inputs=P.zip_files(assets['BUILDIN.ZIP'])
 for n,pin in config['developer_inputs'].items():assert P.identity(inputs[n])==pin,n
 checks.append('All3 original developer inputs preserved under their original builder names')
 for n,row in config['documentation_overlays'].items():
  original=P.zip_files((P.ROOT/config['local'][n]['source']).read_bytes())
  refreshed=P.zip_files(assets[n]);assert set(original)==set(refreshed)
  assert {f:b for f,b in original.items() if f!=row['member']}=={f:b for f,b in refreshed.items() if f!=row['member']}
  assert refreshed[row['member']]==(P.ROOT/row['source']).read_bytes()
 checks.append('All4 guide refreshes preserve every driver/app/helper/support byte')
 assert not set(assets)&set(config['excluded_consumer_alternatives'])
 checks.append('No promoted raw EXE or obsolete desktop wrapper in asset set')
 with tempfile.TemporaryDirectory(prefix='winxt-input-refusal-') as tmp:
  bad=Path(tmp)/'BAD.ZIP';bad.write_bytes(b'not the qualified packet')
  try:P.exact(bad,config['sound']['TWXT2.ZIP']['identity'])
  except ValueError:pass
  else:raise AssertionError('Wrong qualified bytes accepted')
 checks.append('Wrong packet bytes refused before assembly')
 try:P.main_product(P.archive({'README.TXT':b'incomplete'}))
 except ValueError:pass
 else:raise AssertionError('Incomplete main layout accepted')
 checks.append('Incomplete main layout refused')
 for name,data in assets.items():
  if name=='BUILDIN.ZIP':continue
  for member,body in P.zip_files(data).items():
   parts=member.upper().split('/')
   if not member.upper().endswith(('.TXT','.MD')) or any(x in parts for x in ['SRC','SOURCE','DEPS','EVIDENCE','TESTS','HISTORY']):continue
   urls=re.findall(r'https://github.com/[^\s\)\]"<>]+/releases/(?:download|tag)/[^\s\)\]"<>]+',body.decode('latin1'))
   if urls:references.append({'asset':name,'member':member,'release_references':urls})
 return {'checks':checks,'assets':{n:P.identity(b) for n,b in assets.items()},
         'packaged_release_references':references,
         'main_native_gate':'Not exercised by this ancillary check; BUNDLE always calls the gated native producer before output.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sound',type=Path,required=True);p.add_argument('--report',type=Path)
 a=p.parse_args();result=check(a.sound)
 if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='ascii')
 print(json.dumps({'checks':len(result['checks']),'assets':len(result['assets']),'packaged_release_references':result['packaged_release_references']},indent=2))
