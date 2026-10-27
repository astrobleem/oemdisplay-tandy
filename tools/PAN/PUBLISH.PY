"""Publish only the independently reviewed, native-qualified PAN application."""
from pathlib import Path
import argparse,importlib.machinery,json,re,struct
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
C=importlib.machinery.SourceFileLoader('single_pan_recipes',str(HERE/'COMPOSE.PY')).load_module()
ASSETS=('WINXT.ZIP','WINXTSRC.ZIP','WINXT.JSN','WINXT.SHA')
REQUIRED={'pcjr','colorplus','hpxy','cga_pan','cga_fixed','fixed_workspace','native_setup'}
EXPECTED={'pcjr':'PASS_NATIVE_PCJR_SINGLE_APP','colorplus':'PASS_NATIVE_COLORPLUS_SINGLE_APP','hpxy':'PASS_NATIVE_HPXY_SINGLE_APP','cga_pan':'PASS_NATIVE_CGA_PAN_SINGLE_APP','cga_fixed':'PASS_NATIVE_CGA_FIXED_SINGLE_APP','fixed_workspace':'PASS_NATIVE_FIXED_WORKSPACE_SINGLE_APP','native_setup':'PASS_NATIVE_SETUP_SINGLE_APP'}
def require(ok,message):
 if not ok:raise ValueError(message)
def identity(b):return C.identity(b)
def exact(row):
 p=Path(row['path']);require(not p.is_absolute() and '..' not in p.parts,'Unsafe accepted input path')
 b=(ROOT/p).read_bytes();require(identity(b)==row['identity'],'Changed accepted input: '+p.as_posix());return b
def native(b,win):
 require(len(b)>64 and b[:2]==b'MZ','Missing native executable')
 off=struct.unpack_from('<I',b,60)[0];sig=b[off:off+2]
 require(sig==b'NE' if win else sig not in (b'NE',b'PE',b'LE',b'LX'),'Wrong executable target')
 if not win:
  last,pages=struct.unpack_from('<HH',b,2);require(pages*512-(512-last if last else 0)==len(b),'Appended DOS payload refused')
def clean(row):
 q=json.loads(exact(row));require(q.get('lease_acquired') and q.get('lease_released'),'Emulator lease not completed')
 if 'children' in q:require(q.get('status')=='PASS' and bool(q['children']) and not q.get('inventory_after') and all(x.get('pid',0)>0 and x.get('stopped') for x in q['children']),'Owned emulator cleanup incomplete')
 else:require((q.get('pid',0)>0 or q.get('owned_pid',0)>0) and (q.get('owned_child_stopped') or q.get('owned_stopped')),'Owned emulator not stopped')
 return q
def qualification():
 try:q=json.loads((HERE/'ACCEPT.JSN').read_bytes())
 except FileNotFoundError as e:raise ValueError('PAN acceptance pending') from e
 require(q.get('status')=='REVIEWED_NATIVE_SINGLE_APP' and q.get('physical_hardware') is False,'PAN acceptance pending')
 for n,pin in q['sources'].items():exact(dict(path=n,identity=pin))
 h={n:exact(row) for n,row in q['helpers'].items()};require(set(h)==set(C.APP),'Common application inventory differs');require(h['PAN.EXE']==h['PANCFG.EXE'],'Public entry differs from reviewed dispatcher')
 d={n:exact(row) for n,row in q['drivers'].items()};require(set(d)=={'JRPAN.DRV','CPPAN.DRV'},'Software desktop driver inventory differs')
 installers={n:exact(row) for n,row in q['installers'].items()};require(set(installers)=={'CORESET.EXE','FIXXT.EXE','PANSET.EXE','CGASET.EXE'},'Native installer inventory differs')
 for b in list(h.values())+list(d.values()):native(b,True)
 for b in installers.values():native(b,False)
 require(set(q['native'])==REQUIRED,'Native backend/installation coverage incomplete')
 for family,row in q['native'].items():
  receipt=exact(row['result']);result=json.loads(receipt);require(result['outcome']==EXPECTED[family],'Native acceptance failed: '+family)
  require(result['installed_receipt']==row['installed']['identity'],'Native result/installed observation binding differs: '+family)
  clean(row['lease'])
  installed=json.loads(exact(row['installed']));require(installed['family']==family,'Wrong installed-observation family');require(set(row['helpers'])==set(C.APP),'Incomplete installed common application: '+family);require(installed['helpers']==row['helpers'],'Installed observation differs: '+family)
  require(all(identity(h[n])==pin for n,pin in row['helpers'].items()),'Different native helper bytes: '+family)
  if family in ('pcjr','colorplus'):
   name='JRPAN.DRV' if family=='pcjr' else 'CPPAN.DRV'
   require(row.get('driver')==name and installed['driver']==identity(d[name]),'Different native software driver bytes: '+family)
 require(set(q['raster'])=={'pcjr','colorplus'},'Both native software raster comparisons required')
 for adapter,row in q['raster'].items():
  result=json.loads(exact(row['pixels']));require(result['outcome']=='PASS' and result['adapter']==adapter and result['driver']==identity(d['JRPAN.DRV' if adapter=='pcjr' else 'CPPAN.DRV']) and result['pixels_checked']>=704000 and not any(f['mismatches'] for f in result['frames']),'Native pixel comparison failed: '+adapter)
  clean(row['lease']);require(exact(row['driver'])==d['JRPAN.DRV' if adapter=='pcjr' else 'CPPAN.DRV'],'Different pixel-tested driver')
 groups={'core':{'CORESET.EXE','FIXXT.EXE'},'universal':{'PANSET.EXE'},'cga':{'CGASET.EXE'}}
 require(set(q['installer_checks'])==set(groups),'Native installer groups incomplete')
 for group,wanted in groups.items():
  row=q['installer_checks'][group];raw=exact(row['result']);result=json.loads(raw);observation=json.loads(exact(row['installed']))
  require(result['outcome']=='PASS_NATIVE_INSTALLER_TRANSACTION' and result['installed_receipt']==row['installed']['identity'],'Native installer transaction failed: '+group)
  require(set(observation['installers'])==wanted and observation['installers']=={n:identity(installers[n]) for n in wanted},'Different native installer bytes: '+group)
  require(set(observation['helpers'])==set(C.APP) and observation['helpers']=={n:identity(b) for n,b in h.items()},'Different native installer helper bytes: '+group)
  require(bool(row['leases']),'Native installer lease missing: '+group)
  for lease in row['leases']:clean(lease)
  if group=='core':require(set(result['transactions'])=={'FRESH','UPDATE','PANINIT'},'Native canonical Setup coverage incomplete')
 review=json.loads(exact(q['review']));require(review['outcome']=='NO_RESIDUAL_FINDINGS' and review['runtime_source']==q['runtime_source'],'Independent final review incomplete')
 for n,row in q['screenshots'].items():exact(row)
 return q,h,d,installers
def products():
 q,h,d,installers=qualification();packets=C.compose(h,d,installers)
 require({n:identity(b) for n,b in packets.items()}==q['packets'],'Composed consumer identities differ')
 require({n:{p:identity(b) for p,b in C.members(data).items()} for n,data in packets.items()}==q['members'],'Consumer payload inventory differs')
 for name in ('WINXT.ZIP','CGA.ZIP','JRPAN.ZIP','CPPAN.ZIP'):
  before=C.base(name);after=C.members(packets[name]);allowed=set(q['allowed_changes'][name])
  require({n for n in set(before)|set(after) if before.get(n)!=after.get(n)}==allowed,'Unexpected earlier runtime/support change: '+name)
 return q,packets
def verify_core(data):
 q,packets=products();require(data==packets['WINXT.ZIP'],'Different canonical PAN core');return C.members(data)
def verify_alternatives(files):
 q,packets=products()
 for n in ('CGA.ZIP','CPPAN.ZIP','JRPAN.ZIP','PAN.ZIP'):require(files[n]==packets[n],'Different qualified PAN packet: '+n)
 return {n:identity(packets[n]) for n in ('CGA.ZIP','CPPAN.ZIP','JRPAN.ZIP','PAN.ZIP')}
def text(s):return s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
def build(out,commit,verify=False):
 require(re.fullmatch('[0-9a-f]{40}',commit or ''),'Full source commit required')
 q,packets=products();source=(ROOT/'tools/XR1PACK/SOUNDSRC.ZIP').read_bytes()
 report=dict(schema=4,tag='windows-xt',source_commit=commit,binary_source_commit=q['runtime_source'],native_report='docs/QUAL/PAN/FINAL.JSN',physical_qualification=False,archive=identity(packets['WINXT.ZIP']),sound_source=identity(source),files=q['members']['WINXT.ZIP'])
 files={'WINXT.ZIP':packets['WINXT.ZIP'],'WINXTSRC.ZIP':source,'WINXT.JSN':text(json.dumps(report,indent=2)+'\n')};files['WINXT.SHA']=text(''.join(identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
 if out.exists():require({p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}==files,'Producer output differs')
 else:
  require(not verify,'Missing verification output');out.mkdir(parents=True)
  for n,b in files.items():(out/n).write_bytes(b)
 return {n:identity(b) for n,b in files.items()}
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--out',type=Path);g.add_argument('--verify',type=Path);p.add_argument('--commit',required=True);a=p.parse_args(argv)
 try:print(json.dumps(build(a.out or a.verify,a.commit,bool(a.verify)),indent=2))
 except (ValueError,OSError,KeyError) as e:p.exit(1,'Refused: '+str(e)+'\n')

if __name__=='__main__':main()
