"""Assemble the reviewed Cube runtime and first-party source; no native tools or network."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import argparse,hashlib,io,json,re,subprocess,zipfile
HERE=Path(__file__).resolve().parent;APP=HERE.parent;ROOT=HERE.parents[2]
def pin(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def archive(files):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED)as z:
        for name,data in sorted(files.items()):
            item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.create_system=0;item.external_attr=0x20
            z.writestr(item,data)
    return stream.getvalue()
def build(out,commit,review=False):
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Full source commit required')
    known=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if known!=commit:raise ValueError('Source must be the current reviewed checkout commit')
    changed=subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=all','--','examples/CUBE','examples/TSHELL','tools/SOUNDOWN','tools/DOSINST/CRCFAST.H'],text=True)
    if changed.strip():raise ValueError('Commit the closed source/runtime/evidence before packaging')
    acceptance=json.loads((APP/'ACCEPT.JSN').read_bytes())
    SourceFileLoader('cube_acceptance',str(HERE/'VERIFY.PY')).load_module().verify(review)
    if not review and acceptance.get('status')!='READY_FOR_PUBLICATION_APPROVAL':raise ValueError('Native qualification/review incomplete')
    runtime={n:(APP/'BIN'/n).read_bytes()for n in ('CUBE.EXE','CUBESHL.EXE','CUBESET.EXE','TSINPUT.DLL')}
    for n,data in runtime.items():
        if pin(data)!=acceptance['runtime'][n]:raise ValueError('Native runtime identity differs: '+n)
    runtime['README.TXT']=(APP/'README.TXT').read_bytes()
    runtime['TESTS.TXT']=(APP/'TESTS.MD').read_bytes()
    for n in runtime:
        stem,dot,ext=n.partition('.')
        if len(stem)>8 or len(ext)>3:raise ValueError('Non-DOS runtime name')
    source={'SOURCE/.gitattributes':b'* -text\r\n','BUILDSRC.TXT':(APP/'BUILDSRC.TXT').read_bytes()}
    # Closed first-party source closure. No DDK/SDK libraries or installed OS files.
    for folder in (HERE,ROOT/'examples/TSHELL'):
        for path in folder.rglob('*'):
            if path.is_file()and path.suffix.upper()in('.C','.H','.PY','.ASM','.BAT','.DEF','.RSP'):
                source['SOURCE/'+path.relative_to(ROOT).as_posix()]=path.read_bytes()
    for relative in ('tools/SOUNDOWN/BUILDAPP.PY','tools/SOUNDOWN/RUNDOS.PY','tools/DOSINST/CRCFAST.H','examples/TSHELL/TESTS/CONFIG/TESTCFG.C'):
        source['SOURCE/'+relative]=(ROOT/relative).read_bytes()
    for n,p in acceptance['source'].items():
        if pin(source['SOURCE/'+n])!=p:raise ValueError('Source archive closure differs: '+n)
    for relative in ('examples/TSHELL/README.MD','examples/TSHELL/HISTORY.TXT','examples/TSHELL/DOS/README.TXT','examples/TSHELL/IDLE/README.MD'):
        source['SOURCE/'+relative]=(ROOT/relative).read_bytes()
    for path in APP.glob('*.MD'):source[path.name]=path.read_bytes()
    source['README.TXT']=(APP/'README.TXT').read_bytes();source['ACCEPT.JSN']=(APP/'ACCEPT.JSN').read_bytes()
    for path in sorted((APP/'EVIDENCE').rglob('*')):
        if path.is_file():
            if path.suffix.upper()in('.IMG','.DRV','.DLL','.EXE','.LIB','.OBJ'):raise ValueError('Private/foreign binary in evidence closure')
            source['EVIDENCE/'+path.relative_to(APP/'EVIDENCE').as_posix()]=path.read_bytes()
    record=dict(schema=1,source_commit=commit,status='REVIEW_CANDIDATE'if review else acceptance['status'],
                qualification='See TESTS.MD and ACCEPT.JSN; not all adapters/modes or physical hardware qualified',
                runtime={n:pin(b)for n,b in runtime.items()},source={n:pin(b)for n,b in source.items()})
    source['SOURCE.JSN']=(json.dumps(record,indent=2,sort_keys=True)+'\r\n').encode('ascii')
    files={'CUBE.ZIP':archive(runtime),'CUBESRC.ZIP':archive(source)}
    record['artifacts']={n:pin(b)for n,b in files.items()}
    files['CUBE.JSN']=(json.dumps(record,indent=2,sort_keys=True)+'\r\n').encode('ascii')
    files['CUBE.SHA']=''.join(pin(b)['sha256']+'  '+n+'\r\n'for n,b in sorted(files.items())).encode('ascii')
    out.mkdir(parents=True,exist_ok=False)
    for n,b in files.items():(out/n).write_bytes(b)
    print(json.dumps(record['artifacts']))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--commit',required=True);p.add_argument('--review',action='store_true');a=p.parse_args()
    build(a.out.resolve(),a.commit,a.review)
