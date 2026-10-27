"""Fail-closed acceptance of optional compact CGA320/CGA640 profiles.

The preceding PAN gate still qualifies all unchanged products. This gate can
accept only its CGA alternative after exact native installation, application,
cleanup and independent-review evidence is supplied. No emulator runs here.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,io,json,re,struct,sys,zipfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def require(ok,message):
 if not ok:raise ValueError(message)
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def exact(row):
 p=Path(row['path']);require(not p.is_absolute() and '..' not in p.parts,'Unsafe compact evidence path')
 require(not (ROOT/p).is_symlink(),'Linked compact evidence refused')
 b=(ROOT/p).read_bytes();require(identity(b)==row['identity'],'Changed compact input: '+p.as_posix());return b
def members(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  names=z.namelist();require(len(names)==len(set(names)) and not z.testzip(),'Invalid compact archive')
  return {n:z.read(n) for n in names}
def child(q):
 require(q.get('lease_acquired') and q.get('lease_released') and q.get('owned_child_stopped') and
         q.get('pid',0)>0 and q.get('return')==0 and 'error' not in q and not q.get('watchdog'),
         'Compact native child did not complete and release normally')
def lease(q):
 require(q.get('status')=='PASS' and q.get('lease_acquired') and q.get('lease_released') and
         q.get('children') and q.get('inventory_after')==[] and
         all(c.get('pid',0)>0 and c.get('stopped') for c in q['children']),
         'Compact Windows owned-process cleanup incomplete')

def validate_candidate(q,data=None):
 require(q.get('physical_hardware') is False,'Physical hardware remains unqualified')
 require(re.fullmatch('[0-9a-f]{40}',q.get('runtime_source','')),'Full compact runtime source required')
 required_sources={'src/cga/SETUP.C','src/cga/PACKCGA.PY','src/cga/CGASET.PY',
  'src/cga/CMPPACK.PY','src/cga/CMPRSC.PY','src/cga/CMPINST.PY','src/cga/CMPTEST.PY',
  'src/cga/INSTALLT.PY','src/cga/OEMSETUP.INF','tools/PAN/CGASTAGE.PY','tools/PAN/GUIDES/CGA.TXT',
  'tools/PAN/PREPCGA.PY','tools/PAN/PUBLISH.PY','tools/PAN/COMPOSE.PY',
  'tools/CGACMP/HISTORY.PY','tools/CGACMP/VERIFY.PY','docs/QUAL/CGACMP/TESTSRC.ZIP'}
 require(required_sources<=set(q.get('sources',{})),'Compact source binding incomplete')
 for name,pin in q['sources'].items():exact(dict(path=name,identity=pin))
 raw=exact(q['packet'])
 if data is not None:require(data==raw,'Different qualified compact CGA packet')
 files=members(raw);require({n:identity(b) for n,b in files.items()}==q['members'],'Compact member inventory differs')
 require(len(files)==34 and set(n.split('/')[0] for n in files)=={'SETUP.EXE','README.TXT','CGA'},'Compact expanded layout differs')
 require(all(re.fullmatch(r'CGA/[A-Z0-9_]{1,8}\.[A-Z0-9]{1,3}',n) for n in files if n.startswith('CGA/')),'Compact DOS names invalid')
 require(not any(n.upper().endswith(('.ZIP','.PY')) for n in files),'Consumer host preparation refused')
 before=json.loads((ROOT/'docs/QUAL/CGACMP/BASE.JSN').read_bytes())
 baseline=(ROOT/'docs/QUAL/CGACMP/BASE.ZIP').read_bytes()
 require(identity(baseline)==before['packet'],'Preceding CGA packet changed')
 old=members(baseline)
 require({n:identity(b) for n,b in old.items()}==before['members'],'Preceding CGA inventory changed')
 require(set(files)-set(old)=={'CGA/CGA32C.DRV','CGA/CGA64C.DRV'} and not set(old)-set(files),'Unexpected compact payload delta')
 allowed={'SETUP.EXE','README.TXT','CGA/OEMSETUP.INF'}
 require(all(files[n]==b for n,b in old.items() if n not in allowed),'Earlier CGA runtime/support bytes changed')
 require(files['README.TXT']==(ROOT/'tools/PAN/GUIDES/CGA.TXT').read_bytes(),'Compact guide source differs')
 require(files['CGA/OEMSETUP.INF']==(ROOT/'src/cga/OEMSETUP.INF').read_bytes(),'Compact OEM choices differ')
 sys.path.insert(0,str(ROOT/'src/cga'))
 resource=importlib.machinery.SourceFileLoader('qualified_compact_resources',str(ROOT/'src/cga/CMPRSC.PY')).load_module()
 for mode,normal,compact in [('320C','CGA320.DRV','CGA32C.DRV'),('640C','CGA640.DRV','CGA64C.DRV')]:
  derived,audit=resource.compact(old['CGA/'+normal],old['CGA/CGA100.DRV'])
  require(files['CGA/'+compact]==derived and len(audit['segments'])==10,'Compact renderer/resource derivation differs: '+mode)
 exe=files['SETUP.EXE'];require(len(exe)>64 and exe[:2]==b'MZ','Native compact DOS installer missing')
 last,pages=struct.unpack_from('<HH',exe,2)
 require(pages*512-(512-last if last else 0)==len(exe),'Compact DOS image contains appended payload')
 build=json.loads(exact(q['build']));prep=json.loads(exact(q['prepared']))
 require(build.get('build')=='PASS' and build['binary']['sha256']==identity(exe)['sha256'] and
         build['sources']==prep['installer_sources'] and build['source_commit']==q['runtime_source'] and
         build['data_budget']['data_group_headroom_bytes']>=4096,'Compact native build/source/heap binding differs')
 require(not prep['fixture'] and prep['source_commit']==q['runtime_source'],'Synthetic or unrelated compact preparation')
 dos=json.loads(exact(q['native_dos']))
 require(dos.get('status')=='PASS_NATIVE_COMPACT_INSTALLER' and dos['source_commit']==q['runtime_source'] and
         dos.get('inventory_after')==[] and dos.get('owned_stopped') and dos.get('lease_released') and
         dos.get('menu_cancel')=='PASS' and dos.get('undo_exact_files',0)>100 and
         set(dos.get('selected_through_menu',[]))=={'320C','640C'} and
         dos.get('switches')==['320','320C','640','640C','100','PAN','320'] and
         dos.get('legacy_upgrade',{}).get('packet')==before['packet'],'Compact native DOS matrix/preceding installer upgrade incomplete')
 child(dos['compiler_process']);child(dos['installer_process'])
 for mode,name in [('320C','CGA32C.DRV'),('640C','CGA64C.DRV')]:
  require(dos['profiles'][mode]['driver']==identity(files['CGA/'+name]),'Native DOS installed compact driver differs')
 require(set(q.get('windows',{}))=={'320C','640C'},'Both compact Windows profiles required')
 installed={('WINDOWS/' if row['destination']=='WINDOWS' else 'WINDOWS/SYSTEM/')+row['installed']:
            identity(files['CGA/'+n]) for n,row in prep['payload'].items() if row['installed']}
 for mode,width in [('320C',320),('640C',640)]:
  row=q['windows'][mode];result=json.loads(exact(row['result']));observed=json.loads(exact(row['installed']))
  require(result.get('status')=='PASS_NATIVE_COMPACT_WINDOWS' and result.get('profile')==mode and
          result.get('width')==width and result.get('height')==200 and
          result.get('dos_return')=='RETURNED\r\n' and
          result.get('saved_text')=='COMPACT UI SAVED FROM NOTEPAD' and
          result.get('dialog_text_height')==5,'Compact Windows application coverage incomplete: '+mode)
  require(observed.get('files')==installed and observed.get('installer')==identity(exe) and
          result.get('installed_receipt')==row['installed']['identity'],'Different actual native-installed compact files: '+mode)
  require(observed.get('boot_settings')=={'display.drv':'CGA32C.DRV' if mode=='320C' else 'CGA64C.DRV',
          'fonts.fon':'CG1SYS.FON','fixedfon.fon':'CG1FIX.FON','oemfonts.fon':'CG1OEM.FON','286grabber':'CGAGRAB.GR2'},'Actual compact INI selection differs: '+mode)
  require(result.get('machine')=={'cpu_family':'8088','cpu_speed':'4772728','machine':'ibmxt86','mem_size':'640','gfxcard':'cga'} and
          result.get('config')==identity(exact(row['config'])),'Native IBM XT/CGA fixture differs: '+mode)
  lease(json.loads(exact(row['lease'])))
  require(bool(row.get('captures')),'Compact native captures missing')
  for capture in row['captures'].values():exact(capture)
 for kind,row in q['host'].items():
  result=json.loads(exact(row));require(result.get('host')=='PASS','Compact host check failed: '+kind)
 require(set(q['host'])=={'install','legacy','resources'},'Compact host checks incomplete')
 return raw

def candidate(path):
 q=json.loads(Path(path).read_bytes())
 require(q.get('status')=='PENDING_INDEPENDENT_REVIEW','Expected an explicitly pending candidate')
 raw=validate_candidate(q)
 return dict(outcome='PASS_NATIVE_CANDIDATE_PENDING_REVIEW',packet=identity(raw),
             native_profiles=['320C','640C'],publication='REFUSED_UNTIL_INDEPENDENT_REVIEW',physical_hardware=False)

def verify(data=None):
 try:q=json.loads((HERE/'ACCEPT.JSN').read_bytes())
 except FileNotFoundError as e:raise ValueError('Compact acceptance pending: native evidence and independent review required') from e
 require(q.get('status')=='REVIEWED_NATIVE_COMPACT_CGA','Compact acceptance pending')
 raw=validate_candidate(q,data)
 review=json.loads(exact(q['review']))
 require(review.get('outcome')=='NO_RESIDUAL_FINDINGS' and review.get('runtime_source')==q['runtime_source'] and
         review.get('sources')==q['sources'] and review.get('packet')==q['packet']['identity'],
         'Independent compact source/packet review incomplete')
 return dict(packet=identity(raw),members=len(q['members']),physical_hardware=False,
             native_profiles=['320C','640C'],review=review['outcome'])

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);group=ap.add_mutually_exclusive_group();group.add_argument('--packet',type=Path);group.add_argument('--candidate',type=Path);a=ap.parse_args()
 try:print(json.dumps(candidate(a.candidate) if a.candidate else verify(a.packet.read_bytes() if a.packet else None),indent=2))
 except (ValueError,OSError,KeyError) as e:ap.exit(1,'Refused: '+str(e)+'\n')
