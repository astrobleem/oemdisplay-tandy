"""Assemble a new kit from the exact caller-supplied, verified runtime inputs."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();here=Path(__file__).resolve().parent
manifest=json.loads((here/'RUNTIME.JSON').read_text())
if a.out.exists():p.error('--out must not already exist')
for n,v in manifest.items():
 f=a.inputs/n
 if not f.is_file() or f.stat().st_size!=v['bytes'] or hashlib.sha256(f.read_bytes()).hexdigest()!=v['sha256']:p.error('Missing or unexpected binary: '+n)
d=a.out/'WINXT';d.mkdir(parents=True)
for n in manifest:shutil.copyfile(a.inputs/n,d/n)
for n in ('TSSETUP.BAT','TSTART.BAT','TSHELL.INI','TSREADY.TXT','README.TXT','FULLTEST.TXT','RUNTIME.JSON'):
 if (here/n).is_file():shutil.copyfile(here/n,d/n)
print('Complete runtime staged at '+str(d.resolve()))
