"""Prepare canonical same-basename DISPLAY/Other install plus Paintbrush boot.

Uses the previously passing native fixture and bounded owned-child runner.
The observer records the explicit refresh response before feeding Y.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration' / (sys.argv[1] if len(sys.argv) > 1 else 'canonical-install-01')
FIX = Path(r'C:\Users\chad\Documents\Codex\2026-10-24\task-3\native\COMMON-OEM2')
sys.path.insert(0, r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local')
from pyfatfs.PyFatFS import PyFatFS


def ident(b):
    return dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def put(fs, n, b):
    if fs.exists(n):
        fs.remove(n)
    fs.writebytes(n, b)


def one(s, a, b):
    assert s.count(a) == 1, a
    return s.replace(a, b)


def prepare():
    OUT.mkdir()
    shutil.copyfile(FIX / 'DISK.IMG', OUT / 'DISK.IMG')
    shutil.copyfile(FIX / '86box.cfg', OUT / '86box.cfg')
    stage = ROOT.parent / 'tandy-pan-integration/canonical-stage'
    members = {str(p.relative_to(stage)).replace('\\', '/'): p.read_bytes()
               for p in stage.rglob('*') if p.is_file()}
    with PyFatFS(str(OUT / 'DISK.IMG'), offset=8704) as fs:
        fs.makedirs('PANSTEP/WINXT', recreate=True)
        for n, b in members.items():
            put(fs, 'PANSTEP/' + n, b)
        before = {n: ident(fs.readbytes('WINDOWS/SYSTEM/' + n)) for n in
                  ['HPXY.DRV', 'SOUND.DRV', 'KEYBOARD.DRV', 'MOUSE.DRV', 'SYSTEM.DRV']}
        (OUT / 'SYSTEM-BEFORE.INI').write_bytes(fs.readbytes('WINDOWS/SYSTEM.INI'))
        old_source = {n: ident(fs.readbytes('ALT/WINXT/' + n)) for n in fs.listdir('ALT/WINXT')}
        for n in ['SETDONE.TXT', 'RETURNED.TXT', 'APPQA.LOG', 'C16MET.TXT', 'INSTALL.LOG', 'START.LOG']:
            if fs.exists(n):
                fs.remove(n)
        put(fs, 'WINDOWS/APPQA.EXE', (ROOT.parent / 'tandy-pan-integration/app-build-03/APPQA.EXE').read_bytes())
        ini = fs.readbytes('WINDOWS/WIN.INI').decode('latin1').replace('\r', '')
        ini = re.sub(r'(?m)^load=.*$', 'load=', ini)
        ini = re.sub(r'(?m)^run=.*$', 'run=APPQA.EXE', ini)
        put(fs, 'WINDOWS/WIN.INI', ini.replace('\n', '\r\n').encode('latin1'))
        auto = '''@ECHO OFF
PATH C:\;C:\WINDOWS
SET TEMP=C:\WINDOWS\TEMP
C:
CD \PANSTEP\WINXT
VER > C:\DOSVER.TXT
C:\COMMAND.COM /C DISPLAY.BAT
ECHO DISPLAY RETURNED > C:\INSTALL.LOG
ECHO RETURNED > C:\SETDONE.TXT
C:
CD \PANSTEP\WINXT
C:\COMMAND.COM /C DISPWIN.BAT > C:\START.LOG
ECHO RETURNED > C:\RETURNED.TXT
'''
        put(fs, 'AUTOEXEC.BAT', auto.replace('\n', '\r\n').encode())
        # Preserve the already tested exact application input.
        with PyFatFS(str(ROOT.parent / 'tandy-pan-integration/install-02/DISK.IMG'), offset=8704, read_only=True) as old:
            put(fs, 'PANAPP.BMP', old.readbytes('PANAPP.BMP'))
    report = dict(source_image=ident((FIX / 'DISK.IMG').read_bytes()),
        packet=ident((ROOT.parent / 'tandy-pan-integration/CANONICAL.ZIP').read_bytes()),
        installed_before=before, old_source=old_source,
        scope='Normal full expanded packet; drivers-only DISPLAY/Other and same HPXY.DRV refresh; Paintbrush repaint and pan')
    (OUT / 'PREPARE.JSON').write_text(json.dumps(report, indent=2) + '\n')
    s = (ROOT / 'tools/XROEM/QA/OEMALT.PY').read_text()
    s = one(s, "ROOT=Path(__file__).resolve().parent.parent\nOUT=ROOT/'native/COMMON-OEM2';BOUND=240",
            'ROOT=Path(__file__).resolve().parent\nOUT=ROOT;BOUND=900')
    s = s.replace('ALT/WINXT', 'PANSTEP/WINXT').replace('C:\\\\ALT\\\\WINXT', 'C:\\\\PANSTEP\\\\WINXT').replace('C:\\ALT\\WINXT', 'C:\\PANSTEP\\WINXT')
    s = s.replace("['actual_combined_packet']", "['packet']")
    s = one(s, " msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);acquired=True;result['lease_acquired']=True",
            " lease_start=time.monotonic();print('Waiting for shared emulator lease, at most 600 seconds',flush=True)\n while True:\n  try:\n   lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);break\n  except PermissionError:\n   if time.monotonic()-lease_start>=600:raise RuntimeError('Shared lease still held; no child launched')\n   time.sleep(3)\n acquired=True;result['lease_acquired']=True;result['lease_wait_seconds']=round(time.monotonic()-lease_start,1)")
    s = one(s, "if mode==9 and fs.exists('C16MET.TXT') and not exit_sent:", 'if False:')
    s = one(s, "assert exit_sent,'Windows returned before settled desktop'",
            "assert 'END FAILURES=0' in fs.readbytes('APPQA.LOG').decode('latin1'),'Paintbrush probe failed'")
    s = one(s, "metrics=fs.readbytes('C16MET.TXT').decode('latin1');assert 'SM_0=640\\r\\nSM_1=256\\r\\n' in metrics and 'WindowsFlags=64\\r\\n' in metrics,metrics",
            "metrics=fs.readbytes('APPQA.LOG').decode('latin1')\n     for n in fs.listdir('/'):\n      if re.match(r'^[AB]\\d{3}\\.BIN$',n) or n=='APPQA.LOG':(OUT/n).write_bytes(fs.readbytes(n))")
    s = one(s, 'import base64,hashlib,json,msvcrt,os,socket,subprocess,sys,threading,time,zipfile',
            'import base64,hashlib,json,msvcrt,os,re,socket,subprocess,sys,threading,time,zipfile')
    s = one(s, "['stock_sound']", "['installed_before']['SOUND.DRV']")
    s = one(s, "keys(['HOME']+['DEL']*10);keys", "keys(['HOME']);keys(['DEL']*8);keys(['DEL']*8);keys(['DEL']*8);keys")
    s = one(s, "keys(['HOME','DEL','DEL','DEL'])", "keys(['HOME']);keys(['DEL']*8);keys(['DEL']*8);keys(['DEL']*8)")
    s = one(s, "if fs.exists('SETDONE.TXT'):",
            "if 'Replace only SYSTEM' in text and '[y/N]' in text and not result.get('refresh_answered'):\n    result['retained_old_before_refresh']=identity(fs.readbytes('WINDOWS/SYSTEM/HPXY.DRV'))\n    result['refresh_prompt']=text.strip()\n    returned=re.search(r'Windows Setup returned status (-?\\d+)',text)\n    result['raw_setup_return']=int(returned[1]) if returned else None\n    result['refresh_answered']='Y';snap('REFRESH');keys(['Y','ENTER'])\n   if fs.exists('APPQA.LOG') and mode==9 and 'MOVE from=' in fs.readbytes('APPQA.LOG').decode('latin1') and not (OUT/'PAINTBRUSH.PNG').exists():snap('PAINTBRUSH')\n   if fs.exists('SETDONE.TXT'):")
    s = s.replace('unchanged HPXY and complete support', 'canonical HPXY same-name refresh and selected support')
    (OUT / 'NATIVE.PY').write_bytes(s.replace('\n', '\r\n').encode('ascii'))
    print('Prepared canonical native install:', OUT)


if __name__ == '__main__':
    prepare()
