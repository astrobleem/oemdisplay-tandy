"""Stage the existing CGA installer candidate without generating audit manifests.

The accepted input archive stays unchanged. This developer tree contains
licensed/private support inputs and is NOT a redistributable archive.
"""
from pathlib import Path
import sys,zipfile,subprocess,importlib.machinery as M
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/cga'))
for name in ['STAGECGA','CGAFONT','CG6FONT','CGASET','CMPRSC']:
 M.SourceFileLoader(name,str(ROOT/'src/cga'/(name+'.PY'))).load_module()
COMPOSER=M.SourceFileLoader('ui_pan_cga',str(ROOT/'tools/PAN/CGASTAGE.PY')).load_module()
def stage(out):
 with zipfile.ZipFile(ROOT/'downloads/FRESH/CGA.ZIP') as z:
  files={n[4:]:z.read(n) for n in z.namelist() if n.startswith('CGA/')}
 P=COMPOSER.module(dict(files))
 files['OEMSETUP.INF']=(ROOT/'src/cga/OEMSETUP.INF').read_bytes()
 for name in ['CG1SYS.FON','CG2SYS.FON','XTCSYS.FON']:
  files[name]=(ROOT/'tools/SYSFONT/BIN'/name).read_bytes()
 original=P.write
 def no_records(path,text):
  if path.suffix.upper() in ('.JSN','.JSON','.SHA','.SUM'):return
  original(path,text)
 P.write=no_records
 try:P.emit(ROOT,out,files,subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),compact_only=True)
 finally:P.write=original
if __name__=='__main__':stage(Path(sys.argv[1]).resolve())
