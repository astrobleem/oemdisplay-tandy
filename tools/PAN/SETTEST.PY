"""Run already prepared private DOS installer fixtures under the shared lease."""
from pathlib import Path
import argparse,importlib.machinery,json,os
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);p.add_argument('--lease',type=Path,required=True)
a=p.parse_args()
R=importlib.machinery.SourceFileLoader('pan_setup_lease',str(ROOT/'src/softpan/WINRUN.PY')).load_module().Runner
for case in ('FRESH','UPDATE','UNIVERSAL'):
 out=a.out/case
 assert out.is_dir() and not (out/'LEASE.JSON').exists(),case
 runner=R(out/'LEASE.JSON',a.lease)
 with runner.lease():runner.run([str(a.dosbox),'-nopromptfolder','-conf',str((out/'RUN.CNF').resolve())],dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),out/'HOST.LOG',180)
 assert (out/'CROOT/NEWSET.OK').read_text().strip()=='PASS',case
 print(case+' native transaction PASS',flush=True)
(a.out/'RESULT.JSN').write_text(json.dumps(dict(outcome='PASS_NATIVE_PREPARATION_AND_UNIVERSAL_INSTALL',cases=['FRESH','UPDATE','UNIVERSAL']),indent=2))
