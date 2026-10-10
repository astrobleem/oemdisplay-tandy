"""Integrate only original static-logo inputs into an isolated source revision."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def textfile(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode())
def pins(root):
    runtime=root/'distributions/WINXT';flash=root/'tools/FLASHDISK'
    manifest={n:h for h,n in (line.split() for line in (runtime/'MANIFEST.SHA').read_text().splitlines())}
    manifest.pop('CGALOGO.LGO',None)
    manifest['XTSTATIC.LGO']=sha(runtime/'XTSTATIC.LGO')
    manifest['LOGOLIC.TXT']=sha(runtime/'LOGOLIC.TXT')
    manifest['LOGOINFO.TXT']=sha(runtime/'LOGOINFO.TXT')
    for name in manifest:
        if name!='CGA.GR2':manifest[name]=sha(runtime/name)
    textfile(runtime/'MANIFEST.SHA',''.join(manifest[n]+'  '+n+'\n' for n in sorted(manifest)))
    rows=[]
    for name in sorted(set(manifest)|{'MANIFEST.SHA'}):
        if name=='CGA.GR2':digest,size,kind=manifest[name],2104,1
        else:digest,size,kind=sha(runtime/name),(runtime/name).stat().st_size,0
        rows.append(' {"%s","%s",%dUL,%d},\n'%(name,digest,size,kind))
    textfile(flash/'XTPINS.H','/* Unpublished original-static-logo revision; rebuild before use. */\n'
             'static struct pin pins[]={\n'+''.join(rows)+'};\n')
def integrate(root,build):
    if root==ROOT and (root/'STATIC-REVISION.JSON').exists():raise ValueError('Revision already integrated')
    runtime=root/'distributions/WINXT';flash=root/'tools/FLASHDISK'
    baseline=json.loads((build/'BUILD.JSON').read_bytes())
    assert baseline['original_implementation'] and not baseline['publication_allowed']
    assert sha(build/'XTSTATIC.LGO')==baseline['lgo_sha256']
    preserved={n:sha(runtime/n) for n in ('WAVEXT.EXE','XTWAVE.DAT','XTCLEAN.COM','RESERVE.COM','WXTSPL01.RLE')}
    shutil.copyfile(build/'XTSTATIC.LGO',runtime/'XTSTATIC.LGO')
    shutil.copyfile(HERE/'LICENSE',runtime/'LOGOLIC.TXT')
    textfile(runtime/'LOGOINFO.TXT','Original MIT XTSTATIC.LGO; source tools/XTLOGO.\n'
      'Windows Setup joins owned WIN.CNF + XTSTATIC.LGO + original WXTSPL01.RLE.\n'
      'CGA.GR2 remains owned support. Windows itself/loader/kernel are not included.\n'
      'Normal Color slow wave bytes unchanged; no target Python or default SHA.\n'
      'This isolated revision is unpublished and awaits native qualification.\n')
    for name in ('distributions/WINXT/OEMSETUP.INF','src/tandysw/TINST.C'):
        p=root/name;s=p.read_text();assert 'CGALOGO.LGO' in s
        textfile(p,s.replace('CGALOGO.LGO','XTSTATIC.LGO'))
    p=runtime/'STAGE.PY';s=p.read_text().replace("'CGALOGO.LGO': 'd9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807'",'')
    s=s.replace("'CGA.GR2': '1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067', }","'CGA.GR2': '1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067'}")
    s=s.replace('and logo loader require owned media','requires owned media; the static logo is original')
    textfile(p,s)
    p=flash/'PREPXT.C';s=p.read_text()
    obsolete=[line for line in s.splitlines() if 'if(!strcmp(name,"CGALOGO.LGO"))' in line]
    assert len(obsolete)==1
    textfile(p,s.replace(obsolete[0]+'\n',''))
    p=flash/'MAKEIMG.PY';s=p.read_text();s=s.replace("PUBLIC_NAMES = (","PUBLIC_NAMES = ('XTSTATIC.LGO', 'LOGOLIC.TXT', 'LOGOINFO.TXT', ",1)
    s=s.replace("WINDOWS_NAMES = ('CGA.GR2', 'CGALOGO.LGO')","WINDOWS_NAMES = ('CGA.GR2',)")
    s=s.replace('CGA.GR2 and CGALOGO.LGO still require your own matching Windows files.',
                'Only CGA.GR2 requires a matching owned support file. Static logo and fonts are original.')
    s=s.replace('for the two owned non-font files','for the owned non-font grabber')
    s=s.replace('containing CGA.GR2 or CGALOGO.LGO','containing CGA.GR2')
    s=s.replace('ORIGINAL FONT TEST CANDIDATE','ORIGINAL STATIC LOGO TEST CANDIDATE')
    s=s.replace("'original-font-test-candidate'","'original-static-logo-test-candidate'")
    textfile(p,s)
    p=flash/'TESTPKG.PY';s=p.read_text().replace('docs/QUAL/FONTBLD.JSON','docs/QUAL/STATICBLD.JSON')
    s=s.replace("'original-font-test-candidate'","'original-static-logo-test-candidate'")
    textfile(p,s)
    # Existing PUBLISH guards remain pinned to rc.5. A new revision cannot pass
    # those source/runtime identity checks and receives no release authorization.
    textfile(runtime/'README.TXT',runtime.joinpath('README.TXT').read_text()+
      '\nORIGINAL STATIC LOGO REVISION (UNPUBLISHED)\n'
      'XTSTATIC.LGO replaces owned CGALOGO.LGO in Setup and static WIN.COM.\n'
      'Only CGA.GR2 is gathered from owned support; owned Windows/WIN.CNF remain.\n'
      'The accepted Color slow wave is unchanged. Native qualification pending.\n')
    pins(root)
    # Withhold the helper manifest until actual recompilation against new pins.
    stale=flash/'HELPER.SHA'
    if stale.exists():stale.rename(flash/'RC5HELP.SHA')
    assert {n:sha(runtime/n) for n in preserved}==preserved
    report={'baseline_commit':'0c400228eede1b0aedde8c91c3598636b1ea7e1c',
            'native_package_qualified':False,'publication_allowed':False,
            'static_logo':baseline,'preserved_sha256':preserved,
            'owned_support':['CGA.GR2'],'owned_installed_loader':'SYSTEM/WIN.CNF',
            'next':['Compile TINST and regenerate pins','Compile PREPXT against final pins',
                    'Host package checks','Allocated native Setup/start/rollback qualification']}
    textfile(root/'STATIC-REVISION.JSON',json.dumps(report,indent=2)+'\n')
    print('HOST integrated; helper publication pins withheld; native rebuild required')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--pins-only',action='store_true')
    a=p.parse_args();pins(a.root.resolve()) if a.pins_only else integrate(a.root.resolve(),a.build.resolve())
