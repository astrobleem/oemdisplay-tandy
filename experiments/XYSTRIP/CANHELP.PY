"""Build and prepare a focused installed XYCTL 8/4 menu-step Windows check."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration'
HERE = Path(__file__).resolve().parent
BUILD = OUT / 'canonical-helper-build'
CHECK = r'''
static void Helper(void){HWND h;int i;unsigned st[8];char module[128];
 static int commands[4]={102,110,101,109};
 static int wantx[4]={8,8,0,0},wanty[4]={0,4,4,0};
 static unsigned wantbytes[4]={800,640,800,640};
 Check("HELPER_LAUNCH",WinExec("C:\\PANSTEP\\WINXT\\XYCTL.EXE",SW_SHOWMINIMIZED)>=32);
 h=0;for(i=0;i<30&&!h;i++){Pump(250);h=FindWindow("XYOverviewControl",0);}
 Check("HELPER_WINDOW",h!=0);if(!h)return;
 module[0]=0;GetModuleFileName(GetWindowWord(h,GWW_HINSTANCE),module,sizeof(module));AnsiUpper(module);
 Check("HELPER_SOURCE",strstr(module,"PANSTEP\\WINXT\\XYCTL.EXE")!=0);
 stats(st);Check("HELPER_DEFAULT_SOFT",st[0]==0);
 SendMessage(h,WM_COMMAND,107,0L);SendMessage(h,WM_COMMAND,112,0L);
 SendMessage(h,WM_COMMAND,103,0L);SendMessage(h,WM_COMMAND,105,0L);
 for(i=0;i<4;i++){
  SendMessage(h,WM_COMMAND,commands[i],0L);Check("HELPER_QUERY",Pan(-1,0));stats(st);
  wsprintf(line,"HELPER command=%d x=%d y=%d bytes=%u reason=%u\r\n",commands[i],view[0],view[1],st[7],st[3]);Log(line);
  Check("HELPER_STEP",view[0]==wantx[i]&&view[1]==wanty[i]&&st[7]==wantbytes[i]&&st[3]==0&&st[0]==1);
  Snap(10+i);
 }
 SendMessage(h,WM_CLOSE,0,0L);Pump(300);Check("HELPER_CLOSED",FindWindow("XYOverviewControl",0)==0);
}
'''


def build():
    BUILD.mkdir(exist_ok=False)
    source = (HERE / 'APPQA.C').read_text()
    source = source.replace('int PASCAL WinMain(', CHECK + '\nint PASCAL WinMain(')
    source = source.replace('SendMessage(paint,WM_CLOSE,0,0L);', 'Helper();SendMessage(paint,WM_CLOSE,0,0L);')
    (BUILD / 'CANAPP.C').write_bytes(source.replace('\n', '\r\n').encode('ascii'))
    (HERE / 'CANAPP.C').write_bytes((BUILD / 'CANAPP.C').read_bytes())
    (BUILD / 'APPQA.LNK').write_bytes(b'system windows\r\nname APPQA.EXE\r\noption map=APPQA.MAP\r\nfile CANAPP.obj\r\n')
    env = dict(os.environ, WATCOM=r'C:\WATCOM', INCLUDE=r'C:\WATCOM\H;C:\WATCOM\H\WIN')
    with (BUILD / 'BUILD.LOG').open('wb') as log:
        for cmd in [[r'C:\WATCOM\BINNT\WCC.EXE', '-zW', '-0', '-ms', '-od', '-we',
                     r'-i=C:\WATCOM\H', r'-i=C:\WATCOM\H\WIN', 'CANAPP.C'],
                    [r'C:\WATCOM\BINNT\WLINK.EXE', '@APPQA.LNK']]:
            subprocess.run(cmd, cwd=BUILD, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    print('Built installed-helper probe', BUILD)


def prepare(accepted):
    folder = OUT / accepted
    r = json.loads((folder / 'VERIFIED.JSN').read_bytes())
    assert r['complete'] and r['normal_dos_return']
    run = OUT / 'canonical-helper-01'
    run.mkdir()
    for name in ('DISK.IMG', '86box.cfg', 'PREPARE.JSON', 'SYSTEM-BEFORE.INI'):
        shutil.copyfile(folder / name, run / name)
    sys.path.insert(0, r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local')
    from pyfatfs.PyFatFS import PyFatFS
    with PyFatFS(str(run / 'DISK.IMG'), offset=8704) as fs:
        for n in fs.listdir('/'):
            if n in ('RETURNED.TXT', 'APPQA.LOG', 'INSTALL.LOG', 'START.LOG') or (n.endswith('.BIN') and n[0] in 'AB' and n[1:4].isdigit()):
                fs.remove(n)
        fs.remove('WINDOWS/APPQA.EXE')
        fs.writebytes('WINDOWS/APPQA.EXE', (BUILD / 'APPQA.EXE').read_bytes())
        fs.remove('AUTOEXEC.BAT')
        fs.writebytes('AUTOEXEC.BAT', b'@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS\r\nSET TEMP=C:\\WINDOWS\\TEMP\r\nC:\r\nCD \\PANSTEP\\WINXT\r\nC:\\COMMAND.COM /C DISPWIN.BAT > C:\\START.LOG\r\nECHO RETURNED > C:\\RETURNED.TXT\r\n')
    s = (folder / 'NATIVE.PY').read_text()
    s = s.replace("['DOSVER.TXT','INSTALL.LOG','START.LOG']", "['DOSVER.TXT','START.LOG']")
    (run / 'NATIVE.PY').write_bytes(s.replace('\n', '\r\n').encode('ascii'))
    print('Prepared installed helper boot', run)


if __name__ == '__main__':
    if sys.argv[1] == 'build':
        build()
    else:
        prepare(sys.argv[1])
