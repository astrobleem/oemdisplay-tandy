"""Build original test-only DOS helpers on the host; never launches an emulator."""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
out=Path(sys.argv[1]).resolve()
if out.exists():raise ValueError('Fresh helper build output required')
out.mkdir(parents=True)
tools=[Path('C:/WATCOM/binnt/wasm.exe'),Path('C:/WATCOM/binnt/wlink.exe')]
logs=[]
for name in ('SKCTRL','DRAIN'):
    source=(HERE/(name+'.ASM')).read_bytes()
    assert b'\n' not in source.replace(b'\r\n',b'')
    (out/(name+'.ASM')).write_bytes(source)
    for call in ([str(tools[0]),'-0','-zcm=masm','-we','-fo='+name+'.OBJ',name+'.ASM'],
                 [str(tools[1]),'format','dos','com','option','quiet','file',name+'.OBJ','name',name+'.COM','option','map='+name+'.MAP']):
        result=subprocess.run(call,cwd=out,capture_output=True,text=True)
        logs.append(result.stdout+result.stderr)
        if result.returncode:raise ValueError(logs[-1])
    assert len((out/(name+'.COM')).read_bytes())<10000
(out/'BUILD.LOG').write_bytes('\r\n'.join(logs).encode())
report={'status':'HOST BUILT ONLY; no emulator launched','original_test_helpers':True,
        'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir() if p.suffix in ('.ASM','.COM')},
        'tools':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in tools}}
(out/'BUILD.JSON').write_bytes(json.dumps(report,indent=2).replace('\n','\r\n').encode())
print(json.dumps(report,indent=2))
