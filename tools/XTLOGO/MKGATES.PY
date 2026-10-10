"""Reproduce one frozen final-gates kit from pinned, private local inputs.

Host only. No emulator launch, publication or installed Windows/CF writes.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,importlib.util,json,re,shutil,sys
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tf(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def load(n,p):
    l=importlib.machinery.SourceFileLoader(n,str(p));s=importlib.util.spec_from_loader(n,l);m=importlib.util.module_from_spec(s);sys.modules[n]=m;l.exec_module(m);return m
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=REPO);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--base-ledger',type=Path,required=True);ap.add_argument('--controller',type=Path,required=True);ap.add_argument('--native-build',type=Path,required=True);ap.add_argument('--native-emitter',type=Path,required=True);ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    r=a.repo.resolve();base=a.base.resolve();out=a.out.resolve();assert not out.exists();out.mkdir()
    f=r/'tools/FLASHDISK';u=r/'distributions/WINXT';pkg=load('final_gates_package',f/'MAKEIMG.PY');pre=load('final_gates_preflight',HERE/'PREFLITE.PY')
    public=pkg.public_payload(u);headers={n:(f/n).read_bytes() for n in ('XTPINS.H','PACKPINS.H')};pkg.validate_helper_pins(public,headers);transport=pkg.disk_payload(public,headers)
    assert sha(u/'TINST.EXE')=='cc0036bbb82c89cef6dfbe025c10f7d61732d1271f9805031070d4b515517df1'
    assert sha(u/'XTMODE.EXE')=='34ff85d216a7c0233066aedc27c2199c2772e278438e627ce548d07909de4160'
    for name,p in (('TINST.C',r/'src/tandysw/TINST.C'),('XTMODE.C',r/'tools/XTMODE/XTMODE.C'),('XTPINS.H',r/'tools/XTMODE/XTPINS.H')):assert (a.native_build/name).read_bytes()==p.read_bytes(),'Native helper coupling '+name
    prepared_catalog=(a.native_emitter/'OEMSETUP.INF').read_bytes()
    assert prepared_catalog.replace(b'a = C:\\WINXT,',b'a = .,',1)==public['OEMSETUP.INF'],'Native-prepared catalog differs beyond the approved source-path directive'
    assert sha(base/'WINXT/CGA.GR2')==pre.GR2 and sha(base/'WINDOWS/SYSTEM/WIN.CNF')==pre.CNF
    expected_base=json.loads(a.base_ledger.read_bytes())['SET6402']['before_windows_sha256']
    actual_base={str(p.relative_to(base/'WINDOWS')).replace('\\','/'):sha(p) for p in (base/'WINDOWS').rglob('*') if p.is_file()}
    assert actual_base==expected_base,'Private Windows baseline differs from saved preimage'
    assert (a.controller/'BUILD.JSON').is_file();controller=json.loads((a.controller/'BUILD.JSON').read_bytes())
    assert sha(a.controller/'SKCTRL.COM')==controller['binary_sha256'] and sha(a.controller/'SKCTRL.ASM')==controller['source_sha256']
    for name,data in public.items():(out/'CANDIDATE').mkdir(exist_ok=True);(out/'CANDIDATE'/name).write_bytes(data)
    (out/'TRANSPORT/WINXT').mkdir(parents=True)
    for name,data in transport.items():(out/'TRANSPORT/WINXT'/name).write_bytes(data)
    # Reproduction sources only, never compiler/Windows bytes or stale PREPXT.EXE.
    source_names=['src/tandysw/TINST.C']
    source_names+=['tools/XTMODE/'+n for n in sorted(pkg.MODE_SOURCE_NAMES|{'FILES.SHA'})]
    source_names+=['tools/XTFONTS/'+n for n in sorted(pkg.FONT_SOURCE_NAMES|{'FILES.SHA'})]
    source_names+=['tools/FLASHDISK/'+n for n in ('MAKEIMG.PY','FAT12.PY','PREPXT.C','XTPINS.H','PACKPINS.H','SZSTREAM.H','SZPACK.PY','BUILD.BAT','README.MD','PREPXT.TXT','TESTS.MD','TESTPKG.PY','TESTFAT.PY')]
    source_names+=['tools/XTLOGO/'+n for n in ('MKGATES.PY','PREFLITE.PY','LEASE.PY','STATIC.ASM','LICENSE','CONTRACT.MD')]
    for name in source_names:
        p=out/'SOURCE'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/name,p)
    for name in ('SKCTRL.ASM','SKCTRL.COM','CTRLQA.PY','CTRLQA.JSON','BUILD.JSON','DRAIN.ASM','DRAIN.COM'):
        p=out/'CONTROL'/name;p.parent.mkdir(exist_ok=True);shutil.copy2(a.controller/name,p)
    inputs=json.loads(a.inputs.read_bytes());meta={'schema':1,'native_runs_authorized':False,'publication_allowed':False,'ready_to_try':False,
        'compiler_path':inputs['compiler'],'dosbox_path':inputs['dosbox'],'lock':inputs['lock'],
        'catalog_sha256':sha(u/'OEMSETUP.INF'),'runtime_pins':{n:h for h,n in (line.split() for line in (u/'MANIFEST.SHA').read_text().splitlines())},
        'qualified_font_pins':{n:sha(u/n) for n in pkg.PUBLIC_NAMES if n.endswith('.FON')},
        'compiler_flags':{'PREPXT':'/c /AS /G0 /W3 /Od','ZEROPREP':'/c /AS /G0 /W3 /Od /DINSTALL_DIAGNOSTICS /DZERO_SHA_TEST'},
        'fixtures':[],'jobs':{},'max_job_seconds':150,'source_baseline':'static 7879-byte common loader; RC5 is historical only',
        'base_ini_sha256':sha(base/'WINDOWS/SYSTEM.INI'),'native_counter_claim':'Unmeasured. Production default output and diagnostic default counters are separate gates.'}
    meta['base_ledger_sha256']=sha(a.base_ledger);meta['external_toolchain_pins']=dict(inputs['toolchain'])
    for name in ('STDLIB.H','STRING.H','CTYPE.H','SIGNAL.H','DIRECT.H','FCNTL.H','IO.H','TIME.H'):
        path=Path(inputs['compiler'])/'INCLUDE'/name;meta['external_toolchain_pins']['INCLUDE/'+name]=sha(path)
    meta['dosbox_sha256']=sha(Path(inputs['dosbox']))
    settings=['[sdl]','fullscreen=false','output=surface','[dosbox]','machine=tandy','memsize=0','memsizekb=640','allow more than 640kb base memory=false','[cpu]','core=normal','cputype=8086_prefetch','cycles=fixed 200000','fpu=false','[render]','scaler=none','doublescan=false','aspect=false','[dos]','xms=false','ems=false','umb=false','[mixer]','nosound=true','[autoexec]','@echo off']
    def config(group,name,mounts,commands,seconds):
        rel=group+'/'+name+'/RUN.CNF';p=out/rel
        lines=settings+['MOUNT '+drive+' "'+(inputs['compiler'] if drive=='T' else str((out/path).resolve()))+'"' for drive,path in mounts]+commands
        tf(p,'\n'.join(lines)+'\n');meta['jobs'][name]={'config':rel,'purpose':name,'seconds':seconds,'mounts':mounts};return p
    def guest(group,name):
        g=out/group/name/'GUEST';g.mkdir(parents=True);shutil.copytree(base/'WINDOWS',g/'WINDOWS')
        for n in ('AUTOEXEC.BAT','CONFIG.SYS','MEMSNAP.COM'):shutil.copy2(base/n,g/n)
        preimage={str(p.relative_to(g)).replace('\\','/'):sha(p) for p in sorted(g.rglob('*')) if p.is_file()};return g,preimage
    for name,row in (('SET6402',4),('SETTEXT',5)):
        g,preimage=guest('SETUP',name);(g/'WINXT').mkdir()
        for n,data in public.items():(g/'WINXT'/n).write_bytes(data)
        (g/'WINXT/OEMSETUP.INF').write_bytes(prepared_catalog)
        shutil.copy2(base/'WINXT/CGA.GR2',g/'WINXT/CGA.GR2')
        shutil.copy2(u/'OEMSETUP.INF',g/'WINXT/OEMBASE.INF')
        shutil.copy2(base/'WINXT/READY.TAG',g/'WINXT/READY.TAG')
        for n in ('WINXT.BAT','MODES.BAT'):shutil.copy2(a.native_emitter/n,g/'WINXT'/n)
        helpers={}
        for n in ('SKCTRL.COM','DRAIN.COM'):
            shutil.copy2(a.controller/n,g/n);helpers[n]=sha(g/n)
        helpers['MEMSNAP.COM']=sha(g/'MEMSNAP.COM')
        boot={'display.drv':'TR56402.DRV' if row==4 else 'TXTMODE.DRV','fonts.fon':'XTCSYS.FON' if row==4 else 'XTTSYS.FON','fixedfon.fon':'XTCFIX.FON','oemfonts.fon':'XTCOEM.FON','286grabber':'CGA.GR2'}
        lines=['@echo off','set PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\','C:\\WINXT\\SHELLSEL RECOVER C:\\WINDOWS\\SYSTEM.INI','if errorlevel 1 goto FAIL','C:\\WINXT\\XTMODE RECOVER C:\\WINDOWS\\SYSTEM.INI','if errorlevel 1 goto FAIL','C:\\WINXT\\XTMODE ACCEPT C:\\WINDOWS\\SYSTEM.INI','if errorlevel 1 goto FAIL','C:\\WINXT\\CPSET CHECK C:\\WINDOWS','if errorlevel 1 goto FAIL','C:\\WINXT\\RESERVE','if errorlevel 1 goto FAIL','cd \\WINDOWS','C:\\SKCTRL '+str(row),'if errorlevel 1 goto FAIL','DX-CAPTURE /V C:\\WINDOWS\\SETUP.EXE','echo RETURNED>C:\\SETRET.OK','copy SYSTEM.INI C:\\SELECTED.INI >NUL','copy WIN.COM C:\\SELECTED.COM >NUL','copy XTTEST.COM C:\\SELECTED.WAV >NUL','C:\\SKCTRL /D','if errorlevel 2 goto FAIL','C:\\DRAIN','C:\\MEMSNAP > C:\\AFTER.LOG','echo PASS>C:\\DONE.OK','goto END',':FAIL','echo FAILED>C:\\FAIL.TXT',':END','exit']
        tf(g/'START.BAT','\n'.join(lines)+'\n');helpers['START.BAT']=sha(g/'START.BAT')
        meta['fixtures'].append({'name':name,'kind':'setup','guest':'SETUP/'+name+'/GUEST','source':'SETUP/'+name+'/GUEST/WINXT','catalog_sha256':sha(g/'WINXT/OEMSETUP.INF'),'source_files':{p.name:sha(p) for p in (g/'WINXT').iterdir() if p.is_file()},'test_helpers':helpers,'owned_grabbers':{},'preimage':preimage,'row':row,'selected_boot':boot,'wave_preimage_sha256':sha(g/'WINDOWS/XTTEST.COM')})
        config('SETUP',name,[('C','SETUP/'+name+'/GUEST')],['C:','START.BAT'],60)
    b=out/'PREP/BUILD';b.mkdir(parents=True);(b/'TMP').mkdir()
    for n in ('PREPXT.C','XTPINS.H','PACKPINS.H','SZSTREAM.H'):shutil.copy2(f/n,b/n)
    meta['compile_source']={n:sha(b/n) for n in ('PREPXT.C','XTPINS.H','PACKPINS.H','SZSTREAM.H')}
    for name,which in (('PRODBLD','PREPXT'),('ZEROBLD','ZEROPREP')):
        flags=meta['compiler_flags'][which]
        commands=['B:','SET PATH=T:\\BIN','SET INCLUDE=T:\\INCLUDE','SET LIB=T:\\LIB','SET TEMP=B:\\TMP','T:\\BIN\\CL '+flags+' /Fo'+which+'.OBJ PREPXT.C > '+which+'.LOG','IF ERRORLEVEL 1 GOTO FAIL','T:\\BIN\\LINK4 /NOD /ST:4096 '+which+'.OBJ,'+which+'.EXE,'+which+'.MAP,T:\\LIB\\SLIBCE.LIB; >> '+which+'.LOG','IF ERRORLEVEL 1 GOTO FAIL','ECHO PASS>'+which+'.OK','GOTO END',':FAIL','ECHO FAILED>'+which+'.BAD',':END','EXIT']
        config('PREP',name,[('B','PREP/BUILD'),('T','')],commands,45)
    for name,exe,flag,seconds in (('PFAST','PREPXT','',60),('PZERO','ZEROPREP','',60),('PVERIFY','PREPXT',' /VERIFY',150)):
        g,preimage=guest('PREP',name);(g/'MEDIA').mkdir();shutil.copy2(base/'WINXT/CGA.GR2',g/'MEDIA/CGA.GR2');preimage['MEDIA/CGA.GR2']=pre.GR2;tf(g/'YES.TXT','Y\n');preimage['YES.TXT']=sha(g/'YES.TXT')
        lines=['C:','B:\\'+exe+' A:\\WINXT C:\\WINDOWS C:\\MEDIA'+flag+' < C:\\YES.TXT > C:\\PREP.LOG','IF ERRORLEVEL 1 GOTO FAIL','C:\\MEMSNAP > C:\\AFTER.LOG','ECHO PASS>C:\\DONE.OK','GOTO END',':FAIL','ECHO FAILED>C:\\FAIL.TXT',':END','EXIT']
        tf(g/'START.BAT','\n'.join(lines)+'\n')
        meta['fixtures'].append({'name':name,'kind':'prep','guest':'PREP/'+name+'/GUEST','source':'TRANSPORT/WINXT','catalog_sha256':meta['catalog_sha256'],'source_files':{n:hashlib.sha256(data).hexdigest() for n,data in transport.items()},'test_helpers':{n:sha(g/n) for n in ('START.BAT','MEMSNAP.COM')},'owned_grabbers':{'MEDIA/CGA.GR2':pre.GR2},'preimage':preimage})
        config('PREP',name,[('C','PREP/'+name+'/GUEST'),('B','PREP/BUILD'),('A','TRANSPORT')],['C:','START.BAT'],seconds)
    # The familiar runner is copied with mandatory pre/post validation, not bypassed.
    runner=(HERE/'LEASE.PY').read_text('ascii').replace('seconds=min(60,int(job[\'seconds\']))','seconds=min(150,int(job[\'seconds\']))')
    runner=runner.replace('import subprocess,time','import subprocess,time\nimport PREFLITE\nfrom pathlib import Path')
    runner=runner.replace("inputs=json.loads((workspace/'INPUTS.JSON').read_bytes());queue=", "inputs=json.loads((workspace/'INPUTS.JSON').read_bytes());kit=Path(inputs['kit_root']).resolve();PREFLITE.check(kit,workspace.name.lower());queue=")
    runner=runner.replace("if conflicts():raise RuntimeError('Conflicting emulator before job; no launch')","PREFLITE.check(kit,workspace.name.lower(),job['purpose'])\n            if conflicts():raise RuntimeError('Conflicting emulator before job; no launch')")
    runner=runner.replace("cfg=Path(job['config']).resolve();assert cfg.is_relative_to(workspace)","assert job==PREFLITE.readjson(kit/'KIT.JSON')['jobs'][job['purpose']],'Queued job differs from frozen plan'\n            assert job['purpose'] in inputs['planned_jobs'],'Job not in this lease group'\n            cfg=(kit/job['config']).resolve();assert cfg.is_relative_to(workspace)")
    runner=runner.replace("                time.sleep(.3)","                time.sleep(.3)")
    runner=runner.replace("status['active']='idle';save();print('JOB '+json.dumps(rec),flush=True)","if rec['exit_code']!=0:raise RuntimeError('Bounded guest did not return; dependent jobs stopped')\n            rec['validation']=PREFLITE.finish(kit,job['purpose'])\n            status['active']='idle';save();print('JOB '+json.dumps(rec),flush=True)")
    # Missing markers do not hold an idle lease until its deadline.
    runner=runner.replace("(workspace/'PAUSE.LEASE').write_text(status['paused_reason'])","raise RuntimeError(status['paused_reason'])")
    runner=runner.replace("if not jobs:time.sleep(.2);continue","if not jobs:\n                if len(seen)==len(inputs['planned_jobs']):break\n                time.sleep(.2);continue")
    tf(out/'TOOLS/RUNNER.PY',runner);shutil.copy2(HERE/'PREFLITE.PY',out/'TOOLS/PREFLITE.PY')
    for group,order,minutes in (('SETUP',['SET6402','SETTEXT'],3),('PREP',['PRODBLD','ZEROBLD','PFAST','PZERO','PVERIFY'],7)):
        ws=out/group;(ws/'QUEUE').mkdir();(ws/'PENDING').mkdir()
        group_inputs=dict(inputs);group_inputs.update(kit_root=str(out),source=str(out/'SOURCE'),planned_jobs=order,status='Host prepared only; explicit allocation required')
        tf(ws/'INPUTS.JSON',json.dumps(group_inputs,indent=2)+'\n')
        for i,name in enumerate(order):tf(ws/'PENDING'/('%02d-'%i+name+'.JSON'),json.dumps(meta['jobs'][name],indent=2)+'\n')
        tf(ws/'STOP.LEASE','Manual browser testing owns the shared slot. No launch until parent explicitly allocates this group.\n')
    source_roots=['CANDIDATE','TRANSPORT','SOURCE','CONTROL','TOOLS']
    frozen={str(p.relative_to(out)).replace('\\','/'):sha(p) for folder in source_roots for p in sorted((out/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for name,j in meta['jobs'].items():frozen[j['config']]=sha(out/j['config'])
    for case in meta['fixtures']:
        for n,h in case['test_helpers'].items():frozen[case['guest']+'/'+n]=h
        for n,h in case['source_files'].items():frozen[case['source']+'/'+n]=h
        for n,h in case['owned_grabbers'].items():frozen[case['guest']+'/'+n]=h
    meta['frozen_source']=frozen
    meta['requested_leases']={'setup_minutes':3,'prep_minutes':7,'total_bound_minutes':10}
    meta['timing_basis']={'previous_two_build_job_bound_seconds':25,'previous_guest_stopped_after_seconds':23.094,'production_completed_before_stop':True,'diagnostic_wall_time_measured':False,'historical_default_guest_clock_ms':[4120,33230],'historical_VERIFY_guest_clock_ms':[41420,74260],'guest_clock_is_not_host_wall_estimate':True,'new_PROD_and_ZERO_bounds_seconds':[45,45],'new_default_bounds_seconds':[60,60],'new_VERIFY_bound_seconds':150}
    tf(out/'KIT.JSON',json.dumps(meta,indent=2,sort_keys=True)+'\n')
    report=pre.check(out);tf(out/'HOST-PREFLIGHT.JSON',json.dumps(report,indent=2)+'\n')
    tf(out/'START-HERE.TXT',r'''FROZEN FINAL-GATES KIT - PRIVATE LOCAL FIXTURES - NOT A RELEASE

All guest runs remain paused for Chad's manual browser test. STOP.LEASE is
present in both groups. No authorization is granted by this package.

Host check: python TOOLS\PREFLITE.PY KIT-DIRECTORY
Future runner: python TOOLS\RUNNER.PY --workspace KIT\SETUP --minutes 3
or KIT\PREP --minutes 7, only after explicit allocation. Copy the frozen
PENDING jobs into QUEUE and remove STOP.LEASE only within that allocation.
The runner rechecks every catalog/helper/resource/path before the lease and
each job. Native failure, timeout or bad bytes stop dependents and release
the shared lock in finally. Completed groups release early automatically.

Setup uses five-mode plus TEXT source catalogs from the exact candidate.
No SYSTEM.INI mode is authored by the host. The controller's 40-second arm
still disarms unknown prompts without cancellation keys. Each guest is
bounded at 60 seconds. Genuine native captures stay with its fresh clone.

PREP builds production and diagnostics separately (45 seconds each). Fresh
production default and instrumented default preparations each get 60 seconds.
Explicit production VERIFY gets 150 seconds; it is never a vintage default.
New counters remain unmeasured. Only diagnostic PZERO reports/traps SHA work;
production PFAST separately verifies native default output bytes. Each test
checks original Windows/boot bytes and return to 624 KB DOS mode 3.

Only CGA.GR2 is gathered. DOS/Windows, Setup, SYSTEM\WIN.CNF, kernel and other
installed non-font Windows components remain necessary. Source catalog rows
use XTSTATIC.LGO and WXTSPL01.RLE, producing common WIN.COM 7,879 bytes.
The slow wave, seven original fonts and drivers are unchanged. At 160 pixels
dialogs can clip; TEXT GUI corruption is still experimental and opt-in.

Corrected documentation changes helper pins and requires new native builds.
Old failure roots and the prior host review image remain untouched. No E
qualified staging, installed Windows/CF writes or publication are authorized.
Private Windows fixtures and external compiler/emulator must never ship.
''')
    blueprint={str(p.relative_to(out)).replace('\\','/'):p.read_bytes() for folder in ('CANDIDATE','SOURCE','CONTROL','TOOLS') for p in (out/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    blueprint['START-HERE.TXT']=(out/'START-HERE.TXT').read_bytes()
    recipe={'input_pins':{'base_ini_sha256':meta['base_ini_sha256'],'controller':controller,'runtime_pins':meta['runtime_pins'],'compile_source':meta['compile_source']},'job_plan':{n:{'seconds':j['seconds'],'mounts':j['mounts']} for n,j in meta['jobs'].items()},'native_runs_authorized':False,'private_bytes_in_blueprint':False}
    blueprint['RECIPE.JSN']=(json.dumps(recipe,indent=2,sort_keys=True)+'\n').encode('ascii')
    pkg.write_zip(out/'FINAL-GATES-SOURCE.ZIP',blueprint)
    tf(out/'FINAL-GATES-SOURCE.SHA',sha(out/'FINAL-GATES-SOURCE.ZIP')+'  FINAL-GATES-SOURCE.ZIP\n')
    print(json.dumps({'host_preflight':report,'source_kit_sha256':sha(out/'FINAL-GATES-SOURCE.ZIP'),'source_kit_bytes':(out/'FINAL-GATES-SOURCE.ZIP').stat().st_size,'requested_minutes':meta['requested_leases'],'no_guest_launched':True},indent=2))
if __name__=='__main__':main()
