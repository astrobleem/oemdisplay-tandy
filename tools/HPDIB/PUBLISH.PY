"""Build local artifacts only from independently reviewed native DIB acceptance."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,io,json,re,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
M=importlib.machinery.SourceFileLoader('qualified_dib_preparation',str(HERE/'PREPARE.PY')).load_module();P=M.P;C=P.C
V=importlib.machinery.SourceFileLoader('qualified_dib_raster',str(HERE/'CHECKREP.PY')).load_module()
ASSETS=('WINXT.ZIP','WINXTSRC.ZIP','WINXT.JSN','WINXT.SHA')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def identity(b):return M.identity(b)
def exact(row):
 p=Path(row['path']);require(not p.is_absolute() and '..' not in p.parts,'Unsafe accepted input path')
 b=(ROOT/p).read_bytes();require(identity(b)==row['identity'],'Changed accepted input: '+str(p));return b
def clean(lease):
 require(lease.get('status')=='PASS' and lease.get('lease_acquired') is True and lease.get('lease_released') is True and lease.get('inventory_after')==[],'Native lease incomplete')
 children=lease.get('children');require(isinstance(children,list) and children and all(type(c.get('pid')) is int and c['pid']>0 and c.get('stopped') is True for c in children),'Owned child stop missing')
def qualification():
 try:q=json.loads((HERE/'ACCEPT.JSN').read_bytes())
 except FileNotFoundError as e:raise ValueError('DIB native acceptance and final review pending') from e
 require(q.get('status')=='REVIEWED_NATIVE_HPXY_DIB' and q.get('physical_hardware') is False,'DIB qualification pending')
 for name,pin in q['sources'].items():exact(dict(path=name,identity=pin))
 required={'src/hpxydib/DIB.PY','tools/HPDIB/BUILD.PY','tools/HPDIB/PREPARE.PY','tools/HPDIB/PUBLISH.PY','tools/HPDIB/CHECKREP.PY','tools/HPDIB/PROBE.PY','experiments/SOLPERF/ORACLE.PY','experiments/SOLPERF/DIBTEST.C','experiments/SOLPERF/SCENE.C'}
 required.update('tools/HPDIB/'+n for n in ('APPTEST.PY','RUNUI.PY','SETUPIO.PY','VERIFYINST.PY','TESTGATE.PY','TESTPUB.PY'))
 required.update(('tools/UPAN/UICTRL.PY','tools/PAN/EMU86.PY','src/softpan/WINRUN.PY'))
 require(required<=set(q['sources']),'Incomplete source inventory')
 review=json.loads(exact(q['review']));require(review.get('outcome')=='NO_RESIDUAL_FINDINGS' and review.get('reviewed_commit')==q['reviewed_source_commit'] and review.get('sources')==q['sources'],'Independent exact-source review missing')
 runtime={n:exact(row) for n,row in q['runtime'].items()};require(set(runtime)=={'HPXY.DRV','FIXXT.EXE','SETUP.EXE'},'Unexpected native runtime inventory')
 P.native(runtime['HPXY.DRV'],True)
 for n in ('FIXXT.EXE','SETUP.EXE'):P.native(runtime[n],False)
 build=json.loads(exact(q['build']));M.validate_driver(runtime['HPXY.DRV'],build)
 base,packets=P.products();before=C.members(packets['WINXT.ZIP']);require(identity(packets['WINXT.ZIP'])==q['baseline_archive'],'Accepted PAN baseline differs')
 after=M.compose(before,runtime['HPXY.DRV'],runtime['FIXXT.EXE'],runtime['SETUP.EXE']);archive=C.archive(after)
 require(identity(archive)==q['archive'] and {n:identity(b) for n,b in sorted(after.items())}==q['files'],'Different native-qualified core')
 # Re-run the independent oracle from the exact closed raw evidence archive.
 evidence=exact(q['matrix_evidence'])
 with zipfile.ZipFile(io.BytesIO(evidence)) as z,tempfile.TemporaryDirectory(prefix='hpdib-verify-') as tmp:
  names=z.namelist();require(len(names)==len(set(names)) and z.testzip() is None,'Matrix evidence archive corrupt')
  require({n:identity(z.read(n)) for n in names}==q['matrix_members'],'Matrix evidence manifest differs')
  for n in names:
   p=Path(n);require(not p.is_absolute() and '..' not in p.parts and p.parts[0] in ('baseline','candidate') and p.suffix.upper() in ('.BIN','.JSN','.LOG'),'Unsafe matrix evidence member')
   dest=Path(tmp)/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
  for name,want in [('baseline',identity(before['WINXT/HPXY.DRV'])),('candidate',identity(runtime['HPXY.DRV']))]:
   folder=Path(tmp)/name;result=V.verify(folder);native=json.loads((folder/'RESULT.JSN').read_bytes())
   require(result['status']=='PASS' and result['frame_coverage_pass'] and result['lifecycle_pass'] and native['installed_driver']==want,'Native matrix coverage/input differs: '+name)
  for i in (0,1,10,11,12):require((Path(tmp)/('baseline/S%03d.BIN'%i)).read_bytes()==(Path(tmp)/('candidate/S%03d.BIN'%i)).read_bytes(),'Canonical shadow differs')
 require(set(q['preparation'])=={'FRESH','UPDATE'},'Native preparation coverage incomplete')
 for case,count in [('FRESH',387),('UPDATE',99)]:
  record=json.loads(exact(q['preparation'][case]));require(record['status']=='PASS_NATIVE_PREPARATION' and record['archive']==q['archive'] and record['compared_prepared_files']==count and record['differences']==[],'Native preparation failed: '+case);clean(record['lease'])
  for n in ('HPXY.DRV','FIXXT.EXE'):
   for prefix in ('WINXT/','WINXT/FILES/'):require(record['observed'][prefix+n]==identity(runtime[n]),'Different prepared native bytes: '+case+'/'+prefix+n)
 require(set(q['windows'])=={'full_finisher','ordinary_setup'},'Installed Windows routes incomplete')
 for case,row in q['windows'].items():
  result=json.loads(exact(row['result']));clean(json.loads(exact(row['lease'])))
  require(result['status']=='PASS_NATIVE_INSTALLED_HPXY_DIB' and result['normal_dos_return'] is True and result['installed_driver']==identity(runtime['HPXY.DRV']) and result['installed_helpers']=={n:identity(P.exact(r)) for n,r in base['helpers'].items()},'Installed Windows/helper readback incomplete: '+case)
  require(result['driver_not_injected'] is True and result['normal_packet_path'] is True,'Native route was bypassed: '+case)
  if case=='full_finisher':require(result['paintbrush_rgb_equal'] is True and result['pan_controls_pass'] is True and result['repair_complete'] is True,'Application/finisher coverage incomplete')
  else:require(result['native_windows_setup_completed'] is True,'Ordinary Windows Setup missing')
 return q,archive,packets
def products():
 q,archive,packets=qualification();result=dict(packets);result['WINXT.ZIP']=archive;return q,result
def verify_core(data):
 q,packets=products();require(data==packets['WINXT.ZIP'],'Different qualified DIB core');return C.members(data)
def verify_alternatives(files):return P.verify_alternatives(files)
def text(s):return s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
def build(out,commit,verify=False):
 require(re.fullmatch('[0-9a-f]{40}',commit or ''),'Full source commit required')
 q,packets=products();source=(ROOT/'tools/XR1PACK/SOUNDSRC.ZIP').read_bytes()
 report=dict(schema=5,tag='windows-xt',source_commit=commit,binary_source_commit=q['runtime_source'],native_report='docs/QUAL/HPDIB/FINAL.JSN',physical_qualification=False,archive=q['archive'],sound_source=identity(source),files=q['files'])
 files={'WINXT.ZIP':packets['WINXT.ZIP'],'WINXTSRC.ZIP':source,'WINXT.JSN':text(json.dumps(report,indent=2)+'\n')};files['WINXT.SHA']=text(''.join(identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
 if out.exists():require({p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}==files,'Producer output differs')
 else:
  require(not verify,'Missing verification output');out.mkdir(parents=True)
  for n,b in files.items():(out/n).write_bytes(b)
 return {n:identity(b) for n,b in files.items()}
def main(argv=None):
 a=argparse.ArgumentParser(description=__doc__);g=a.add_mutually_exclusive_group(required=True);g.add_argument('--out',type=Path);g.add_argument('--verify',type=Path);a.add_argument('--commit',required=True);v=a.parse_args(argv)
 try:print(json.dumps(build(v.out or v.verify,v.commit,bool(v.verify)),indent=2))
 except (ValueError,OSError,KeyError) as e:a.exit(1,'Refused: '+str(e)+'\n')
if __name__=='__main__':main()
