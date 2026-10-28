"""Check real current ZIP inputs and documentation-only package refreshes."""
from pathlib import Path
import argparse,copy,importlib.machinery,json,re,tempfile,zipfile
from unittest import mock
P=importlib.machinery.SourceFileLoader('current_catalog',str(Path(__file__).with_name('BUNDLE.PY'))).load_module()

def check(sound,core):
 config=P.spec();
 for n,pin in config['core_identities'].items():assert P.identity((core/n).read_bytes())==pin,n
 assets=P.ancillary(sound,(core/'WINXT.ZIP').read_bytes());checks=[];references=[]
 P.verify_alternatives(assets);checks.append('CGA exact qualified packet and preserved earlier runtime verified')
 fresh=importlib.machinery.SourceFileLoader('catalog_fresh_snapshot_refusal',str(P.HERE/'FRESHVIEW.PY')).load_module()
 with tempfile.TemporaryDirectory(prefix='fresh-catalog-refusal-') as tmp:
  original=P.zip_files((P.HERE/'CGASNAP.ZIP').read_bytes());changed=dict(original)
  changed['tools/CURRENT/BUNDLE.PY']+=b'changed'
  (Path(tmp)/'CGASNAP.ZIP').write_bytes(P.archive(changed))
  with mock.patch.object(fresh,'HERE',Path(tmp)):
   try:fresh.verify(assets['CGA.ZIP'])
   except ValueError:pass
   else:raise AssertionError('Changed original fresh source accepted')
 checks.append('Changed frozen catalog source refused; all original fresh CGA pins retained')
 checks.append('All4 qualified core identities pinned; supplied producer commit preserved')
 checks.append('All'+str(len(assets))+' ancillary files match qualified inputs and deterministic build-input archive')
 if 'CUBE.ZIP' in assets:
  checks.append('Cube exact runtime/source/metadata and all10 frozen native roles verified; four core identities unchanged')
  bad=dict(assets);bad['CUBE.ZIP']=P.archive({'README.TXT':b'incomplete'})
  try:P.verify_cube(bad)
  except ValueError:pass
  else:raise AssertionError('Unbound Cube packet accepted')
  checks.append('Modified Cube packet refused by its producer/artifact binding')
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
 collection=P.zip_files(assets['TANDYLAB.ZIP']);original=P.zip_files((P.ROOT/config['collection']['source']).read_bytes())
 for n,b in original.items():
  if n.startswith('TANDYLAB/DRIVERS/') or n in ['TANDYLAB/README.TXT','TANDYLAB/CHECK.TXT','TANDYLAB/MANIFEST.SHA','TANDYLAB/CATALOG.TXT']:continue
  assert collection[n]==b,n
 main=P.main_product((core/'WINXT.ZIP').read_bytes())
 assert {n[len('TANDYLAB/DRIVERS/'):]:b for n,b in collection.items() if n.startswith('TANDYLAB/DRIVERS/WINXT/')}=={n:b for n,b in main.items() if n.startswith('WINXT/')}
 assert not any(n.upper().endswith(('.ZIP','.PY')) for n in collection if n.startswith('TANDYLAB/DRIVERS/'))
 assert collection['TANDYLAB/CATALOG.TXT'].split(b'OPTIONAL WINDOWS XT DISPLAY SOURCE')[0]==original['TANDYLAB/CATALOG.TXT'].split(b'DISPLAY TOOLKIT (OPTIONAL, MODERN PC PREPARATION ONLY)')[0]
 for n in ['TANDYLAB/README.TXT','TANDYLAB/CHECK.TXT','TANDYLAB/CATALOG.TXT','TANDYLAB/DRIVERS/README.TXT']:
  assert not any(chore in collection[n] for chore in [b'STAGE.PY',b'T88TOOLS.ZIP',b'CGASYS.FON EGAFIX.FON']),n
 checks.append('TANDYLAB app bytes unchanged; complete qualified movable OEM folder replaces Python toolkit')
 for name,data in assets.items():
  if name=='BUILDIN.ZIP' or name in config.get('metadata',{}):continue
  for member,body in P.zip_files(data).items():
   parts=member.upper().split('/')
   if not member.upper().endswith(('.TXT','.MD')) or any(x in parts for x in ['SRC','SOURCE','DEPS','EVIDENCE','TESTS','HISTORY']):continue
   urls=re.findall(r'https://github.com/[^\s\)\]"<>]+/releases/(?:download|tag)/[^\s\)\]"<>]+',body.decode('latin1'))
   if urls:references.append({'asset':name,'member':member,'release_references':urls})
 return {'checks':checks,'assets':{n:P.identity(b) for n,b in assets.items()},
         'packaged_release_references':references,
         'main_native_gate':'Replayed through main_product; BUNDLE additionally reproduces all four core artifacts through the gated producer.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sound',type=Path,required=True);p.add_argument('--core',type=Path,required=True);p.add_argument('--report',type=Path)
 a=p.parse_args();result=check(a.sound,a.core)
 if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='ascii')
 print(json.dumps({'checks':len(result['checks']),'assets':len(result['assets']),'packaged_release_references':result['packaged_release_references']},indent=2))
