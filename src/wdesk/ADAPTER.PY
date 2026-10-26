"""Strict actual WDWIN/WTPlace host tests; USER mocks only, no native claim."""
from pathlib import Path
import argparse,hashlib,json,os,shlex,subprocess,sys
here=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--placement',type=Path,default=here/'PLACE')
a=p.parse_args();out=a.out.resolve();place=a.placement.resolve()
for name in ['WTPLACE.C','WTPLACE.H','TESTS/windows.h']:
    if not (place/name).is_file():p.error('missing placement input: '+name)
out.mkdir(parents=True,exist_ok=False)
source=[here/'WDCORE.C',here/'WDWIN.C',place/'WTPLACE.C',here/'WDWTEST.C']
compiler=([sys.executable,str(Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'),'--']
          if os.name=='nt' else shlex.split(os.environ.get('CC','cc')))
command=compiler+['-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Wconversion',
         '-Wshadow','-Wstrict-prototypes','-Werror','-I'+str(place/'TESTS'),
         '-I'+str(place),'-I'+str(here)]+[str(x) for x in source]+['-o',str(out/'WDWTEST.EXE')]
compiled=subprocess.run(command,capture_output=True)
(out/'COMPILE.LOG').write_bytes(compiled.stdout+compiled.stderr)
if compiled.returncode:raise SystemExit(compiled.returncode)
run=subprocess.run([str(out/'WDWTEST.EXE')],capture_output=True)
(out/'RUN.LOG').write_bytes(run.stdout+run.stderr)
record={'evidence':'host USER mocks only','returncode':run.returncode,'command':command,
        'source':{str(x):{'bytes':len(x.read_bytes()),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}
                  for x in source+[here/'WDCORE.H',here/'WDWIN.H',place/'WTPLACE.H',place/'TESTS/windows.h']}}
(out/'RESULT.JSON').write_text(json.dumps(record,indent=2)+'\n',encoding='ascii')
print(run.stdout.decode('ascii'),end='')
raise SystemExit(run.returncode)
