"""Focused negative checks of the real accepted-byte publication boundary."""
from pathlib import Path
import argparse,copy,importlib.machinery,json,tempfile
HERE=Path(__file__).resolve().parent
P=importlib.machinery.SourceFileLoader('unified_gate_under_test',str(HERE/'PUBLISH.PY')).load_module()
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
original=HERE/'ACCEPT.JSN';q=json.loads(original.read_bytes());checks=[]
P.products();checks.append('qualified inputs and all five closed member inventories accepted')

def refused(candidate,reason,substitutions=None):
    old_here=P.HERE;old_exact=P.exact
    with tempfile.TemporaryDirectory(prefix='upan-gate-') as temp:
        folder=Path(temp);(folder/'ACCEPT.JSN').write_text(json.dumps(candidate));P.HERE=folder
        if substitutions:
            def substituted(row):
                if row['path'] in substitutions:
                    b=substitutions[row['path']];assert P.identity(b)==row['identity'];return b
                return old_exact(row)
            P.exact=substituted
        try:
            try:P.qualification()
            except ValueError as error:assert reason in str(error),str(error)
            else:raise AssertionError('Incomplete acceptance was allowed')
        finally:P.HERE=old_here;P.exact=old_exact

bad=copy.deepcopy(q);bad['status']='PENDING';refused(bad,'acceptance pending');checks.append('pending acceptance refused')
bad=copy.deepcopy(q);bad['native'].pop('fixed_workspace');refused(bad,'coverage incomplete');checks.append('missing backend refused')
bad=copy.deepcopy(q);bad['native']['pcjr']['result']=q['native']['hpxy']['result'];refused(bad,'Native acceptance failed: pcjr');checks.append('unrelated passing result refused')
bad=copy.deepcopy(q);bad['raster'].pop('colorplus');refused(bad,'Both native software raster');checks.append('missing adapter raster refused')
bad=copy.deepcopy(q);bad['installer_checks']['core']['leases']=[];refused(bad,'lease missing');checks.append('unobserved installer declarations refused')
bad=copy.deepcopy(q);target=bad['installer_checks']['universal'];receipt=json.loads(P.exact(target['installed']));receipt['helpers']={}
rb=json.dumps(receipt).encode();result=dict(outcome='PASS_NATIVE_INSTALLER_TRANSACTION',installed_receipt=P.identity(rb));resultb=json.dumps(result).encode()
target['installed']=dict(path='TEST-INSTALLED',identity=P.identity(rb));target['result']=dict(path='TEST-RESULT',identity=P.identity(resultb))
refused(bad,'Different native installer helper bytes',{'TEST-INSTALLED':rb,'TEST-RESULT':resultb});checks.append('internally matched empty installed inventory refused')
bad=copy.deepcopy(q);target=bad['native']['pcjr'];receipt=json.loads(P.exact(target['installed']));receipt['driver']=q['drivers']['CPPAN.DRV']['identity']
rb=json.dumps(receipt).encode();result=json.loads(P.exact(target['result']));result['installed_receipt']=P.identity(rb);resultb=json.dumps(result).encode()
target['installed']=dict(path='TEST-INSTALLED',identity=P.identity(rb));target['result']=dict(path='TEST-RESULT',identity=P.identity(resultb))
refused(bad,'Different native software driver bytes',{'TEST-INSTALLED':rb,'TEST-RESULT':resultb});checks.append('wrong adapter driver observation refused')
bad=copy.deepcopy(q);target=bad['native']['pcjr'];lease=json.loads(P.exact(target['lease']));lease['lease_released']=False;rb=json.dumps(lease).encode();target['lease']=dict(path='TEST-LEASE',identity=P.identity(rb))
refused(bad,'lease not completed',{'TEST-LEASE':rb});checks.append('unclean emulator lease refused')
bad=copy.deepcopy(q);target=bad['native']['pcjr'];lease=json.loads(P.exact(target['lease']));lease['children']=[];rb=json.dumps(lease).encode();target['lease']=dict(path='TEST-LEASE',identity=P.identity(rb))
refused(bad,'cleanup incomplete',{'TEST-LEASE':rb});checks.append('empty owned-process list refused')
old_root=P.ROOT
with tempfile.TemporaryDirectory(prefix='upan-changed-') as temp:
    folder=Path(temp);P.ROOT=folder;b=b'original';(folder/'INPUT').write_bytes(b'changed')
    try:
        try:P.exact(dict(path='INPUT',identity=P.identity(b)))
        except ValueError as error:assert 'Changed accepted input' in str(error)
        else:raise AssertionError('Changed source/runtime input accepted')
    finally:P.ROOT=old_root
checks.append('changed pinned source/runtime input refused')
a.out.write_text(json.dumps(dict(outcome='PASS_HOST_PUBLICATION_GUARDS',checks=checks),indent=2));print('\n'.join(checks))
