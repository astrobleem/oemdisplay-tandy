"""Build private unified-panning packets; native acceptance is separate."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,io,json,shutil,sys,zipfile
import NATIVE as N
import COMPOSE as C
ROOT=N.ROOT
HERE=N.HERE

def load(label,path):return importlib.machinery.SourceFileLoader(label,str(ROOT/path)).load_module()
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def members(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  if len(z.namelist())!=len(set(z.namelist())) or z.testzip():raise ValueError('Invalid base ZIP')
  return {n:z.read(n) for n in z.namelist() if not n.endswith('/')}
def archive(files):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as z:
  for n,b in sorted(files.items()):
   info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.create_system=0;info.external_attr=32;z.writestr(info,b)
 return out.getvalue()
def emit(out,files):
 out.mkdir(parents=True,exist_ok=False)
 for n,b in files.items():
  p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def helpers(build):
 rec=json.loads((build/'BUILD.JSN').read_bytes());files={}
 if rec['status']!='BUILT_NOT_RUNTIME_QUALIFIED':raise ValueError('Missing native build')
 for n,pin in rec['binaries'].items():
  b=(build/n).read_bytes()
  if identity(b)!=pin:raise ValueError('Changed helper '+n)
  files[n]=b
 return rec,files

def prepare(build,out,watcom,commit):
 out.mkdir(parents=True,exist_ok=False);rec,h=helpers(build)
 before,base=C.baseline_core()
 cpbuild=out/'native-cpset';cpbuild.mkdir();shutil.copyfile(HERE/'CPSET.C',cpbuild/'CPSET.C')
 cpset=N.compile_native(cpbuild,watcom,'CPSET',True)
 native=out/'native-core';N.stage(native,h,support={'CPSET.EXE':cpset})
 fix=N.compile_native(native,watcom)
 corehelpers={n:h[n] for n in ('XTPAN.EXE','XYCTL.EXE','PANCFG.EXE','PANKEY.DLL')}
 N.aliases(native,dict(corehelpers,**{'FIXXT.EXE':fix,'CPSET.EXE':cpset}))
 setup=N.compile_native(native,watcom,'SETUP',True)
 files=C.core(before,h,fix,setup,cpset=cpset)
 emit(out/'core-expanded',files);(out/'WINXT.ZIP').write_bytes(archive(files))
 # PCjr and ColorPlus use the same checked native transaction; the selected
 # driver, reservation guards and complete support payload stay unchanged.
 small=out/'native-small';N.stage(small,h,True);utility=N.compile_native(small,watcom)
 alternatives={}
 for name in ('JRPAN','CPPAN'):
  body=C.alternative(name,h,utility)
  emit(out/(name+'-expanded'),body);alternatives[name+'.ZIP']=archive(body)
  (out/(name+'.ZIP')).write_bytes(alternatives[name+'.ZIP'])
 # Reuse all accepted CGA drivers/fonts; only the owners/input/configuration
 # and the installer that knows their exact inventory are new.
 sys.path.insert(0,str(ROOT/'src/cga'));import PACKCGA
 cga=C.cga_payload(h)
 cgarec=PACKCGA.emit(ROOT,out/'cga-prepared',cga,commit)
 result=dict(status='DEVELOPMENT_PACKETS_NOT_RUNTIME_QUALIFIED',source_commit=commit,
  helpers=rec['binaries'],core_baseline=identity(base),
  packets={n:identity((out/n).read_bytes()) for n in ('WINXT.ZIP','JRPAN.ZIP','CPPAN.ZIP')},
  sources={p.relative_to(ROOT).as_posix():identity(p.read_bytes()) for p in HERE.glob('*.PY')},
  cga_prepared=cgarec['packet_id'])
 N.write(out/'PREPARE.JSN',json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('build','out','watcom'):ap.add_argument('--'+n,type=Path,required=True)
 ap.add_argument('--commit',required=True);a=ap.parse_args();print(json.dumps(prepare(a.build,a.out,a.watcom,a.commit),indent=2))
