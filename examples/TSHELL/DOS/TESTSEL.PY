#!/usr/bin/env python3
"""Compile the exact C source with host syscall shims; exhaustive checkpoints."""
import os, pathlib, shutil, subprocess, tempfile, json
ROOT=pathlib.Path(__file__).resolve().parent
EXE=ROOT/'SHELLSEL'
subprocess.run(['gcc','-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-DHOST_TEST','-o',str(EXE),str(ROOT/'SHELLSEL.C')],check=True)
BASE=b'; preserve this\r\n[boot]\r\n  Shell = PROGMAN.EXE  ; original\r\nfonts.fon=VGA.FON\r\n[keyboard]\r\nx=1\r\n'
SELECTED=BASE.replace(b'PROGMAN.EXE',b'TSHELL.EXE')
count=0
logs=[]
def fixture(data=BASE):
    p=pathlib.Path(tempfile.mkdtemp(prefix='tsel-'))
    (p/'SYSTEM.INI').write_bytes(data)
    h=bytearray(192);h[:2]=b'MZ';h[60]=128;h[128:130]=b'NE';h[128+0x36]=2
    (p/'TSHELL.EXE').write_bytes(h)
    (p/'WIN.COM').write_bytes(b'\xeb\x09XWtest')
    return p
def run(p, cmd, crash=None, short=None):
    env=os.environ.copy()
    if crash:env['TS_CRASH']=str(crash)
    if short:env['TS_SHORT']=str(short)
    return subprocess.run([str(EXE),cmd,str(p/'SYSTEM.INI')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def ok(r):
    assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
def check(v,msg=''):
    global count
    assert v,msg
    count+=1
# Byte-exact idempotence, repeated launches, later edits.
p=fixture(); ok(run(p,'RECOVER')); ok(run(p,'SELECT')); ok(run(p,'SELECT'))
check((p/'SYSTEM.INI').read_bytes()==SELECTED)
changed=SELECTED.replace(b'x=1',b'x=2\r\nnew=later')
(p/'SYSTEM.INI').write_bytes(changed); ok(run(p,'RECOVER'))
check((p/'SYSTEM.INI').read_bytes()==changed.replace(b'TSHELL.EXE',b'PROGMAN.EXE'))
ok(run(p,'RECOVER')); ok(run(p,'SELECT')); ok(run(p,'RECOVER'))
check((p/'TSHELL.BAK').read_bytes()==BASE)
shutil.rmtree(p)
# Selection interruption after every completed mutation, through completion.
for step in range(1,20):
    p=fixture(); r=run(p,'SELECT',crash=step)
    if r.returncode==0:shutil.rmtree(p);break
    check(r.returncode==99,('selection crash',step,r.stderr))
    ok(run(p,'RECOVER')); check((p/'SYSTEM.INI').read_bytes()==BASE,step)
    ok(run(p,'SELECT')); ok(run(p,'RECOVER')); shutil.rmtree(p)
logs.append({'select_mutation_checkpoints':step-1})
# Recovery interruption, preserving arbitrary later unrelated edits.
for step in range(1,20):
    p=fixture();ok(run(p,'SELECT'))
    (p/'SYSTEM.INI').write_bytes(changed)
    r=run(p,'RECOVER',crash=step)
    if r.returncode==0:shutil.rmtree(p);break
    check(r.returncode==99,('recover crash',step,r.stderr))
    ok(run(p,'RECOVER')); check((p/'SYSTEM.INI').read_bytes()==changed.replace(b'TSHELL.EXE',b'PROGMAN.EXE'),step)
    ok(run(p,'RECOVER'));shutil.rmtree(p)
logs.append({'recover_mutation_checkpoints':step-1})
# Interrupt recovery again after every possible interrupted SELECT checkpoint.
nested=0
for initial in range(1,8):
    for stop in range(1,15):
        p=fixture();check(run(p,'SELECT',crash=initial).returncode==99)
        r=run(p,'RECOVER',crash=stop)
        if r.returncode==0:shutil.rmtree(p);break
        check(r.returncode==99,(initial,stop,r.stderr));ok(run(p,'RECOVER'))
        check((p/'SYSTEM.INI').read_bytes()==BASE,(initial,stop));nested+=1;shutil.rmtree(p)
logs.append({'nested_recovery_interruptions':nested})
# Recovery may restore the value but cannot discard a read-only journal.
p=fixture();ok(run(p,'SELECT'));(p/'TSHELL.JRN').chmod(0o444)
check(run(p,'RECOVER').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==BASE);check((p/'TSHELL.JRN').exists())
(p/'TSHELL.JRN').chmod(0o644);ok(run(p,'RECOVER'));shutil.rmtree(p)
# Malformed inputs, duplicates, controls, ambiguous states, bounded length.
for data in [b'', b'[boot]\r\nx=1\r\n', BASE+b'[boot]\r\nshell=x\r\n', BASE+b'[KEYBOARD]\r\ny=2\r\n', BASE.replace(b'fonts.fon',b'shell'), BASE.replace(b'PROGMAN.EXE',b''), BASE+b'\x00',BASE+b'a'*16001,BASE.replace(b'[boot]',b'[boot]junk'), BASE.replace(b'PROGMAN.EXE',b'TSHELL.EXE')]:
    p=fixture(data);r=run(p,'SELECT');check(r.returncode!=0);check((p/'SYSTEM.INI').read_bytes()==data);shutil.rmtree(p)
for name in ['TSHELL.JRN','TSHELL.SAV','TSHELL.BAK','TSHELL.NEW','TSHELL.OLD','TSHELL.RST']:
    p=fixture();(p/name).write_bytes(b'foreign file');r=run(p,'SELECT');check(r.returncode!=0,name);check((p/'SYSTEM.INI').read_bytes()==BASE);check((p/name).read_bytes()==b'foreign file');shutil.rmtree(p)
# Required app missing or invalid, read-only INI.
for name in ['TSHELL.EXE','WIN.COM']:
    p=fixture();(p/name).unlink();check(run(p,'SELECT').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==BASE);shutil.rmtree(p)
p=fixture();(p/'SYSTEM.INI').chmod(0o444);check(run(p,'SELECT').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==BASE);shutil.rmtree(p)
# Unexpected shell change and missing current must never roll back unrelated edits.
p=fixture();ok(run(p,'SELECT'));alien=changed.replace(b'TSHELL.EXE',b'OTHER.EXE');(p/'SYSTEM.INI').write_bytes(alien);check(run(p,'RECOVER').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==alien);check((p/'TSHELL.JRN').exists());shutil.rmtree(p)
p=fixture();ok(run(p,'SELECT'));(p/'SYSTEM.INI').unlink();check(run(p,'RECOVER').returncode!=0);check(not (p/'SYSTEM.INI').exists());shutil.rmtree(p)
# Faults inside write leave original untouched or selected with retained journal.
for cmd in ['SELECT','RECOVER']:
    for step in range(1,6):
        p=fixture()
        if cmd=='RECOVER':ok(run(p,'SELECT'))
        before=(p/'SYSTEM.INI').read_bytes();r=run(p,cmd,short=step)
        if r.returncode:
            check((p/'SYSTEM.INI').read_bytes()==before,(cmd,step))
            if cmd=='RECOVER':check((p/'TSHELL.JRN').exists())
        shutil.rmtree(p)
# Invalid executable headers never permit a config write.
for name,data in [('TSHELL.EXE',b'MZ'),('TSHELL.EXE',b'x'*192),('WIN.COM',b'test')]:
    p=fixture();(p/name).write_bytes(data);check(run(p,'SELECT').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==BASE);shutil.rmtree(p)
# SELECT itself is restartable after each completed mutation.
for step in range(1,8):
    p=fixture();check(run(p,'SELECT',crash=step).returncode==99);ok(run(p,'SELECT'));check((p/'SYSTEM.INI').read_bytes()==SELECTED);ok(run(p,'RECOVER'));shutil.rmtree(p)
# Unknown edits during recovery retain both evidence and the exact current bytes.
p=fixture();ok(run(p,'SELECT'));check(run(p,'RECOVER',crash=1).returncode==99)
alien=SELECTED+b'after=recovery-started\r\n';(p/'SYSTEM.INI').write_bytes(alien)
check(run(p,'RECOVER').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==alien);check((p/'TSHELL.JRN').exists());shutil.rmtree(p)
# Backup or ownership changes are never silently overwritten.
for name in ['TSHELL.BAK','TSHELL.SAV']:
    p=fixture();ok(run(p,'SELECT'));ok(run(p,'RECOVER'));(p/name).write_bytes(b'changed')
    check(run(p,'SELECT').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==BASE);check((p/name).read_bytes()==b'changed');shutil.rmtree(p)
# CRLF/LF/CR inputs, shell spacing and no trailing newline retained.
for data in [BASE.replace(b'\r\n',b'\n'),BASE.replace(b'\r\n',b'\r'),BASE.rstrip(b'\r\n'),BASE.replace(b'PROGMAN.EXE',b'C:\\WIN\\MYAPP.EXE /arg')]:
    p=fixture(data);ok(run(p,'SELECT'));ok(run(p,'RECOVER'));check((p/'SYSTEM.INI').read_bytes()==data);shutil.rmtree(p)
print(json.dumps({'passed':count,'checkpoints':logs},indent=2))
