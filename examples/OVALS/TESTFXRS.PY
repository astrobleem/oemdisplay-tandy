"""Actual saver pen-init/destroy snippets with injected resource failures.
Host GDI/resource stubs; not Windows ownership/lifecycle execution.
"""
from pathlib import Path
import argparse,json,subprocess,tempfile
HERE=Path(__file__).resolve().parent
def check():
 source=(HERE/'ORBITS.C').read_text();init=source[source.index('static int initDraw('):source.index('LONG FAR PASCAL SaverProc')];a=source.index(' case WM_DESTROY:');b=source.index(' }return DefWindowProc',a);cleanup=source[a:b].split('case WM_DESTROY:',1)[1]
 header=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define TRUE 1
#undef NULL
#define NULL 0
#define PS_SOLID 0
#define WM_USER 1024
#define RGB(r,g,b) ((unsigned long)(r)|((unsigned long)(g)<<8)|((unsigned long)(b)<<16))
typedef int HWND;typedef int HPEN;typedef unsigned long COLORREF;
static struct {int before;HPEN pens[8];int after;} pool;
#define ringPens pool.pens
static int colors,starCount,running,draining,saverMode,hidden,backDC,bitmap,oldBitmap,screenDC,saver,qaMode,qa;
static int failDC,failPen,creates,created,deleted,dcLive,dcReleases,cursorRestores,cursorShows,captureReleases,quitPosts,qaPosts;
static int live[8];
static int GetDC(int w){if(failDC)return 0;assert(!dcLive);dcLive=1;return 1001;}
static int ReleaseDC(int w,int dc){assert(dc==1001&&dcLive);dcLive=0;dcReleases++;return 1;}
static int CreatePen(int style,int width,COLORREF color){int n=creates++;assert(style==PS_SOLID&&width==1&&n<8);if(colors<=2)assert(color==RGB(255,255,255));if(failPen==n+1)return 0;assert(!live[n]);live[n]=1;created++;return 100+n;}
static int DeleteObject(int pen){int n=pen-100;assert(n>=0&&n<8&&live[n]);live[n]=0;deleted++;return 1;}
static int SelectObject(int dc,int object){assert(0);return 0;}
static int DeleteDC(int dc){assert(0);return 0;}
static void KillTimer(int w,int id){assert(id==1);}
static int GetCapture(void){return saverMode?saver:0;}
static void ReleaseCapture(void){captureReleases++;}
static void restoreOwnedCursor(void){cursorRestores++;}
static void ShowCursor(int yes){assert(yes);cursorShows++;}
static void PostMessage(int w,int m,int a,int b){assert(m==WM_USER+3);qaPosts++;}
static void PostQuitMessage(int code){assert(!code);quitPosts++;}
'''
 tests=r'''
int main(void){int c,n,f,q,cycle,i,result,expected;int modes[]={2,4,16};long cases=0;
for(c=0;c<3;c++)for(n=2;n<=16;n*=2)for(f=0;f<10;f++)for(q=0;q<2;q++)for(cycle=0;cycle<3;cycle++){
 assert(!dcLive);for(i=0;i<8;i++)assert(!live[i]&&!ringPens[i]);
 colors=modes[c];starCount=n;failDC=f==9;failPen=f>=1&&f<=8?f:0;
 creates=created=deleted=dcReleases=cursorRestores=cursorShows=captureReleases=qaPosts=quitPosts=0;
 running=draining=hidden=1;saverMode=1;saver=7;qa=8;qaMode=q;pool.before=0x5555;pool.after=0x6666;
 result=initDraw(7);expected=f==0?8:f==9?0:f-1;assert(result==(f==0)&&created==expected);
 destroy(7);assert(!dcLive&&!screenDC&&!saver&&!running&&!draining&&!hidden&&deleted==created);
 assert(dcReleases==(f==9?0:1)&&cursorRestores==1&&cursorShows==1&&captureReleases==1);
 assert(qaPosts==q&&quitPosts==!q);assert(pool.before==0x5555&&pool.after==0x6666);
 for(i=0;i<8;i++)assert(!live[i]&&!ringPens[i]);
 /* Cleanup is resource-idempotent even when no resources remain. */
 saverMode=0;destroy(7);assert(deleted==created&&dcReleases==(f==9?0:1)&&cursorShows==1);cases++;
}
printf("PASS resource_cases=%ld (three repeated cycles, ten failure/success points)\n",cases);return 0;}
'''
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)
  def build(name,body):
   src=root/(name+'.c');exe=root/name;src.write_text(header+init+'\nstatic int destroy(int w){int n;'+body+'}\n'+tests);subprocess.run(['gcc','-std=c89','-O1','-fsanitize=undefined,address','-fno-sanitize-recover=all',str(src),'-o',str(exe)],check=True);return subprocess.run([str(exe)],capture_output=True,text=True)
  normal=build('normal',cleanup)
  if normal.returncode:raise ValueError(normal.stdout+normal.stderr)
  for name,replacement in [('count-dependent','n<starCount'),('out-of-bounds','n<16')]:
   mutant=cleanup.replace('n<8','n<starCount' if name=='count-dependent' else 'n<16')
   if mutant==cleanup:raise ValueError('Mutation anchor missing')
   r=build(name,mutant)
   if r.returncode==0:raise ValueError('Resource cleanup mutation escaped: '+name)
 return {'pass':True,'result':normal.stdout.strip(),'cleanup_mutations_detected':['density-dependent early exit','16-element walk of8-pen array'],'scope':'host exact source snippets, ASan/UBSan, allocation/DC/cursor/cleanup stubs; no native Windows lifecycle/quantization/ownership proof'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=check();a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
