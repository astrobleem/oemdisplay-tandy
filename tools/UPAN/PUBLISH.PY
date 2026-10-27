"""Publish local, native-qualified unified-panning packets. No network or compiler."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,io,json,re,struct,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
C=importlib.machinery.SourceFileLoader('unified_payload_recipes',str(HERE/'COMPOSE.PY')).load_module()
ASSETS=('WINXT.ZIP','WINXTSRC.ZIP','WINXT.JSN','WINXT.SHA')
REQUIRED={'pcjr','hpxy','fixed_window','cga_pan','cga_fixed','native_setup'}
CASE_HELPERS={
 'pcjr':{'XTPAN.EXE','PANCFG.EXE','PANKEY.DLL'},
 'hpxy':{'XYCTL.EXE','PANCFG.EXE','PANKEY.DLL'},
 'fixed_window':{'XTPAN.EXE','PANCFG.EXE','PANKEY.DLL'},
 'cga_pan':{'PANCTL.EXE','CGACTL.EXE','XTPAN.EXE','PANCFG.EXE','PANKEY.DLL'},
 'cga_fixed':{'PANCTL.EXE','CGACTL.EXE','XTPAN.EXE','PANCFG.EXE','PANKEY.DLL'},
 'native_setup':{'XTPAN.EXE','XYCTL.EXE','PANCFG.EXE','PANKEY.DLL'}}
# Installer transactions are qualified separately from unchanged helper runs.

def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def require(ok,message):
 if not ok:raise ValueError(message)
def text(s):return s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
def archive(files):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as z:
  for n,b in sorted(files.items()):
   require(not n.startswith('/') and '..' not in n.split('/'),'Unsafe packet path')
   item=zipfile.ZipInfo(n,(1980,1,1,0,0,0));item.create_system=0;item.external_attr=32;z.writestr(item,b)
 return out.getvalue()
def exact(row):
 p=Path(row['path']);require(not p.is_absolute() and '..' not in p.parts,'Unsafe qualification path')
 b=(ROOT/p).read_bytes();require(identity(b)==row['identity'],'Changed qualified input: '+p.as_posix());return b

def checked_binary(b,kind):
 require(len(b)>=64 and b[:2]==b'MZ','Missing native executable')
 off=struct.unpack_from('<I',b,60)[0];sig=b[off:off+2] if off<len(b) else b''
 require(sig not in (b'PE',b'LE',b'LX'),'Protected/modern executable refused')
 if kind=='win16':require(sig==b'NE','Missing Win16 NE header')
 else:
  require(sig!=b'NE','DOS installer is a Windows program')
  last,pages=struct.unpack_from('<HH',b,2)
  require(pages*512-(512-last if last else 0)==len(b),'Appended archive/native length mismatch')

EXPECTED={'pcjr':'PASS_NATIVE_PCJR','hpxy':'PASS_NATIVE_HPXY','fixed_window':'PASS_NATIVE_FIXED_WORKSPACE','cga_pan':'PASS_NATIVE_CGA_PAN','cga_fixed':'PASS_NATIVE_CGA_FIXED','native_setup':'PASS_NATIVE_SETUP'}

def clean_lease(row,name):
 lease=json.loads(exact(row))
 require(lease.get('lease_acquired') and lease.get('lease_released'),'Lease incomplete: '+name)
 if 'children' in lease:require(lease['status']=='PASS' and not lease['inventory_after'] and all(c['stopped'] for c in lease['children']),'Owned cleanup incomplete: '+name)
 else:require(lease.get('owned_stopped') or lease.get('owned_child_stopped'),'Owned emulator still running: '+name)
 return lease

def qualification():
 try:q=json.loads((HERE/'ACCEPT.JSN').read_bytes())
 except FileNotFoundError as e:raise ValueError('Unified panning native acceptance is not installed') from e
 require(q['schema']==1 and q['status']=='NATIVE_EMULATION_QUALIFIED_REVIEWED','Unified panning acceptance pending')
 require(q['physical_hardware'] is False,'Unsubstantiated hardware claim')
 for name,pin in q['sources'].items():
  exact(dict(path=name,identity=pin))
 require(set(q['native'])==REQUIRED,'Native backend/installation coverage incomplete')
 helpers={n:exact(row) for n,row in q['helpers'].items()}
 require(set(helpers)=={'XTPAN.EXE','XYCTL.EXE','PANCTL.EXE','CGACTL.EXE','PANCFG.EXE','PANKEY.DLL'},'Helper inventory incomplete')
 native={n:exact(row) for n,row in q['native_binaries'].items()}
 require(set(native)=={'SETUP.EXE','FIXXT.EXE','PANINST.EXE','CSETUP.EXE','CPSET.EXE'},'Native installer inventory incomplete')
 build=json.loads(exact(q['helper_build']))
 require(build['target']=='Win3 real mode 8086' and build['binaries']=={n:identity(b) for n,b in helpers.items()},'Different helper build receipt')
 for b in helpers.values():checked_binary(b,'win16')
 for b in native.values():checked_binary(b,'dos')
 for name,row in q['native'].items():
  result=json.loads(exact(row['result']));lease=json.loads(exact(row['lease']))
  require(result['outcome']==EXPECTED[name],'Native check failed: '+name)
  installed_bytes=exact(row['installed_receipt']);installed=json.loads(installed_bytes)
  require(result['installed_receipt']==identity(installed_bytes),'Native result receipt mismatch: '+name)
  require(installed['case']==name and installed['helpers']==row['tested_helpers'],'Native installed receipt mismatch: '+name)
  require(lease.get('lease_acquired') and lease.get('lease_released'),'Lease incomplete: '+name)
  if 'children' in lease:
   require(lease['status']=='PASS' and not lease['inventory_after'] and all(c['stopped'] for c in lease['children']),'Owned emulator cleanup incomplete: '+name)
  else:require(lease.get('owned_stopped') or lease.get('owned_child_stopped'),'Owned emulator still running: '+name)
  require(set(row['tested_helpers'])==CASE_HELPERS[name] and all(pin==identity(helpers[n]) for n,pin in row['tested_helpers'].items()),'Different native helper bytes: '+name)
 # Native installer checks bind the actual prepared/installed outputs and run
 # receipts separately, so a guard-only rebuild does not relabel an older UI run.
 covered={}
 expected_transactions={'core':({'SETUP.EXE','FIXXT.EXE','CPSET.EXE'},{'XTPAN.EXE','XYCTL.EXE','PANCFG.EXE','PANKEY.DLL'},3),'alternative':({'PANINST.EXE'},{'XTPAN.EXE','PANCFG.EXE','PANKEY.DLL'},1),'cga':({'CSETUP.EXE'},CASE_HELPERS['cga_pan'],1)}
 require(len(q['installer_checks'])==3 and {row['group'] for row in q['installer_checks']}==set(expected_transactions),'Installer groups incomplete')
 for row in q['installer_checks']:
  expected_installers,expected_helpers,min_leases=expected_transactions[row['group']]
  require(len(row['leases'])>=min_leases,'Native installer leases missing')
  record_bytes=exact(row['result']);record=json.loads(record_bytes)
  for lease_row in row['leases']:clean_lease(lease_row,'installer')
  require(record['outcome']=='PASS_NATIVE_INSTALLER_TRANSACTION','Native installer check failed')
  receipt_bytes=exact(row['receipt']);receipt=json.loads(receipt_bytes)
  require(record['receipt']==identity(receipt_bytes),'Installer result/receipt mismatch')
  require(receipt['group']==row['group'] and set(receipt['installers'])==expected_installers and set(receipt['installed_helpers'])==expected_helpers,'Installer output inventory incomplete')
  for n,pin in receipt['installers'].items():
   require(n in native and pin==identity(native[n]),'Different tested installer: '+n);covered[n]=pin
  for n,pin in receipt['installed_helpers'].items():require(n in helpers and pin==identity(helpers[n]),'Different installer output: '+n)
 require(set(covered)==set(native),'Installer transaction coverage incomplete')
 review=json.loads(exact(q['review']))
 require(review['outcome']=='NO_RESIDUAL_FINDINGS' and review['runtime_source']==q['runtime_source'],'Independent review incomplete')
 evidence=exact(q['evidence'])
 with zipfile.ZipFile(io.BytesIO(evidence)) as z:
  require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'Native evidence corrupt')
  for name,row in q['screenshots'].items():
   b=(ROOT/name).read_bytes();require(identity(b)==row['identity'] and z.read(row['capture'])==b,'Screenshot differs from native scanout: '+name)
 return q,helpers,native

def composed(q,helpers,native):
 before,base=C.baseline_core();require(identity(base)==q['baselines']['core'],'Preserved core baseline differs')
 for name,row in q['baselines']['alternatives'].items():exact(row)
 core=C.core(before,helpers,native['FIXXT.EXE'],native['SETUP.EXE'],True,cpset=native['CPSET.EXE'])
 products={'WINXT.ZIP':archive(core),'CGA.ZIP':archive(C.cga(helpers,native['CSETUP.EXE'],True))}
 for name in ('JRPAN','CPPAN'):products[name+'.ZIP']=archive(C.alternative(name,helpers,native['PANINST.EXE'],True))
 for name,b in products.items():
  require(identity(b)==q['packets'][name],'Qualified packet differs: '+name)
  files=C.members(b);require({n:identity(data) for n,data in files.items()}==q['members'][name],'Closed member inventory differs: '+name)
  require(not any(n.upper().endswith(('.PY','.ZIP')) for n in files),'Consumer host preparation/nested archive')
 # Explicitly preserve every earlier runtime/support member except the reviewed
 # helpers/installers/entry scripts and short consumer guides.
 changed={'SETUP.EXE','README.TXT','WINXT/FIXXT.EXE','WINXT/XYCTL.EXE','WINXT/CPSET.EXE','WINXT/DISPLAY.BAT','WINXT/DISPWIN.BAT'}
 require(set(core)-set(before)=={'WINXT/XTPAN.EXE','WINXT/PANCFG.EXE','WINXT/PANKEY.DLL'} and not set(before)-set(core),'Core inventory changed unexpectedly')
 require(all(core[n]==b for n,b in before.items() if n not in changed),'Unrelated core driver/app/support changed')
 for kind in ('CGA','JRPAN','CPPAN'):
  old=C.members((HERE/'BASE'/(kind+'.ZIP')).read_bytes());new=C.members(products[kind+'.ZIP']);prefix='CGA/' if kind=='CGA' else 'JRPAN/' if kind=='JRPAN' else ''
  allowed={prefix+n for n in ('XTPAN.EXE','PANCFG.EXE','PANKEY.DLL','PANINST.EXE','INSTALL.BAT','INSTALL.TXT','JRSTART.BAT','CPWIN.BAT')}
  if kind=='CGA':allowed={'SETUP.EXE','README.TXT','CGA/CGACTL.EXE','CGA/PANCTL.EXE','CGA/PANKEY.DLL'}
  added={'CGA/PANCFG.EXE','CGA/XTPAN.EXE'} if kind=='CGA' else {prefix+'PANKEY.DLL',prefix+'PANINST.EXE'}
  if kind=='JRPAN':added.add(prefix+'OWATCOM.TXT')
  require(set(new)-set(old)==added and not set(old)-set(new),'Unexpected alternative inventory: '+kind)
  require(all(new[n]==b for n,b in old.items() if n not in allowed),'Earlier driver/support changed: '+kind)
 return products

def products():
 q,helpers,native=qualification();return q,composed(q,helpers,native)
def verify_core(data):
 q,files=products();require(data==files['WINXT.ZIP'],'Different canonical unified core');return C.members(data)
def verify_alternatives(files):
 q,expected=products()
 for n in ('CGA.ZIP','CPPAN.ZIP','JRPAN.ZIP'):require(files[n]==expected[n],'Different qualified packet: '+n)
 return {n:identity(expected[n]) for n in ('CGA.ZIP','CPPAN.ZIP','JRPAN.ZIP')}

def build(output,commit,verify=False):
 require(re.fullmatch('[0-9a-f]{40}',commit or ''),'Full source commit required')
 q,packets=products();source=(ROOT/'tools/XR1PACK/SOUNDSRC.ZIP').read_bytes()
 report=dict(schema=3,tag='windows-xt',source_commit=commit,binary_source_commit=q['runtime_source'],native_report='docs/QUAL/UPAN/FINAL.JSN',physical_qualification=False,archive=identity(packets['WINXT.ZIP']),sound_source=identity(source),files=q['members']['WINXT.ZIP'])
 files={'WINXT.ZIP':packets['WINXT.ZIP'],'WINXTSRC.ZIP':source,'WINXT.JSN':text(json.dumps(report,indent=2)+'\n')}
 files['WINXT.SHA']=text(''.join(identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
 if output.exists():require({p.name:p.read_bytes() for p in output.iterdir() if p.is_file()}==files,'Current producer output differs')
 else:
  require(not verify,'Verification directory missing');output.mkdir(parents=True)
  for n,b in files.items():(output/n).write_bytes(b)
 return {n:identity(b) for n,b in files.items()}
def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__);action=ap.add_mutually_exclusive_group(required=True);action.add_argument('--out',type=Path);action.add_argument('--verify',type=Path);ap.add_argument('--commit',required=True);a=ap.parse_args(argv)
 try:print(json.dumps(build(a.out or a.verify,a.commit,bool(a.verify)),indent=2))
 except (ValueError,OSError,KeyError) as e:ap.exit(1,'Refused: '+str(e)+'\n')
if __name__=='__main__':main()
