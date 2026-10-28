"""Fresh CGA producer corruption guards and independent source-ZIP rebuild.

No emulator is started. Native original-media Setup is a separate required gate.
"""
import argparse,json,shutil,subprocess,sys,zipfile
from pathlib import Path
import FRESHPK as P

def refused(fn):
    try:fn()
    except ValueError:return True
    raise AssertionError('Invalid input was accepted')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','build','packet','watcom','out'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=a.repo.resolve();built=a.build.resolve();packet=a.packet.resolve()
    original,fresh=P.inputs(repo)
    with zipfile.ZipFile(packet/'CGAFRESH.ZIP') as z:
        assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()}
    assert all(files[n]==b for n,b in original.items() if n!='README.TXT')
    assert files['CGAOLD.TXT']==original['README.TXT']
    assert files['README.TXT']==files['FRESH.TXT']
    assert {n[9:]:b for n,b in files.items() if n.startswith('FRESH640/')}==fresh
    assert files['FRESH.EXE']==(built/'FRESH.EXE').read_bytes()
    assert all(len(part.split('.')[0])<=8 and ('.' not in part or len(part.rsplit('.',1)[1])<=3)
               for n in files for part in n.split('/'))
    r=dict(accepted_base_members_preserved=len(original)-1,original_readme_preserved_as='CGAOLD.TXT',fresh_instructions_are_root_readme=True,closed_fresh_inventory=True,dos_83_names=True)
    for sig in (b'PE',b'NE',b'LE',b'LX'):
        bad=b'MZ'+b'\0'*58+(64).to_bytes(4,'little')+sig
        r[sig.decode()+'_refused']=refused(lambda:P.dos_exe(bad))
    r['oversized_launcher_refused']=refused(lambda:P.dos_exe(b'MZ'+b'\0'*40000))
    base=out/'changed-base'/P.BASE;base.parent.mkdir(parents=True);base.write_bytes(b'changed')
    r['changed_base_refused']=refused(lambda:P.inputs(out/'changed-base'))
    shutil.copytree(built,out/'changed-build')
    exe=out/'changed-build/FRESH.EXE';exe.write_bytes(exe.read_bytes()+b'changed')
    r['changed_launcher_refused']=refused(lambda:P.pack(repo,out/'changed-build',out/'bad-pack'))
    assert not (out/'bad-pack').exists()
    with zipfile.ZipFile(packet/'CGAFSRC.ZIP') as z:
        assert z.testzip() is None;z.extractall(out/'source')
    subprocess.run([sys.executable,str(out/'source/src/cga/FRESHPK.PY'),'build','--repo',str(out/'source'),
                    '--watcom',str(a.watcom.resolve()),'--out',str(out/'rebuild')],check=True)
    assert (out/'rebuild/FRESH.EXE').read_bytes()==(built/'FRESH.EXE').read_bytes()
    r['standalone_source_rebuild_identical']=True;r['launcher']=P.identity((built/'FRESH.EXE').read_bytes())
    r['emulator_started']=False;P.receipt(out/'RESULT.JSN',r);print(json.dumps(r,indent=2))

if __name__=='__main__':main()
