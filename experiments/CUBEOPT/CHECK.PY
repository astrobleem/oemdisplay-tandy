"""Bind partial native Cube evidence to isolated candidate source, never a release."""
from pathlib import Path, PureWindowsPath
import argparse, hashlib, json, re, subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
NATIVE={'CUBE.C','CUBECORE.C','CUBECORE.H','CUBERECT.H','CUBE.DEF','CUBE.RSP','BUILD.BAT','CUBECTL.C','CUBECTL.DEF','CUBECTL.RSP'}

def pin(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def committed(root,candidate,commit):
    head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    if commit!='HEAD'and commit!=head:raise ValueError('Candidate must match the reviewed commit')
    a=json.loads((candidate/'CANDIDAT.JSN').read_bytes());prefix=candidate.relative_to(root).as_posix()+'/'
    paths=set(a['receipts'])|set(a['accepted_files'])|{prefix+'SOURCE/'+n for n in a['source']}
    paths|={prefix+n for n in('CANDIDAT.JSN','CHECK.PY','TESTCHK.PY','README.MD','EVIDENCE/INDEPENDENT/CUBE-BEFORE.C')}
    data=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-z',head,'--',*sorted(paths)])
    blobs={}
    for entry in data.split(b'\0'):
        if entry:
            info,name=entry.split(b'\t',1);mode,kind,sha=info.split();blobs[name.decode()]=sha.decode()
    for name in paths:
        raw=(root/name).read_bytes();sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blobs.get(name)!=sha:raise ValueError('Candidate input/evidence is not committed exactly: '+name)
    return dict(source_commit=head,committed_members=len(paths))

def exact(base,name,want):
    path=Path(name)
    if path.is_absolute()or PureWindowsPath(name).drive or '\\'in name or '..'in path.parts:raise ValueError('Unsafe manifest path: '+name)
    data=(base/path).read_bytes()
    if pin(data)!=want:raise ValueError('Identity differs: '+name)
    return data

def verify(root=ROOT,candidate=HERE):
    a=json.loads((candidate/'CANDIDAT.JSN').read_bytes())
    if a['schema']!=1 or a['status']!='PARTIAL_NATIVE_NOT_RELEASE':raise ValueError('Candidate must remain explicitly unqualified for release')
    expected={p.name for p in(candidate/'SOURCE').iterdir()if p.is_file()and p.suffix.upper()in('.C','.H','.PY','.DEF','.RSP','.BAT')}
    if set(a['source'])!=expected:raise ValueError('Candidate source inventory differs')
    for n,want in a['source'].items():exact(candidate/'SOURCE',n,want)
    exact(candidate,'EVIDENCE/INDEPENDENT/CUBE-BEFORE.C',a['control'])
    for n,want in a['accepted_files'].items():exact(root,n,want)
    # These are separate candidate pins. ACCEPT.JSN and all accepted runtime,
    # source and native receipt pins are verified by the unchanged release gate.
    for n,want in a['receipts'].items():exact(root,n,want)
    def receipt(n):
        if n not in a['receipts']:raise ValueError('Unpinned candidate receipt: '+n)
        return json.loads((root/n).read_bytes())
    build=receipt(a['native_build'])
    if set(build['source'])!=NATIVE:raise ValueError('Incomplete native input inventory')
    for n,want in build['source'].items():
        if a['source'].get(n)!=want:raise ValueError('Candidate source lacks native build binding: '+n)
    if build['runtime']!=a['runtime']or build['source_commit']!=a['native_tested_source_commit']:raise ValueError('Candidate runtime/build binding differs')
    for key in ('builder','guard'):
        n=a['native_'+key]
        if n not in a['receipts']:raise ValueError('Native recipe is not pinned')
        exact(root,n,build[key])
    accepted=json.loads((root/'examples/CUBE/ACCEPT.JSN').read_bytes())
    if a['runtime']==accepted['runtime']['CUBE.EXE']:raise ValueError('Candidate confused with accepted runtime')
    if set(a['native_modes'])!={'160x200x16','320x200x16'}:raise ValueError('Partial native scope differs')
    evidence='examples/CUBE/EVIDENCE/RNDTR5/'
    modes={}
    for mode,row in a['native_modes'].items():
        runs={}
        for variant in ('control','selected'):
            folder=evidence+row[variant]+'/'
            result=receipt(folder+'RESULT.JSON');prep=receipt(folder+'PREPARE.JSON')
            if result['status']!='PASS'or result.get('owned_stopped')is not True or result.get('lease_released')is not True:raise ValueError('Native cleanup missing: '+mode+' '+variant)
            if prep['environment']['display.drv']['sha256']!=row['driver']:raise ValueError('Native driver identity differs')
            if prep['cube']!=result['runtime']:raise ValueError('Prepared/native runtime binding differs')
            if variant=='selected'and(result['runtime']!=a['runtime']or prep['controller']!=build['controller']):raise ValueError('Selected native runtime differs')
            log=(root/(folder+'CUBE.LOG')).read_text()
            if folder+'CUBE.LOG'not in a['receipts']:raise ValueError('Native log is not pinned')
            cases=re.findall(r'QA step=\d+ frames=13 errors=0 leaks=0 capture=0 resources=0',log)
            if len(cases)!=6 or 'QA DONE PASS'not in log:raise ValueError('Native case scope differs')
            captures={Path(n).name:want for n,want in a['receipts'].items()if n.startswith(folder+'STYLE')and n.endswith('.PNG')}
            if len(captures)!=12:raise ValueError('Native capture scope differs')
            runs[variant]=dict(captures=captures,frames=78,environment=prep['environment'],cpu=prep['cpu'],memory_kb=prep['memory_kb'])
        if any(runs['control'][key]!=runs['selected'][key]for key in('environment','cpu','memory_kb')):raise ValueError('Native comparison conditions differ')
        if runs['control']['captures']!=runs['selected']['captures']:raise ValueError('Native scanout bytes differ')
        modes[mode]=dict(frames_per_variant=78,identical_capture_pairs=12,driver_sha256=row['driver'])
    return dict(status='PASS',qualification=a['status'],candidate_runtime=a['runtime'],source_count=len(a['source']),native_modes=modes,scope='Isolated source and partial native evidence integrity; accepted qualification remains separate')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--commit',default='HEAD');a=p.parse_args()
    result=verify();result.update(committed(ROOT,HERE,a.commit));a.out.mkdir(parents=True,exist_ok=False);(a.out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
