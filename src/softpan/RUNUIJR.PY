"""Bound one PCjr native-Setup session in a disposable folder clone.

Guest-side UITEST observes native controls and receives command-file input.
No host window/input APIs are used. Windows Setup alone changes the display.
"""
from pathlib import Path
import argparse,importlib.machinery,json,os,shutil,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--windows',type=Path);ap.add_argument('--apps',type=Path);ap.add_argument('--packet',type=Path)
    ap.add_argument('--stage',default='INSTALL');ap.add_argument('--initial-drive',choices=('C','Z'),default='C');a=ap.parse_args();out=a.out.resolve();c=out/'CROOT';w=c/'WINDOWS'
    if a.prepare:
        out.mkdir(parents=True,exist_ok=False);shutil.copytree(a.windows,w)
        shutil.copytree(a.packet,c/'JRPAN')
        with zipfile.ZipFile(ROOT/'downloads/experimental/PCJR/PCJRSET.ZIP') as z:
            for n in z.namelist():
                p=Path(n)
                if n.endswith('/'):continue
                target=c/'PCJREXP'/p.name;target.parent.mkdir(exist_ok=True);target.write_bytes(z.read(n))
        shutil.copyfile(c/'PCJREXP/TNDYJR.DRV',w/'SYSTEM/TNDYJR.DRV')
        shutil.copyfile(a.apps/'UITEST.EXE',w/'UITEST.EXE')
        h=importlib.machinery.SourceFileLoader('ui_ini',str(HERE/'RUNTEST.PY')).load_module()
        s=(w/'SYSTEM.INI').read_text(encoding='latin1')
        for k,v in [('display.drv','TNDYJR.DRV'),('shell','PROGMAN.EXE')]:s=h.ini(s,'boot',k,v)
        write(w/'SYSTEM.INI',s)
        s=(w/'WIN.INI').read_text(encoding='latin1');s=h.ini(s,'windows','load',r'C:\WINDOWS\UITEST.EXE');s=h.ini(s,'windows','run','');write(w/'WIN.INI',s)
        s=(w/'PROGMAN.INI').read_text(encoding='latin1');s=h.ini(s,'Settings','Window','0 0 320 200 1');write(w/'PROGMAN.INI',s)
        task=b'0 SNAP\r\n';(c/'UITASK.TXT').write_bytes(task+b' '*(4096-len(task)))
        print('Prepared fixed-profile disposable PCjr clone',out)
        return
    stage=a.stage.upper();assert stage.isalnum()
    # Each boot is launched by the package's actual guarded launcher.
    launcher=r'C:\PCJREXP\JRWIN' if stage in ('INSTALL','FIXED') else r'C:\JRPAN\JRSTART'
    bat='@ECHO OFF\nSET PATH=C:\\WINDOWS;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\n'+a.initial_drive+':\nCALL '+launcher+'\nCD \\\nECHO RETURNED > C:\\RET'+stage+'.TXT\nEXIT\n'
    write(c/'TEST.BAT',bat)
    cfg='[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=pcjr\nmemsizekb=640\nworking directory option=force\nworking directory default='+str(out)+'\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@echo off\nmount C "'+str(c)+'"\nC:\nTEST.BAT\n'
    write(out/'RUN.CNF',cfg)
    m=importlib.machinery.SourceFileLoader('ui_lease',str(HERE/'WINRUN.PY')).load_module();r=m.Runner(out/(stage+'-LEASE.JSON'))
    with r.lease():r.run([r'C:\DOSBox-X\dosbox-x.exe','-nopromptfolder','-conf',out/'RUN.CNF'],dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),out/(stage+'-HOST.LOG'),900)
    assert (c/('RET'+stage+'.TXT')).exists(),'Windows did not return normally'
    print('Returned to DOS:',stage)
if __name__=='__main__':main()
