from pathlib import Path
import sys,subprocess,json,hashlib,struct,shutil,importlib.util
from importlib.machinery import SourceFileLoader
root=Path(__file__).resolve().parent;repo=root/(sys.argv[2] if len(sys.argv)>2 else 'cube-render');source=repo/'examples/CUBE/SOURCE'
out=root/sys.argv[1];out.mkdir()
files=('CUBE.C','CUBECORE.C','CUBECORE.H','CUBE.DEF','CUBE.RSP','BUILD.BAT','CUBECTL.C','CUBECTL.DEF','CUBECTL.RSP')
if (source/'CUBERECT.H').is_file():files+=('CUBERECT.H',)
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
def pin(p):
 b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
for n in files:
 assert (source/n).read_bytes()==subprocess.check_output(['git','-C',str(repo),'show',commit+':examples/CUBE/SOURCE/'+n]),n
 shutil.copyfile(source/n,out/n)
tool=Path(r'C:\Users\chad\Documents\Codex\2026-10-23\task-7\native\toolchain')
expected_tools=json.loads((root/'native-candidate/BUILD.JSON').read_text())['toolchain']
actual_tools={n:pin(tool/n)for n in expected_tools}
assert actual_tools==expected_tools,'External toolchain differs from the pinned baseline'
cfg=(root/'native-candidate/BUILD.CNF').read_text().replace(str(root/'native-candidate'),str(out))
(out/'BUILD.CNF').write_text(cfg)
guard=root/'RUNDOS-X86.PY'
loader=SourceFileLoader('render_x86_guard',str(guard));spec=importlib.util.spec_from_loader(loader.name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module)
module.run(Path(r'C:\Program Files\DOSBox-X\dosbox-x.exe'),out/'BUILD.CNF',Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock'),120)
log=(out/'BUILD.LOG').read_text();assert 'PASS' in log and 'FAIL' not in log,log
for n in ('CUBE.EXE','CUBECTL.EXE'):
 p=out/n;b=bytearray(p.read_bytes());ne=struct.unpack_from('<I',b,0x3c)[0];assert b[ne:ne+2]==b'NE';struct.pack_into('<H',b,ne+0x3e,0x0300);p.write_bytes(b)
record=dict(source_commit=commit,source={n:pin(source/n)for n in files},runtime=pin(out/'CUBE.EXE'),controller=pin(out/'CUBECTL.EXE'),guard=pin(guard),builder=pin(Path(__file__)),compiler='/G0 /Gw /AS /W3 /Oat MSC6 LINK4',scope='Local compile/link only; private x86 guard excludes Mesen per Chad parallel authorization',toolchain=actual_tools)
(out/'BUILD.JSON').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
