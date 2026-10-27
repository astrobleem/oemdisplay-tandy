from pathlib import Path
import importlib.machinery,sys,json,hashlib
here=Path(__file__).resolve().parent
xr=importlib.machinery.SourceFileLoader('startup_xr',str(here.parent/'XYRRECT/XRBUILD.PY')).load_module()
solid=importlib.machinery.SourceFileLoader('startup_solid',str(here/'SOLID.PY')).load_module()
load=importlib.machinery.SourceFileLoader.load_module
# XRBUILD loads its patcher after argument parsing. Extend that staged-only pass.
def patched(self,*a,**k):
 m=load(self,*a,**k)
 if self.name=='xypatch':
  original=m.patch
  def apply(renderer,**kw):original(renderer,**kw);solid.patch(renderer)
  m.patch=apply
 return m
importlib.machinery.SourceFileLoader.load_module=patched
xr.main()
out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
p=out/'RESULT.json';r=json.loads(p.read_text())
r.update(candidate='PRIVATE HPXY solid eight-pixel conversion',runtime='NOT_TESTED_BY_BUILD',solid_overlay_sha256=hashlib.sha256((here/'SOLID.PY').read_bytes()).hexdigest(),source_base='c40e380e13b6e7cc6201b1958c580fd287cf4374',accepted_runtime_replaced=False)
p.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
