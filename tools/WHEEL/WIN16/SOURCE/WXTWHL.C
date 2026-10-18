/* Optional Windows 3.0 / 8086 vertical wheel bridge. No hooks or ISR calls.
   The existing MOUSE driver remains the hardware owner. All USER work runs
   from this task's window procedure. Synthetic ingress exists only in /QA. */
#define WINVER 0x0300
#ifdef WHEEL_HOST
#include "../HOST/WINSTUB.H"
#else
#include <windows.h>
#include <dos.h>
#endif
#include "WHEEL.H"
typedef WORD (FAR PASCAL *WHEELVER)(void);
typedef int (FAR PASCAL *WHEELREAD)(void);
typedef WORD (FAR PASCAL *WHEELLOST)(void);
static WHEELREAD wheelRead;
static WHEELLOST wheelLost;
static WORD wheelMessage,qaMessage;
static BOOL qa,busy,blocked,owned;
static HWND lastFocus,lastActive;
static DWORD lastTick,lastDos,stats[ST_COUNT];
static signed char queue[32];
static unsigned head,tail;
static unsigned count(void) {return (tail-head)&31;}
static void clear(void) {stats[ST_DISCARD]+=count();head=tail=0;}
static void push(int d) {
 unsigned next=(tail+1)&31,n;
 if(!d)return;
 if(next==head){++stats[ST_DROP];return;}
 queue[tail]=(signed char)d;tail=next;n=count();
 if((DWORD)n>stats[ST_HIGH])stats[ST_HIGH]=(DWORD)n;
}
static DWORD dosclock(void) {
 struct dostime_t t;_dos_gettime(&t);
 return ((DWORD)t.hour*3600L+(DWORD)t.minute*60L+t.second)*1000L+t.hsecond*10L;
}
static BOOL legacy(void) {
 HWND w=FindWindow("WindowsXTToiletPaper",NULL);
 return w && GetProp(w,CLIENT_PROP)!=(HANDLE)BRIDGE_VERSION;
}
static BOOL allowed(HWND f,HWND a) {
 HWND owner;
 if(!f||!a||!IsWindow(f)||!IsWindow(a)||IsIconic(a)||
    !IsWindowVisible(f)||!IsWindowEnabled(f)||!IsWindowEnabled(a)||
    GetSysModalWindow()||GetCapture())return FALSE;
 if(f!=a&&!IsChild(a,f))return FALSE;
 owner=GetWindow(a,GW_OWNER);
 if(owner&&!IsWindowEnabled(owner))return FALSE;
 if(FindWindow("TandyMatrixSaver",NULL)||FindWindow("TandyMazeSaver",NULL)||
    FindWindow("TandyStarfieldSaver",NULL)||GetModuleHandle("TEXIT"))return FALSE;
 return TRUE;
}
/* Return kind: 1 own window bar, 2 scrollbar control, 3 edit, 4 list,
   5 opted-in wheel client. No sibling enumeration and no owner traversal. */
static int target(HWND focus,HWND active,HWND *receiver,HWND *bar) {
 HWND w=focus,p;LONG style;char name[40];int depth;
 *bar=NULL;
 /* An active app's explicit opt-in owns its child controls as well. */
 if(active&&GetProp(active,CLIENT_PROP)==(HANDLE)BRIDGE_VERSION){*receiver=active;return 5;}
 for(depth=0;w&&depth<16;++depth){
  if(!IsWindow(w)||!IsWindowVisible(w)||!IsWindowEnabled(w))return 0;
  if(GetProp(w,CLIENT_PROP)==(HANDLE)BRIDGE_VERSION){*receiver=w;return 5;}
  style=GetWindowLong(w,GWL_STYLE);
  if(!GetClassName(w,name,sizeof(name)))return 0;
  if(!lstrcmpi(name,"COMBOBOX"))return 0;
  p=(style&WS_CHILD)?GetParent(w):NULL;
  /* Single-line combo edits must not spill wheel activity to a document. */
  if(p){char parentName[16];GetClassName(p,parentName,sizeof(parentName));
   if(!lstrcmpi(parentName,"COMBOBOX"))return 0;}
  if(!lstrcmpi(name,"EDIT")){
   if(!(style&ES_MULTILINE))return 0;
   *receiver=w;return 3;
  }
  if(!lstrcmpi(name,"LISTBOX")){
   if(style&(LBS_MULTICOLUMN|LBS_OWNERDRAWVARIABLE))return 0;
   *receiver=w;return 4;
  }
  if(!lstrcmpi(name,"SCROLLBAR")){
   RECT rect;
   if(!p)return 0;
   /* USER 3.0 removes SBS_VERT from the retrieved style in the native
      fixture. Use a conservative geometry guard: accept only a tall bar;
      horizontal and square/size-box controls are excluded. */
   GetWindowRect(w,&rect);
   if(rect.right<=rect.left||rect.bottom-rect.top<=rect.right-rect.left)return 0;
   *receiver=p;*bar=w;return 2;
  }
  if(style&WS_VSCROLL){int lo,hi;GetScrollRange(w,SB_VERT,&lo,&hi);
   if(hi>lo){*receiver=w;return 1;}return 0;}
  if(w==active || !(style&WS_CHILD))break;
  w=p;
 }
 return 0;
}
static BOOL context(HWND f,HWND a) {
 return GetFocus()==f&&GetActiveWindow()==a&&allowed(f,a);
}
static void discardraw(void) {
 int n,d;for(n=0;n<32;++n){++stats[ST_READS];d=wheelRead();if(!d)break;++stats[ST_DISCARD];}
}
static void tick(void) {
 HWND f,a,r,bar;DWORD now,dos,begin;BOOL stop,gap;int n,d,kind,units,sign,budget;
 if(busy){++stats[ST_REENTRY];return;}busy=TRUE;begin=GetTickCount();++stats[ST_POLLS];
 /* Never compete with an unchanged TP, including a background TP. */
 if(legacy()){clear();blocked=TRUE;stats[ST_READY]=0;busy=FALSE;return;}
 f=GetFocus();a=GetActiveWindow();now=GetTickCount();dos=dosclock();
 gap=(DWORD)(now-lastTick)>500L || dos<lastDos ||
     (dos>=lastDos && dos-lastDos>(DWORD)(now-lastTick)+250L);
 lastTick=now;lastDos=dos;
 stop=!allowed(f,a)||gap||f!=lastFocus||a!=lastActive||blocked;
 lastFocus=f;lastActive=a;blocked=!allowed(f,a);
 stats[ST_READY]=!stop;
 if(stop){clear();discardraw();goto done;}
 /* At most the hardware ring capacity plus its empty sentinel per turn. */
 for(n=0;n<32;++n){++stats[ST_READS];d=wheelRead();if(!d)break;
  if(d>=-8&&d<=7)push(d);else ++stats[ST_DISCARD];}
 if(head==tail)goto done;
 kind=target(f,a,&r,&bar);if(!kind){clear();goto done;}
 /* Ordinary window notifications go through the recipient's task queue.
    Unlike synchronous cross-task SendMessage, this cannot leave the bridge
    waiting inside an application's scrolling/repainting loop. Controls keep
    the documented synchronous API. At most two queued messages per turn. */
 if(kind==1||kind==2){
  if(context(f,a)){
   sign=queue[head]<0?-1:1;
   if(PostMessage(r,WM_VSCROLL,sign<0?SB_LINEUP:SB_LINEDOWN,MAKELONG(0,bar))){
    ++stats[ST_MESSAGES];++stats[ST_UNITS];queue[head]=(signed char)(queue[head]-sign);
    if(!queue[head])head=(head+1)&31;
    if(PostMessage(r,WM_VSCROLL,SB_ENDSCROLL,MAKELONG(0,bar)))++stats[ST_MESSAGES];
   }
  }
  goto done;
 }
 budget=8;
 while(head!=tail && budget && context(f,a)){
  sign=queue[head]<0?-1:1;units=0;
  /* Coalesce only adjacent same-direction detents, never reversals. */
  while(head!=tail&&budget&&(queue[head]<0?-1:1)==sign){
   queue[head]=(signed char)(queue[head]-sign);++units;--budget;
   if(!queue[head])head=(head+1)&31;
  }
  if(kind==3){SendMessage(r,EM_LINESCROLL,0,MAKELONG(sign*units,0));++stats[ST_MESSAGES];}
  else if(kind==4){LONG top,total,next;
   top=SendMessage(r,LB_GETTOPINDEX,0,0L);total=SendMessage(r,LB_GETCOUNT,0,0L);
   if(top<0||total<=0){clear();break;}next=top+sign*units;
   if(next<0)next=0;
   if(next>=total)next=total-1;
   SendMessage(r,LB_SETTOPINDEX,(WPARAM)next,0L);++stats[ST_MESSAGES];
  }else if(kind==5){SendMessage(r,wheelMessage,(WPARAM)(sign*units),1L);++stats[ST_MESSAGES];}
  stats[ST_UNITS]+=units;
 }
 if(!context(f,a))clear();
done:
 if(wheelLost && !(stats[ST_POLLS]%10))stats[ST_LOST]=wheelLost();
 stats[ST_WORKMS]+=(DWORD)(GetTickCount()-begin);busy=FALSE;
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 if(qa&&m==qaMessage){
  if(lp==QA_INJECT && (int)wp>=-8&&(int)wp<=7&&wp){unsigned old=count();push((int)wp);return count()>old;}
  if(lp==QA_STAT&&wp<ST_COUNT)return stats[wp];
  if(lp==QA_BURST&&wp>0&&wp<=64){unsigned n;for(n=0;n<(unsigned)wp;++n)push(1);return count();}
  return 0;
 }
 switch(m){
 case WM_TIMER:if(wp==1)tick();return 0;
 case WM_QUERYENDSESSION:return TRUE;
 case WM_ENDSESSION:if(wp)DestroyWindow(w);return 0;
 case WM_CLOSE:DestroyWindow(w);return 0;
 case WM_DESTROY:
  KillTimer(w,1);RemoveProp(w,BRIDGE_PROP);RemoveProp(w,QA_PROP);clear();
  if(owned&&!legacy())discardraw();
  owned=FALSE;
  PostQuitMessage(0);return 0;
 }
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;HMODULE mouse;WHEELVER ver;FARPROC proc;
 (void)show;
 w=FindWindow(BRIDGE_CLASS,NULL);
 if(cmd&&(!lstrcmpi(cmd,"/STOP"))){if(w)PostMessage(w,WM_CLOSE,0,0L);return 0;}
 if(w||prev)return 0;
 qa=cmd&&!lstrcmpi(cmd,"/QA");
 mouse=GetModuleHandle("MOUSE");ver=mouse?(WHEELVER)GetProcAddress(mouse,"WheelApiVersion"):NULL;
 if(!ver||ver()!=BRIDGE_VERSION){
  MessageBox(NULL,"The Windows XT wheel driver API 1.0 is not loaded. Start Windows with your working WHEEL.DRV configuration, then launch the bridge.","Windows XT wheel",MB_OK|MB_ICONEXCLAMATION);
  return 2;
 }
 wheelRead=(WHEELREAD)GetProcAddress(mouse,"WheelReadDelta");
 wheelLost=(WHEELLOST)GetProcAddress(mouse,"WheelLostPackets");if(!wheelRead)return 3;
 wheelMessage=RegisterWindowMessage(WHEEL_NAME);qaMessage=RegisterWindowMessage(QA_NAME);
 if(!wheelMessage||!qaMessage)return 4;
 proc=MakeProcInstance((FARPROC)WndProc,inst);if(!proc)return 5;
 wc.style=0;wc.lpfnWndProc=(WNDPROC)proc;wc.cbClsExtra=wc.cbWndExtra=0;
 wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;
 wc.lpszMenuName=NULL;wc.lpszClassName=BRIDGE_CLASS;if(!RegisterClass(&wc)){FreeProcInstance(proc);return 5;}
 w=CreateWindow(BRIDGE_CLASS,"Windows XT wheel bridge",WS_OVERLAPPED,0,0,0,0,NULL,NULL,inst,NULL);
 if(!w){FreeProcInstance(proc);return 6;}
 lastFocus=GetFocus();lastActive=GetActiveWindow();lastTick=GetTickCount();lastDos=dosclock();
 /* Driver packets predate this ownership session and carry no timestamp. */
 blocked=TRUE;
 if(!SetTimer(w,1,100,NULL)){DestroyWindow(w);FreeProcInstance(proc);return 7;}
 if(!SetProp(w,BRIDGE_PROP,(HANDLE)BRIDGE_VERSION)||(qa&&!SetProp(w,QA_PROP,(HANDLE)BRIDGE_VERSION))){DestroyWindow(w);FreeProcInstance(proc);return 8;}
 owned=TRUE;
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 FreeProcInstance(proc);return 0;
}
