"""Replay the actual source ZIP's inventory, committed bytes and host build closure."""
from pathlib import Path, PureWindowsPath
import argparse, hashlib, json, subprocess, sys, zipfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.archive)as z:
    names=z.namelist()
    if len(names)!=len(set(names))or z.testzip()is not None:raise ValueError('Invalid source ZIP')
    for n in names:
        if Path(n).is_absolute()or PureWindowsPath(n).drive or '..'in Path(n).parts or '..'in PureWindowsPath(n).parts:raise ValueError('Unsafe source member')
    z.extractall(out)
root=out/'SOURCE';accept=json.loads((out/'ACCEPT.JSN').read_bytes())
manifest=json.loads((out/'SOURCE.JSN').read_bytes())
for args in (['init','-q'],['add','.'],['-c','user.name=SourceTest','-c','user.email=source-test@example.invalid','commit','-qm','source']):
    subprocess.run(['git','-C',str(root),*args],check=True)
checked={}
for name,want in accept['source'].items():
    path=(root/name).resolve()
    if not path.is_relative_to(root):raise ValueError('Unsafe declared source')
    data=path.read_bytes();actual=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if actual!=want:raise ValueError('Source archive differs: '+name)
    if subprocess.check_output(['git','-C',str(root),'show','HEAD:'+name])!=data:raise ValueError('Committed source bytes differ: '+name)
    checked[name]=actual
subprocess.run([sys.executable,str(root/'examples/CUBE/SOURCE/RUNHOST.PY'),'--out',str(out/'HOST')],check=True)
host=json.loads((out/'HOST/RESULT.JSON').read_bytes())
if host['status']!='PASS':raise ValueError('Extracted source host checks failed')
result=dict(status='PASS',scope='Actual source archive/build closure; not new native qualification',producer_commit=manifest['source_commit'],archive_sha256=hashlib.sha256(a.archive.read_bytes()).hexdigest(),checked_sources=checked,host_checks=host['checks'])
(out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(checked),'closed source files, committed bytes and host checks')
