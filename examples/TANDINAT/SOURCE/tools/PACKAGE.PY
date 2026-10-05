#!/usr/bin/env python3
"""Package only project-owned artifacts. Never package fixture/toolchain files."""
from pathlib import Path
import json,hashlib,shutil,subprocess,zipfile,re
P=Path(__file__).resolve().parents[1];OUT=P/'package';ROOT=OUT/'TANDI02'
assert not ROOT.exists(),'Package into a clean destination'
(ROOT/'RUN').mkdir(parents=True);(ROOT/'SOURCE').mkdir();(ROOT/'EVIDENCE').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
exe=sha(P/'src/TANDI.EXE');db=sha(P/'build/TANDY.DAT')
assert json.loads((P/'build/DBTEST.JSON').read_text())['failed']==0
arttest=json.loads((P/'evidence/ARTTEST.JSON').read_text())
assert arttest['failed']==0 and arttest['skipped']==0
for mode in ['320x200x16','640x200x2','640x200x4','320x200x16-scale','320x200x16-corrupt']:
    source=P/'evidence'/('art-'+mode);r=json.loads((source/'RESULT.JSON').read_text())
    assert r['exe_sha256']==exe and 'COMPLETE=1' in r['log']
    assert r['returncode']==0 and 'RETURNED' in r['returned']
    if r['negative']:assert 'APP_ERROR=1' in r['log'] and 'ERRORS=1' in r['log']
    if not r['negative']:
        assert 'ERRORS=0' in r['log'] and r['partial_repaint_exact'] and r['border_expose_exact']
        assert r['focus_restore_exact'] and 'ART_READY=1' in r['log']
        assert 'QUESTION_CABINET_UNTOUCHED=0' not in r['log']
        assert r['eyes']['changed_pixels']>0 and r['eyes']['only_eye_rectangles_changed']
    target=ROOT/'EVIDENCE'/mode;target.mkdir()
    for file in source.glob('*.PNG'):shutil.copyfile(file,target/file.name)
    for file in source.glob('*.JSON'):shutil.copyfile(file,target/file.name)
    shutil.copyfile(source/'RUN.CNF',target/'RUN.CNF')
    for pattern in ['*.BIN','TANDI.LOG','CPUCHECK.TXT','LATERCPU.TXT','RESERVE.TXT','RETURNED.TXT']:
        for file in (source/'guest').glob(pattern):shutil.copyfile(file,target/file.name)
for name in ['SIMFINAL.JSON','SIMSCALE.JSON','ENGTEST.LOG','SCALECHECK.LOG','AUDIT.JSON','DISASM.TXT','PERFSUM.JSON','JSONCHECK.TXT','ARTPERF.JSON','ARTTEST.JSON','ARTDBTEST.LOG','UNCHANGED.JSON']:
    shutil.copyfile(P/'evidence'/name,ROOT/'EVIDENCE'/name)
for folder,patterns in [('src',['*.C','*.H','*.DEF','*.RSP','*.BAT']),('data',['*.JSON','*.TXT','*.PY']),('tools',['*.PY','*.C']),('tests',['*.PY','*.C']),('art',['*.PNG','*.JSON'])]:
    dest=ROOT/'SOURCE'/folder;dest.mkdir()
    for pat in patterns:
        for file in (P/folder).glob(pat):shutil.copyfile(file,dest/file.name)
(ROOT/'SOURCE/build').mkdir();(ROOT/'SOURCE/evidence').mkdir()
for name in ['TANDY.DAT','SCALE.DAT','DBREPORT.JSON','DBTEST.JSON','SCALE.JSON']:
    shutil.copyfile(P/'build'/name,ROOT/'SOURCE/build'/name)
for name in ['BUILD.LOG','TANDI.MAP']:
    shutil.copyfile(P/'src'/name,ROOT/'EVIDENCE'/name)
for name in ['README.TXT','ENGINE.TXT','BUILDING.TXT','ROSTER.TXT','PERF.TXT','QA.TXT','NOTICE.TXT']:
    shutil.copyfile(P/name,ROOT/name);shutil.copyfile(P/name,ROOT/'SOURCE'/name)
for source,name in [(P/'src/TANDI.EXE','TANDI.EXE'),(P/'build/TANDY.DAT','TANDY.DAT'),(P/'README.TXT','README.TXT'),(P/'ROSTER.TXT','ROSTER.TXT')]:
    shutil.copyfile(source,ROOT/'RUN'/name)
install='''@ECHO OFF
IF EXIST C:\\TANDINAT\\TANDI.EXE GOTO EXISTS
IF EXIST C:\\TANDINAT\\TANDY.DAT GOTO EXISTS
IF NOT EXIST C:\\TANDINAT\\NUL MD C:\\TANDINAT
COPY TANDI.EXE C:\\TANDINAT\\TANDI.EXE
IF ERRORLEVEL 1 GOTO BAD
COPY TANDY.DAT C:\\TANDINAT\\TANDY.DAT
IF ERRORLEVEL 1 GOTO BAD
ECHO Installed. Start Windows with your guarded WindowsXT launcher.
ECHO Normally: C:\\WINXT\\WINXT
ECHO Do not bypass reservation/recovery errors.
ECHO Program Manager File-Run: C:\\TANDINAT\\TANDI.EXE
GOTO END
:EXISTS
ECHO Existing TANDINATOR files found. No files were copied.
ECHO Back up the old files and remove them before installing an update.
GOTO END
:BAD
ECHO Copy failed. Check free disk space and the target folder.
:END
'''
(ROOT/'RUN/INSTALL.BAT').write_bytes(install.replace('\n','\r\n').encode('ascii'))
commits=subprocess.check_output(['git','log','--oneline'],cwd=P,text=True)
(ROOT/'SOURCE/COMMITS.TXT').write_bytes(commits.replace('\n','\r\n').encode('ascii'))
subprocess.run(['git','bundle','create',str(ROOT/'SOURCE/TANDI.BUNDLE'),'--all'],cwd=P,check=True)
rows=[]
for file in sorted(ROOT.rglob('*')):
    if file.is_file():rows.append(sha(file)+'  '+file.relative_to(ROOT).as_posix())
(ROOT/'SHA256.TXT').write_bytes(('\r\n'.join(rows)+'\r\n').encode('ascii'))
zip_path=OUT/'TANDINATOR-v0.2-native-art-private-kit.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for file in sorted(ROOT.rglob('*')):
        if file.is_file():z.write(file,file.relative_to(OUT))
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    assert z.read('TANDI02/RUN/TANDI.EXE')==(P/'src/TANDI.EXE').read_bytes()
    assert z.read('TANDI02/RUN/TANDY.DAT')==(P/'build/TANDY.DAT').read_bytes()
for mode in ['320x200x16','640x200x2','640x200x4']:
    shutil.copyfile(P/('evidence/art-'+mode+'/QUESTION.PNG'),OUT/('TANDINATOR-v0.2-'+mode+'.png'))
report={'zip':str(zip_path),'bytes':zip_path.stat().st_size,'sha256':sha(zip_path),'exe_sha256':exe,'database_sha256':db,'files':len(rows)+1}
(OUT/'PACKAGE02.JSON').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
