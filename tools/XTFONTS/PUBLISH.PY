"""Build/verify original-font release assets around the exact native-tested disk.

No emulator/native rebuild, private media or compiler inputs. Runtime disk
bytes remain unchanged; separate qualification authorizes publication of the
preserved pre-native BUILD.JSON snapshot. Font tool code is MIT licensed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/FLASHDISK'))
import TESTPKG
from BUILD import build, textfile
from ENCQA import emitted

ALIASES={'CGASYS':'XTCSYS','CGAFIX':'XTCFIX','CGAOEM':'XTCOEM','EGASYS':'XTESYS',
         'EGAFIX':'XTEFIX','EGAOEM':'XTEOEM','TXTSYS':'XTTSYS'}
PACKAGE={'WINXT720.IMG','WINXT720.ZIP','WXTTOOLS.ZIP','BUILD.JSON','README.TXT','SHA256SUMS'}
ASSETS=(PACKAGE-{'SHA256SUMS'})|{'PKGSUMS.TXT','XT-PIXELS-R10-SOURCE.zip',
        'XT-PIXELS-R10-FONTS.zip','XT-PIXELS-R10-PREVIEWS.zip','FONT-LICENSE.TXT',
        'START-HERE.TXT','QUALIFY.JSON','RELEASE.JSON','SHA256SUMS'}

def sha(data):return hashlib.sha256(data).hexdigest()
def check(condition,message):
    if not condition:raise ValueError(message)
def read(path):
    check(path.is_file() and not path.is_symlink() and path.stat().st_size<=2097152,'Missing/linked/oversized input '+str(path))
    return path.read_bytes()
def zipdata(path,files):
    with zipfile.ZipFile(path,'x') as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
            info.create_system=0;info.external_attr=0x20;info.compress_type=zipfile.ZIP_STORED
            z.writestr(info,data)
def zipped(path):
    with zipfile.ZipFile(path) as z:
        check(z.namelist()==sorted(set(z.namelist())) and not z.comment,'ZIP order/duplicates')
        for i in z.infolist():
            check(i.date_time==(1980,1,1,0,0,0) and i.create_system==0 and i.external_attr==0x20
                  and i.compress_type==zipfile.ZIP_STORED and not i.extra and not i.comment
                  and not i.flag_bits and i.file_size<=1048576,'Unexpected ZIP metadata')
        return {i.filename:z.read(i) for i in z.infolist()}

def qualification():
    q=json.loads(read(ROOT/'docs/QUAL/FONTSR10.JSON'))
    check(q['native_package_qualified'] is True and q['publication_allowed'] is True,'Font publication not qualified/authorized')
    check(q['release_tag']=='v0.1.0-rc.5','Unexpected release tag')
    for name,digest in q['source_pins'].items():check(sha(read(ROOT/name))==digest,'Qualified source changed '+name)
    runtime=ROOT/'distributions/WINXT'
    payload=TESTPKG.package.public_payload(runtime)
    check(set(q['runtime_payload_pins'])==set(payload),'Runtime allowlist changed')
    for name,pin in q['runtime_payload_pins'].items():
        check(len(payload[name])==pin['bytes'] and sha(payload[name])==pin['sha256'],'Native runtime bytes changed '+name)
    check(sha(read(ROOT/'tools/FLASHDISK/PREPXT.EXE'))==q['helper_sha256'],'Native helper changed')
    zero=json.loads(read(ROOT/'docs/QUAL/ZEROFAST.JSON'))
    # Only the explicitly qualified font/installer/docs changes differ from
    # the accepted combined base. Keep its faster START/Settings/Computer.
    changed={'TINST.EXE','MANIFEST.SHA','OEMSETUP.INF','README.TXT','TESTS.TXT','TEXTMODE.TXT'}
    for name,pin in zero['payload_pins'].items():
        if name not in changed:
            check(name in payload and len(payload[name])==pin['bytes'] and sha(payload[name])==pin['sha256'],
                  'Unrelated qualified base runtime changed '+name)
    native=q['native_default_transaction'];deep=q['native_verify_transaction']
    check(native['sha_blocks']==[0,0] and native['compared_bytes']==[0],'Default verification is not zero')
    check(all(deep['sha_blocks']) and all(deep['compared_bytes']),'VERIFY work missing')
    for record in (native,deep):
        check(record['staged_fonts_exact']==7 and record['selected_fonts_exact']==3 and
              record['original_windows_files_restored']==113 and record['boot_files_restored']==2 and
              record['native_fixed_run_exact'] and record['native_system_runs_exact']==4 and
              record['native_oem_codes_exact']==64,'Native transaction evidence incomplete')
    return q

def source_files():
    allowed={p.name for p in HERE.iterdir() if p.is_file() and p.suffix in ('.PY','.C','.H','.DEF','.RC','.JSON','.MD')}
    allowed.add('LICENSE')
    return {'tools/XTFONTS/'+name:read(HERE/name) for name in sorted(allowed)}

def fonts_files(q,generated):
    files={'LICENSE.TXT':read(HERE/'LICENSE'),'README.MD':read(HERE/'README.MD'),
           'MISSING.JSON':read(generated/'MISSING.JSON')}
    for old,new in ALIASES.items():
        raw=read(generated/(old+'.FON'))
        check(sha(raw)==q['font_sha256'][old+'.FON'],'Generated font differs '+old)
        check(raw==read(ROOT/'distributions/WINXT'/(new+'.FON')),'Alias differs '+new)
        files[new+'.FON']=raw
        files[new+'.FNT']=emitted(generated,old+'.FON')
    files['ALIASES.JSON']=(json.dumps({a+'.FON':b+'.FON' for a,b in ALIASES.items()},indent=2)+'\r\n').encode()
    return files

def start_text():
    return b'''WINDOWS XT rc.5 - ORIGINAL XT PIXELS FONTS\r\n\r\nUse WINXT720.IMG (720KB data disk) with your existing DOS/Windows3.0.\r\nAt A:\\ run INSTALL, giving an owned support folder if needed. Confirm\r\nthe fresh C:\\WINXT stage. Then C: / CD \\WINXT / INSTALL.\r\nRun C:\\WINXT\\WINXT SETUP. Choose Other display and use C:\\WINXT at\r\nEVERY source prompt. Complete Changes; CONFIG.SYS option3 means no changes.\r\nStart with C:\\WINXT\\WINXT. Keep the video/recovery guards.\r\nRollback after exit: C:\\WINXT\\BACKUP\\B001\\RESTORE YES; use the printed\r\nnumbered path and read BACKUP.TXT.\r\n\r\nNo Python or Windows font media is needed on the Tandy. Fonts are original\r\nMIT drawings. Windows itself, CGA.GR2, CGALOGO.LGO and other non-font\r\nWindows components still require your owned files; they are not included.\r\nNormal preparation/install/start skips SHA work. /VERIFY is expensive\r\noptional developer diagnostics. The qualified faster guarded startup stays.\r\n\r\nAt160 pixels wide dialogs can clip with preserved metrics. Experimental\r\n80x25 text retains known corruption. Missing ANSI slots use boxes; no Euro\r\nor Unicode emoji is supplied. Native emulator tests are not physical timing.\r\n\r\nImage/BUILD/README are unchanged pre-publication snapshots to preserve the\r\nexact tested bytes. QUALIFY.JSON/RELEASE.JSON and this guide are current.\r\nManual: https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/USERMAN.MD\r\nFonts: https://github.com/astrobleem/oemdisplay-tandy/tree/main/tools/XTFONTS\r\n'''.replace(b'Windows3.0',b'Windows 3.0').replace(b'option3',b'option 3').replace(b'At160',b'At 160')

def make(package,out,commit):
    check(not out.exists(),'Output exists; choose a fresh directory')
    check(commit=='working-tree' or re.fullmatch('[0-9a-f]{40}',commit),'Require exact commit or local working-tree check')
    q=qualification()
    TESTPKG.verify(package)
    check({p.name for p in package.iterdir()}==PACKAGE,'Unexpected package files')
    for name,digest in q['package_sha256'].items():check(sha(read(package/name))==digest,'Package differs from native R10 '+name)
    with tempfile.TemporaryDirectory(prefix='xt-pixels-publish-') as td:
        generated=Path(td)/'FONTS';build(generated)
        ready=fonts_files(q,generated)
        out.mkdir(parents=True)
        for name in sorted(PACKAGE-{'SHA256SUMS'}):shutil.copyfile(package/name,out/name)
        shutil.copyfile(package/'SHA256SUMS',out/'PKGSUMS.TXT')
        zipdata(out/'XT-PIXELS-R10-FONTS.zip',ready)
        sources=source_files()
        sources.update({'FONTS/'+name:data for name,data in ready.items()})
        sources['README.MD']=read(HERE/'README.MD')
        zipdata(out/'XT-PIXELS-R10-SOURCE.zip',sources)
        shots=ROOT/'docs/FONTS/SHOTS'
        zipdata(out/'XT-PIXELS-R10-PREVIEWS.zip',{p.name:read(p) for p in shots.iterdir() if p.is_file()})
        (out/'FONT-LICENSE.TXT').write_bytes(read(HERE/'LICENSE'))
        (out/'START-HERE.TXT').write_bytes(start_text())
        q['publication_commit']=commit
        q['source_archives_sha256']={'XT-PIXELS-R10-SOURCE.zip':sha(read(out/'XT-PIXELS-R10-SOURCE.zip'))}
        textfile(out/'QUALIFY.JSON',json.dumps(q,indent=2)+'\n')
        release={'schema':1,'release_tag':q['release_tag'],'publication_commit':commit,
                 'native_binary_identity_preserved':True,'publication_allowed':True,
                 'Windows_support_included':False,'fonts_are_original_MIT':True,
                 'package_sha256':q['package_sha256'],
                 'assets_sha256':{p.name:sha(read(p)) for p in sorted(out.iterdir())}}
        textfile(out/'RELEASE.JSON',json.dumps(release,indent=2)+'\n')
        (out/'SHA256SUMS').write_bytes(''.join(sha(read(p))+'  '+p.name+'\n' for p in sorted(out.iterdir())).encode())
    verify(out,commit)

def verify(out,commit=None):
    q=qualification()
    check({p.name for p in out.iterdir()}==ASSETS,'Unexpected release assets')
    expected=''.join(sha(read(out/n))+'  '+n+'\n' for n in sorted(ASSETS-{'SHA256SUMS'})).encode()
    check(read(out/'SHA256SUMS')==expected,'Release checksum mismatch')
    release=json.loads(read(out/'RELEASE.JSON'));published=json.loads(read(out/'QUALIFY.JSON'))
    check(release['release_tag']==q['release_tag'] and release['publication_allowed'] is True and
          release['native_binary_identity_preserved'] is True and release['Windows_support_included'] is False,
          'Invalid release authorization/provenance')
    if commit:check(release['publication_commit']==commit and published['publication_commit']==commit,'Publication commit mismatch')
    for name,digest in q['package_sha256'].items():
        check(sha(read(out/('PKGSUMS.TXT' if name=='SHA256SUMS' else name)))==digest,'Native package bytes changed '+name)
    check(read(out/'START-HERE.TXT')==start_text() and read(out/'FONT-LICENSE.TXT')==read(HERE/'LICENSE'),'Instructions/license mismatch')
    with tempfile.TemporaryDirectory(prefix='xt-pixels-verify-') as td:
        generated=Path(td)/'FONTS';build(generated);ready=fonts_files(q,generated)
        check(zipped(out/'XT-PIXELS-R10-FONTS.zip')==ready,'Ready font ZIP mismatch')
        sources=source_files();sources.update({'FONTS/'+n:b for n,b in ready.items()});sources['README.MD']=read(HERE/'README.MD')
        check(zipped(out/'XT-PIXELS-R10-SOURCE.zip')==sources,'Source ZIP mismatch')
    shots=ROOT/'docs/FONTS/SHOTS'
    check(zipped(out/'XT-PIXELS-R10-PREVIEWS.zip')=={p.name:read(p) for p in shots.iterdir() if p.is_file()},'Native preview ZIP mismatch')
    for name,digest in release['assets_sha256'].items():check(sha(read(out/name))==digest,'Release record mismatch '+name)
    check(published['native_package_qualified'] is True and published['publication_allowed'] is True,'Final qualification absent')
    print('PASS exact native disk/runtime/source + original font/source/preview release assets',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--verify',type=Path);p.add_argument('--commit',default='working-tree')
    a=p.parse_args()
    if a.verify:verify(a.verify,a.commit)
    else:
        if not a.package or not a.out:p.error('--package and --out required')
        make(a.package,a.out,a.commit)
