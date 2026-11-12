"""Host-only geometry microbenchmark against immutable pre-optimization source.
No emulator, GDI, Windows frame-time or 8088 performance claim.
"""
from pathlib import Path
import argparse, hashlib, json, os, statistics, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '832daf29599c5a0a392a3f8135fa40206ae550af'
BASE_HASH = 'e73cc486cdf1bb33d26da5b8ec69a7b7c6062a981d96602751018f6505864986'
HARNESS = r'''
#include <stdio.h>
#include <time.h>
#include "CUBECORE.H"
void ReferenceFrame(unsigned,int,int,int,int,CFRAME*);
static volatile unsigned long checksum;
static void run(int reference) {
 unsigned long i; CFRAME f; clock_t start=clock();
 for(i=0;i<2000000UL;i++) {
  if(reference)ReferenceFrame((unsigned)(i&65535UL),112,64,168,96,&f);
  else CubeFrame((unsigned)(i&65535UL),112,64,168,96,&f);
  checksum+=(unsigned)f.point[i&7].x+(unsigned)f.shade[i%6];
 }
 printf("%s %.6f CPU seconds\n",reference?"baseline":"symmetry",(double)(clock()-start)/CLOCKS_PER_SEC);
}
int main(void){int i;for(i=0;i<7;i++){run(i&1);run(!(i&1));}printf("checksum %lu\n",checksum);return 0;}
'''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    base = subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE + ':examples/CUBE/SOURCE/CUBECORE.C'])
    if hashlib.sha256(base).hexdigest() != BASE_HASH:
        raise ValueError('Baseline source hash differs')
    (out/'BASE.C').write_bytes(base)
    (out/'BENCH.C').write_text(HARNESS)
    env = os.environ.copy()
    if os.name == 'nt':
        compiler = [sys.executable, str(Path(os.environ['USERPROFILE'])/'Documents/Codex/toolchains/gcc-ucrt64.py'), '--']
        env['PATH'] = r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH', '')
    else:
        compiler = ['gcc']
    flags = ['-x', 'c', '-std=c89', '-pedantic', '-Wall', '-Wextra', '-Werror', '-O2', '-I', str(HERE)]
    commands = []
    def run(args):
        commands.append(args)
        return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True, env=env)
    rename = ['-DCubeFrame=ReferenceFrame', '-DCubeSin=ReferenceSin', '-DCubeFaces=ReferenceFaces', '-DCubeEdges=ReferenceEdges']
    run(compiler+flags+rename+['-c', str(out/'BASE.C'), '-o', str(out/'BASE.O')])
    run(compiler+flags+['-c', str(HERE/'CUBECORE.C'), '-o', str(out/'OPT.O')])
    run(compiler+flags+['-c', str(out/'BENCH.C'), '-o', str(out/'BENCH.O')])
    run(compiler+[str(out/n) for n in ('BASE.O', 'OPT.O', 'BENCH.O')]+['-o', str(out/'BENCH.EXE')])
    raw = run([str(out/'BENCH.EXE')])
    (out/'BENCH.LOG').write_text(raw)
    samples = {name: [float(line.split()[1]) for line in raw.splitlines() if line.startswith(name+' ')] for name in ('baseline', 'symmetry')}
    result = dict(scope=__doc__, baseline_commit=BASE, baseline_sha256=BASE_HASH,
                  candidate_sha256=hashlib.sha256((HERE/'CUBECORE.C').read_bytes()).hexdigest(),
                  compiler=run(compiler+['--version']).splitlines()[0], commands=commands,
                  frames_per_sample=2000000, cpu_seconds=samples,
                  median_cpu_seconds={name: statistics.median(values) for name, values in samples.items()})
    (out/'RESULT.JSN').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['median_cpu_seconds']))

if __name__ == '__main__':
    main()
