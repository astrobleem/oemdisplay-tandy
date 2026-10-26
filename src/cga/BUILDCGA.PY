#!/usr/bin/env python3
"""Scheduled native CGA build through BUILD88 and the existing shared runner.

An explicit coordinated emulator slot is required before invoking this tool.
--lease is the existing shared lock, not a new/private lock. Merely creating
or acquiring a lock is not scheduling authorization. No guest is run by
STAGECGA.PY, TESTCGA.PY or CGAFONT.PY.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
from pathlib import Path
from STAGECGA import MODES, read, write

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--mode', choices=tuple(MODES), required=True)
    ap.add_argument('--hardware', choices=('ibm-cga',), required=True,
                    help='Explicit evaluation target; no autodetection or clone/PCjr/Tandy claim')
    ap.add_argument('--dosbox', type=Path, required=True)
    ap.add_argument('--lease', type=Path, required=True)
    args = ap.parse_args()
    repo,out = args.repo.resolve(),args.out.resolve()
    # A pinned cga source view must carry its own builder and first-party kit.
    if HERE != repo/'src'/'cga':
        ap.error('Run the builder inside the supplied commit-pinned cga view')
    base = repo/'src'/'tandysw'
    sys.path.insert(0,str(base))
    b88 = importlib.machinery.SourceFileLoader('build88_cga',str(base/'BUILD88.PY')).load_module()
    runner = importlib.machinery.SourceFileLoader('cga_rundos',str(repo/'tools'/'SOUNDOWN'/'RUNDOS.PY')).load_module()
    state = {}
    original_prepare = b88.baseline.prepare

    def prepare(r,o):
        renderer,resources = original_prepare(r,o)
        state.update(renderer=renderer,resources=resources)
        return renderer,resources

    def run(command,env,path,timeout=180):
        if 'patched' not in state:
            if args.mode == '160x100x16':
                patch = importlib.machinery.SourceFileLoader('cga100_build',str(HERE/'CGA100.PY')).load_module()
                state['patched'] = patch.stage(state['renderer'],state['resources'])
            else:
                state['patched'] = {'normal_mode':'upstream staged bytes unchanged'}
        # Reuse the watchdog/lease runner. Give each child fresh receipts.
        job = out/('native-'+path.stem)
        job.mkdir()
        config = Path(command[command.index('-conf')+1])
        lines = [command[i+1] for i,v in enumerate(command[:-1]) if v == '-c']
        write(job/'BUILD.CNF',read(config)+'\n'+'\n'.join(lines)+'\nexit\n')
        runner.run(args.dosbox,job/'BUILD.CNF',args.lease,timeout)
        shutil.copyfile(job/'HOST.LOG',path)

    b88.baseline.prepare = prepare
    b88.bounded_run = run
    sys.argv = ['BUILD88.PY','--repo',str(repo),'--out',str(out),'--dosbox',str(args.dosbox),
                '--mode',MODES[args.mode][0]]
    b88.main()
    result = json.loads((out/'RESULT.json').read_bytes())
    if result.get('build') != 'PASS' or 'patched' not in state:
        raise RuntimeError('Missing complete BUILD88 acceptance evidence')
    original = out/result['mode']['profile']['driver']
    target = out/MODES[args.mode][1]
    shutil.copyfile(original,target)
    record = dict(mode=args.mode,driver=target.name,hardware=args.hardware,build='PASS',
                  runtime='NOT_TESTED',sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  bytes=target.stat().st_size,adapter=state['patched'],
                  build88_audits='RESULT.json',native_process_receipts='native-*/PROCESS.JSON')
    write(out/'CGABUILD.JSN',json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__ == '__main__': main()
