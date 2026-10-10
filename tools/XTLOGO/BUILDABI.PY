"""Build original private DOS ABI capsules; does not execute them."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
def build(fonts,out,wasm,wlink):
    if out.exists():raise ValueError('Fresh output required')
    lgo=(fonts/'XTSTATIC.LGO').read_bytes();art=(fonts/'WXTSPL01.RLE').read_bytes()
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='static-abi-') as temporary:
        work=Path(temporary);(work/'ABI.ASM').write_bytes((HERE/'ABI.ASM').read_bytes())
        for call in ([str(wasm),'-0','-zcm=masm','-we','-fo=ABI.OBJ','ABI.ASM'],
                     [str(wlink),'format','dos','com','option','quiet','file','ABI.OBJ','name','ABI.COM']):
            r=subprocess.run(call,cwd=work,capture_output=True,text=True)
            if r.returncode:raise ValueError(r.stdout+r.stderr)
        raw=(work/'ABI.COM').read_bytes();assert raw[-4:]==b'LEND'
        raw=raw[:-4];assert (len(raw)+0x100)%16==0
        bad=bytearray(art);bad[62:64]=b'\0\2'
        for name,data in (('GOOD.COM',art),('BADRLE.COM',bytes(bad)),('TRUNC.COM',art[:62]+b'\0'*4000)):
            (out/name).write_bytes(raw+lgo+data)
    report={'status':'HOST BUILT ONLY; no native execution',
            'source_sha256':hashlib.sha256((HERE/'ABI.ASM').read_bytes()).hexdigest(),
            'capsules':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir())}}
    (out/'BUILDABI.JSON').write_bytes((json.dumps(report,indent=2)+'\n').replace('\n','\r\n').encode())
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fonts',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--wasm',type=Path,required=True)
    p.add_argument('--wlink',type=Path,required=True);a=p.parse_args()
    build(a.fonts.resolve(),a.out.resolve(),a.wasm.resolve(),a.wlink.resolve())
