"""Capture exact host-check outcomes without invoking an emulator."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration'
phase = sys.argv[1]
names = (['tools/DOSINST/TESTDISP.PY', 'tools/SOUNDOWN/TESTFIX.PY',
          'tools/DOSINST/TESTCRC.PY'] if phase == 'basic' else
         ['tools/XR1PACK/TESTPREP.PY', 'tools/XR1PACK/TESTPUB.PY',
          'tools/DOSINST/TESTPUB.PY', 'tools/DOSINST/TESTHPXY.PY'])
rows = []
with (OUT / ('HOST-' + phase.upper() + '.LOG')).open('wb') as log:
    for name in names:
        data = (ROOT / name).read_bytes()
        p = subprocess.run([sys.executable, '-B', name], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.write((name + '\r\n').encode('ascii') + p.stdout + b'\r\n')
        log.flush()
        row = dict(script=name, source=dict(bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest()), return_code=p.returncode,
            output_sha256=hashlib.sha256(p.stdout).hexdigest())
        rows.append(row)
        print(name, 'PASS' if p.returncode == 0 else 'FAIL', flush=True)
        if p.returncode:
            raise SystemExit(p.returncode)
(OUT / ('HOST-' + phase.upper() + '.JSN')).write_bytes(
    (json.dumps(dict(status='PASS', phase=phase, checks=rows,
         native_execution=False), indent=2) + '\r\n').encode('ascii'))
