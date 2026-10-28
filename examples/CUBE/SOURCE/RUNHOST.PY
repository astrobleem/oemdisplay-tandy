"""Focused geometry/bounds and existing shell transaction regressions. No emulator."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
env=os.environ.copy()
if os.name=='nt':
    launcher=Path(os.environ['USERPROFILE'])/'Documents/Codex/toolchains/gcc-ucrt64.py'
    compiler=[sys.executable,str(launcher),'--']
    env['PATH']=r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH','')
else:compiler=['gcc']
checks=[]
for label,include,files in [('core',HERE,[HERE/'TESTCORE.C',HERE/'CUBECORE.C']),('config',ROOT/'examples/TSHELL',[ROOT/'examples/TSHELL/TESTS/CONFIG/TESTCFG.C',ROOT/'examples/TSHELL/SCFGCORE.C']),('idle',ROOT/'examples/TSHELL/IDLE',[ROOT/'examples/TSHELL/IDLE/tests/HOSTTEST.C']),('hold',ROOT/'examples/TSHELL/IDLE',[ROOT/'examples/TSHELL/IDLE/tests/HOLDTEST.C'])]:
    exe=out/(label+'.exe')
    flags=['-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror']
    if label in ('idle','hold'):flags.append('-Wno-unused-parameter')
    cmd=compiler+flags+['-I',str(include),*[str(f)for f in files],'-o',str(exe)]
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(label+'-build.log')).write_bytes(r.stdout);r.check_returncode()
    r=subprocess.run([str(exe)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(label+'.log')).write_bytes(r.stdout);r.check_returncode()
    pins=list(files)
    if label in ('idle','hold'):pins.extend([include/'TSINPUT.C',include/'TSINPUT.H',include/'tests/WINSTUB.H'])
    checks.append(dict(check=label,result=r.stdout.decode().strip(),sources={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()for f in pins}))
record=dict(status='PASS',scope='Host C89 policy/math checks only; no native/hardware qualification',checks=checks)
(out/'RESULT.JSON').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
