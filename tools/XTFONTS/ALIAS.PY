"""Prepare collision-free 8.3 font packaging in a new isolated source tree.

Windows 3.0 Setup may retain an already installed same-name font. The
original generated FON bytes/resource ordinals/metrics stay unchanged;
only first-party transport and OEM font filenames change. No native launch.
Rebuild helper/installer and qualify Setup/rollback before acceptance.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from BUILD import textfile

NAMES = {'CGASYS.FON':'XTCSYS.FON','CGAFIX.FON':'XTCFIX.FON',
         'CGAOEM.FON':'XTCOEM.FON','EGASYS.FON':'XTESYS.FON',
         'EGAFIX.FON':'XTEFIX.FON','EGAOEM.FON':'XTEOEM.FON',
         'TXTSYS.FON':'XTTSYS.FON'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(source,out):
    if out.exists():raise ValueError('Choose a fresh isolated alias source tree')
    shutil.copytree(source,out)
    runtime=out/'distributions/WINXT';flash=out/'tools/FLASHDISK'
    original={old:sha(runtime/old) for old in NAMES}
    for old,new in NAMES.items():
        (runtime/old).rename(runtime/new)
        if sha(runtime/new)!=original[old]:raise ValueError('Alias changed FON bytes')
    files=['distributions/WINXT/OEMSETUP.INF','distributions/WINXT/README.TXT',
           'distributions/WINXT/STAGE.PY','distributions/WINXT/TESTS.TXT',
           'distributions/WINXT/TEXTMODE.TXT','tools/FLASHDISK/MAKEIMG.PY',
           'tools/FLASHDISK/PACKPINS.H','tools/FLASHDISK/SZPACK.PY',
           'src/tandysw/TINST.C']
    for name in files:
        p=out/name;text=p.read_text()
        for old,new in NAMES.items():text=text.replace(old,new).replace(old[:-1]+'_',new[:-1]+'_')
        textfile(p,text)
    textfile(runtime/'FONTINFO.TXT','Original XT Pixels R10 fonts; MIT, see FONTLIC.TXT.\n'
             'Collision-free 8.3 names prevent Setup from reusing Microsoft fonts.\n'
             + ''.join(old+' -> '+new+'\n' for old,new in NAMES.items())
             + 'FON bytes, resource ordinals, System/Terminal faces and metrics unchanged.\n'
             + 'Windows and non-font support dependencies remain. No vintage Python.\n')
    manifest={NAMES.get(name,name):digest for digest,name in
              (line.split() for line in (runtime/'MANIFEST.SHA').read_text().splitlines())}
    for name in manifest:
        if name not in ('CGA.GR2','CGALOGO.LGO'):manifest[name]=sha(runtime/name)
    textfile(runtime/'MANIFEST.SHA',''.join(manifest[n]+'  '+n+'\n' for n in sorted(manifest)))
    pins=(flash/'XTPINS.H').read_text()
    rows=re.findall(r'\{"([A-Z0-9_.]+)","([a-f0-9]{64})",(\d+)UL,([01])\}',pins)
    result='/* Unpublished original-font collision-free package; rebuild required. */\nstatic struct pin pins[]={\n'
    for name,digest,size,kind in rows:
        name=NAMES.get(name,name)
        if kind=='0':digest,size=sha(runtime/name),str((runtime/name).stat().st_size)
        result+=' {"%s","%s",%sUL,%s},\n'%(name,digest,size,kind)
    result+='};\n';textfile(flash/'XTPINS.H',result)
    if set(n for n,h,s,k in re.findall(r'\{"([A-Z0-9_.]+)","([a-f0-9]{64})",(\d+)UL,([01])\}',result))!=set(manifest)|{'MANIFEST.SHA'}:
        raise ValueError('Pin allowlist drift')
    # These copied binaries/pins implement the previous names and are not
    # acceptable in this new source tree. Removing these exact private copies
    # ensures MAKEIMG refuses packaging until reviewed native recompilation.
    for p in (flash/'PREPXT.EXE',flash/'HELPER.SHA',out/'REBUILD.JSON'):
        if p.exists():p.unlink()
    report={'status':'HOST-PREPARED ONLY; native rebuild and installation required',
            'native_package_qualified':False,'publication_allowed':False,
            'source':str(source),'font_install_names':NAMES,
            'font_alias_sha256':{new:sha(runtime/new) for new in NAMES.values()},
            'original_font_sha256':original,'font_bytes_unchanged':True,
            'next_gates':['Recompile TINST/PREPXT and diagnostics; regenerate coupled pins',
                          'Host image build/tests/FAT12','Font-free DOS preparation',
                          'Setup-selected alias fonts exact; cold GUI glyph pixel proof',
                          'Exact rollback and default/deep verification transactions']}
    textfile(out/'ALIAS.JSON',json.dumps(report,indent=2)+'\n')
    textfile(out/'RECOMPILE.TXT','ALIAS SOURCE ONLY. Recompile TINST and PREPXT; no prior helper binary is accepted.\n')
    print('HOST-PREPARED ONLY:',out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.source.resolve(),a.out.resolve())
