"""Strict rc.6 source/evidence/asset publication binding; no guest execution.

MIT, Copyright (c) 2026 Windows XT contributors.
Historical rc.5 font publication remains tools/XTFONTS/PUBLISH.PY.
"""
import argparse
import hashlib
import importlib.machinery as machinery
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for folder in (HERE, ROOT/'tools/XTFONTS'):
    sys.path.insert(0, str(folder))
    sys.path_importer_cache[str(folder)] = machinery.FileFinder(str(folder),
        (machinery.SourceFileLoader, machinery.SOURCE_SUFFIXES+['.PY']),
        (machinery.SourcelessFileLoader, machinery.BYTECODE_SUFFIXES),
        (machinery.ExtensionFileLoader, machinery.EXTENSION_SUFFIXES))
import TESTPKG
from BUILD import build, textfile
from ENCQA import emitted

ALIASES = {'CGASYS':'XTCSYS','CGAFIX':'XTCFIX','CGAOEM':'XTCOEM',
           'EGASYS':'XTESYS','EGAFIX':'XTEFIX','EGAOEM':'XTEOEM','TXTSYS':'XTTSYS'}
PACKAGE = {'WINXT720.IMG','WINXT720.ZIP','WXTTOOLS.ZIP','BUILD.JSON','README.TXT','SHA256SUMS'}
ASSETS = (PACKAGE-{'SHA256SUMS'}) | {'PKGSUMS.TXT','WINXT-RC6-SOURCE.zip',
    'WINXT-RC6-FONTS.zip','WINXT-RC6-PREVIEWS.zip','FONT-LICENSE.TXT',
    'START-HERE.TXT','QUALIFY.JSON','RELEASE.JSON','SHA256SUMS'}
FORBIDDEN = {'CGA.GR2','CGALOGO.LGO','CGASYS.FON','CGAFIX.FON','CGAOEM.FON',
    'EGASYS.FON','EGAFIX.FON','EGAOEM.FON','WIN.CNF','WIN.COM','KERNEL.EXE',
    'USER.EXE','GDI.EXE','SETUP.EXE','CL.EXE','LINK.EXE','LINK4.EXE','DOSBOX.EXE'}

def sha(data): return hashlib.sha256(data).hexdigest()
def check(value, message):
    if not value: raise ValueError(message)
def read(path):
    check(path.is_file() and not path.is_symlink() and path.stat().st_size<=67108864,
          'Missing/linked/oversized file '+str(path))
    return path.read_bytes()
def object_at(path): return json.loads(read(path))
def safe_name(name):
    p=Path(name)
    check(not p.is_absolute() and '..' not in p.parts and '\\' not in name
          and ':' not in name and not name.startswith('/') and p.name.upper() not in FORBIDDEN,
          'Forbidden source/resource '+name)
def zipped(path):
    with zipfile.ZipFile(path) as z:
        check(z.namelist()==sorted(set(z.namelist())) and not z.comment, 'ZIP order/duplicates')
        for i in z.infolist():
            safe_name(i.filename)
            check(i.date_time==(1980,1,1,0,0,0) and i.create_system==0 and
                  i.external_attr==0x20 and i.compress_type==zipfile.ZIP_STORED and
                  not i.extra and not i.comment and not i.flag_bits and i.file_size<=2097152,
                  'Unexpected ZIP metadata '+i.filename)
        return {i.filename:z.read(i) for i in z.infolist()}
def zipdata(path, files):
    with zipfile.ZipFile(path,'x') as z:
        for name,data in sorted(files.items()):
            safe_name(name)
            i=zipfile.ZipInfo(name,(1980,1,1,0,0,0));i.create_system=0
            i.external_attr=0x20;i.compress_type=zipfile.ZIP_STORED;z.writestr(i,data)

def qualification():
    q=object_at(ROOT/'docs/QUAL/RC6.JSON')
    check(q['release_tag']=='v0.1.0-rc.6' and q['publication_allowed'] is True
          and q['required_final_gates_pass'] is True, 'rc.6 release not authorized/qualified')
    check(q['native_implementation_qualified'] is True and
          q['documentation_pin_refresh_verified'] is True and
          q['refreshed_binary_rerun_in_guest'] is False and q['hardware_qualified'] is False,
          'Qualification scope changed')
    for n,h in q['source_pins'].items():
        safe_name(n);check(sha(read(ROOT/n))==h, 'Qualified source/evidence changed '+n)
    payload=TESTPKG.package.public_payload(ROOT/'distributions/WINXT')
    check(set(payload)==set(q['runtime_payload_pins']), 'Runtime allowlist changed')
    for n,p in q['runtime_payload_pins'].items():
        check(len(payload[n])==p['bytes'] and sha(payload[n])==p['sha256'], 'Qualified runtime changed '+n)
    helper=TESTPKG.package.helper_payload()
    check(sha(helper['PREPXT.EXE'])==q['helper_sha256'], 'Document-bound helper changed')
    binding=object_at(HERE/'DOCPINS/BIND.JSON')
    check(binding['native_base_sha256']==q['native_base_helper_sha256'] and
          binding['helper_sha256']==q['helper_sha256'] and
          binding['all_59_binary_pin_rows_match_source'] is True and
          binding['MZ_header_code_relocations_non_document_data_exact'] is True and
          {r['name'] for r in binding['changed_rows']}=={'MODEINFO.TXT','LOGOINFO.TXT','README.TXT','MANIFEST.SHA'},
          'Native implementation / document data boundary changed')
    ev=ROOT/'docs/QUAL/RC6EV'
    for n in ('PFAST','PZERO','PVERIFY'):
        r=object_at(ev/(n+'.JSON'))
        check(r['native_pass'] and r['runtime_and_owned_bytes_exact'] and
              r['Windows_and_boot_preimages_exact'] and r['DOS_KB']==624 and r['DOS_mode']==3,
              'Native preparation gate missing '+n)
    check(object_at(ev/'PZERO.JSON')['default_counters']==[0,0] and
          b'SHA blocks=0; output readback=0 bytes' in read(ev/'PZERO.LOG'), 'Default SHA/readback is not zero')
    check(b'Deep verification ON.' in read(ev/'PVERIFY.LOG') and
          b'SHA-256 self-test passed' in read(ev/'PVERIFY.LOG') and
          b'Verified C:\\WINXT\\XTSTATIC.LGO' in read(ev/'PVERIFY.LOG'), 'Explicit VERIFY evidence missing')
    for name,row,driver in [('SET6402',4,'TR56402.DRV'),('SETTEXT',5,'TXTMODE.DRV')]:
        r=object_at(ev/(name+'.JSON'))
        check(r['native_Setup_pass'] and r['row']==row and r['phase']==6 and
              r['actions']>=6 and r['common_bytes']==7879 and r['wave_unchanged'] and
              r['selected_boot']['display.drv']==driver and r['DOS_KB']==624 and r['DOS_mode']==3,
              'Native Setup gate missing '+name)
    first=object_at(ev/'MODE-FIRST.JSON');second=object_at(ev/'MODE-SECOND.JSON')
    check(first['checks']['native_new_installer_rollback']['pass'] and
          first['checks']['native_new_installer_rollback']['preimage_files']==120,
          'Native whole-installer rollback missing')
    check(all(first['graphics'][n]['pass'] and first['graphics'][n]['native_224_advances_exact']
              and all(first['graphics'][n]['raw_framebuffers_identical_to_prior_qualified_native_GDI'].values())
              for n in ('32016','6404','16016','3204')) and second['G6402']['pass'] and
          second['G6402']['native_advances_exact'] and all(second['G6402']['native_framebuffers_identical'].values()),
          'Saved five-mode GDI acceptance missing')
    guard=second['actual_Windows_launched_DOS_guard']
    check(guard['pass'] and guard['active_Windows_message_verified_for_each'] and
          guard['all_preimage_files_unchanged']==254 and len(guard['refused_commands'])==10 and
          guard['CHECK_again_succeeded_in_DOS'], 'Actual Windows-launched DOS guard missing')
    for n in ('PREP-LEASE','SETUP-FIRST-LEASE','SETUP-TEXT-LEASE'):
        lease=object_at(ev/(n+'.JSON'))
        check(lease['active']=='released' and lease['conflicts_after']==[], 'Native lease not cleaned up '+n)
    return q

def source_files(q):
    files={n:read(ROOT/n) for n in q['source_pins']}
    files['docs/QUAL/RC6.JSON']=read(ROOT/'docs/QUAL/RC6.JSON')
    return files
def fonts_files(q, generated):
    files={'LICENSE.TXT':read(ROOT/'tools/XTFONTS/LICENSE'),
           'README.MD':read(ROOT/'tools/XTFONTS/README.MD'),'MISSING.JSON':read(generated/'MISSING.JSON')}
    for old,new in ALIASES.items():
        raw=read(generated/(old+'.FON'))
        check(sha(raw)==q['runtime_payload_pins'][new+'.FON']['sha256'], 'Original font reproduction changed '+new)
        files[new+'.FON']=raw;files[new+'.FNT']=emitted(generated,old+'.FON')
    files['ALIASES.JSON']=(json.dumps({a+'.FON':b+'.FON' for a,b in ALIASES.items()},indent=2)+'\r\n').encode()
    return files
def previews():
    shots=ROOT/'docs/FONTS/SHOTS'
    return {p.name:read(p) for p in shots.iterdir() if p.is_file()}
def start_text():
    return TESTPKG.package.dos('''WINDOWS XT rc.6 - ORIGINAL FONTS, STATIC LOGO AND DOS MODE MENU

Use WINXT720.IMG (720 KB data disk) with your existing DOS/Windows 3.0.
Back up Windows first. From A: run INSTALL; give your owned support folder
when requested and confirm fresh C:\\WINXT staging. Then C: / CD \\WINXT /
INSTALL. Run C:\\WINXT\\WINXT SETUP, choose Other display, and use
C:\\WINXT at every source prompt. Complete Changes; CONFIG.SYS option 3
means no changes. Start with C:\\WINXT\\WINXT and keep its recovery guards.

After initial Setup, exit Windows and run C:\\WINXT\\MODES for the DOS mode
menu. U undoes the most recent switch. RECOVER runs before video reservation
at startup. Read MODEINFO.TXT and BACKUP.TXT before changing or restoring.
Whole-install rollback uses the numbered BACKUP\\B001\\RESTORE YES path
printed by INSTALL; use your actual backup number.

No vintage Python, Windows font media or CGALOGO.LGO is required. The fonts
and static module are original MIT work. DOS/Windows, Setup, WIN.CNF,
CGA.GR2 and other non-font Windows components remain yours and are excluded.
Normal preparation and startup skip SHA work. /VERIFY is an expensive
optional diagnostic. This candidate preserves the accepted Color wave.

Native emulator tests passed for the implementation. PREPXT's four document
pin rows were then refreshed reproducibly on the host; executable code,
MZ header and relocations are exact. That refreshed binary was not rerun
in a guest. QUALIFY.JSON records this scope. No physical hardware claim.
160-pixel stock dialogs can clip and small menus can wrap. TEXT is opt-in
and retains known extended/adjacent renderer corruption. See MISSING.JSON
for fallback encoding slots. No Unicode emoji or Euro extension is supplied.

WINXT-RC6-SOURCE.zip contains matching distributable sources and runtime.
WINXT-RC6-FONTS.zip contains original FON/FNT files and license/coverage.
WINXT-RC6-PREVIEWS.zip contains genuine saved native font captures, identified
by its README; host font specimens are generated by the source tools.
Checksums are for verification on a modern host.
Manual: https://github.com/astrobleem/oemdisplay-tandy/blob/v0.1.0-rc.6/docs/USERMAN.MD
''')
def package_checks(folder,q):
    check({p.name for p in folder.iterdir()}==PACKAGE, 'Package allowlist changed')
    TESTPKG.verify(folder)
    for n,h in q['package_sha256'].items(): check(sha(read(folder/n))==h, 'Qualified package differs '+n)

def make(package,out,commit):
    check(not out.exists(), 'Choose a fresh output directory')
    check(commit=='working-tree' or re.fullmatch('[0-9a-f]{40}',commit), 'Require exact commit')
    q=qualification();package_checks(package,q)
    with tempfile.TemporaryDirectory(prefix='rc6-publish-') as td:
        generated=Path(td)/'FONTS';build(generated);fonts=fonts_files(q,generated)
        out.mkdir(parents=True)
        for n in PACKAGE-{'SHA256SUMS'}: shutil.copyfile(package/n,out/n)
        shutil.copyfile(package/'SHA256SUMS',out/'PKGSUMS.TXT')
        zipdata(out/'WINXT-RC6-SOURCE.zip',source_files(q))
        zipdata(out/'WINXT-RC6-FONTS.zip',fonts)
        zipdata(out/'WINXT-RC6-PREVIEWS.zip',previews())
        (out/'FONT-LICENSE.TXT').write_bytes(read(ROOT/'tools/XTFONTS/LICENSE'))
        (out/'START-HERE.TXT').write_bytes(start_text())
        q['publication_commit']=commit;textfile(out/'QUALIFY.JSON',json.dumps(q,indent=2)+'\n')
        r={'schema':1,'release_tag':q['release_tag'],'publication_commit':commit,
           'publication_allowed':True,'native_code_identity_preserved':True,
           'document_pin_data_refreshed':True,'refreshed_helper_executed_in_guest':False,
           'Windows_support_included':False,'fonts_are_original_MIT':True,
           'assets_sha256':{p.name:sha(read(p)) for p in sorted(out.iterdir())}}
        textfile(out/'RELEASE.JSON',json.dumps(r,indent=2)+'\n')
        (out/'SHA256SUMS').write_bytes(''.join(sha(read(p))+'  '+p.name+'\n' for p in sorted(out.iterdir())).encode())
    verify(out,commit)

def verify(out,commit=None):
    q=qualification();check({p.name for p in out.iterdir()}==ASSETS, 'Release allowlist changed')
    expected=''.join(sha(read(out/n))+'  '+n+'\n' for n in sorted(ASSETS-{'SHA256SUMS'})).encode()
    check(read(out/'SHA256SUMS')==expected, 'Release checksums mismatch')
    r=object_at(out/'RELEASE.JSON');published=object_at(out/'QUALIFY.JSON')
    c=r['publication_commit']
    check(c=='working-tree' or re.fullmatch('[0-9a-f]{40}',c), 'Invalid publication identity')
    if commit: check(c==commit, 'Publication commit differs')
    expected_q=dict(q,publication_commit=c)
    check(published==expected_q, 'Qualification/source identity differs')
    check(r=={'schema':1,'release_tag':q['release_tag'],'publication_commit':c,
        'publication_allowed':True,'native_code_identity_preserved':True,
        'document_pin_data_refreshed':True,'refreshed_helper_executed_in_guest':False,
        'Windows_support_included':False,'fonts_are_original_MIT':True,
        'assets_sha256':{n:sha(read(out/n)) for n in sorted(ASSETS-{'RELEASE.JSON','SHA256SUMS'})}},
        'Release scope/assets identity differs')
    for n,h in q['package_sha256'].items():
        check(sha(read(out/('PKGSUMS.TXT' if n=='SHA256SUMS' else n)))==h, 'Package pin changed '+n)
    with tempfile.TemporaryDirectory(prefix='rc6-verify-') as td:
        folder=Path(td)/'PACKAGE';folder.mkdir()
        for n in PACKAGE: shutil.copyfile(out/('PKGSUMS.TXT' if n=='SHA256SUMS' else n),folder/n)
        package_checks(folder,q)
        generated=Path(td)/'FONTS';build(generated)
        check(zipped(out/'WINXT-RC6-FONTS.zip')==fonts_files(q,generated), 'Font source reproduction differs')
    check(zipped(out/'WINXT-RC6-SOURCE.zip')==source_files(q), 'Matching source ZIP differs')
    check(zipped(out/'WINXT-RC6-PREVIEWS.zip')==previews(), 'Native previews differ')
    check(read(out/'START-HERE.TXT')==start_text() and read(out/'FONT-LICENSE.TXT')==read(ROOT/'tools/XTFONTS/LICENSE'),
          'Instructions/license differ')
    print('PASS rc.6 exact source/runtime/package/evidence + original fonts + bounded document binding',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--package',type=Path)
    ap.add_argument('--out',type=Path);ap.add_argument('--verify',type=Path)
    ap.add_argument('--commit',default='working-tree');a=ap.parse_args()
    if a.verify: verify(a.verify,a.commit)
    else:
        if not a.package or not a.out: ap.error('--package and --out are required')
        make(a.package,a.out,a.commit)
