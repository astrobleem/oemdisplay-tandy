"""Verify Cube's closed native/source identities and honestly scoped native receipts."""
from pathlib import Path
import argparse,hashlib,json,re
APP=Path(__file__).resolve().parents[1];ROOT=APP.parents[1]
def pin(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def verify(review=False):
    a=json.loads((APP/'ACCEPT.JSN').read_bytes())
    if a['status']!='READY_FOR_PUBLICATION_APPROVAL'and not review:raise ValueError('Cube qualification/review is incomplete')
    for n,p in a['runtime'].items():
        if pin((APP/'BIN'/n).read_bytes())!=p:raise ValueError('Runtime differs: '+n)
    for n,p in a['source'].items():
        path=(ROOT/n).resolve()
        if not path.is_relative_to(ROOT)or pin(path.read_bytes())!=p:raise ValueError('Source differs: '+n)
    for n,p in a['receipts'].items():
        path=(APP/n).resolve()
        if not path.is_relative_to(APP/'EVIDENCE')or pin(path.read_bytes())!=p:raise ValueError('Receipt differs: '+n)
    if not review:
        roles=a['native']
        if not {'low','mono','tandy','virtual','ui','installer'}.issubset(roles):raise ValueError('Required native scope missing')
        for role,row in roles.items():
            if row['receipt']not in a['receipts']:raise ValueError('Native receipt is not pinned: '+role)
            if row['prepare_receipt']not in a['receipts']:raise ValueError('Native fixture is not pinned: '+role)
            prep=json.loads((APP/row['prepare_receipt']).read_bytes())
            r=json.loads((APP/row['receipt']).read_bytes())
            if prep['payload']['CUBE.EXE']!=a['runtime']['CUBE.EXE']['sha256']:raise ValueError('Prepared Cube identity differs: '+role)
            for target,payload in [('WINXT/CUBE.EXE','CUBE.EXE'),('WINDOWS/TSHELL.EXE','CUBESHL.EXE'),('WINDOWS/TSINPUT.DLL','TSINPUT.DLL')]:
                if r['installed'][target]!=a['runtime'][payload]:raise ValueError('Installed identity differs: '+role+' '+target)
            if role=='low'and 'START width=160 height=100 colors=16'not in r['native_log']:raise ValueError('Low-resolution scope missing')
            if role=='mono'and 'colors=2'not in r['native_log']:raise ValueError('Monochrome scope missing')
            if role=='virtual'and not re.search(r'VIEWPORT SET 160,28 \d+x\d+ logical=\d+x\d+',r['ui_log']):raise ValueError('Nonzero viewport scope missing')
            if r['status']!='PASS'or r.get('owned_stopped')is not True or r.get('lease_released')is not True or str(r.get('inventory_after'))!='0':raise ValueError('Native execution/cleanup missing: '+role)
            if row['cube_sha256']!=a['runtime']['CUBE.EXE']['sha256']:raise ValueError('Native Cube identity differs: '+role)
            if role=='ui':
                if prep['payload']['TSINPUT.DLL']!=a['runtime']['TSINPUT.DLL']['sha256']or row['shell_sha256']!=a['runtime']['CUBESHL.EXE']['sha256']:raise ValueError('UI shell identity differs')
                for text in ('UI SAVE PASS','UI SHELL SAVE PASS','UI IDLE CUBE PASS','UI DONE PASS'):
                    if text not in r['ui_log']:raise ValueError('UI event absent: '+text)
            elif role=='installer':
                if prep['payload']['CUBESET.EXE']!=a['runtime']['CUBESET.EXE']['sha256']or row['installer_sha256']!=a['runtime']['CUBESET.EXE']['sha256']or row.get('undo_reinstall')is not True or 'Original Tandy Start/input restored'not in r['undo_log']or 'Installed.'not in r['reinstall_log']:raise ValueError('Final installer acceptance missing')
            else:
                log=r['native_log']
                if 'QA DONE PASS'not in log or 'QA HELD PASS'not in log or len(re.findall(r'PIXEL source=16777215 target=16777215',log))!=6 or len(re.findall(r'QA step=\d+ frames=13 errors=0 leaks=0 capture=0 resources=0',log))!=6:raise ValueError('Native render/input/readback scope differs: '+role)
    return dict(status=a['status'],runtime=a['runtime'],native_roles=sorted(a['native']))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review',action='store_true');a=p.parse_args();print(json.dumps(verify(a.review)))
