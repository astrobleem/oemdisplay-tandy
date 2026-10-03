#!/usr/bin/env python3
"""Automated Paintbrush proof in an isolated Windows 3.0 guest clone.
Uses native Windows messages and the guest clipboard, not host desktop input.
The test-only executable refuses to run without the isolated-run marker.
"""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
from PIL import Image
ap=argparse.ArgumentParser()
for name in ('guest','build','test-build','fixtures','dosbox','out'):
    ap.add_argument('--'+name, type=Path, required=True)
ap.add_argument('--profile', choices=['baseline','160','3204','6404','6402'], required=True)
ap.add_argument('--output-drive', choices=['C','D','R'], default='C', help='C or D: nested ART directory; R: C root')
a=ap.parse_args(); o=a.out.resolve(); drive=a.output_drive
if o.exists(): ap.error('--out must be new')
o.mkdir(parents=True); g=o/'guest'; d=o/'drive-d'
shutil.copytree(a.guest, g); (g/'ART').mkdir(exist_ok=True); (d/'ART').mkdir(parents=True)
shutil.copyfile(a.build/'GIFLOAD.EXE', g/'GIFLOAD.EXE')
shutil.copyfile(a.test_build/'PBTEST.EXE', g/'PBTEST.EXE')
shutil.copyfile(a.fixtures/'TEST.GIF', g/'TEST.GIF')
(g/'GIFTEST.TAG').write_text('ISOLATED GIF TEST\n')
for name in ['BEFORE.BMP','EDITED.BMP','PBTEST.LOG','TEST.BMP','ART/TEST.BMP','DONE.TXT']:
    (g/name).unlink(missing_ok=True)  # isolated clone only
config=r"""[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
captures={out}/captures
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 20000
fpu=false
[render]
scaler=none
doublescan=false
aspect=false
[dos]
xms=false
ems=false
umb=false
[serial]
serial1=serialmouse
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount c "{guest}"
mount d "{drive_d}"
c:
set path=c:\windows;z:\
set temp=c:\windows\temp
c:\tandy88\reserve > C:\RESERVE.TXT
cd c:\windows
DX-CAPTURE /V win /r c:\pbtest.exe {drive}
echo DONE>C:\DONE.TXT
exit
"""
(o/'RUN.CNF').write_text(config.format(out=o,guest=g,drive_d=d,drive=drive))
env=dict(os.environ, SDL_VIDEODRIVER='dummy')
status='timeout'
with (o/'HOST.LOG').open('wb') as f:
    proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'RUN.CNF')],stdout=f,stderr=f,env=env)
    start=time.monotonic()
    try:
        while time.monotonic()-start<600:
            s=(g/'PBTEST.LOG').read_text(errors='replace') if (g/'PBTEST.LOG').exists() else ''
            if 'PASS workflow' in s or 'FAIL ' in s:
                status='finished'; time.sleep(.5); break
            if proc.poll() is not None: status='exited'; break
            time.sleep(.25)
    finally:
        if proc.poll() is None: proc.kill()
        proc.wait()
s=(g/'PBTEST.LOG').read_text() if (g/'PBTEST.LOG').exists() else ''
result={'profile':a.profile,'output_drive':drive,'status':status,'log':s,'accepted':False,
        'exe_sha256':hashlib.sha256((g/'GIFLOAD.EXE').read_bytes()).hexdigest(),
        'test_exe_sha256':hashlib.sha256((g/'PBTEST.EXE').read_bytes()).hexdigest(),
        'cpu':'8086_prefetch','base_memory_kb':640,'ems_xms_umb':False,
        'interaction':'Automated Windows messages; Edit Paste of guest clipboard bitmap'}
try:
    assert 'PASS workflow' in s and 'FAIL ' not in s, s
    mode={'baseline':16,'160':16,'3204':4,'6404':5,'6402':2}[a.profile]
    assert (g/'BEFORE.BMP').read_bytes()==(a.fixtures/('TEST'+str(mode)+'.BMP')).read_bytes(), 'Automatic palette mismatch'
    assert (g/'TEST.GIF').read_bytes()==(a.fixtures/'TEST.GIF').read_bytes(), 'Input changed'
    final_path=g/'TEST.BMP' if drive=='R' else (g if drive=='C' else d)/'ART/TEST.BMP'
    before=Image.open(g/'BEFORE.BMP').convert('RGB')
    edited=Image.open(g/'EDITED.BMP').convert('RGB')
    final=Image.open(final_path).convert('RGB')
    assert before.size==edited.size==final.size==(96,64)
    bp=list(before.getdata()); ep=list(edited.getdata()); fp=list(final.getdata())
    changed=[(i%96,i//96,ep[i]) for i in range(len(bp)) if bp[i]!=ep[i]]
    assert changed, 'No actual edit persisted'
    assert fp==ep, 'Reopened save changed pixels'
    xs=[c[0] for c in changed]; ys=[c[1] for c in changed]
    assert max(xs)-min(xs)<8 and max(ys)-min(ys)<8 and all(c[2]==(255,255,255) for c in changed), 'Unexpected edit extent or color'
    result.update(accepted=True,changed_pixels=len(changed),changed_bbox=[min(xs),min(ys),max(xs),max(ys)],reopen_pixels_compared=len(fp),reopen_mismatches=0)
except Exception as e:
    result['failure']=str(e)
(o/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
if not result['accepted']: raise SystemExit(1)
