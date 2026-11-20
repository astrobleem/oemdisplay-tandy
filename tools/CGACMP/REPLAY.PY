"""Replay only the pre-UI compact proof's immutable, still-pin-checked sources.

No packet/receipt is changed and no new runtime is qualified. Git objects must
be available explicitly; this helper never fetches or substitutes another ref.
"""
from pathlib import Path
import ast,hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
REVISION='cba234b88b0d120ca7b31bfefbc1b4de3f9fc822'
INPUTS=frozenset(('src/cga/SETUP.C','src/cga/PACKCGA.PY','src/cga/CGASET.PY',
 'src/cga/CMPRSC.PY','src/cga/OEMSETUP.INF','tools/PAN/GUIDES/CGA.TXT'))
GATE='tools/CGACMP/VERIFY.PY'
FRESH_INPUTS=frozenset(('docs/CGA.MD','src/cga/FRESH.TXT'))

def identity(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def original(name,pin):
 if name not in INPUTS and name!=GATE and name not in FRESH_INPUTS:
  raise ValueError('Changed historical source outside immutable UI replay: '+name)
 try:
  data=subprocess.check_output(['git','show',REVISION+':'+name],cwd=ROOT,stderr=subprocess.PIPE)
 except subprocess.CalledProcessError as e:
  raise ValueError('Immutable pre-UI source unavailable; fetch exact revision '+REVISION) from e
 if identity(data)!=pin:raise ValueError('Immutable pre-UI source pin differs: '+name)
 return data

class SourceView:
 """Leave all evidence/current guards real; overlay only the closed old sources."""
 def __init__(self):
  self.directory=tempfile.TemporaryDirectory(prefix='compact-original-source-')
  self.frozen=Path(self.directory.name)
  pins=json.loads((ROOT/'tools/CGACMP/ACCEPT.JSN').read_bytes())['sources']
  for name in (*INPUTS,GATE):
   path=self.frozen/name;path.parent.mkdir(parents=True,exist_ok=True)
   path.write_bytes(original(name,pins[name]))
 def __del__(self):
  directory=getattr(self,'directory',None)
  if directory is not None:directory.cleanup()
 def __truediv__(self,name):
  name=Path(name).as_posix()
  return (self.frozen if name in INPUTS or name==GATE else ROOT)/name

def bootstrap(namespace):
 """Run the unchanged recorded verifier, including its original CLI/refusals."""
 view=SourceView();data=(view/GATE).read_bytes()
 name=namespace['__name__'];filename=namespace['__file__']
 # Defer its CLI until the immutable source view is installed. Functions use
 # this same namespace so existing refusal tests can still patch exact/HERE.
 namespace['__name__']=name+'._historical'
 exec(compile(data,filename,'exec'),namespace)
 namespace['__name__']=name;namespace['ROOT']=view
 if name=='__main__':
  cli=ast.parse(data,filename).body[-1]
  if not isinstance(cli,ast.If):raise ValueError('Recorded verifier CLI differs')
  exec(compile(ast.Module(body=cli.body,type_ignores=[]),filename,'exec'),namespace)
