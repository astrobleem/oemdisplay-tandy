"""Focused negative checks of the real accepted-byte publication boundary."""
from pathlib import Path
import argparse,copy,importlib.machinery,json,tempfile
HERE=Path(__file__).resolve().parent
P=importlib.machinery.SourceFileLoader('unified_gate_under_test',str(HERE/'PUBLISH.PY')).load_module()
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
original=HERE/'ACCEPT.JSN';q=json.loads(original.read_bytes());checks=[]
P.products();checks.append('qualified inputs and all four closed member inventories accepted')

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

bad=copy.deepcopy(q);bad['native'].pop('fixed_window');refused(bad,'coverage incomplete');checks.append('missing backend acceptance refused')
bad=copy.deepcopy(q);bad['native']['pcjr']['result']=q['native']['hpxy']['result'];refused(bad,'Native check failed: pcjr');checks.append('unrelated passing native result cannot stand in for the required run')
bad=copy.deepcopy(q);bad['installer_checks'][0]['leases']=[];refused(bad,'leases missing');checks.append('installer declarations without owned clean native leases refused')
bad=copy.deepcopy(q);target=bad['installer_checks'][0];receipt=json.loads(P.exact(target['receipt']));receipt['installed_helpers']={}
rb=json.dumps(receipt).encode();result=dict(outcome='PASS_NATIVE_INSTALLER_TRANSACTION',receipt=P.identity(rb));resultb=json.dumps(result).encode()
target['receipt']=dict(path='TEST-RECEIPT',identity=P.identity(rb));target['result']=dict(path='TEST-RESULT',identity=P.identity(resultb))
refused(bad,'output inventory incomplete',{'TEST-RECEIPT':rb,'TEST-RESULT':resultb});checks.append('internally matched installer records with empty output observations refused')
old_root=P.ROOT
with tempfile.TemporaryDirectory(prefix='upan-changed-') as temp:
    folder=Path(temp);P.ROOT=folder;b=b'original';(folder/'INPUT').write_bytes(b'changed')
    try:
        try:P.exact(dict(path='INPUT',identity=P.identity(b)))
        except ValueError as error:assert 'Changed qualified input' in str(error)
        else:raise AssertionError('Changed source/runtime input accepted')
    finally:P.ROOT=old_root
checks.append('changed pinned source/runtime input refused')
a.out.write_text(json.dumps(dict(outcome='PASS_HOST_PUBLICATION_GUARDS',checks=checks),indent=2));print('\n'.join(checks))
