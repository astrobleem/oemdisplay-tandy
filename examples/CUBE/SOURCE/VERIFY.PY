"""Verify Cube's closed build/source/runtime identities and native receipts."""
from pathlib import Path
import argparse,hashlib,json,re,zlib
APP=Path(__file__).resolve().parents[1];ROOT=APP.parents[1]
ROLES={'low','mono','tandy','virtual','cgapan','t6404','cga320','t160','ui','installer'}
def pin(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def verify(review=False):
    a=json.loads((APP/'ACCEPT.JSN').read_bytes())
    if a['status']!='READY_FOR_PUBLICATION_APPROVAL'and not review:raise ValueError('Cube qualification/review is incomplete')
    if set(a['runtime'])!={'CUBE.EXE','CUBESHL.EXE','CUBESET.EXE','TSINPUT.DLL'}:raise ValueError('Runtime inventory differs')
    for n,p in a['runtime'].items():
        if pin((APP/'BIN'/n).read_bytes())!=p:raise ValueError('Runtime differs: '+n)
    expected={p.relative_to(ROOT).as_posix()for folder in (APP/'SOURCE',ROOT/'examples/TSHELL')for p in folder.rglob('*')if p.is_file()and p.suffix.upper()in('.C','.H','.PY','.ASM','.DEF','.RSP','.BAT')}
    if set(a['source'])!=expected:raise ValueError('Source inventory is incomplete or stale')
    for n,p in a['source'].items():
        path=(ROOT/n).resolve()
        if not path.is_relative_to(ROOT)or pin(path.read_bytes())!=p:raise ValueError('Source differs: '+n)
    for n,p in a['receipts'].items():
        path=(APP/n).resolve()
        if not path.is_relative_to(APP/'EVIDENCE')or pin(path.read_bytes())!=p:raise ValueError('Receipt differs: '+n)
    def receipt(name):
        n='EVIDENCE/BUILD/'+name+'.JSN'
        if n not in a['receipts']:raise ValueError('Build receipt not pinned: '+name)
        return json.loads((APP/n).read_bytes())
    sources={}
    def source(name,want):
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT)or pin(path.read_bytes())!=want:raise ValueError('Stale build source: '+name)
        sources[name]=want
    cube,shell,idle,install=(receipt(n)for n in ('CUBE','SHELL','INPUT','INSTALL'))
    for n,actual in [('CUBE.EXE',cube['runtime']),('CUBESHL.EXE',shell['runtime']['TSHELL.EXE']),('TSINPUT.DLL',idle['runtime']),('CUBESET.EXE',install['runtime'])]:
        if actual!=a['runtime'][n]:raise ValueError('Build/runtime identity differs: '+n)
    required={'CUBE.C','CUBECORE.C','CUBECORE.H','CUBERECT.H','CUBE.DEF','CUBE.RSP','BUILD.BAT','CUBECTL.C','CUBECTL.DEF','CUBECTL.RSP'}
    if set(cube['source'])!=required:raise ValueError('Incomplete Cube build source inventory')
    for n,p in cube['source'].items():source('examples/CUBE/SOURCE/'+n,p)
    shellnames={}
    for n,p in shell['source_pins'].items():
        prefix='unified/oemdisplay-tandy/'
        if not n.startswith(prefix):raise ValueError('Unexpected shell build source root')
        name=n[len(prefix):]
        if not name.startswith('examples/TSHELL/'):raise ValueError('Unexpected shell build source')
        source(name,p);shellnames[name]=p
    if not {'TSHELL.C','TSSAVER.C','TSSAVCFG.C','SCFGCORE.C','SCFGCORE.H','TSHOLD.C','TSHELL.DEF','TSHELL.RSP','BUILD.BAT','PSGOWN.H'}.issubset({Path(n).name for n in shellnames}):raise ValueError('Incomplete shell build source inventory')
    if not {'TSINPUT.C','TSINPUT.H','TSINPUT.DEF','TSINPUT.RSP','LIBENTRY.ASM','BUILD.BAT'}.issubset(idle['source']):raise ValueError('Incomplete input build source inventory')
    for n,p in idle['source'].items():source('examples/TSHELL/IDLE/'+n,p)
    bind=receipt('SRCBIND')
    if bind['status']!='PASS'or bind['sources']!=sources or bind['runtime']!=a['runtime']:raise ValueError('Native source/runtime binding differs')
    for n,p in [('examples/CUBE/SOURCE/BUILD.PY',cube['builder']),('tools/SOUNDOWN/RUNDOS.PY',cube['guard']),('examples/TSHELL/BUILD.PY',shell['build_wrapper']),('tools/SOUNDOWN/BUILDAPP.PY',shell['shared_builder']),('tools/SOUNDOWN/RUNDOS.PY',shell['guard'])]:
        if pin((ROOT/n).read_bytes())!=p:raise ValueError('Stale native build recipe: '+n)
    ins=receipt('INSSRC')
    if ins['status']!='PASS'or ins['source']!=pin((APP/'SOURCE/CUBESET.C').read_bytes())or ins['crc_header']!=pin((ROOT/'tools/DOSINST/CRCFAST.H').read_bytes())or ins['runtime']!=a['runtime']['CUBESET.EXE']:raise ValueError('Installer source binding differs')
    for tag,name in [('CUBE','CUBE.EXE'),('SHELL','CUBESHL.EXE'),('IDLE','TSINPUT.DLL')]:
        want=dict(a['runtime'][name],crc32=zlib.crc32((APP/'BIN'/name).read_bytes()))
        if install['pins'][tag]!=want:raise ValueError('Installer payload binding differs: '+tag)
    if not review:
        roles=a['native']
        if not ROLES.issubset(roles):raise ValueError('Required advertised native scope missing')
        for role,row in roles.items():
            if row['receipt']not in a['receipts']or row['prepare_receipt']not in a['receipts']:raise ValueError('Native evidence is not pinned: '+role)
            prep=json.loads((APP/row['prepare_receipt']).read_bytes());r=json.loads((APP/row['receipt']).read_bytes())
            if prep['payload']['CUBE.EXE']!=a['runtime']['CUBE.EXE']['sha256']:raise ValueError('Prepared Cube identity differs: '+role)
            for target,payload in [('WINXT/CUBE.EXE','CUBE.EXE'),('WINDOWS/TSHELL.EXE','CUBESHL.EXE'),('WINDOWS/TSINPUT.DLL','TSINPUT.DLL')]:
                if r['installed'][target]!=a['runtime'][payload]:raise ValueError('Installed identity differs: '+role+' '+target)
            if role=='low'and 'START width=160 height=100 colors=16 'not in r['native_log']:raise ValueError('Low-resolution scope missing')
            if role=='mono'and not re.search(r'colors=2(?: |$)',r['native_log']):raise ValueError('Monochrome scope missing')
            if role in ('virtual','cgapan')and ('view=160,28,'not in r['native_log']or not re.search(r'VIEWPORT SET 160,28 \d+x\d+ logical=\d+x\d+',r['ui_log'])):raise ValueError('Nonzero viewport scope missing')
            if r['status']!='PASS'or r.get('owned_stopped')is not True or r.get('lease_released')is not True or str(r.get('inventory_after'))!='0':raise ValueError('Native execution/cleanup missing: '+role)
            if row['cube_sha256']!=a['runtime']['CUBE.EXE']['sha256']:raise ValueError('Native Cube identity differs: '+role)
            if role=='ui':
                if r['settings']!=dict(choice='Cube',enabled=1,idle_seconds=10):raise ValueError('Actual saved UI settings differ')
                if prep['payload']['TSINPUT.DLL']!=a['runtime']['TSINPUT.DLL']['sha256']or row['shell_sha256']!=a['runtime']['CUBESHL.EXE']['sha256']:raise ValueError('UI shell identity differs')
                for event in ('UI SAVE PASS','UI PREVIEW RETURN PASS','UI PREVIEW OWNER PASS','UI SHELL SAVE PASS','UI IDLE CUBE PASS','UI DONE PASS'):
                    if event not in r['ui_log']:raise ValueError('UI event absent: '+event)
            elif role=='installer':
                if prep['install_guards']is not True or 'Unrecognized'not in r['unknown_guard_log']or 'Standalone installed'not in r['standalone_guard_log']or r['installed']['CUBE/AFTERSH.EXE']['sha256']!=hashlib.sha256(b'UNKNOWN\r\n').hexdigest():raise ValueError('Unknown-file/standalone guards missing')
                if prep['payload']['CUBESET.EXE']!=a['runtime']['CUBESET.EXE']['sha256']or row['installer_sha256']!=a['runtime']['CUBESET.EXE']['sha256']or row.get('undo_reinstall')is not True or 'Original Tandy Start/input restored'not in r['undo_log']or 'Installed.'not in r['reinstall_log']:raise ValueError('Final installer acceptance missing')
            else:
                log=r['native_log']
                if 'QA DONE PASS'not in log or 'QA HELD PASS'not in log or len(re.findall(r'PIXEL source=16777215 target=16777215',log))!=6 or len(re.findall(r'QA step=\d+ frames=13 errors=0 leaks=0 capture=0 resources=0',log))!=6:raise ValueError('Native render/input/readback scope differs: '+role)
    return dict(status=a['status'],runtime=a['runtime'],native_roles=sorted(a['native']))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review',action='store_true');args=p.parse_args();print(json.dumps(verify(args.review)))
