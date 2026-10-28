"""Replay the source ZIP's complete manifest, committed bytes and host build closure."""
from pathlib import Path, PureWindowsPath
import argparse, hashlib, json, subprocess, sys, zipfile

def identity(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def inspect_archive(archive):
    with zipfile.ZipFile(archive)as z:
        names=z.namelist()
        if len(names)!=len(set(names))or z.testzip()is not None:raise ValueError('Invalid source ZIP')
        for n in names:
            if Path(n).is_absolute()or PureWindowsPath(n).drive or '..'in Path(n).parts or '..'in PureWindowsPath(n).parts:raise ValueError('Unsafe source member')
        files={n:z.read(n)for n in names}
    manifest=json.loads(files['SOURCE.JSN'])
    if set(files)!=set(manifest['source'])|{'SOURCE.JSN'}:raise ValueError('Source archive member inventory differs')
    for name,want in manifest['source'].items():
        if identity(files[name])!=want:raise ValueError('Source archive member differs: '+name)
    return manifest,files

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();manifest,files=inspect_archive(a.archive)
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        target=(out/name).resolve()
        if not target.is_relative_to(out):raise ValueError('Unsafe extracted member')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    root=out/'SOURCE';accept=json.loads(files['ACCEPT.JSN'])
    for args in (['init','-q'],['add','.'],['-c','user.name=SourceTest','-c','user.email=source-test@example.invalid','commit','-qm','source']):
        subprocess.run(['git','-C',str(root),*args],check=True)
    checked={}
    for name,want in accept['source'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root):raise ValueError('Unsafe declared source')
        data=path.read_bytes();actual=identity(data)
        if actual!=want:raise ValueError('Source archive differs: '+name)
        if subprocess.check_output(['git','-C',str(root),'show','HEAD:'+name])!=data:raise ValueError('Committed source bytes differ: '+name)
        checked[name]=actual
    subprocess.run([sys.executable,str(root/'examples/CUBE/SOURCE/RUNHOST.PY'),'--out',str(out/'HOST')],check=True)
    host=json.loads((out/'HOST/RESULT.JSON').read_bytes())
    if host['status']!='PASS':raise ValueError('Extracted source host checks failed')
    result=dict(status='PASS',scope='Full archive manifest and actual source/build closure; not new native qualification',producer_commit=manifest['source_commit'],archive_sha256=identity(a.archive.read_bytes())['sha256'],validated_members=len(files),checked_sources=checked,host_checks=host['checks'])
    (out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(files),'manifest members;',len(checked),'closed sources, committed bytes and host checks')
if __name__=='__main__':main()
