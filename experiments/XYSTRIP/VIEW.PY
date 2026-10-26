"""Private integration views with exact Git objects and verified dependency lock."""
from pathlib import Path
import importlib.machinery,io,subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT.parent/'tandy-pan-integration'
m=importlib.machinery.SourceFileLoader('integration_deps',str(ROOT/'tools/BUILDDEPS/DEPS.PY')).load_module()
def git(repo,*args,input=None):
    return subprocess.run(['git','--no-replace-objects','--git-dir='+str(Path(repo)/'.git'),
        '--work-tree='+str(repo),'-c','protocol.allow=never',*args],input=input,
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
def blobs(repo,rows):
    items=sorted(rows.items())
    b=io.BytesIO(git(repo,'cat-file','--batch',input=''.join(v[2]+'\n' for n,v in items).encode()))
    data={}
    for name,(mode,kind,oid) in items:
        assert mode in ('100644','100755') and kind=='blob'
        header=b.readline().decode().split();assert header[:2]==[oid,'blob']
        data[name]=b.read(int(header[2]));assert b.read(1)==b'\n'
    assert not b.read()
    return data
m.git=git;m.blobs=blobs
m.main(['view','--lock',str(ROOT/'tools/BUILDDEPS/LOCK.JSON'),'--deps',
    r'C:\Users\chad\Documents\Codex\2026-10-25\task-2\legacy-inputs',
    '--source-repo',str(ROOT),'--source-commit','8d48aa04560a4730c9ee3d946bed865ca9be0c43',
    '--profile','experiments','--out',str(OUT/'baseline-view')])
shutil.copytree(OUT/'baseline-view',OUT/'candidate-view')
for name in ['XYPAN.ASM','XYCOPY.ASM','XYPATCH.PY']:
    shutil.copyfile(ROOT/'experiments/XYPAN'/name,OUT/'candidate-view/experiments/XYPAN'/name)
p=OUT/'candidate-view/experiments/XYRRECT/XRBUILD.PY'
s=p.read_text();assert 'stage_bytes=1440' in s
p.write_bytes(s.replace('stage_bytes=1440','stage_bytes=2816').replace('\n','\r\n').encode('ascii'))
print('Staged isolated baseline/candidate views',OUT)
