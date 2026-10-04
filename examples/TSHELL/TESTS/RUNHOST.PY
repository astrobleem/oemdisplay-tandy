#!/usr/bin/env python3
"""Run portable host checks without generating files in the source tree."""
from pathlib import Path
import os,shutil,subprocess,sys,tempfile
root=Path(__file__).resolve().parent.parent
cc=os.environ.get('CC','gcc')
subprocess.run([sys.executable,str(root/'TESTS/GRPTEST.PY')],check=True)
with tempfile.TemporaryDirectory(prefix='tshell-tests-') as tmp:
 out=Path(tmp)
 for name in ['SHELLSEL.C','TESTSEL.PY']:
  shutil.copyfile(root/'DOS'/name,out/name)
 subprocess.run([sys.executable,str(out/'TESTSEL.PY')],check=True)
 cases=[
  ('TESTBOOT',['-std=c89','-I'+str(root/'TESTS/HSTINC'),str(root/'TESTS/TESTBOOT.C')]),
  ('TESTSV',['-std=c89','-DHOST_TEST',str(root/'TESTS/TESTSV.C'),str(root/'SVCORE.C')]),
  ('HOSTTEST',['-std=c89',str(root/'IDLE/TESTS/HOSTTEST.C')]),
 ]
 for name,args in cases:
  exe=out/name
  subprocess.run([cc,'-x','c']+args+['-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
subprocess.run([sys.executable,str(root/'IDLE/TESTS/VERIFY.PY'),str(root/'TSINPUT.DLL')],check=True)
print('TSHELL 06 portable host and DLL contract checks PASS')
