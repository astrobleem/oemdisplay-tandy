"""Build the cube using explicit MSC6 inputs and the shared bounded emulator guard."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import argparse, hashlib, importlib.util, json, shutil, struct, subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
FILES=('CUBE.C','CUBECORE.C','CUBECORE.H','CUBE.DEF','CUBE.RSP','BUILD.BAT','CUBECTL.C','CUBECTL.DEF','CUBECTL.RSP')
def pin(p):
    data=p.read_bytes()
    return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('dosbox','toolchain','lease','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();tool=a.toolchain.resolve()
    if any(c in str(out)+str(tool) for c in ('"','\r','\n')):p.error('Unsafe mount path')
    inputs=('BIN/CL.EXE','BIN/LINK4.EXE','LIB/SLIBCEW.LIB','LIB/LIBW.LIB','DDK/286/INC/WINDOWS.H')
    for n in inputs:
        if not (tool/n).is_file():p.error('Missing external input '+n)
    if not a.lease.is_file():p.error('Existing shared lease required')
    commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    for n in FILES:
        saved=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+(HERE/n).relative_to(ROOT).as_posix()])
        if saved!=(HERE/n).read_bytes():p.error('Commit the source snapshot before native build: '+n)
    out.mkdir(parents=True,exist_ok=False)
    for n in FILES:shutil.copyfile(HERE/n,out/n)
    cfg=f'''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=1
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
fpu=false
[dos]
xms=false
ems=false
umb=false
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount C "{tool}" -ro
mount D "{out}"
D:
CALL BUILD.BAT
exit
'''
    (out/'BUILD.CNF').write_text(cfg)
    guard=ROOT/'tools/SOUNDOWN/RUNDOS.PY'
    loader=SourceFileLoader('cube_guard',str(guard));spec=importlib.util.spec_from_loader(loader.name,loader)
    module=importlib.util.module_from_spec(spec);loader.exec_module(module)
    module.run(a.dosbox,out/'BUILD.CNF',a.lease,120)
    log=(out/'BUILD.LOG').read_text(errors='replace')
    if 'PASS' not in log or 'FAIL' in log:raise RuntimeError('Native build failed; inspect BUILD.LOG')
    exe=out/'CUBE.EXE';data=bytearray(exe.read_bytes());ne=struct.unpack_from('<I',data,0x3c)[0]
    assert data[ne:ne+2]==b'NE' and not struct.unpack_from('<H',data,ne+0xc)[0]&8
    struct.pack_into('<H',data,ne+0x3e,0x0300);exe.write_bytes(data)
    probe=out/'CUBECTL.EXE';data=bytearray(probe.read_bytes());ne=struct.unpack_from('<I',data,0x3c)[0]
    struct.pack_into('<H',data,ne+0x3e,0x0300);probe.write_bytes(data)
    record=dict(source_commit=commit,target='Windows 3.0 real mode / 8086/8088',compiler='/G0 /Gw /AS /W3 /Oat MSC6 LINK4',
                source={n:pin(HERE/n) for n in FILES},toolchain={n:pin(tool/n) for n in inputs},
                runtime=pin(exe),builder=pin(HERE/'BUILD.PY'),guard=pin(guard),scope='Compile/link only; native execution is separate')
    (out/'BUILD.JSON').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
