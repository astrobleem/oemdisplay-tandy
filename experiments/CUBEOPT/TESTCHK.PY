"""Reject source drift, receipt tampering and accidental release promotion."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    root=out/'checkout';candidate=root/'experiments/CUBEOPT';candidate.mkdir(parents=True)
    manifest=json.loads((HERE/'CANDIDAT.JSN').read_bytes())
    def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    copy(HERE/'CANDIDAT.JSN',candidate/'CANDIDAT.JSN')
    for n in manifest['source']:copy(HERE/'SOURCE'/n,candidate/'SOURCE'/n)
    copy(HERE/'EVIDENCE/INDEPENDENT/CUBE-BEFORE.C',candidate/'EVIDENCE/INDEPENDENT/CUBE-BEFORE.C')
    for n in set(manifest['accepted_files'])|set(manifest['receipts']):copy(ROOT/n,root/n)
    gate=SourceFileLoader('isolated_cube_candidate_gate',str(HERE/'CHECK.PY')).load_module()
    checks=[]
    gate.verify(root,candidate);checks.append('intact partial native candidate')
    def rejects(label,action):
        undo=action()
        try:
            try:gate.verify(root,candidate)
            except (ValueError,FileNotFoundError,KeyError):checks.append(label)
            else:raise AssertionError('Candidate check accepted '+label)
        finally:undo()
    def change(path):
        old=path.read_bytes();path.write_bytes(old+b'changed');return lambda:path.write_bytes(old)
    def edit_manifest(edit):
        path=candidate/'CANDIDAT.JSN';old=path.read_bytes();value=json.loads(old);edit(value);path.write_text(json.dumps(value));return lambda:path.write_bytes(old)
    rejects('changed native header',lambda:change(candidate/'SOURCE/CUBERECT.H'))
    def repin():
        path=candidate/'SOURCE/CUBERECT.H';old=path.read_bytes();path.write_bytes(old+b'/* drift */\r\n');data=path.read_bytes()
        undo=edit_manifest(lambda m:m['source'].update({'CUBERECT.H':dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())}))
        def restore():path.write_bytes(old);undo()
        return restore
    rejects('source repinned without native rebuild',repin)
    rejects('modified native receipt',lambda:change(root/manifest['native_build']))
    rejects('modified accepted recipe',lambda:change(root/'examples/CUBE/SOURCE/BUILD.PY'))
    rejects('unqualified candidate relabeled ready',lambda:edit_manifest(lambda m:m.update(status='READY_FOR_PUBLICATION_APPROVAL')))
    rejects('omitted candidate source',lambda:edit_manifest(lambda m:m['source'].pop('CUBERECT.H')))
    rejects('missing native input binding',lambda:edit_manifest(lambda m:m['receipts'].pop(m['native_build'])))
    selected='examples/CUBE/EVIDENCE/RNDTR5/runtime-tr51616-selected/STYLE1-STEP0-N2-P55.PNG'
    rejects('modified scanout capture',lambda:change(root/selected))
    record=dict(status='PASS',checks=checks,scope='Candidate integrity/tamper controls; no new native execution')
    (out/'RESULT.JSN').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
