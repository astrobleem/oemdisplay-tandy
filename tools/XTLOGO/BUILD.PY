"""Reproduce the original static LGO with an explicitly supplied host assembler."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ART=ROOT/'distributions/WINXT/WXTSPL01.RLE'
ART_SHA='eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c'
def sha(b):return hashlib.sha256(b).hexdigest()
def textfile(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def build(out,wasm,wlink):
    if out.exists():raise ValueError('Choose a fresh output directory')
    source=(HERE/'STATIC.ASM').read_bytes();art=ART.read_bytes()
    assert len(art)==4062 and sha(art)==ART_SHA
    assert b'\n' not in source.replace(b'\r\n',b'')
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='xt-static-') as temporary:
        work=Path(temporary);(work/'STATIC.ASM').write_bytes(source)
        calls=[[str(wasm),'-0','-zcm=masm','-we','-fo=STATIC.OBJ','STATIC.ASM'],
               [str(wlink),'format','raw','bin','option','quiet','file','STATIC.OBJ',
                'name','XTSTATIC.LGO','option','map=STATIC.MAP']]
        logs=[]
        for call in calls:
            result=subprocess.run(call,cwd=work,capture_output=True,text=True)
            logs.append(result.stdout+result.stderr)
            if result.returncode:raise ValueError('Build refused: '+logs[-1])
        lgo=(work/'XTSTATIC.LGO').read_bytes()
        assert lgo[:7]==b'LOGO\xe9\x29\x00'
        assert len(lgo)+len(art)+3456<=65280
        assert lgo[-62:]==art[:62]
        (out/'XTSTATIC.LGO').write_bytes(lgo)
        (out/'WXTSPL01.RLE').write_bytes(art)
        (out/'STATIC.MAP').write_bytes((work/'STATIC.MAP').read_bytes())
        textfile(out/'BUILD.LOG','\n'.join(logs))
    report={'baseline':'v0.1.0-rc.5','original_implementation':True,
            'native_qualified':False,'publication_allowed':False,
            'lgo_bytes':len(lgo),'lgo_sha256':sha(lgo),'rle_bytes':len(art),
            'rle_sha256':sha(art),'resident_bytes':48,'hide_offset':7,'show_offset':4,
            'private_com_bytes':3456+len(lgo)+len(art),
            'source_sha256':sha(source),
            'tools':{str(p):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in (wasm,wlink)}}
    textfile(out/'BUILD.JSON',json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--wasm',required=True,type=Path)
    parser.add_argument('--wlink',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.out.resolve(),args.wasm.resolve(),args.wlink.resolve()),indent=2))
