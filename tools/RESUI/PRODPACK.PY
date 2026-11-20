"""Private release-candidate composition; no upload, manifests or OS files.

Use stage to add the existing original-media fresh entry to a native CGA
candidate. Compile its FRESH.C and native-src/SETUP.C with the existing
8086 toolchain, then use pack. The historical accepted archives stay intact.
"""
from pathlib import Path
import argparse,importlib.machinery as M,shutil,zipfile
ROOT=Path(__file__).resolve().parents[2]
F=M.SourceFileLoader('production_fresh',str(ROOT/'src/cga/FRESHPK.PY')).load_module()
G=M.SourceFileLoader('production_ui',str(ROOT/'tools/RESUI/GRAPHICS.PY')).load_module()
O=M.SourceFileLoader('production_media',str(ROOT/'tools/RESUI/OWNMEDIA.PY')).load_module()

def stage(native,out):
 if out.exists():raise ValueError('Fresh candidate directory required')
 original,fresh=F.inputs(ROOT)
 fresh['NOTICE.TXT']=(ROOT/'src/cga/NOTICE.TXT').read_bytes()
 fresh['XTCSYS.FON']=(ROOT/'tools/SYSFONT/BIN/XTCSYS.FON').read_bytes()
 fresh=O.strip(G.apply(fresh))
 out.mkdir(parents=True);shutil.copytree(native/'packet',out/'expanded')
 for n,b in fresh.items():F.save(out/'expanded/FRESH640'/n,b)
 previous=F.inputs;F.inputs=lambda repo:(original,fresh)
 try:sources=F.sources(ROOT)
 finally:F.inputs=previous
 for n,b in sources.items():F.save(out/'fresh-src'/n,b)
 for n in ('FRESH.TXT','FRESHLIC.TXT'):
  F.save(out/'expanded'/n,(ROOT/'src/cga'/n).read_bytes())
 (out/'expanded/OWATCOM.TXT').write_bytes((ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes())
 (out/'expanded/CGAOLD.TXT').write_bytes((out/'expanded/README.TXT').read_bytes())
 (out/'expanded/README.TXT').write_bytes((ROOT/'src/cga/FRESH.TXT').read_bytes())
 # Original source inputs only; a self-contained launcher rebuild is bundled
 # without the old source ZIP's embedded accepted CGA archive/stock grabber.
 shutil.copytree(out/'fresh-src',out/'source')
 shutil.copytree(out/'expanded/FRESH640',out/'source/FRESH640')
 (out/'source/FRESHLIC.TXT').write_bytes((ROOT/'src/cga/FRESHLIC.TXT').read_bytes())
 (out/'source/FRESH.TXT').write_bytes((ROOT/'src/cga/FRESH.TXT').read_bytes())
 (out/'source/BUILD.BAT').write_bytes(b'@ECHO OFF\r\nCL /nologo /G0 /AS /Os FRESH.C /link /STACK:4096\r\n')
 print('Staged project-only CGA/fresh candidate; compile before pack:',out)

def archive(path,folder):
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in sorted(folder.rglob('*')):
   if p.is_file():
    rel=p.relative_to(folder).as_posix()
    if p.suffix.upper() in ('.JSN','.JSON','.SHA','.SUM'):raise ValueError('Unexpected record: '+rel)
    z.writestr(rel,p.read_bytes())

def pack(out):
 exe=(out/'fresh-src/FRESH.EXE').read_bytes();F.dos_exe(exe)
 (out/'expanded/FRESH.EXE').write_bytes(exe)
 if not (out/'expanded/SETUP.EXE').is_file():raise ValueError('Compile/copy native SETUP.EXE first')
 # Refuse a stock Windows grabber under any consumer filename.
 original=O.stock()
 for p in (out/'expanded').rglob('*'):
  if p.is_file() and p.read_bytes()==original:raise ValueError('Stock Windows file: '+str(p))
 archive(out/'CGA.ZIP',out/'expanded');archive(out/'CGASRC.ZIP',out/'source')
 print('Private candidates only:',out/'CGA.ZIP',out/'CGASRC.ZIP')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('stage','pack'));p.add_argument('--out',type=Path,required=True);p.add_argument('--native',type=Path);a=p.parse_args()
 if a.action=='stage':stage(a.native,a.out)
 else:pack(a.out)
