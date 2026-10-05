#!/usr/bin/env python3
from pathlib import Path
import os,fcntl,subprocess
P=Path(__file__).resolve().parents[1]
with (P.parent/'borders-text-20261005/emulator.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 with (P/'build/HOSTART02.LOG').open('w') as out:
  result=subprocess.run(['/workspace/shared/dosbox-x/run','-nopromptfolder','-conf',str(P/'build/BUILD.CNF')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=out,stderr=subprocess.STDOUT,timeout=120)
print(result.returncode)
print((P/'src/BUILD.LOG').read_text())
assert result.returncode==0 and (P/'src/BUILD.OK').exists()
