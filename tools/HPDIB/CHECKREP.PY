"""Independent framebuffer oracle plus expanded native DIB matrix/timing checks."""
from pathlib import Path
import collections,importlib.machinery,json,re,statistics,sys
ROOT=Path(__file__).resolve().parents[2]
O=importlib.machinery.SourceFileLoader('dib_repeat_pixel_oracle',str(ROOT/'experiments/SOLPERF/ORACLE.PY')).load_module()
def verify(out):
 result=O.verify(str(out));log=(out/'PANQA.LOG').read_text()
 rows=[{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)} for line in log.splitlines() if line.startswith('DIB w=')]
 wanted=collections.Counter((w,3,p,perm,0) for w in (1,7,8,9,15,16,17,37) for p in range(3) for perm in range(2))
 wanted.update([(37,11,2,1,1),(37,11,3,1,0),(37,11,3,1,1),(640,1,2,1,1)])
 wanted.update((80,32,p,1,0) for p in range(3) for trial in range(3))
 actual=collections.Counter(tuple(r[k] for k in ('w','h','pattern','perm','cross')) for r in rows)
 batch=re.findall(r'DIBBENCH dir=(SET|GET) calls=64 pattern=(\d+) trial=(\d+) ms=(\d+)',log)
 keys=collections.Counter((d,int(p),int(t)) for d,p,t,ms in batch)
 expected=collections.Counter((d,p,t) for d in ('SET','GET') for p in range(3) for t in range(3))
 passed=actual==wanted and all(r['setbad']==r['getbad']==r['guardbad']==0 for r in rows) and keys==expected and all(int(ms)>0 for d,p,t,ms in batch) and 'END FAILURES=0' in log
 result.update(dib_matrix_pass=passed,dib_cases=rows,benchmark_batches=[dict(direction=d,pattern=int(p),trial=int(t),ms=int(ms)) for d,p,t,ms in batch],native_failures_zero='END FAILURES=0' in log)
 if not passed:result['status']='FAIL'
 result['benchmark_summary']={d:{str(p):dict(median_ms=statistics.median([int(ms) for dd,pp,t,ms in batch if dd==d and int(pp)==p]),trials_ms=[int(ms) for dd,pp,t,ms in batch if dd==d and int(pp)==p]) for p in range(3)} for d in ('SET','GET')} if keys==expected else {}
 (out/'VERIFIED.JSN').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 r=verify(Path(sys.argv[1]));print(r['status']);raise SystemExit(0 if r['status']=='PASS' else 1)
