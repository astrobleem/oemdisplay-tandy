from pathlib import Path
import os, subprocess, tempfile
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='tscp-') as tmp:
 exe=Path(tmp)/'CPTEST.EXE'
 cc=os.environ.get('CC','gcc')
 subprocess.run([cc,'-x','c','-std=c89','-Wall','-Wextra','-Werror',
  '-I'+str(r),str(r/'CPTEST.C'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
