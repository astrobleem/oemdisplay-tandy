"""Verify public bytes and replay the saved post-integration pixel oracle."""
from pathlib import Path
import importlib.machinery,json,tempfile,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P=importlib.machinery.SourceFileLoader('sp_package',str(HERE/'PACKAGE.PY')).load_module()
C=importlib.machinery.SourceFileLoader('sp_oracle',str(ROOT/'src/softpan/SPCHK.PY')).load_module()
P.verify(ROOT/'downloads/experimental/SOFTPAN')
spec=json.loads((HERE/'PUBLIC.JSN').read_bytes())
qpath=ROOT/'docs/SOFTPAN/PUBLISH/QUALIFY.JSON';q=json.loads(qpath.read_bytes())
U=importlib.machinery.SourceFileLoader('sp_native_settings',str(ROOT/'src/panui/VERIFY.PY')).load_module()
ui,binaries=U.verify()
assert spec['qualification']['ui_update']=={'path':'docs/QUAL/WDESK/NATIVE.JSN',
    'manifest':P.identity((ROOT/'docs/QUAL/WDESK/NATIVE.JSN').read_bytes())}
assert q['pass'] and q['main']=='d12ba426faba8b79575f44a9b48e241420944590'
assert P.identity(qpath.read_bytes())==spec['qualification']['manifest']
support_pin=spec['qualification']['support_update']
support_bytes=(ROOT/support_pin['path']).read_bytes()
assert P.identity(support_bytes)==support_pin['manifest']
support=json.loads(support_bytes)
assert support['pass'] and support['native_install']['phase']==6
assert support['native_install']['installed_grabber_sha256']==P.identity(P.supplied_grabber())['sha256']
assert support['native_install']['installed_driver_sha256']==q['drivers']['CPPAN']['sha256']
for kind,adapter in [('JRPAN','pcjr'),('CPPAN','colorplus')]:
    payload=HERE/'PAYLOAD'/kind
    assert P.identity((payload/(kind+'.DRV')).read_bytes())==q['drivers'][kind]
    for n in ('XTPAN.EXE','PANCFG.EXE'):
        assert (payload/n).read_bytes()==binaries[n]
    record=q['profiles'][kind]
    assert record['native_install']['phase']==6 and record['native_rollback']['phase']==6
    assert record['native_install']['driver_matches_public_bytes']
    assert record['native_rollback']['driver_matches_public_bytes']
    archive=ROOT/record['frames_archive']
    assert P.identity(archive.read_bytes())==record['frames_identity']
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)
        with zipfile.ZipFile(archive) as z:
            for n in z.namelist():
                p=Path(n)
                assert not p.is_absolute() and '..' not in p.parts
                assert p.parts[0] in ('RUN1','RUN2')
            z.extractall(target)
        for i in (1,2):
            result=C.check(target/('RUN'+str(i)),payload/(kind+'.DRV'),adapter,write_images=False)
            assert result['pass'] and result['frames']==32
            assert result['assertions']['config_reenabled'] and result['assertions']['helper_reset_sync']
            assert result['driver_sha256']==q['drivers'][kind]['sha256']
    print('PASS '+kind+': public identities, native Setup/rollback, 64 frames, re-enable and viewport synchronization')
assert P.supplied_grabber()==(HERE/'PAYLOAD/CPPAN/CGA.GR2').read_bytes()
print('PASS public downloads reproduce exactly with the supplied CGA grabber')
