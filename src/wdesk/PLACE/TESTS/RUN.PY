"""Strict actual-source placement checks; host USER mocks, no native claim."""
from pathlib import Path
import argparse,hashlib,json,os,shlex,subprocess,sys
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
args.out.mkdir(parents=True,exist_ok=False)
out=args.out.resolve()
launcher=Path(r'C:\Users\chad\Documents\Codex\toolchains\gcc-ucrt64.py')
compiler=([sys.executable,str(launcher),'--'] if os.name=='nt'
          else shlex.split(os.environ.get('CC','cc')))
command=compiler+['-x','c','-std=c89','-pedantic',
         '-Wall','-Wextra','-Wconversion','-Wshadow','-Wstrict-prototypes','-Werror',
         '-I'+str(root/'TESTS'),'-I'+str(root),str(root/'WTPLACE.C'),
         str(root/'TESTS/WTTEST.C'),'-o',str(out/'WTTEST.EXE')]
compiled=subprocess.run(command,capture_output=True)
(out/'COMPILE.LOG').write_bytes(compiled.stdout+compiled.stderr)
if compiled.returncode:raise SystemExit(compiled.returncode)
run=subprocess.run([str(out/'WTTEST.EXE')],capture_output=True)
(out/'RUN.LOG').write_bytes(run.stdout+run.stderr)
record={'evidence':'host USER mocks only','returncode':run.returncode,
        'command':command,'source':{p.relative_to(root).as_posix():
        {'bytes':len(p.read_bytes()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in [root/'WTPLACE.C',root/'WTPLACE.H',root/'TESTS/windows.h',root/'TESTS/WTTEST.C']}}
(out/'RESULT.JSON').write_text(json.dumps(record,indent=2)+'\n',encoding='ascii')
print(run.stdout.decode('ascii'),end='')
raise SystemExit(run.returncode)
