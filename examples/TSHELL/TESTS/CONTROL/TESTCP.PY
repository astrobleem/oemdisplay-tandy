from pathlib import Path
import os, shutil, subprocess, tempfile
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='tscp-') as tmp:
 exe=Path(tmp)/'CPTEST.EXE'
 # Keep the DOS source/shim uppercase; Linux resolves its lowercase include.
 shutil.copyfile(r/'WINDOWS.H',Path(tmp)/'windows.h')
 cc=os.environ.get('CC','gcc')
 subprocess.run([cc,'-x','c','-std=c89','-Wall','-Wextra','-Werror',
  '-I'+str(Path(tmp)),'-I'+str(r),str(r/'CPTEST.C'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
