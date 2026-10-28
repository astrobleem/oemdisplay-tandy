"""Guarded MSC6/MASM build of the matching TSINPUT DLL and private native probes."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import argparse,hashlib,importlib.util,json,shutil,struct,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];IDLE=ROOT/'examples/TSHELL/IDLE'
FILES=('TSINPUT.C','TSINPUT.H','TSINPUT.DEF','TSINPUT.RSP','LIBENTRY.ASM','IDLEPROB.C','IDLEPROB.DEF','IDLEPROB.RSP','HOLDPROB.C','HOLDPROB.DEF','HOLDPROB.RSP','BUILD.BAT')
def pin(path):
    b=path.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('toolchain','dosbox','lease','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();tool=a.toolchain.resolve()
    if any(c in str(out)+str(tool)for c in ('"','\r','\n')):p.error('Unsafe mount path')
    for n in ('BIN/CL.EXE','BIN/MASM.EXE','BIN/LINK4.EXE','LIB/LIBW.LIB'):
        if not(tool/n).is_file():p.error('Missing explicit external input '+n)
    commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    for n in FILES:
        b=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+(IDLE/n).relative_to(ROOT).as_posix()])
        if b!=(IDLE/n).read_bytes():p.error('Commit input source first: '+n)
    out.mkdir(parents=True,exist_ok=False)
    for n in FILES:shutil.copyfile(IDLE/n,out/n)
    config=f'''[sdl]
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
    (out/'BUILD.CNF').write_text(config)
    guard=ROOT/'tools/SOUNDOWN/RUNDOS.PY';loader=SourceFileLoader('cube_input_guard',str(guard));spec=importlib.util.spec_from_loader(loader.name,loader)
    m=importlib.util.module_from_spec(spec);loader.exec_module(m);m.run(a.dosbox,out/'BUILD.CNF',a.lease,120)
    log=(out/'BUILD.LOG').read_text(errors='replace')
    if 'PASS'not in log or 'FAIL'in log:raise RuntimeError('Input build failed')
    for n in ('TSINPUT.DLL','IDLEPROB.EXE','HOLDPROB.EXE'):
        f=out/n;b=bytearray(f.read_bytes());ne=struct.unpack_from('<I',b,0x3c)[0];assert b[ne:ne+2]==b'NE';struct.pack_into('<H',b,ne+0x3e,0x0300);f.write_bytes(b)
    verify=subprocess.check_output(['python',str(IDLE/'tests/VERIFY.PY'),str(out/'TSINPUT.DLL')])
    (out/'VERIFY.JSN').write_bytes(verify)
    r=dict(source_commit=commit,source={n:pin(IDLE/n)for n in FILES},runtime=pin(out/'TSINPUT.DLL'),scope='Compile/link and NE ABI contract; native behavior separate')
    (out/'BUILD.JSON').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['runtime']))
if __name__=='__main__':main()
