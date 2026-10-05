#!/usr/bin/env python3
"""Private emulator QA; requires user's licensed Windows/MSC6 and built drivers.
No Windows, toolchain, BIOS or DOSBox binaries are distributed in the kit.
"""
from pathlib import Path
import os,sys,json,shutil,subprocess,hashlib,time,fcntl,re
P=Path(__file__).resolve().parents[1]
ROOT=Path('/workspace/scratch/a84592844d2c/borders-text-20261005')
FIX=Path(os.environ.get('TANDI_WINDOWS','/workspace/shared/windows30/round05-c'))
DOSBOX=os.environ.get('TANDI_DOSBOX','/workspace/shared/dosbox-x/run')
MODES={'320x200x16':('TANDY88.DRV',320,16,4,160),
       '640x200x2':('TNDY6402.DRV',640,2,2,80),
       '640x200x4':('TNDY6404.DRV',640,4,4,160)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ini(path,section,key,value):
    out=[];active=False;found=False
    for line in path.read_text().splitlines():
        if line.strip().startswith('['):
            if active and not found:out.append(key+'='+value);found=True
            active=line.strip().lower()=='['+section.lower()+']'
        if active and '=' in line and line.split('=',1)[0].strip().lower()==key.lower():
            out.append(key+'='+value);found=True
        else:out.append(line)
    if not found:
        if not active:out.append('['+section+']')
        out.append(key+'='+value)
    path.write_bytes(('\r\n'.join(out)+'\r\n').encode('ascii'))
def decode(raw,mode):
    _,w,c,banks,pitch=MODES[mode];out=bytearray(w*200);bpp={16:4,4:2,2:1}[c]
    for y in range(200):
        base=y%banks*8192+y//banks*pitch
        for x in range(w):
            if w==640 and c==4:
                a=base+2*(x//8);v=((raw[a]>>(7-x%8))&1)|(((raw[a+1]>>(7-x%8))&1)<<1)
            else:v=raw[base+x//(8//bpp)]>>((8//bpp-1-x%(8//bpp))*bpp)&(c-1)
            out[y*w+x]=v
    return bytes(out)
def render(run,mode):
    from PIL import Image,ImageDraw
    _,w,c,_,_=MODES[mode]
    palettes={16:[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)],2:[(0,0,0),(255,255,255)],4:[(0,0,0),(255,85,85),(85,255,85),(255,255,255)]}
    labels=['WELCOME','QUESTION','GUESS','SUCCESS','DEBUG','HELP','EYELEFT','EYERIGHT']
    frames={}
    for name in labels:
        file=run/'guest'/(name+'.BIN')
        if not file.exists():continue
        raw=decode(file.read_bytes(),mode);frames[name]=raw
        image=Image.new('RGB',(w,200));image.putdata([palettes[c][x] for x in raw])
        image.resize((640,400),Image.Resampling.NEAREST).save(run/(name+'.PNG'))
    if 'EYELEFT' in frames and 'EYERIGHT' in frames:
        diffs=[i for i,(a,b) in enumerate(zip(frames['EYELEFT'],frames['EYERIGHT'])) if a!=b]
        sx=1 if w<400 else 2
        local=all((45*sx<=i%w<52*sx or 53*sx<=i%w<60*sx) and 85<=i//w<94 for i in diffs)
        return {'changed_pixels':len(diffs),'only_eye_rectangles_changed':local}
    return {}
def run(mode,negative=False,scale=False):
    name,w,c,_,_=MODES[mode]
    root=P/'evidence'/('art-'+((mode+'-corrupt') if negative else (mode+'-scale' if scale else mode)))
    if root.exists():raise RuntimeError('Use a fresh result directory; do not overwrite evidence')
    root.mkdir(parents=True);guest=root/'guest';guest.mkdir()
    shutil.copytree(FIX/'WINDOWS',guest/'WINDOWS')
    for n in ['CPUCHECK.COM','LATERCPU.COM','RESERVE.COM']:shutil.copyfile(FIX/n,guest/n)
    exe=P/'src/TANDI.EXE';db=P/('build/SCALE.DAT' if scale else 'build/TANDY.DAT');driver=ROOT/'builds/combined'/mode/name
    shutil.copyfile(exe,guest/'WINDOWS/TANDI.EXE');shutil.copyfile(db,guest/'WINDOWS/TANDY.DAT')
    if negative:
        data=bytearray((guest/'WINDOWS/TANDY.DAT').read_bytes());data[-1]^=1
        (guest/'WINDOWS/TANDY.DAT').write_bytes(data)
    shutil.copyfile(driver,guest/'WINDOWS/SYSTEM/TRIAL.DRV')
    for k,v in [('display.drv','TRIAL.DRV'),('shell','TANDI.EXE'),('fonts.fon','cgasys.fon'),('fixedfon.fon','cgafix.fon'),('oemfonts.fon','cgaoem.fon')]:ini(guest/'WINDOWS/SYSTEM.INI','boot',k,v)
    ini(guest/'WINDOWS/WIN.INI','TANDINATOR','Test','1')
    ini(guest/'WINDOWS/WIN.INI','TANDINATOR','TestExit',str(list(MODES).index(mode)+1))
    for k in ['run','load']:ini(guest/'WINDOWS/WIN.INI','windows',k,'')
    start='''@ECHO OFF
CPUCHECK > CPUCHECK.TXT
LATERCPU > LATERCPU.TXT
RESERVE > RESERVE.TXT
IF ERRORLEVEL 1 GOTO BAD
SET PATH=C:\\WINDOWS;Z:\\
SET TEMP=C:\\WINDOWS\\TEMP
CD WINDOWS
WIN /R
CD \\
ECHO RETURNED > RETURNED.TXT
GOTO DONE
:BAD
ECHO RESERVE_FAILED > RETURNED.TXT
:DONE
EXIT
'''
    (guest/'START.BAT').write_bytes(start.replace('\n','\r\n').encode('ascii'))
    conf=(ROOT/'baseline'/mode/'RUN.CNF').read_text().split('[autoexec]')[0]
    conf=re.sub('captures=.*','captures='+str(root/'captures'),conf)
    conf+='[autoexec]\nmount C "'+str(guest)+'"\nC:\nSTART.BAT\n'
    (root/'RUN.CNF').write_text(conf)
    env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    begun=time.monotonic()
    with (ROOT/'emulator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        with (root/'HOST.LOG').open('w') as out:
            result=subprocess.run([DOSBOX,'-nopromptfolder','-conf',str(root/'RUN.CNF')],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=180)
    log=(guest/'TANDI.LOG').read_text() if (guest/'TANDI.LOG').exists() else ''
    result={'mode':mode,'negative':negative,'synthetic_scale':scale,'host_seconds':time.monotonic()-begun,'returncode':result.returncode,'log':log,'exe_sha256':sha(exe),'database_sha256':sha(guest/'WINDOWS/TANDY.DAT'),'driver_sha256':sha(driver),'cpu':(guest/'CPUCHECK.TXT').read_text(),'later_cpu':(guest/'LATERCPU.TXT').read_text(),'reserve':(guest/'RESERVE.TXT').read_text(),'returned':(guest/'RETURNED.TXT').read_text() if (guest/'RETURNED.TXT').exists() else None,'eyes':render(root,mode)}
    if not negative:
        result['partial_repaint_exact']=(guest/'PARTIAL.BIN').read_bytes()==(guest/'FULLDRAW.BIN').read_bytes()
        result['border_expose_exact']=(guest/'WELCOME.BIN').read_bytes()==(guest/'EXPOSE.BIN').read_bytes()
        result['focus_restore_exact']=(guest/'WELCOME.BIN').read_bytes()==(guest/'FOCUS.BIN').read_bytes()
    (root/'RESULT.JSON').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
    assert result['returncode']==0 and result['returned'] and 'RETURNED' in result['returned']
    if negative:
        assert 'COMPLETE=1' in log and 'APP_ERROR=1' in log and 'ERRORS=1' in log
    if not negative:
        assert 'ART_READY=1' in log and 'UNCHANGED_MOUSE_NO_REDRAW=1' in log
        assert 'FOCUS_OTHER_WINDOW=1' in log and 'FOCUS_RETURNED=1' in log and 'FOCUS_STATE_PRESERVED=1' in log
        assert result['focus_restore_exact']
        assert 'QUESTION_CABINET_UNTOUCHED=1' in log and 'QUESTION_CABINET_UNTOUCHED=0' not in log
        assert 'COMPLETE=1' in log and 'ERRORS=0' in log and 'TARGET_SUCCESS=1' in log and 'WINFLAGS=64' in log
        assert 'OVERLAYS_PRESERVE_STATE=1' in log and 'TAB_FOCUS_MOVED=1' in log
        assert 'MOUSE_REPLAY_STARTED=1' in log
        assert result['partial_repaint_exact'] and result['border_expose_exact']
        assert result['eyes']['changed_pixels']>0 and result['eyes']['only_eye_rectangles_changed']
    return result
if __name__=='__main__':
    for mode in (sys.argv[1:] or MODES):run(mode)
