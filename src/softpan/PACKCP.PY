"""Create a separate local ColorPlus candidate and byte-exact fixed rollback choice.

The default grabber is the repository-supplied Windows 3.0 CGA.GR2.
Compressed SZDD input is expanded on the developer host.
"""
from pathlib import Path
import argparse,hashlib,json,zipfile,importlib.machinery

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def text(s):return s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('driver','apps','fixed','out'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--grabber',type=Path,default=ROOT/'distributions/WINXT/CGA.GR2')
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    fixed=a.fixed.read_bytes();pin=json.loads((ROOT/'tools/SPPACK/PUBLIC.JSN').read_text())['profiles']['CPPAN']['files']['PCP3216.DRV']
    assert len(fixed)==pin['bytes'] and hashlib.sha256(fixed).hexdigest()==pin['sha256']
    decoder=importlib.machinery.SourceFileLoader('cp_expand',str(ROOT/'tools/XR1PACK/PREPARE.PY')).load_module()
    files={'CPPAN.DRV':a.driver.read_bytes(),'PCP3216.DRV':fixed,'CGA.GR2':decoder.expanded_file(a.grabber.read_bytes(),'CGA.GR2')}
    for n in ('XTPAN.EXE','PANCFG.EXE'):files[n]=(a.apps/n).read_bytes()
    for n in ('XTESYS.FON','XTEFIX.FON','XTEOEM.FON','XTSTATIC.LGO','WXTSPL01.RLE','FONTLIC.TXT','LOGOLIC.TXT'):
        files[n]=(ROOT/'distributions/WINXT'/n).read_bytes()
    files['OEMSETUP.INF']=text('''[data]
Version = "3.0"
[disks]
a = C:\\CPPAN, "ColorPlus software panning candidate (C:\\CPPAN)", OEMSETUP.INF
[display]
CPPAN = a:CPPAN.DRV, "EXPERIMENTAL ColorPlus 320x400 panning", "133,96,72", a:CGA.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE
PCP3216 = a:PCP3216.DRV, "ColorPlus 320x200 fixed (rollback)", "133,96,72", a:CGA.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE
[sysfonts]
a:XTESYS.FON, "EGA System Font", "133,96,72"
[fixedfonts]
a:XTEFIX.FON, "EGA Fixed System Font", "133,96,72"
[oemfonts]
a:XTEOEM.FON, "EGA Terminal Font (USA/Europe)", "133,96,72", 1
''')
    files['CPWIN.BAT']=text('ECHO OFF\nC:\nCD \\WINDOWS\nWIN /R\n')
    files['INSTALL.TXT']=text('''ColorPlus software panning candidate - Windows 3.0 real mode

This provides a 320x400 desktop through a 320x200 screen. The card's normal
two-plane mode is used; panning copies pixels in software. Shadow memory is
64,000 bytes, 32,000 more than the fixed driver. The Windows tests use PC
DOS 3.20 on an emulated 640 KB XT. Physical hardware is not qualified.

INSTALL IN AN EXISTING WINDOWS 3.0 INSTALLATION
1. Copy this folder to C:\\CPPAN. Exit Windows to plain DOS.
2. CD \\WINDOWS, run SETUP, change Display to Other, enter C:\\CPPAN,
   and select EXPERIMENTAL ColorPlus 320x400 panning. Keep the PC/XT
   keyboard choice. Return to DOS when Setup finishes.
3. Start Windows with C:\\CPPAN\\CPWIN. In Program Manager, File > Run,
   run C:\\CPPAN\\PANCFG. It starts the helper and enables it for later
   sessions while preserving other startup programs.

USE
Move the pointer past the visible area or dwell at its top/bottom edge.
Alt+PgDn moves down; Alt+PgUp moves up; Alt+F9 returns to the top.
Newly activated windows are brought into view. Wider-than-320-pixel
dialogs still need keyboard navigation. For DOS programs, exit Windows
and run them from DOS. No PCjr or Tandy memory reservation helper is used:
the ColorPlus card has dedicated video RAM.

RETURN TO THE FIXED DRIVER
In Windows File > Run, run C:\\CPPAN\\PANCFG OFF. Exit Windows, run
SETUP, choose Other, C:\\CPPAN, then ColorPlus 320x200 fixed (rollback).
The included PCP3216.DRV is the qualified current fixed driver.

The required CGA.GR2 grabber, fonts, logos and helpers are included.
Use an existing Windows 3.0 installation.
''')
    for n,b in files.items():(out/n).write_bytes(b)
    manifest={n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())}
    (out/'MANIFEST.JSN').write_bytes(text(json.dumps(manifest,indent=2)))
    with zipfile.ZipFile(out.with_suffix('.ZIP'),'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,'CPPAN/'+p.name)
    print(out.with_suffix('.ZIP'))
if __name__=='__main__':main()
