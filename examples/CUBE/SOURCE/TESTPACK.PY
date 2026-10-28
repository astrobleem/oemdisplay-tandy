"""Exercise review gating and exact-source/runtime/receipt tamper rejection. No emulator."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import argparse,json,shutil,hashlib,zipfile
HERE=Path(__file__).resolve().parent;APP=HERE.parent;ROOT=HERE.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
target=out/'checkout';kit=target/'examples/CUBE';accept=json.loads((APP/'ACCEPT.JSN').read_bytes())
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
copy(APP/'ACCEPT.JSN',kit/'ACCEPT.JSN')
for n in accept['runtime']:copy(APP/'BIN'/n,kit/'BIN'/n)
for n in accept['source']:copy(ROOT/n,target/n)
for n in accept['receipts']:copy(APP/n,kit/n)
for n in ('tools/SOUNDOWN/RUNDOS.PY','tools/SOUNDOWN/BUILDAPP.PY','tools/DOSINST/CRCFAST.H'):copy(ROOT/n,target/n)
v=SourceFileLoader('cube_test_gate',str(HERE/'VERIFY.PY')).load_module();v.APP=kit;v.ROOT=target
checks=[]
def rejects(label,action,review):
    undo=action()
    try:
        try:v.verify(review)
        except (ValueError,FileNotFoundError,KeyError):checks.append(label)
        else:raise AssertionError('Gate accepted '+label)
    finally:undo()
def change(path):
    original=path.read_bytes();path.write_bytes(original+b'changed')
    return lambda:path.write_bytes(original)
def acceptance_change(change):
    path=kit/'ACCEPT.JSN';original=path.read_bytes();a=json.loads(original);change(a);path.write_text(json.dumps(a));return lambda:path.write_bytes(original)
v.verify(True);checks.append('intact review closure')
if accept['status']=='READY_FOR_PUBLICATION_APPROVAL':
    v.verify(False);checks.append('complete native gate')
rejects('missing native scope despite ready label',lambda:acceptance_change(lambda a:a.update(status='READY_FOR_PUBLICATION_APPROVAL',native={})),False)
if accept['status']!='READY_FOR_PUBLICATION_APPROVAL':
    rejects('incomplete qualification',lambda:lambda:None,False)
rejects('omitted source inventory',lambda:acceptance_change(lambda a:a['source'].pop(next(iter(a['source'])))),True)
rejects('runtime modification',lambda:change(kit/'BIN/CUBE.EXE'),True)
rejects('source modification',lambda:change(target/next(iter(accept['source']))),True)
def native_source_drift():
    path=target/'examples/CUBE/SOURCE/CUBE.C';original=path.read_bytes();changed=original.replace(b'((colors>0&&colors<=2)?2:1)',b'((colors>0&&colors<=2)?3:1)');assert changed!=original;path.write_bytes(changed)
    undo=acceptance_change(lambda a:a['source'].update({'examples/CUBE/SOURCE/CUBE.C':dict(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest())}))
    def restore():path.write_bytes(original);undo()
    return restore
rejects('source repinned without native rebuild',native_source_drift,True)
if accept['status']=='READY_FOR_PUBLICATION_APPROVAL':
    rejects('omitted advertised rendering role',lambda:acceptance_change(lambda a:a['native'].pop('t160')),False)
rejects('receipt modification',lambda:change(kit/next(iter(accept['receipts']))),True)
src=SourceFileLoader('cube_source_manifest_test',str(HERE/'TESTSRC.PY')).load_module()
helper='SOURCE/tools/SOUNDOWN/RUNDOS.PY';base={helper:b'guard source', 'ACCEPT.JSN':b'{}'}
manifest=dict(source={n:src.identity(b)for n,b in base.items()});base['SOURCE.JSN']=json.dumps(manifest).encode('ascii')
def packed(name,files):
    path=out/name
    with zipfile.ZipFile(path,'w',zipfile.ZIP_STORED)as z:
        for n,data in files.items():z.writestr(n,data)
    return path
src.inspect_archive(packed('intact.zip',base));checks.append('intact full source manifest')
for label,files in [('modified outside-acceptance helper',dict(base,**{helper:b'changed guard'})),('missing manifest member',{n:b for n,b in base.items()if n!=helper}),('extra archive member',dict(base,**{'unexpected.txt':b'extra'}))]:
    try:src.inspect_archive(packed('bad'+str(len(checks))+'.zip',files))
    except ValueError:checks.append(label)
    else:raise AssertionError('Source replay accepted '+label)
record=dict(status='PASS',scope='Packet integrity/gating only; no native qualification',checks=checks)
(out/'RESULT.JSN').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
