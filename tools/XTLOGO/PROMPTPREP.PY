"""Fresh prompt-driven native fixtures; host preparation only."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT.parent;OUT=WORK/'STATIC-PROMPT'
sys.path.insert(0,str(ROOT/'tools/XTFONTS'))
from NATIVE import config
MODES=('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE')
BUILD=OUT/'HOSTBUILD3'
def tf(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(p):return {str(f.relative_to(p)).replace('\\','/'):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def rootclean(g):
    for p in g.glob('*'):
        if p.is_file() and p.name not in ('AUTOEXEC.BAT','MEMSNAP.COM','TEXT3.COM') and p.suffix.upper() in ('.BAT','.LOG','.OK','.TXT','.INI','.COM','.WAV','.BIN'):p.unlink()
def helpers(g):
    for n in ('SKCTRL.COM','DRAIN.COM'):shutil.copyfile(BUILD/n,g/n)
def prepare():
    assert (BUILD/'CTRLQA.JSON').is_file(),'Host instruction QA required first'
    assert not (OUT/'CASES.JSON').exists(),'Fresh native fixture preparation required'
    (OUT/'QUEUE').mkdir()
    jobs=[];cases={}
    common='@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nC:\n'
    private=WORK/'FONT-NATIVE6/CGA/GUEST/WINDOWS';rt=ROOT/'distributions/WINXT'
    cnf=(private/'SYSTEM/WIN.CNF').read_bytes();art=(rt/'WXTSPL01.RLE').read_bytes()
    def save(name,g,s,seconds,extra):
        tf(g/'START.BAT',s)
        tf(g.parent/'RUN.CNF',config([('C',g)],'C:\nSTART.BAT\n',g,True))
        cases[name]={'initial_files':hashes(g),'seconds':seconds,**extra}
        jobs.append({'config':str(g.parent/'RUN.CNF'),'purpose':name,'seconds':seconds})
    g=OUT/'CTRLTEST/GUEST';g.mkdir(parents=True);helpers(g)
    shutil.copyfile(WORK/'STATIC-NATIVE/TR53216/GUEST/MEMSNAP.COM',g/'MEMSNAP.COM')
    s=common+'C:\\MEMSNAP > C:\\BEFORE.LOG\nC:\\SKCTRL 0\nC:\\DRAIN\nC:\\SKCTRL /D\nIF ERRORLEVEL 2 GOTO FAIL\nC:\\DRAIN\nC:\\MEMSNAP > C:\\AFTER.LOG\nECHO RETURNED>C:\\DONE.OK\nGOTO END\n:FAIL\nECHO CTRL_TEST_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n'
    save('CTRLTEST',g,s,10,{'kind':'Native install/remove/idle control; no Windows application'})
    selections=[('B64',1,True),('BTXT',5,True)]+[('C%d'%i,i,False) for i in range(6)]
    for name,index,baseline in selections:
        mode=MODES[index];g=OUT/name/'GUEST'
        shutil.copytree(WORK/'STATIC-NATIVE'/mode/'GUEST',g);rootclean(g);helpers(g)
        # Restore only the fixture's starting SYSTEM.INI from its actual snapshot.
        # The tested profile is always selected by real Windows Setup below.
        shutil.copyfile(g/'WINXT/BACKUP/B001/ROOT/SYSTEM.INI',g/'WINDOWS/SYSTEM.INI')
        if baseline:
            shutil.copyfile(WORK/'STATIC-DIAG-1/RC5/TINST.EXE',g/'WINXT/TINST.EXE')
            shutil.copyfile(WORK/'STATIC-DIAG-1/RC5/OEMSETUP.INF',g/'WINXT/OEMSETUP.INF')
            lgo=(private/'SYSTEM/CGALOGO.LGO').read_bytes();(g/'WINXT/CGALOGO.LGO').write_bytes(lgo)
        else:lgo=(rt/'XTSTATIC.LGO').read_bytes()
        (g/'WINDOWS/WIN.COM').write_bytes(cnf+lgo+art)
        s=common+'C:\\SKCTRL '+str(index)+'\nIF ERRORLEVEL 1 GOTO FAIL\nCD \\WINDOWS\n'
        s+='CALL C:\\WINXT\\WINXT.BAT SETUP > C:\\SETUP.LOG\n'
        s+='COPY SYSTEM.INI C:\\SELECTED.INI >NUL\nCOPY WIN.COM C:\\SELECTED.COM >NUL\nCOPY XTTEST.COM C:\\SELECTED.WAV >NUL\nECHO RETURNED>C:\\SETRETURN.OK\n'
        s+='C:\\SKCTRL /D\nIF ERRORLEVEL 1 ECHO CTRL_INCOMPLETE>C:\\CTRLFAIL.TXT\nC:\\MEMSNAP > C:\\PREIDLE.LOG\nC:\\DRAIN\nC:\\MEMSNAP > C:\\AFTER.LOG\nECHO RETURNED>C:\\DRAIN.OK\nIF EXIST C:\\CTRLFAIL.TXT GOTO FAIL\nECHO RETURNED>C:\\DONE.OK\nGOTO END\n:FAIL\nECHO PROMPT_SEQUENCE_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n'
        save(name,g,s,60,{'kind':'Prompt-driven real Setup + unhook/idle/teardown','profile':mode,'index':index,'baseline':baseline,'windows_before_setup':hashes(g/'WINDOWS')})
    for name,mode in (('G160','TR51616'),('G3204','TR53204'),('G6402','TR56402')):
        g=OUT/name/'GUEST';shutil.copytree(WORK/'STATIC-NATIVE'/mode/'GUEST',g);rootclean(g);helpers(g)
        expected=cnf+(rt/'XTSTATIC.LGO').read_bytes()+art
        assert (g/'WINDOWS/WIN.COM').read_bytes()==expected
        assert 'display.drv='+mode+'.DRV' in (g/'WINDOWS/SYSTEM.INI').read_text('ascii')
        s=common+'C:\\WINXT\\RESERVE.COM\nCD \\WINDOWS\nC:\\MEMSNAP > C:\\BEFORE.LOG\nCALL C:\\WINXT\\WINXT.BAT > C:\\LAUNCH.LOG\nC:\\MEMSNAP > C:\\PREIDLE.LOG\nC:\\DRAIN\nC:\\MEMSNAP > C:\\AFTER.LOG\nIF NOT EXIST C:\\FONT.LOG GOTO FAIL\nCOPY C:\\FONT.LOG C:\\COMPLETE.LOG >NUL\nECHO RETURNED>C:\\DONE.OK\nGOTO END\n:FAIL\nECHO PROBE_MISSING>C:\\FAIL.TXT\n:END\nEXIT\n'
        save(name,g,s,55,{'kind':'Remaining graphics normal launcher GDI gate','profile':mode})
    recovery=OUT/'RECOVERY';recovery.mkdir();s=''
    for i,mode in enumerate(MODES):
        g=OUT/('C%d'%i)/'GUEST'
        s+='Z:\nMOUNT C "'+str(g)+'"\nC:\nCD \\WINDOWS\nECHO ROLLBACK_MUTATION>CONTROL.INI\nECHO ROLLBACK_MUTATION>WIN.INI\nC:\\WINXT\\TINST.EXE /ZERO\nCALL C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES > C:\\RESTORE.LOG\nIF ERRORLEVEL 1 ECHO NONZERO>C:\\RESTERR.TXT\nC:\\DRAIN\nECHO RETURNED>C:\\RESTRET.OK\nZ:\nMOUNT -U C\n'
    s+='EXIT\n';tf(recovery/'RUN.CNF',config([],s,recovery,True))
    jobs.append({'config':str(recovery/'RUN.CNF'),'purpose':'RECOVERY','seconds':45})
    for i,job in enumerate(jobs):tf(OUT/'QUEUE'/('%02d-%s.JSON'%(i,job['purpose'])),json.dumps(job))
    inputs=json.loads((WORK/'STATIC-NATIVE/INPUTS.JSON').read_bytes());inputs['status']='HOST PREPARED; 15-minute allocation begins at lock acquisition'
    tf(OUT/'INPUTS.JSON',json.dumps(inputs,indent=2));tf(OUT/'CASES.JSON',json.dumps(cases,indent=2))
    tf(OUT/'STOP.LEASE','Host prepared; remove only when starting authorized 15-minute acquisition.\n')
    tf(OUT/'PLAN.JSON',json.dumps({'allocated_minutes_from_acquisition':15,'job_bounds_seconds':sum(j['seconds'] for j in jobs),'jobs':jobs,'stage_only_after_qualified':True,'publication_allowed':False},indent=2))
    print(json.dumps({'status':'HOST PREPARED ONLY','cases':len(jobs),'bound_seconds':sum(j['seconds'] for j in jobs)},indent=2))
if __name__=='__main__':prepare()
