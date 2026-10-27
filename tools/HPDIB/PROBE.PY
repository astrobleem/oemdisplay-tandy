"""Generate the expanded native regression probe; execution is separately leased."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Probe source anchor changed: '+a[:60])
 return s.replace(a,b)
def generate(out):
 out.mkdir(parents=True,exist_ok=False)
 source=ROOT/'experiments/SOLPERF';scene=(source/'SCENE.C').read_text();dib=(source/'DIBTEST.C').read_text()
 dib=once(dib,'static struct DIBINFO16 dinfo,dout;','static struct DIBINFO16 dinfo,dout;\nstatic int dtrial;')
 for direction in ('SET','GET'):
  dib=once(dib,'DIBBENCH dir='+direction+' calls=64 ms=%lu\\r\\n",end-begin','DIBBENCH dir='+direction+' calls=64 pattern=%d trial=%d ms=%lu\\r\\n",pattern,dtrial,end-begin')
 start=dib.index('static void DibTests(void) {')
 dib=dib[:start]+'''static void DibTests(void) {
 HDC dc,mem;int i,p,perm;static int widths[8]={1,7,8,9,15,16,17,37};
 dc=GetDC(mainWnd);mem=CreateCompatibleDC(dc);Check("DIB_DC",mem!=0);
 if(mem){
  for(i=0;i<8;i++)for(p=0;p<3;p++)for(perm=0;perm<2;perm++)
   DCase(dc,mem,widths[i],3,p,perm,0,0);
  DCase(dc,mem,37,11,2,1,1,0);
  DCase(dc,mem,37,11,3,1,0,0);
  DCase(dc,mem,37,11,3,1,1,0);
  DCase(dc,mem,640,1,2,1,1,0);
  for(p=0;p<3;p++)for(dtrial=0;dtrial<3;dtrial++)
   DCase(dc,mem,80,32,p,1,0,1);
  DeleteDC(mem);
 }
 ReleaseDC(mainWnd,dc);
}
'''
 scene=once(scene,'int PASCAL WinMain(',dib+'\nint PASCAL WinMain(')
 scene=once(scene,' Bench();SetCursor(0);',' DibTests();Bench();SetCursor(0);')
 (out/'DIBREP.C').write_bytes(scene.replace('\n','\r\n').encode())
 record=dict(status='GENERATED_NOT_RUN',dib_cases=61,benchmark_batches=18,patterns=['uniform eight-pixel groups','checkerboard','dense'],trials_per_pattern=3,frames=41,sources={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ('SCENE.C','DIBTEST.C')})
 (out/'PROBE.JSN').write_bytes((json.dumps(record,indent=2)+'\n').replace('\n','\r\n').encode());return record
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',type=Path,required=True);v=a.parse_args();print(json.dumps(generate(v.out),indent=2))
