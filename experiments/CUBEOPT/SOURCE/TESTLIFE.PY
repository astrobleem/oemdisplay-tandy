"""Compile actual stop/WM_DESTROY code with API spies; verify focus policy, not native ordering."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]

def block(text,marker):
    start=text.index(marker);masked=re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*',lambda m:' '*len(m[0]),text,flags=re.S)
    at=masked.index('{',start);depth=0
    for end in range(at,len(masked)):
        if masked[end]=='{':depth+=1
        elif masked[end]=='}':
            depth-=1
            if not depth:return text[start:end+1]
    raise ValueError('Unclosed production function')

STUB=r'''
#include <stdio.h>
#include <stdarg.h>
typedef void *HWND;typedef long LONG;typedef unsigned long DWORD;typedef char *LPSTR;
#define SW_SHOW 5
#define WM_USER 1024
static HWND saver,config,qa,previousActive,previousFocus,active,focus,capture;
static void *canvas,*bitmap,*edge;
static int closing,returnFocus,running,draining,timerOn,frames,errors,qaMode,showConfig,shutdown;
static int activations,focuses,quits,posts;
static DWORD drawTotal,drawMax,start;
HWND GetActiveWindow(void){return active;}
HWND GetCapture(void){return capture;}
HWND GetParent(HWND w){return w==(HWND)4?config:(HWND)0;}
HWND SetActiveWindow(HWND w){HWND old=active;activations++;active=w;return old;}
HWND SetFocus(HWND w){HWND old=focus;focuses++;focus=w;return old;}
int ShowWindow(HWND w,int how){if(how==SW_SHOW){activations++;active=w;}return 1;}
int IsWindow(HWND w){return w!=0;}
int IsWindowVisible(HWND w){return w!=0;}
int IsWindowEnabled(HWND w){return w!=0;}
int IsChild(HWND p,HWND w){return p==config&&w==(HWND)4;}
int KillTimer(HWND w,unsigned n){(void)w;(void)n;return 1;}
void ReleaseCapture(void){capture=0;}
void restoreCursor(void){}
void releaseDraw(void){canvas=bitmap=edge=0;}
DWORD GetTickCount(void){return 1000UL;}
int wsprintf(char *b,char *fmt,...){int n;va_list a;va_start(a,fmt);n=vsprintf(b,fmt,a);va_end(a);return n;}
void logtext(char *s){(void)s;}
void PostQuitMessage(int n){(void)n;quits++;}
int PostMessage(HWND w,unsigned m,unsigned wp,long lp){(void)w;(void)m;(void)wp;(void)lp;posts++;return 1;}
static LONG destroyBranch(HWND w);
int DestroyWindow(HWND w){(void)destroyBranch(w);return 1;}
@STOP@
static LONG destroyBranch(HWND w){
@DESTROY@
}
int main(void){int n;
 for(n=0;n<5;n++){
  saver=(HWND)1;config=(HWND)2;qa=(HWND)40;previousActive=config;previousFocus=(HWND)4;
  active=focus=(HWND)3;capture=(HWND)3;canvas=bitmap=edge=(void*)1;
  closing=returnFocus=draining=frames=errors=qaMode=shutdown=0;running=timerOn=showConfig=1;
  activations=focuses=quits=posts=0;drawTotal=drawMax=start=0;
  if(n==1){returnFocus=1;active=saver;capture=saver;}
  if(n==2){showConfig=0;config=0;}
  if(n==3)shutdown=1;
  if(n==4){qaMode=1;showConfig=0;config=0;}
  stop(saver,"policy-test");
  if(saver||running||draining||timerOn||canvas||bitmap||edge){puts("FAIL cleanup state");return 1;}
  if(n==1){if(active!=(HWND)2||focus!=(HWND)4||activations!=1||focuses!=1){puts("FAIL ordinary wake focus restore");return 1;}}
  else if(activations||focuses||active!=(HWND)3||focus!=(HWND)3){printf("FAIL ownership-loss activation requests=%d focus=%d\n",activations,focuses);return 1;}
  if(n==0&&capture!=(HWND)3){puts("FAIL foreign capture changed");return 1;}
  if((n==2||n==3)?quits!=1:quits!=0){puts("FAIL quit policy");return 1;}
  if(n==4?posts!=1:posts!=0){puts("FAIL QA callback policy");return 1;}
 }
 puts("PASS five production teardown paths; only ordinary input wake restores focus");return 0;
}
'''

def compile_run(source,out,compiler,env):
    raw=source.read_bytes();text=raw.decode('ascii').replace('\r\n','\n');stop=block(text,'static void stop(');proc=block(text,'LONG FAR PASCAL CubeProc(')
    after=proc.split('case WM_DESTROY:',1)[1];destroy=after.split('\n }\n return DefWindowProc',1)[0]
    if not destroy.rstrip().endswith('return 0;'):raise ValueError('Unexpected production teardown shape')
    out.mkdir();c=out/'LIFE.C';c.write_text(STUB.replace('@STOP@',stop).replace('@DESTROY@',destroy))
    exe=out/'LIFE.EXE';cmd=compiler+['-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',str(c),'-o',str(exe)]
    p=subprocess.run(cmd,capture_output=True,env=env);(out/'BUILD.LOG').write_bytes(p.stdout+p.stderr);p.check_returncode()
    r=subprocess.run([str(exe)],capture_output=True,env=env);(out/'RUN.LOG').write_bytes(r.stdout+r.stderr)
    return dict(source_sha256=hashlib.sha256(raw).hexdigest(),returncode=r.returncode,output=r.stdout.decode().strip(),stop_sha256=hashlib.sha256(stop.encode()).hexdigest(),destroy_sha256=hashlib.sha256(destroy.encode()).hexdigest())

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--control',type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    control=a.control
    if control is None:
        candidates=[HERE.parent/'EVIDENCE/INDEPENDENT/CUBE-BEFORE.C',ROOT.parent/'EVIDENCE/INDEPENDENT/CUBE-BEFORE.C']
        control=next((n for n in candidates if n.is_file()),None)
    if control is None:raise ValueError('Frozen pre-fix source control is required')
    env=os.environ.copy()
    if os.name=='nt':
        cc=[sys.executable,str(Path(os.environ['USERPROFILE'])/'Documents/Codex/toolchains/gcc-ucrt64.py'),'--'];env['PATH']=r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH','')
    else:cc=['gcc']
    before=compile_run(control,out/'before',cc,env);after=compile_run(HERE/'CUBE.C',out/'after',cc,env)
    if before['returncode']==0 or 'ownership-loss activation'not in before['output']or after['returncode']!=0:raise ValueError('Teardown regression control failed')
    result=dict(status='PASS',scope='Actual production stop and WM_DESTROY code under API stubs; not native message-order reproduction',before=before,after=after)
    (out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
