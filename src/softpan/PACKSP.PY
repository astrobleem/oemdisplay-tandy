"""Make a separate local PCjr panning installation packet, leaving accepted packets intact."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def text(s):
    return s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--driver',type=Path,required=True)
    ap.add_argument('--apps',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    files={'JRPAN.DRV':a.driver.read_bytes()}
    for n in ('XTPAN.EXE','PANCFG.EXE','JRGUARD.COM'):
        files[n]=(a.apps/n).read_bytes()
    with zipfile.ZipFile(ROOT/'downloads/experimental/PCJR/PCJRSET.ZIP') as z:
        for n in ('JRGRAB.GR2','XTESYS.FON','XTEFIX.FON','XTEOEM.FON','XTSTATIC.LGO','WXTSPL01.RLE','FONTLIC.TXT','LOGOLIC.TXT'):
            matches=[p for p in z.namelist() if p.upper().endswith('/'+n)]
            assert len(matches)==1,n
            files[n]=z.read(matches[0])
    inf=(ROOT/'src/pcjr/INSTALL/OEMSETUP.INF').read_text()
    inf=inf.replace('C:\\PCJREXP','C:\\JRPAN').replace('TNDYJR','JRPAN').replace('320x200 16 colors','320x400 software panning')
    inf=inf.replace('320x200x16','320x400 logical').replace('\\JRWIN','\\JRSTART')
    files['OEMSETUP.INF']=text(inf)
    files['JRSTART.BAT']=text('ECHO OFF\nC:\\JRPAN\\JRGUARD.COM\nIF ERRORLEVEL 1 GOTO FAIL\nC:\nCD \\WINDOWS\nWIN /R\nGOTO END\n:FAIL\nECHO The PCjr video page must be reserved before Windows starts.\n:END\n')
    files['INSTALL.TXT']=text('''PCjr software panning candidate - Windows 3.0 real mode

This adds a 320x400 desktop through the normal 320x200 screen. Panning
copies pixels in software. It uses 64,000 bytes of shadow RAM, 32,000 more
than the fixed driver. PCjr emulator tests passed; physical hardware has
not been qualified.

INSTALL
1. Copy this folder to C:\\JRPAN. Exit Windows to plain DOS.
2. Run C:\\JRPAN\\JRGUARD. It must say OK. The existing PCjr memory
   driver must reserve the 32 KB video page; this guard does not reserve it.
3. CD \\WINDOWS, run SETUP, change Display to Other, enter C:\\JRPAN,
   and select EXPERIMENTAL IBM PCjr 320x400 software panning.
   For a new Windows installation, make the same display selection during
   Setup and select the PC/XT keyboard. Return to DOS when Setup finishes.
4. Start Windows with C:\\JRPAN\\JRSTART. In Program Manager, File > Run,
   run C:\\JRPAN\\PANCFG. This starts the panning helper and enables it
   for later Windows sessions. Existing startup programs are preserved.

USE
Start Windows with C:\\JRPAN\\JRSTART each time so the memory guard runs.
Move the pointer past the visible area, or dwell at its upper/lower edge.
Alt+PgDn moves down; Alt+PgUp moves up; Alt+F9 returns to the top.
The helper also follows newly activated windows. Dialogs wider than 320
pixels still require keyboard navigation.

RETURN TO THE FIXED DRIVER
In Windows File > Run, run C:\\JRPAN\\PANCFG OFF to remove the helper
from startup. Exit Windows, run SETUP, and choose the previous display.
For the accepted PCjr packet, choose Other, C:\\PCJREXP, then its
320x200 entry. Continue to use its guarded JRWIN launcher.

The accepted PCjr and Tandy packages are separate and are not modified by
building this packet. No Windows media is included.
''')
    for n,b in files.items():(out/n).write_bytes(b)
    manifest={n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())}
    (out/'MANIFEST.JSN').write_bytes(text(json.dumps(manifest,indent=2)))
    with zipfile.ZipFile(out.with_suffix('.ZIP'),'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,'JRPAN/'+p.name)
    print(str(out.with_suffix('.ZIP')))


if __name__=='__main__':main()
