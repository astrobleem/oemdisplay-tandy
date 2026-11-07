"""Hover damage regression; optionally compare an earlier tracker directory."""
from pathlib import Path
import os,subprocess,json,sys,argparse
p=argparse.ArgumentParser();p.add_argument('--cc',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',type=Path);a=p.parse_args()
R=Path(__file__).resolve().parent.parent;O=a.out.resolve();O.mkdir(exist_ok=True,parents=True);GCC=a.cc.resolve()
env=dict(os.environ,PATH=str(GCC.parent)+os.pathsep+os.environ['PATH'])
with (O/'LAYOUT.log').open('w') as log:
 subprocess.run([sys.executable,str(R/'TESTS/MENUTEST.PY'),'--cc',str(GCC),'--out',str(O/'shim')],stdout=log,stderr=subprocess.STDOUT,check=True)
h=(O/'shim/windows.h').read_text().replace('#endif','long TSMenuProc(int,unsigned,unsigned,long);\n#endif')
(O/'windows.h').write_text(h)
code=(O/'shim/MENUHOST.C').read_text().split('static void keys(',1)[0]
code=code.replace('static RECT rectangles[100];','static int frames,invalids,destroyed,clipL,clipT,clipR,clipB;\nstatic RECT rectangles[100];')
code=code.replace('int IntersectClipRect(int d,int l,int t,int r,int b){return 1;}','int IntersectClipRect(int d,int l,int t,int r,int b){clipL=l;clipT=t;clipR=r;clipB=b;return 1;}')
code=code.replace('int FrameRect(int d,RECT*r,int b){return 1;}','int FrameRect(int d,RECT*r,int b){if(clipL<=r->left&&clipT<=r->top&&clipR>=r->right&&clipB>=r->bottom)frames++;return 1;}')
code=code.replace('int DestroyWindow(int w){return 1;}int UpdateWindow(int w){return 1;}int InvalidateRect(int w,void*p,int b){return 1;}','int DestroyWindow(int w){destroyed++;return 1;}int UpdateWindow(int w){TSMenuProc(w,WM_PAINT,0,0);return 1;}int InvalidateRect(int w,void*p,int b){invalids++;return 1;}')
code=code.replace('int BeginPaint(int w,PAINTSTRUCT*p){return 1;}','int BeginPaint(int w,PAINTSTRUCT*p){GetClientRect(w,&p->rcPaint);return 1;}')
code+=r'''
int main(void){int i,n,lev,before;POINT p;
 apps[3].name="Read notes";
 screenW=sw=160;screenH=sh=200;row=9;menuOwner=menuInstance=menuDC=1;depth=0;running=1;
 openmenu(1,0,99);selectrow(0,0);enter(1);selectrow(1,0);enter(1);
 frames=drawn=invalids=destroyed=0;before=nextwindow;
 for(i=0;i<1000;i++)selectrow(2,0);
 printf("UNCHANGED_ITEM text=%d full_frames=%d invalidations=%d opens=%d closes=%d\n",drawn,frames,invalids,nextwindow-before,destroyed);
 frames=drawn=invalids=destroyed=0;before=nextwindow;
 for(i=0;i<10;i++)trim(depth);
 printf("NOOP_TRIM text=%d full_frames=%d invalidations=%d opens=%d closes=%d\n",drawn,frames,invalids,nextwindow-before,destroyed);
 frames=drawn=invalids=destroyed=0;before=nextwindow;
 for(i=0;i<20;i++)selectrow(2,(i+1)&1);
 printf("TWENTY_ROW_CHANGES text=%d full_frames=%d invalidations=%d opens=%d closes=%d\n",drawn,frames,invalids,nextwindow-before,destroyed);
 frames=drawn=invalids=destroyed=0;before=nextwindow;
 p.y=levels[2].rect.top+4;
 for(i=0;i<100;i++){
  p.x=levels[2].rect.left+(i&1?1:-1);lev=hit(p,&n);
  if(lev>=0&&n>=0){selectrow(lev,n);if((state(&levels[lev],n)&MF_POPUP)&&lev==depth-1)enter(0);}
 }
 printf("OVERLAP_BOUNDARY text=%d full_frames=%d invalidations=%d opens=%d closes=%d depth=%d\n",drawn,frames,invalids,nextwindow-before,destroyed,depth);
 return 0;
}
'''

(O/'HOVHOST.C').write_text(code)
results={};sources=[('fixed',R)]
if a.baseline:sources.insert(0,('delivered',a.baseline.resolve()))
for label,path in sources:
 subprocess.run([str(GCC),'-std=c89','-w','-I'+str(O),'-I'+str(path),'-I'+str(R),'-x','c',str(O/'HOVHOST.C'),'-o',str(O/(label+'.exe'))],env=env,check=True)
 r=subprocess.run([str(O/(label+'.exe'))],capture_output=True,text=True,env=env,check=True)
 (O/(label+'.log')).write_text(r.stdout);results[label]=r.stdout;print(label+'\n'+r.stdout)
assert 'UNCHANGED_ITEM text=0 full_frames=0 invalidations=0 opens=0 closes=0' in results['fixed']
assert 'NOOP_TRIM text=0 full_frames=0 invalidations=0 opens=0 closes=0' in results['fixed']
assert 'TWENTY_ROW_CHANGES text=40 full_frames=0 invalidations=0 opens=0 closes=0' in results['fixed']
assert 'OVERLAP_BOUNDARY text=0 full_frames=0 invalidations=0 opens=0 closes=0 depth=3' in results['fixed']
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',results=results),indent=2))
