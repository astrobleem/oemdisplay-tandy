"""Host-only fresh catalog gate refusals; no emulator or publication."""
from pathlib import Path
import argparse,copy,importlib.machinery,io,json,zipfile
from unittest import mock
V=importlib.machinery.SourceFileLoader('fresh_gate_under_test',str(Path(__file__).with_name('VERIFY.PY'))).load_module()
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True,type=Path);a.add_argument('--path-only',action='store_true');a.add_argument('--candidate',action='store_true');v=a.parse_args();v.out.mkdir(parents=True,exist_ok=False)
    checks=[]
    def refused(name,fn):
        try:fn()
        except (ValueError,KeyError):checks.append(name);return
        raise AssertionError('Invalid gate input accepted: '+name)
    for path in (r'\Users\chad\outside.txt',r'C:relative.txt',r'C:\outside.txt',r'\\host\share\proof.txt',
                 '../escape.txt','/outside.txt','a/../../outside.txt'):
        refused('Unsafe evidence path refused: '+path,lambda p=path:V.exact(dict(path=p,identity=dict(bytes=0,sha256='0'*64))))
    if v.path_only:
        report=dict(status='PASS_FRESH_EVIDENCE_PATH_REFUSALS',checks=checks,native_gate_evaluated=False)
        (v.out/'RESULT.JSN').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return
    check=V.validate if v.candidate else V.reviewed
    q=json.loads((V.HERE/'ACCEPT.JSN').read_bytes());packet=check(q);checks.append('Exact native fresh packet accepted')
    refused('Changed packet refused',lambda:check(q,packet+b'changed'))
    for key in ('packet','source_packet','native_entry','native_completion','build','host','config')+(() if v.candidate else ('review',)):
        bad=copy.deepcopy(q);bad[key]['identity']['sha256']='0'*64
        refused('Changed '+key+' refused',lambda b=bad:check(b))
    bad=copy.deepcopy(q);bad['sources'].pop('src/cga/FRESH.C');refused('Missing launcher source binding refused',lambda:check(bad))
    bad=copy.deepcopy(q);bad['status']='ENTRY_ONLY';refused('Entry-only acceptance refused',lambda:check(bad))
    bad=copy.deepcopy(q);bad['physical_hardware']=True;refused('Physical-hardware claim refused',lambda:check(bad))
    bad=copy.deepcopy(q);bad['captures'].pop('first_start');refused('First-start capture missing refused',lambda:check(bad))
    original_exact=V.exact
    full=json.loads(original_exact(q['native_completion']))
    for key,value in [('complete_os_installation',False),('first_ordinary_win_r_start',False),
                      ('normal_dos_return',False),('original_media_unchanged',False),
                      ('driver_replaced_after_setup',True),('owned_stopped',False),('lease_released',False)]:
        broken=copy.deepcopy(full);broken[key]=value
        def fixture(row,b=broken):
            return json.dumps(b).encode() if row==q['native_completion'] else original_exact(row)
        with mock.patch.object(V,'exact',side_effect=fixture):
            refused('Incomplete native '+key+' refused',lambda:check(q))
    config=original_exact(q['config'])
    bad_config=config.replace(b'mem_size = 640',b'mem_size = 2048')
    with mock.patch.object(V,'exact',side_effect=lambda row:bad_config if row==q['config'] else original_exact(row)):
        refused('Expanded native memory refused',lambda:check(q))
    entry=json.loads(original_exact(q['native_entry']));entry['launcher']='0'*64
    with mock.patch.object(V,'exact',side_effect=lambda row:json.dumps(entry).encode() if row==q['native_entry'] else original_exact(row)):
        refused('Different native-tested launcher refused',lambda:check(q))
    source=V.members(original_exact(q['source_packet']))
    for name in ('tools/DOSINST/CRCFAST.H','EXTRA.TXT'):
        changed=dict(source);changed[name]=b'changed'
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w')as z:
            for n,b in changed.items():z.writestr(n,b)
        with mock.patch.object(V,'exact',side_effect=lambda row,b=stream.getvalue():b if row==q['source_packet'] else original_exact(row)):
            refused('Changed source inventory/header refused: '+name,lambda:check(q))
    report=dict(status='PASS_FRESH_CANDIDATE_REFUSALS_PENDING_REVIEW' if v.candidate else 'PASS_FRESH_CATALOG_GATE_REFUSALS',checks=checks,packet=V.identity(packet),emulator_started=False,independent_review_required_for_catalog=True)
    (v.out/'RESULT.JSN').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
