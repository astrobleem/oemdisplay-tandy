"""Run an explicitly allocated remaining-font/installation checkpoint.

Host preparation is separate. Never auto-allocate; exclusive existing lock,
bounded owned process, private fixtures, cleanup in finally. No publication.
"""
import argparse
import datetime
import hashlib
import json
import msvcrt
import re
import shutil
import struct
import subprocess
import time
from pathlib import Path
from BUILD import textfile
from NATIVE import conflicts, config
from NATIVEQA import metrics, pattern, exact
from ENCQA import validate as encoding_validate
from PIL import Image


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pictures(guest, width, bios):
    palette = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),
               (170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),
               (85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    ids = [0,12,10,15] if bios == 10 else [0,3,5,15] if bios == 4 else [0,15]
    for name in ('NORMAL', 'DIALOG'):
        raw = (guest / (name + '.BIN')).read_bytes()
        if len(raw) != 32768: raise ValueError('Short framebuffer')
        pixels = []
        for y in range(200):
            for x in range(width):
                if bios == 10:
                    at = y % 4 * 8192 + y // 4 * 160 + x // 8 * 2
                    c = (raw[at] >> (7-x%8) & 1) | ((raw[at+1] >> (7-x%8) & 1) << 1)
                else:
                    bits = 1 if bios == 6 else 2 if bios == 4 else 4
                    at = y % (4 if bios == 9 else 2) * 8192 + y // (4 if bios == 9 else 2) * (160 if bios == 9 else 80) + x // (8//bits)
                    c = raw[at] >> ((8//bits-1-x%(8//bits))*bits) & ((1<<bits)-1)
                pixels.append(palette[c if bios in (8,9) else ids[c]])
        image = Image.new('RGB', (width,200)); image.putdata(pixels)
        image.save(guest / (name + '.PNG'))


def prepare(out):
    inputs = json.loads((out / 'FULL-INPUTS.JSON').read_text())
    alias=Path(inputs['candidate'])/'ALIAS.JSON'
    if alias.exists(): inputs['font_install_names']=json.loads(alias.read_text())['font_install_names']
    original = out / 'INSTALL/GUEST'
    if any((original / n).exists() for n in ('WINXT','FAIL.TXT','PREP.OK')):
        raise ValueError('Use an untouched preparation fixture')
    if list((original / 'SOURCEOS').rglob('*.FON')) or list((original / 'MEDIA').rglob('*.FON')):
        raise ValueError('Font source media unexpectedly present')
    target = out / 'VERIFY/GUEST'
    if target.exists(): raise ValueError('Choose a fresh VERIFY fixture')
    shutil.copytree(original, target)
    for name, guest in (('INSTALL',original),('VERIFY',target)):
        batch = (guest / 'START.BAT').read_text()
        if name == 'VERIFY':
            batch = batch.replace('C:\\MEDIA <', 'C:\\MEDIA /VERIFY <')
            batch = batch.replace('TINSTD C:\\WINDOWS >', 'TINSTD C:\\WINDOWS /VERIFY >')
        save = 'COPY C:\\WINDOWS\\SYSTEM.INI C:\\SELECTED.INI > NUL\nMD C:\\RUNFONTS\n'
        for f in [inputs.get('font_install_names',{}).get(n+'.FON',n+'.FON')[:-4] for n in ('CGASYS','CGAFIX','CGAOEM','EGASYS','EGAFIX','EGAOEM','TXTSYS')]:
            save += 'IF EXIST C:\\WINDOWS\\SYSTEM\\%s.FON COPY C:\\WINDOWS\\SYSTEM\\%s.FON C:\\RUNFONTS\\%s.FON > NUL\n' % (f,f,f)
        save += 'MD C:\\RUNDRV\nCOPY C:\\WINDOWS\\SYSTEM\\TR*.DRV C:\\RUNDRV > NUL\n'
        batch = batch.replace('ECHO SETUP_RETURNED>C:\\SETUP.OK\n', 'ECHO SETUP_RETURNED>C:\\SETUP.OK\n' + save)
        batch = batch.replace('ECHO COLD_GUI_RETURNED>C:\\GUI.OK\n', 'ECHO COLD_GUI_RETURNED>C:\\GUI.OK\nECHO FONT_ROLLBACK_TEST>C:\\WINDOWS\\CONTROL.INI\nECHO FONT_ROLLBACK_TEST>C:\\WINDOWS\\WIN.INI\n')
        textfile(guest / 'START.BAT', batch)
        cfg = config([('C',guest),('D',out/'BUILD')], '', guest, True)
        cfg += 'IMGMOUNT A "' + str(out/'PACKAGE/WINXT720.IMG') + '" -T FLOPPY\nC:\nSTART.BAT\n'
        textfile(out/name/'ROUND.CNF', cfg)
    textfile(out/'ROUND-INPUTS.JSON', json.dumps(inputs,indent=2)+'\n')
    print('PREPARED ONLY: unchanged compiled inputs/image, fresh VERIFY, no font media')


def installation(out, name, inputs):
    guest = out/name/'GUEST'; deep = name == 'VERIFY'
    if (guest/'FAIL.TXT').exists() or not all((guest/n).exists() for n in ('PREP.OK','INST.OK','SETUP.OK','GUI.OK','ROLL.OK','DONE.OK')):
        raise ValueError('Incomplete ' + name + ' transaction')
    changed = [n for n,h in inputs['install_original_windows_sha256'].items() if not (guest/'WINDOWS'/n).is_file() or sha(guest/'WINDOWS'/n) != h]
    if changed: raise ValueError('Original rollback mismatch: ' + repr(changed))
    if any(sha(guest/n) != h for n,h in inputs['install_original_boot_sha256'].items()):
        raise ValueError('Boot rollback mismatch')
    fonts = Path(inputs['fonts']); candidate = Path(inputs['candidate'])
    for f in ('CGASYS','CGAFIX','CGAOEM','EGASYS','EGAFIX','EGAOEM','TXTSYS'):
        if sha(guest/'WINXT'/inputs.get('font_install_names',{}).get(f+'.FON',f+'.FON')) != sha(fonts/(f+'.FON')): raise ValueError('Staged font differs')
    selected = {}; section = ''
    for line in (guest/'SELECTED.INI').read_text('latin1').splitlines():
        if line.strip().startswith('['): section = line.strip().lower()
        elif section == '[boot]' and '=' in line:
            k,v = line.split('=',1); selected[k.lower()] = v.upper().strip()
    modes = {'TR53216.DRV':(320,9,'EGA'),'TR51616.DRV':(160,8,'CGA'),'TR53204.DRV':(320,4,'CGA'),'TR56404.DRV':(640,10,'CGA'),'TR56402.DRV':(640,6,'CGA')}
    driver = selected.get('display.drv')
    if driver not in modes: raise ValueError('Setup did not select a candidate driver: '+str(driver))
    width,bios,family = modes[driver]
    for k,suffix in (('fonts.fon','SYS'),('fixedfon.fon','FIX'),('oemfonts.fon','OEM')):
        original=family+suffix+'.FON'; f=inputs.get('font_install_names',{}).get(original,original)
        if selected.get(k) != f or sha(guest/'RUNFONTS'/f) != sha(fonts/original): raise ValueError('Setup-selected font differs: '+k)
    if sha(guest/'RUNDRV'/driver) != sha(candidate/'distributions/WINXT'/driver): raise ValueError('Selected driver bytes differ')
    log = (guest/'FONT.LOG').read_text('latin1')
    if 'DONE=1' not in log or 'SCREEN_WIDTH='+str(width) not in log: raise ValueError('Cold GUI probe incomplete')
    pictures(guest,width,bios)
    from INSPECT import fontinfo
    keymap={'HEIGHT':'height','ASCENT':'ascent','INTERNAL':'internal','EXTERNAL':'external','AVERAGE':'avg_width','MAXIMUM':'max_width','FIRST':'first','LAST':'last','CHARSET':'charset'}
    found=metrics(log)
    for stock,suffix in ((13,'SYS'),(16,'FIX'),(10,'OEM')):
        info=fontinfo((fonts/(family+suffix+'.FNT')).read_bytes())
        if any(found[stock][k]!=info[v] for k,v in keymap.items()): raise ValueError('Cold GUI stock metric mismatch')
    raw=(fonts/(family+'SYS.FNT')).read_bytes()
    if list(struct.unpack('<224H',(guest/'WIDTHS.BIN').read_bytes()))!=fontinfo(raw)['widths']: raise ValueError('Cold GUI advance mismatch')
    im=Image.open(guest/'NORMAL.PNG').convert('RGB'); pixels=(*im.size,bytes(int(c==(0,0,0)) for c in im.getdata()))
    rows=pattern(raw,b'XT Pixels / Win3'); anchors=[(x,y) for y in range(30,90) for x in range(2,15) if exact(pixels,rows,x,y)]
    if len(anchors)!=1: raise ValueError('Cold GUI glyph anchor mismatch')
    x,y=anchors[0];oem=(fonts/(family+'OEM.FNT')).read_bytes();fixed=(fonts/(family+'FIX.FNT')).read_bytes()
    cases=[(raw,b'XT Pixels / Win3',0),(raw,b'File Edit View Help',16),(raw,b'Il1 O0 rn m ; !?',32),(raw,bytes([0x7f,0x80,0x81,0xff]),48),(fixed,b'Fixed: Il1 O0 rn m',116)]
    cases += [(oem,bytes(range(176+r*16,192+r*16)),68+r*10) for r in range(4)]
    if any(not exact(pixels,pattern(font,codes),x,y+dy) for font,codes,dy in cases):raise ValueError('Cold GUI System/Fixed/OEM native glyph pixels differ')

    prep=(guest/'PREP.LOG').read_text('latin1'); install=(guest/'INSTALL.LOG').read_text('latin1')
    counts=list(map(int,re.findall(r'SHA blocks=(\d+)',prep))); compared=list(map(int,re.findall(r'compared=(\d+)',install)))
    if not counts or not compared or (not deep and (any(counts) or any(compared))) or (deep and (not all(counts) or not any(compared))):
        raise ValueError('Diagnostic verification counters mismatch')
    record={'status':'PASS native '+name+' preparation/Setup/cold GUI/rollback','deep':deep,'selected':selected,'staged_fonts_exact':7,'selected_fonts_exact':3,'original_windows_files_restored':len(inputs['install_original_windows_sha256']),'deliberate_CONTROL_WININI_changes_restored':True,'boot_files_restored':2,'sha_blocks':counts,'compared_bytes':compared,'native_ui_size':[width,200],'native_system_pixel_anchor':anchors[0],'native_system_runs_exact':4,'native_fixed_run_exact':True,'native_oem_codes_exact':64,'native_visual_review_required':True}
    textfile(out/name/'ROUND-QA.JSON',json.dumps(record,indent=2)+'\n');print(record['status'],flush=True)
    return record


def run(out,lockpath,seconds,deadline_utc=None,cases=None,build_first=False):
    inputs=json.loads((out/'ROUND-INPUTS.JSON').read_text()); candidate=Path(inputs['candidate']); build=out/'BUILD'
    for n,h in inputs['compiler_sha256'].items():
        if sha(Path(inputs['compiler'])/n)!=h: raise ValueError('Compiler inputs changed')
    if not build_first:
        pins=json.loads((candidate/'REBUILD.JSON').read_text())
        if sha(build/'PREPXT.EXE')!=pins['helper_sha256'] or sha(build/'TINST.EXE')!=pins['installer_sha256']: raise ValueError('Reviewed build changed')
    if conflicts(): raise ValueError('BUSY: another emulator; no launch/kill')
    lock=lockpath.open('rb'); held=False; process=None; state={'status':'RUNNING','allocation_seconds':seconds,'runs':[],'native_package_qualified':False}
    def save():
        textfile(out/'ROUND-STATUS.JSON',json.dumps(state,indent=2)+'\n');print(json.dumps(state),flush=True)
    def stop():
        nonlocal process
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: process.kill();process.wait(timeout=2)
        process=None
    def launch(name,cfg,guest,bound):
        nonlocal process
        if conflicts(): raise ValueError('BUSY before '+name)
        now=time.monotonic()
        if end-now<10: raise ValueError('Allocated deadline reached before '+name)
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        with (out/(name+'.ROUND-HOST.LOG')).open('wb') as log:
            process=subprocess.Popen([inputs['dosbox'],'-nopromptfolder','-conf',str(cfg)],cwd=guest,stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
            state['active']=name;state['active_pid']=process.pid;save(); beat=now
            while process.poll() is None and time.monotonic()<min(end-3,now+bound):
                if time.monotonic()-beat>15:save();beat=time.monotonic()
                time.sleep(.2)
            result={'name':name,'exit_code':process.poll(),'seconds':round(time.monotonic()-now,3)};stop()
        state['runs'].append(result);save()
        if result['exit_code']!=0:raise ValueError('Failed/bounded '+name)
    try:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);held=True;began=time.monotonic();end=began+seconds
        if deadline_utc:
            absolute=datetime.datetime.fromisoformat(deadline_utc);end=min(end,began+(absolute-datetime.datetime.now(datetime.timezone.utc)).total_seconds())
        state['acquired_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['deadline_utc']=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=max(0,end-time.monotonic()))).isoformat();save()
        if build_first:
            from PINBUILD import main as pin_build
            launch('BUILD',build/'BUILD.CNF',build,70)
            pin_build(argparse.Namespace(candidate=candidate,build=build))
            if not (candidate/'tools/FLASHDISK/HELPER.SHA').exists():
                shutil.copyfile(candidate/'tools/FLASHDISK/XTPINS.H',build/'XTPINS.H')
                launch('REBUILD',build/'REBUILD.CNF',build,30)
                with (build/'BUILD.LOG').open('ab') as log:log.write((build/'REBUILD.LOG').read_bytes())
                pin_build(argparse.Namespace(candidate=candidate,build=build))
            for probe in ('FONENC','FONTPRB'):
                raw=bytearray((build/(probe+'.EXE')).read_bytes());ne=struct.unpack_from('<I',raw,60)[0]
                if raw[ne:ne+2]!=b'NE' or struct.unpack_from('<H',raw,ne+12)[0]&8:raise ValueError('Protected-mode-only probe')
                struct.pack_into('<H',raw,ne+62,0x300);(build/(probe+'.EXE')).write_bytes(raw)
            result=subprocess.run(['python',str(candidate/'tools/FLASHDISK/MAKEIMG.PY'),'--runtime',str(candidate/'distributions/WINXT'),'--out',str(out/'PACKAGE')],capture_output=True,text=True,timeout=min(60,max(1,end-time.monotonic()-3)))
            textfile(out/'PACKAGE.LOG',result.stdout+result.stderr)
            if result.returncode:raise ValueError('Host package build failed')
            verify=subprocess.run(['python',str(candidate/'tools/FLASHDISK/TESTPKG.PY'),'--verify',str(out/'PACKAGE')],capture_output=True,text=True,timeout=min(60,max(1,end-time.monotonic()-3)))
            textfile(out/'PACKAGE-VERIFY.LOG',verify.stdout+verify.stderr)
            if verify.returncode:raise ValueError('Host package verification failed')
        for name in (cases or ('B160','INSTALL','TXFONT','VERIFY','TXMODE')):
            guest=out/('INSTALL' if name=='RECOVER' else name)/'GUEST'
            probe='FONTPRB' if name in ('B160','INSTALL','VERIFY') else 'FONENC'
            shutil.copyfile(build/(probe+'.EXE'),guest/(probe+'.EXE'))
            cfg=out/'INSTALL/RECOVER.CNF' if name=='RECOVER' else out/name/('ROUND.CNF' if name in ('INSTALL','VERIFY') else 'RUN.CNF')
            launch(name,cfg,guest,180 if name=='VERIFY' else 160 if name=='INSTALL' else 45)
            if name in ('INSTALL','VERIFY','RECOVER'): installation(out,'INSTALL' if name=='RECOVER' else name,inputs)
            elif name=='B160':
                baseline=(guest/'FONT.LOG').read_text('latin1'); prior=out.parent/'FONT-NATIVE3/C160/FONT.LOG'; previous=prior.read_text('latin1')
                keys=('DIALOG_BASE','DIALOG_LEFT','DIALOG_RIGHT','DIALOG_BOTTOM','DIALOG_SCREEN_OVERFLOW','CANCEL_TEXT_WIDTH','CANCEL_CLIENT_WIDTH')
                def geometry(s):
                    rows=dict(line.split('=',1) for line in s.splitlines() if '=' in line);return {k:int(rows[k]) for k in keys}
                comparison={'baseline':geometry(baseline),'original_font_candidate':geometry(previous),'stock_metric_match':metrics(baseline)==metrics(previous)}
                comparison['same_geometry']=comparison['baseline']==comparison['original_font_candidate']
                if 'DONE=1' not in baseline or not comparison['same_geometry'] or not comparison['stock_metric_match']:raise ValueError('Baseline 160 geometry changed')
                pictures(guest,160,8);textfile(out/'BASE160.JSON',json.dumps(comparison,indent=2)+'\n');print('PASS baseline160 geometry/metrics',flush=True)
            elif name=='TXFONT':encoding_validate(guest,Path(inputs['fonts']),'TXT',6,640)
            else:
                log=(guest/'FONENC.LOG').read_text('latin1')
                if 'DONE=1' not in log or log.count('WIDTH_QUERY=1')!=3:raise ValueError('Text-mode probe incomplete')
                textfile(out/'TXMODE.JSON',json.dumps({'font_probe_completed':True,'stock_metrics':metrics(log),'native_text_renderer_pixels_qualified':False,'reason':'BIOS character cells require separate semantic review'},indent=2)+'\n')
        state['status']='COMPLETED; review native captures and text semantics before package acceptance'
    except Exception as error:
        state['status']='STOPPED: '+repr(error);raise
    finally:
        stop()
        if held:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);state['held_seconds']=round(time.monotonic()-began,3);state['released_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        lock.close();state['active_pid']=None;state['remaining_conflicts']=conflicts();save()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--out',type=Path,required=True);p.add_argument('--lock',type=Path);p.add_argument('--deadline-utc');p.add_argument('--cases',nargs='+');p.add_argument('--build-first',action='store_true');p.add_argument('--allocated-seconds',type=int,choices=range(60,481));a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve())
    else:
        if not a.lock or not a.allocated_seconds:p.error('run requires an explicitly allocated bound and existing shared lock')
        run(a.out.resolve(),a.lock,a.allocated_seconds,a.deadline_utc,a.cases,a.build_first)
