#!/usr/bin/env python3
"""Prepare a fresh project-only captured-evidence tree; no emulator/OS setup."""
from pathlib import Path
import argparse,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 dest=a.out.resolve()
 if dest.exists():raise SystemExit('Choose a fresh --out; existing files are never replaced')
 subprocess.run([sys.executable,str(ROOT/'TESTPUB.PY')],check=True)
 dest.mkdir(parents=True)
 with zipfile.ZipFile(ROOT/'TANDI04.ZIP') as z:
  for n in z.namelist():
   if n.startswith('TANDI04/SOURCE/'):
    rel=n[len('TANDI04/SOURCE/'):];target=dest/rel
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
  for source,target in [('RUN/TANDI.EXE','src/TANDI.EXE'),('EVIDENCE/TANDI.MAP','src/TANDI.MAP')]:
   (dest/target).write_bytes(z.read('TANDI04/'+source))
  for mode in ['320x200x16','640x200x2','640x200x4']:
   prefix='TANDI04/EVIDENCE/'+mode+'/'
   run=dest/'evidence'/('art-'+mode+'-ui04');(run/'guest').mkdir(parents=True)
   for n in z.namelist():
    if n.startswith(prefix):
     rel=n[len(prefix):];target=run/rel;target.parent.mkdir(parents=True,exist_ok=True)
     target.write_bytes(z.read(n))
   shutil.copyfile(run/'NATIVE.BIN',run/'guest/NATIVE.BIN')
 baseline=dest/'evidence/art-320x200x16';baseline.mkdir(parents=True)
 shutil.copyfile(ROOT/'BASELINE.PNG',baseline/'QUESTION.PNG')
 print('Prepared source plus captured evidence at '+str(dest))
 print('No Windows media, emulator run, installation or settings change occurred.')
if __name__=='__main__':main()
