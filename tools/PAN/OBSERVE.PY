"""Read actual installed files from a stopped private fixture; never edits it."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
HELPERS={n:('XTPAN.EXE','XYCTL.EXE','PANCTL.EXE','CGACTL.EXE','PANCFG.EXE','PAN.EXE','PANKEY.DLL') for n in ('pcjr','colorplus','hpxy','fixed_workspace','cga_pan','cga_fixed','native_setup')}

def pin(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
ap=argparse.ArgumentParser();ap.add_argument('--case',choices=HELPERS,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--deps',type=Path);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--image',type=Path);g.add_argument('--directory',type=Path);a=ap.parse_args()
paths={n:'WINDOWS/'+('SYSTEM/' if n.endswith('.DLL') else '')+n for n in HELPERS[a.case]}
if a.image:
 sys.path.insert(0,str(a.deps));from pyfatfs.PyFatFS import PyFatFS
 with a.image.open('rb') as f:h=f.read(512)
 offset=next(struct.unpack_from('<I',h,454+i*16)[0]*512 for i in range(4) if h[450+i*16])
 with PyFatFS(str(a.image),offset=offset,read_only=True) as f:
  data={n:f.readbytes(p) for n,p in paths.items()};win=f.readbytes('WINDOWS/WIN.INI');system=f.readbytes('WINDOWS/SYSTEM.INI');driver=f.readbytes('WINDOWS/SYSTEM/'+('JRPAN.DRV' if a.case=='pcjr' else 'CPPAN.DRV')) if a.case in ('pcjr','colorplus') else None
 fixture=pin(a.image.read_bytes())
else:
 data={n:(a.directory/p).read_bytes() for n,p in paths.items()};win=(a.directory/'WINDOWS/WIN.INI').read_bytes();system=(a.directory/'WINDOWS/SYSTEM.INI').read_bytes();fixture=None;driver=(a.directory/('WINDOWS/SYSTEM/'+('JRPAN.DRV' if a.case=='pcjr' else 'CPPAN.DRV'))).read_bytes() if a.case in ('pcjr','colorplus') else None
record=dict(schema=1,family=a.case,observation='Actual installed files read from stopped owned fixture',fixture=fixture,helpers={n:pin(b) for n,b in data.items()},destinations=paths,win_ini=pin(win),system_ini=pin(system))
if driver is not None:record['driver']=pin(driver)
a.out.write_text(json.dumps(record,indent=2));print(json.dumps(record['helpers']))
