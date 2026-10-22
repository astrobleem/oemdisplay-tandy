#define WINVER 0x0300
#include <windows.h>
#include <string.h>
#include <stdlib.h>
#define ESC_XY 0x5860
#define ESC_MODE 0x5861
#define XY_MAP_LEFT 8
#define XY_MAP_TOP 58
#define XY_RECOVER 116
#define XY_CLASS_NAME "XYOverviewControl"
#define XY_WINDOW_TITLE "XY overview"
#define XY_HELPER_PATH "C:\\WINXT\\XYCTL.EXE"
#define QA_LINE_CAP 288
#define QA_CLASS_CAP 24
#define QA_TITLE_CAP 32
#define QA_MODULE_CAP 96
#define QA_ACTION_CAP 24
typedef int (FAR PASCAL *ROWS)(LPSTR,unsigned,unsigned);
typedef int (FAR PASCAL *STATS)(unsigned FAR *);
static HWND mainWnd;
static HCURSOR cursor,active;
static HFILE logFile;
static ROWS rowsProc;
static STATS statsProc;
/* The longest helper record is under 256 bytes with these bounded fields. */
static char buffer[3840],line[QA_LINE_CAP];
static int failures,run;
static unsigned stats[8];
static int pan[6];
static int overviewOnly,overviewSelectorPresent;
static void Log(LPSTR s) { _lwrite(logFile,s,lstrlen(s));_lclose(logFile);logFile=_lopen("C:\\XY.LOG",OF_WRITE);_llseek(logFile,0L,2); }
static void CopyDiagText(char *dest,LPSTR src,unsigned cap) {
 unsigned i;
 if(!cap)return;
 for(i=0;i+1<cap && src[i];i++)dest[i]=src[i];
 dest[i]=0;
}
static void Check(LPSTR s,int ok) {
 wsprintf(line,"CHECK %s=%d\r\n",s,ok!=0);Log(line);if(!ok)failures++;
}
static void Pump(DWORD ms) {
 DWORD start;MSG msg;start=GetTickCount();
 while((DWORD)(GetTickCount()-start)<ms)while(PeekMessage(&msg,0,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}
}
static void Pan(int x,int y) {
 HDC dc;int in[2],ok;dc=GetDC(0);in[0]=x;in[1]=y;
 ok=Escape(dc,ESC_XY,4,(LPSTR)in,(LPSTR)pan)>0;if(x!=-1 || !ok)Check("ESC_XY",ok);ReleaseDC(0,dc);
}
static int PanCheck(LPSTR label,int expectedX,int expectedY) {
 Pan(-1,0);wsprintf(line,"PAN %s expected=%d,%d actual=%d,%d\r\n",label,expectedX,expectedY,pan[0],pan[1]);Log(line);
 Check(label,pan[0]==expectedX && pan[1]==expectedY);return pan[0]==expectedX && pan[1]==expectedY;
}
static void RectRecord(LPSTR label,RECT *expected,RECT *actual) {
 wsprintf(line,"RECT %s expected=%d,%d,%d,%d actual=%d,%d,%d,%d\r\n",label,expected->left,expected->top,expected->right,expected->bottom,actual->left,actual->top,actual->right,actual->bottom);Log(line);
}
static void ExpectedHomeRect(RECT *before,RECT *expected) {
 int width,height,caption,maxX,maxY,x,y;
 width=before->right-before->left;height=before->bottom-before->top;
 caption=GetSystemMetrics(SM_CYCAPTION)+2*GetSystemMetrics(SM_CYFRAME);
 if(caption<1)caption=18;if(caption>height)caption=height;
 maxX=pan[2]-(width<pan[2]?width:pan[2]);if(maxX<0)maxX=0;
 maxY=pan[3]-(caption<pan[3]?caption:pan[3]);if(maxY<0)maxY=0;
 x=before->left;if(x<0)x=0;if(x>maxX)x=maxX;
 y=before->top;if(y<0)y=0;if(y>maxY)y=maxY;
 expected->left=x;expected->top=y;expected->right=x+width;expected->bottom=y+height;
}
static int RectOutsideDesk(RECT *r) {
 return r->right<=0 || r->left>=pan[4] || r->bottom<=0 || r->top>=pan[5];
}
static int RectSameSize(RECT *a,RECT *b) {
 return a->right-a->left==b->right-b->left && a->bottom-a->top==b->bottom-b->top;
}
static int RectSame(RECT *a,RECT *b) {
 return a->left==b->left && a->top==b->top && a->right==b->right && a->bottom==b->bottom;
}
static void Mode(int m) {HDC dc;dc=GetDC(0);Check("ESC_MODE",Escape(dc,ESC_MODE,2,(LPSTR)&m,0)>0);ReleaseDC(0,dc);}
static COLORREF Color(int k) {int r,g,b;r=(k&4)?170:0;g=(k&2)?170:0;b=(k&1)?170:0;if(k&8){r+=85;g+=85;b+=85;}return RGB(r,g,b);}
static void Pattern(HDC dc) {
 int x,y;RECT r;HBRUSH b;
 for(y=0;y<256;y+=32)for(x=0;x<640;x+=80){
  r.left=x;r.top=y;r.right=x+80;r.bottom=y+32;
  b=CreateSolidBrush(GetNearestColor(dc,Color((x/80+2*(y/32))&15)));FillRect(dc,&r,b);DeleteObject(b);
 }
 TextOut(dc,4,190,"BAND 199/200",12);TextOut(dc,340,234,"LOWER RIGHT",11);
}
static void Snap(int id,int visible,int x,int y) {
 HFILE f;char name[24];unsigned first,count,n,off;char FAR *video;POINT point;int rowsOK;
 active=visible?cursor:(HCURSOR)0;SetCursorPos(x,y);SetCursor(active);Pump(150);SetCursor(active);
 GetCursorPos(&point);x=point.x;y=point.y;Pan(-1,0);statsProc(stats);
 wsprintf(name,"C:\\S%03d.BIN",id);f=_lcreat(name,0);Check("SHADOW_FILE",f!=HFILE_ERROR);
 rowsOK=1;if(f!=HFILE_ERROR){for(first=0;first<256;first+=12){count=256-first;if(count>12)count=12;n=rowsProc(buffer,first,count);if(n!=count*320)rowsOK=0;if(_lwrite(f,buffer,n)!=n)rowsOK=0;}_lclose(f);}Check("ROWS_STREAM",rowsOK);
 wsprintf(name,"C:\\V%03d.BIN",id);f=_lcreat(name,0);video=(char FAR *)MAKELONG(0,0xb800);
 if(f!=HFILE_ERROR){for(off=0;off<32768U;off+=8192U)_lwrite(f,video+off,8192);_lclose(f);}else Check("VIDEO_FILE",0);
 wsprintf(line,"STEP id=%d left=%d top=%d head=%u enabled=%u reason=%u hw=%u sw=%u bytes=%u cursor=%d x=%d y=%d\r\n",id,pan[0],pan[1],stats[2],stats[0],stats[3],stats[4],stats[5],stats[7],visible,x,y);Log(line);
 f=_lcreat("C:\\XYSTEP.TXT",0);_lwrite(f,line,lstrlen(line));_lclose(f);Pump(1200);
}
long FAR PASCAL __export Wnd(HWND w,UINT m,WPARAM a,LPARAM b) {
 PAINTSTRUCT ps;HDC dc;
 if(m==WM_SETCURSOR){SetCursor(active);return 1;}
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);Pattern(dc);EndPaint(w,&ps);return 0;}
 return DefWindowProc(w,m,a,b);
}

static HWND helper,candidateWindow;
static HINSTANCE instanceUI;
static HINSTANCE candidateOwner;
static int candidateCount,candidateOwned;
static unsigned enumVisited;
static int enumDumpNext=1;
static FARPROC enumProcInstance;
static char candidateModule[QA_MODULE_CAP];
static int dialogTicks,dialogReady,dialogX,dialogY;
static UINT dialogTimer;
static unsigned dialogHW,dialogSW;
static void CheckHelperVisible(LPSTR label);
BOOL FAR PASCAL __export EnumerateOverview(HWND hwnd,LPARAM data){
 char cls[QA_CLASS_CAP],title[QA_TITLE_CAP],path[QA_MODULE_CAP];HINSTANCE owner;int cn,tn,mn;
 cls[0]=title[0]=path[0]=0;
 cn=GetClassName(hwnd,cls,sizeof(cls));tn=GetWindowText(hwnd,title,sizeof(title));
 enumVisited++;
 if(enumDumpNext){wsprintf(line,"ENUM_WINDOW hwnd=%u cn=%d tn=%d class=%s title=%s\r\n",(unsigned)hwnd,cn,tn,(LPSTR)cls,(LPSTR)title);Log(line);}
 if(cn<=0 || tn<=0 || lstrcmpi(cls,XY_CLASS_NAME) || lstrcmpi(title,XY_WINDOW_TITLE))return 1;
 candidateCount++;owner=(HINSTANCE)GetWindowWord(hwnd,GWW_HINSTANCE);path[0]=0;
 mn=owner?GetModuleFileName(owner,path,sizeof(path)):0;path[sizeof(path)-1]=0;if(mn<=0)path[0]=0;
 wsprintf(line,"HELPER_CANDIDATE hwnd=%u owner=%u class=%s title=%s module=%s\r\n",(unsigned)hwnd,(unsigned)owner,(LPSTR)cls,(LPSTR)title,(LPSTR)path);Log(line);
 if(!lstrcmpi(path,XY_HELPER_PATH)){candidateOwned++;if(candidateOwned==1){candidateWindow=hwnd;candidateOwner=owner;lstrcpy(candidateModule,path);}}
 return 1;
}
static int LocateOverview(void){
 int enumResult;
 candidateWindow=0;candidateOwner=0;candidateCount=candidateOwned=0;candidateModule[0]=0;
 if(!enumProcInstance){enumProcInstance=MakeProcInstance((FARPROC)EnumerateOverview,instanceUI);if(!enumProcInstance){Log("HELPER_ENUM_THUNK_FAIL\r\n");return -1;}}
 enumVisited=0;enumResult=EnumWindows((WNDENUMPROC)enumProcInstance,0L);
 if(enumResult && enumVisited)enumDumpNext=0;
 wsprintf(line,"HELPER_ENUM_RESULT result=%d visited=%u candidates=%d owned=%d hwnd=%u\r\n",enumResult,enumVisited,candidateCount,candidateOwned,(unsigned)candidateWindow);Log(line);
 if(!enumResult){Log("HELPER_ENUM_FAIL\r\n");return -1;}
 if(candidateCount){wsprintf(line,"HELPER_ENUM count=%d owned=%d hwnd=%u\r\n",candidateCount,candidateOwned,(unsigned)candidateWindow);Log(line);}
 if(!candidateCount)return 0;
 if(candidateCount!=1 || candidateOwned!=1 || !candidateWindow)return -1;
 return 1;
}
static int VerifyHelper(LPSTR action){int state,ok;char actionLabel[QA_ACTION_CAP];
 state=LocateOverview();ok=state==1 && helper && candidateWindow==helper;
 CopyDiagText(actionLabel,action,sizeof(actionLabel));
 wsprintf(line,"HELPER_TARGET action=%s hwnd=%u owner=%u class=%s title=%s module=%s status=%d\r\n",(LPSTR)actionLabel,(unsigned)helper,(unsigned)candidateOwner,(LPSTR)XY_CLASS_NAME,(LPSTR)XY_WINDOW_TITLE,(LPSTR)candidateModule,ok);Log(line);
 Check("HELPER_IDENTITY",ok);return ok;
}
static int WaitForHelper(DWORD limit,LPSTR action){DWORD start;int state;start=GetTickCount();
 while((DWORD)(GetTickCount()-start)<limit){Pump(100);state=LocateOverview();if(state>0){helper=candidateWindow;return VerifyHelper(action);}if(state<0){helper=0;Check("HELPER_IDENTITY",0);return 0;}}
 Check("HELPER_START",0);return 0;
}
static int StartHelper(int launchIfMissing){int state;HINSTANCE result;
 state=LocateOverview();if(state>0){helper=candidateWindow;return VerifyHelper("attach");}
 if(state<0){Check("HELPER_IDENTITY",0);return 0;}
 if(!launchIfMissing)return WaitForHelper(10000L,"startup");
 enumDumpNext=1;
 result=(HINSTANCE)WinExec(XY_HELPER_PATH,SW_SHOW);Check("HELPER_EXEC",(unsigned)result>31);if((unsigned)result<=31)return 0;
 return WaitForHelper(10000L,"restart");
}
static int NoOverviewWindow(void){return LocateOverview()==0;}
static int Command(int code){
 if(!VerifyHelper("command"))return 0;
 wsprintf(line,"COMMAND_TARGET code=%d hwnd=%u\r\n",code,(unsigned)helper);Log(line);
 SendMessage(helper,WM_COMMAND,code,0L);Pan(-1,0);return 1;
}
static void Marker(LPSTR name){HFILE f;f=_lcreat(name,0);_lwrite(f,"READY",5);_lclose(f);}
static int WaitPan(int x,int y,DWORD limit){DWORD start;start=GetTickCount();while((DWORD)(GetTickCount()-start)<limit){Pump(50);Pan(-1,0);if(pan[0]==x && pan[1]==y)return 1;}return 0;}
static int StartOverviewTest(void){
 if(!StartHelper(0))return 0;Check("HELPER_START",helper!=0);if(!helper)return 0;Pan(-1,0);statsProc(stats);Check("SAFE_SOFTWARE",stats[0]==0);PanCheck("SAFE_HOME",0,0);Command(105);
 if(VerifyHelper("paint-home")){InvalidateRect(helper,0,TRUE);UpdateWindow(helper);}Check("OVERVIEW_VISIBLE",IsWindow(helper)&&IsWindowVisible(helper));CheckHelperVisible("OVERVIEW_HELPER_IN_HOME");Marker("C:\\XYHOME.TXT");Pump(1000);return 1;
}
static void MapMessage(UINT message,WPARAM keysDown,int x,int y){if(!VerifyHelper("map-message"))return;wsprintf(line,"MAPMSG hwnd=%u message=%u keys=%u client=%d,%d\r\n",(unsigned)helper,(unsigned)message,(unsigned)keysDown,x,y);Log(line);SendMessage(helper,message,keysDown,MAKELONG(x,y));}
static void CheckHelperVisible(LPSTR label){RECT r;if(!VerifyHelper("visibility")){Check(label,0);return;}GetWindowRect(helper,&r);Check(label,r.left>=pan[0]&&r.top>=pan[1]&&r.right<=pan[0]+320&&r.bottom<=pan[1]+200);}
static void OverviewTest(void){
 Pan(0,0);MapMessage(WM_LBUTTONDOWN,MK_LBUTTON,XY_MAP_LEFT+120,XY_MAP_TOP+10);MapMessage(WM_LBUTTONUP,0,XY_MAP_LEFT+120,XY_MAP_TOP+10);PanCheck("MAP_CLICK_CLAMP",320,0);CheckHelperVisible("MAP_HELPER_VISIBLE_RIGHT");
 MapMessage(WM_LBUTTONDOWN,MK_LBUTTON,XY_MAP_LEFT+159,XY_MAP_TOP+63);MapMessage(WM_LBUTTONUP,0,XY_MAP_LEFT+159,XY_MAP_TOP+63);PanCheck("MAP_BOTTOM_RIGHT",320,56);Check("MAP_ALIGN",(pan[0]&7)==0&&(pan[1]&3)==0);CheckHelperVisible("MAP_HELPER_VISIBLE_BOTTOM_RIGHT");
 Command(103);PanCheck("MAP_HOME",0,0);CheckHelperVisible("MAP_HELPER_VISIBLE_HOME");
 MapMessage(WM_LBUTTONDOWN,MK_LBUTTON,XY_MAP_LEFT+20,XY_MAP_TOP+10);MapMessage(WM_MOUSEMOVE,MK_LBUTTON,XY_MAP_LEFT+40,XY_MAP_TOP+14);MapMessage(WM_LBUTTONUP,0,XY_MAP_LEFT+40,XY_MAP_TOP+14);PanCheck("MAP_DRAG_RELEASE",80,16);CheckHelperVisible("MAP_HELPER_VISIBLE_DRAG");Marker("C:\\XYDRAG.TXT");Pump(1000);Marker("C:\\XYDRSET.TXT");Pump(1000);
  Pan(0,0);MapMessage(WM_LBUTTONDOWN,MK_LBUTTON,XY_MAP_LEFT+20,XY_MAP_TOP+10);MapMessage(WM_MOUSEMOVE,MK_LBUTTON,XY_MAP_LEFT+40,XY_MAP_TOP+18);if(VerifyHelper("cancel-mode"))SendMessage(helper,WM_CANCELMODE,0,0L);MapMessage(WM_LBUTTONUP,0,XY_MAP_LEFT+40,XY_MAP_TOP+18);PanCheck("MAP_CANCEL",0,0);
  Pan(0,0);MapMessage(WM_LBUTTONDOWN,MK_LBUTTON,XY_MAP_LEFT+20,XY_MAP_TOP+10);MapMessage(WM_MOUSEMOVE,MK_LBUTTON,XY_MAP_LEFT+40,XY_MAP_TOP+18);if(VerifyHelper("escape-cancel"))SendMessage(helper,WM_KEYDOWN,VK_ESCAPE,1L);MapMessage(WM_LBUTTONUP,0,XY_MAP_LEFT+40,XY_MAP_TOP+18);PanCheck("MAP_ESCAPE_CANCEL",0,0);
 /* Pan outside the helper between input messages; no timer message is pumped before mouse-up. */
  Pan(0,0);MapMessage(WM_LBUTTONDOWN,MK_LBUTTON,XY_MAP_LEFT+20,XY_MAP_TOP+10);MapMessage(WM_MOUSEMOVE,MK_LBUTTON,XY_MAP_LEFT+40,XY_MAP_TOP+14);Pan(80,16);MapMessage(WM_LBUTTONUP,0,XY_MAP_LEFT+40,XY_MAP_TOP+14);PanCheck("MAP_EXTERNAL_RELEASE_CANCEL",80,16);CheckHelperVisible("MAP_EXTERNAL_RELEASE_VISIBLE");
}
static void RecoveryTest(void){
  HWND off,normal,within,hidden,minimized,maximized;RECT before,after,withinBefore,requested,offBefore,offExpected,hiddenBefore,minimizedBefore,maximizedBefore;
 Pan(160,28);PanCheck("RECOVERY_STARTS_PANNED",160,28);
 normal=CreateWindow("STATIC","QA normal",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,24,24,100,60,0,0,instanceUI,0);ShowWindow(normal,SW_SHOW);
 within=CreateWindow("STATIC","QA within logical desk",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,500,30,100,60,0,0,instanceUI,0);ShowWindow(within,SW_SHOW);
 off=CreateWindow("STATIC","QA offscreen",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,700,280,100,60,0,0,instanceUI,0);ShowWindow(off,SW_SHOW);
 hidden=CreateWindow("STATIC","QA hidden",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,700,280,100,60,0,0,instanceUI,0);
 minimized=CreateWindow("STATIC","QA minimized",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,700,280,100,60,0,0,instanceUI,0);ShowWindow(minimized,SW_MINIMIZE);
 maximized=CreateWindow("STATIC","QA maximized",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MAXIMIZEBOX,700,280,100,60,0,0,instanceUI,0);ShowWindow(maximized,SW_MAXIMIZE);
 Check("RECOVERY_FIXTURE",normal&&within&&off&&hidden&&minimized&&maximized);
 if(!normal || !within || !off || !hidden || !minimized || !maximized){if(normal)DestroyWindow(normal);if(within)DestroyWindow(within);if(off)DestroyWindow(off);if(hidden)DestroyWindow(hidden);if(minimized)DestroyWindow(minimized);if(maximized)DestroyWindow(maximized);return;}
  GetWindowRect(normal,&before);GetWindowRect(within,&withinBefore);requested.left=700;requested.top=280;requested.right=800;requested.bottom=340;GetWindowRect(off,&offBefore);RectRecord("RECOVERY_OFFSCREEN_START",&requested,&offBefore);Check("RECOVERY_START_OUTSIDE_DESK",RectOutsideDesk(&offBefore));ExpectedHomeRect(&offBefore,&offExpected);
  GetWindowRect(hidden,&hiddenBefore);GetWindowRect(minimized,&minimizedBefore);GetWindowRect(maximized,&maximizedBefore);
  Command(XY_RECOVER);PanCheck("RECOVERY_HOME_BEFORE_MOVE",0,0);GetWindowRect(off,&after);RectRecord("RECOVERY_OFFSCREEN",&offExpected,&after);
  Check("RECOVERY_EXPECTED_RECT",RectSame(&offExpected,&after));Check("RECOVERY_SIZE_UNCHANGED",RectSameSize(&offBefore,&after));Check("RECOVERY_OFFSCREEN",after.left>=0&&after.left<pan[2]&&after.top+GetSystemMetrics(SM_CYCAPTION)+2*GetSystemMetrics(SM_CYFRAME)<=pan[3]);
  GetWindowRect(normal,&after);RectRecord("RECOVERY_NORMAL",&before,&after);Check("RECOVERY_PRESERVE_NORMAL",after.left==before.left&&after.top==before.top&&after.right==before.right&&after.bottom==before.bottom);
  GetWindowRect(within,&after);RectRecord("RECOVERY_PANNED_DESK",&withinBefore,&after);Check("RECOVERY_PRESERVE_PANNED_DESK",after.left==withinBefore.left&&after.top==withinBefore.top&&after.right==withinBefore.right&&after.bottom==withinBefore.bottom);
  Check("RECOVERY_SKIP_HIDDEN",!IsWindowVisible(hidden));GetWindowRect(hidden,&after);RectRecord("RECOVERY_HIDDEN",&hiddenBefore,&after);Check("RECOVERY_SKIP_HIDDEN_POS",after.left==hiddenBefore.left&&after.top==hiddenBefore.top&&after.right==hiddenBefore.right&&after.bottom==hiddenBefore.bottom);
  Check("RECOVERY_SKIP_MINIMIZED",IsIconic(minimized));GetWindowRect(minimized,&after);RectRecord("RECOVERY_MINIMIZED",&minimizedBefore,&after);Check("RECOVERY_SKIP_MINIMIZED_POS",after.left==minimizedBefore.left&&after.top==minimizedBefore.top&&after.right==minimizedBefore.right&&after.bottom==minimizedBefore.bottom);
  Check("RECOVERY_SKIP_MAXIMIZED",IsZoomed(maximized));GetWindowRect(maximized,&after);RectRecord("RECOVERY_MAXIMIZED",&maximizedBefore,&after);Check("RECOVERY_SKIP_MAXIMIZED_POS",after.left==maximizedBefore.left&&after.top==maximizedBefore.top&&after.right==maximizedBefore.right&&after.bottom==maximizedBefore.bottom);
  DestroyWindow(normal);DestroyWindow(within);DestroyWindow(off);DestroyWindow(hidden);DestroyWindow(minimized);DestroyWindow(maximized);Command(103);PanCheck("RECOVERY_HOME",0,0);
}
static int CloseHelperForQA(void){DWORD start;
 if(!helper || !IsWindow(helper)){helper=0;return NoOverviewWindow();}
 if(!VerifyHelper("close"))return 0;
 SendMessage(helper,WM_CLOSE,0,0L);start=GetTickCount();while(IsWindow(helper)&&(DWORD)(GetTickCount()-start)<5000L)Pump(50);
 helper=0;return NoOverviewWindow();
}
static void RecoveryCloseTest(void){HWND off;RECT r,expected,requested,beforeClose,afterClose;unsigned titlebar;int moved;
 Check("RECOVERY_CLOSE_HELPER_IDENTITY",helper && VerifyHelper("recovery-close"));if(!helper || !IsWindow(helper))return;
 off=CreateWindow("STATIC","QA recovery survives close",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,700,280,100,60,0,0,instanceUI,0);
 Check("RECOVERY_CLOSE_FIXTURE",off!=0);if(!off){CloseHelperForQA();return;}ShowWindow(off,SW_SHOW);
  Pan(160,28);PanCheck("RECOVERY_CLOSE_STARTS_PANNED",160,28);
  requested.left=700;requested.top=280;requested.right=800;requested.bottom=340;GetWindowRect(off,&beforeClose);RectRecord("RECOVERY_CLOSE_START",&requested,&beforeClose);Check("RECOVERY_CLOSE_START_OUTSIDE_DESK",RectOutsideDesk(&beforeClose));ExpectedHomeRect(&beforeClose,&expected);
  Command(XY_RECOVER);PanCheck("RECOVERY_CLOSE_RECOVERS_HOME",0,0);
  GetWindowRect(off,&r);RectRecord("RECOVERY_CLOSE_BEFORE",&expected,&r);titlebar=(unsigned)(GetSystemMetrics(SM_CYCAPTION)+2*GetSystemMetrics(SM_CYFRAME));
  Check("RECOVERY_CLOSE_EXPECTED_RECT",RectSame(&expected,&r));Check("RECOVERY_CLOSE_SIZE_UNCHANGED",RectSameSize(&beforeClose,&r));moved=r.left>=0&&r.left<pan[2]&&r.top>=0&&r.top+(int)titlebar<=pan[3];Check("RECOVERY_CLOSE_VISIBLE_BEFORE",moved);
 Check("RECOVERY_CLOSE_HELPER",CloseHelperForQA());Pan(-1,0);statsProc(stats);
 Check("RECOVERY_CLOSE_RESET",NoOverviewWindow()&&pan[0]==0&&pan[1]==0&&stats[0]==0);
  GetWindowRect(off,&afterClose);RectRecord("RECOVERY_CLOSE_AFTER",&r,&afterClose);Check("RECOVERY_CLOSE_POSITION_STABLE",RectSame(&r,&afterClose));Check("RECOVERY_CLOSE_SIZE_STABLE",RectSameSize(&beforeClose,&afterClose));r=afterClose;moved=IsWindowVisible(off)&&r.left>=0&&r.left<pan[2]&&r.top>=0&&r.top+(int)titlebar<=pan[3];
 Check("RECOVERY_SURVIVES_CLOSE",moved);Marker("C:\\XYCLOSE.TXT");Pump(1200);DestroyWindow(off);
}
static void RestartCheck(void){int closed;
 helper=0;Check("RESTART_START",StartHelper(1));if(!helper)return;Pan(-1,0);statsProc(stats);Check("RESTART_SOFTWARE",stats[0]==0);Check("RESTART_HOME",pan[0]==0&&pan[1]==0);
 closed=CloseHelperForQA();Pan(-1,0);statsProc(stats);Check("RESTART_CLOSE_RESET",closed&&NoOverviewWindow()&&pan[0]==0&&pan[1]==0&&stats[0]==0);
}
static int EdgeLeg(int x,int y,int dx,int dy,int tx,int ty,int id,int full){
 DWORD start,first,last;int oldx,oldy,ok,expected,steps,coalesced;POINT p;unsigned before,after,sw;
 Command(107);Pan(x,y);active=run==2?cursor:(HCURSOR)0;SetCursor(active);SetCursorPos(x+(dx<0?0:dx>0?319:160),y+(dy<0?0:dy>0?199:100));statsProc(stats);before=stats[4];
 Command(106);oldx=x;oldy=y;ok=1;first=last=0;coalesced=0;start=GetTickCount();
 while((DWORD)(GetTickCount()-start)<60000L){Pump(50);Pan(-1,0);if(pan[0]!=oldx || pan[1]!=oldy){
  if(!first)first=GetTickCount()-start;last=GetTickCount()-start;
  if((dx==0 && pan[0]!=oldx)||(dy==0 && pan[1]!=oldy)||(dx && (pan[0]-oldx)*dx<0)||(dy && (pan[1]-oldy)*dy<0))ok=0;
  if((pan[0]&7)||(pan[1]&3)||pan[0]<0||pan[0]>320||pan[1]<0||pan[1]>56)ok=0;
  if(abs(pan[0]-oldx)>8||abs(pan[1]-oldy)>4)coalesced++;
  GetCursorPos(&p);if(p.x-pan[0]!=(dx<0?0:dx>0?319:160)||p.y-pan[1]!=(dy<0?0:dy>0?199:100))ok=0;
  oldx=pan[0];oldy=pan[1];
 }if(pan[0]==tx && pan[1]==ty)break;}
 Command(107);statsProc(stats);after=stats[4];sw=stats[5];expected=abs(tx-x)/8;steps=abs(ty-y)/4;if(steps>expected)expected=steps;
 Check("EDGE_MONOTONIC_POINTER",ok);Check("EDGE_TARGET",pan[0]==tx&&pan[1]==ty);Check("EDGE_FIRST_DWELL",first>=500L);Check("EDGE_COMMITS",(unsigned)(after-before)==expected);
 wsprintf(line,"LEG id=%d dx=%d dy=%d startX=%d startY=%d endX=%d endY=%d first=%lu last=%lu commits=%u coalesced=%d\r\n",id,dx,dy,x,y,pan[0],pan[1],first,last,after-before,coalesced);Log(line);
 if(full && pan[0]==tx && pan[1]==ty){Command(106);Pump(800);Pan(-1,0);statsProc(stats);Check("LIMIT_ORIGIN",pan[0]==tx&&pan[1]==ty);Check("LIMIT_HW_COUNT",stats[4]==after);Check("LIMIT_SW_COUNT",stats[5]==sw);Command(107);}
 GetCursorPos(&p);Snap(id,run==2,p.x,p.y);return ok&&pan[0]==tx&&pan[1]==ty;
}
BOOL FAR PASCAL __export Dlg(HWND w,UINT m,WPARAM a,LPARAM b){RECT r,expected;int moved;
 if(m==WM_INITDIALOG){dialogTicks=dialogReady=0;expected.left=480;expected.top=218;expected.right=624;expected.bottom=254;
  moved=SetWindowPos(w,0,480,218,144,36,SWP_NOZORDER);Check("DIALOG_SET_POS",moved);GetWindowRect(w,&r);RectRecord("DIALOG_INIT",&expected,&r);
  dialogTimer=SetTimer(w,2,250,0);Check("DIALOG_TIMER_SET",dialogTimer!=0);Log("DIALOG_INIT_RECEIVED\r\n");if(!dialogTimer){Log("DIALOG_ABORT reason=TIMER_SETUP\r\n");EndDialog(w,0);}return 1;}
 if(m==WM_TIMER){if(dialogTicks==0)Log("DIALOG_TIMER_FIRST\r\n");dialogTicks++;Pan(-1,0);statsProc(stats);
  if(!dialogReady){GetWindowRect(w,&r);if(!(r.left>=pan[0]&&r.right<=pan[0]+320&&r.top>=pan[1]&&r.bottom<=pan[1]+200)&&dialogTicks<12)return 1;
   if(dialogTicks>=12)Log("DIALOG_FIT_WAIT_EXPIRED\r\n");Check("DIALOG_INITIAL_FIT",r.left>=pan[0]&&r.right<=pan[0]+320&&r.top>=pan[1]&&r.bottom<=pan[1]+200);dialogReady=1;dialogTicks=0;dialogX=pan[0];dialogY=pan[1];dialogHW=stats[4];dialogSW=stats[5];SetCursorPos(dialogX,dialogY+100);}
  else Check("FOLLOW_EDGE_NO_OSCILLATION",pan[0]==dialogX&&pan[1]==dialogY&&stats[4]==dialogHW&&stats[5]==dialogSW);
  if(dialogTicks>=8){KillTimer(w,dialogTimer);dialogTimer=0;GetWindowRect(w,&r);Check("DIALOG_FITS",r.left>=pan[0]&&r.right<=pan[0]+320&&r.top>=pan[1]&&r.bottom<=pan[1]+200);Log("DIALOG_AUTO_CLOSE\r\n");Snap(615,0,pan[0],pan[1]+100);EndDialog(w,1);}return 1;
 }return 0;
}
static void DialogTest(void){HGLOBAL memory;BYTE FAR *p;FARPROC thunk;DWORD style;char *s;int dialogResult;
 Command(107);Pan(0,0);Command(111);Command(106);memory=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,128);Check("DIALOG_ALLOC",memory!=0);if(!memory)return;
 p=(BYTE FAR *)GlobalLock(memory);Check("DIALOG_LOCK",p!=0);if(!p){GlobalFree(memory);return;}style=WS_POPUP|WS_CAPTION|DS_MODALFRAME;*p++=(BYTE)LOWORD(style);*p++=(BYTE)(LOWORD(style)>>8);*p++=(BYTE)HIWORD(style);*p++=(BYTE)(HIWORD(style)>>8);*p++=0;
 *p++=0;*p++=0;*p++=0;*p++=0;*p++=80;*p++=0;*p++=20;*p++=0;*p++=0;*p++=0;s="Edge follow priority";while(*s)*p++=*s++;*p++=0;GlobalUnlock(memory);
 thunk=MakeProcInstance((FARPROC)Dlg,instanceUI);Check("DIALOG_THUNK",thunk!=0);if(!thunk){GlobalFree(memory);return;}
 Log("DIALOG_CALL_BEGIN\r\n");dialogResult=DialogBoxIndirect(instanceUI,memory,mainWnd,(DLGPROC)thunk);wsprintf(line,"DIALOG_CALL_RETURN result=%d\r\n",dialogResult);Log(line);
 Check("DIALOG_RESULT",dialogResult==1);FreeProcInstance(thunk);GlobalFree(memory);Command(107);Command(112);
}
static void UI(void){DWORD start;int x,y;POINT p;
 if(!StartOverviewTest())return;
 OverviewTest();RecoveryTest();
 RecoveryCloseTest();
 if(overviewOnly){Log("LEGACY_DIALOG status=SKIPPED_FOCUSED; full_test_retained\r\n");return;}
 if(!StartHelper(1))return;
 if(run==1){
  if(!EdgeLeg(0,28,1,0,320,28,610,1))return;
  if(!EdgeLeg(320,28,-1,0,0,28,611,1))return;
  Command(114);if(!EdgeLeg(160,28,1,0,184,28,614,0))return;
  Command(115);if(!EdgeLeg(160,28,-1,0,136,28,616,0))return;Command(113);
  if(!EdgeLeg(160,0,0,1,160,56,612,1))return;
  if(!EdgeLeg(160,56,0,-1,160,0,613,1))return;
  /* Leave edge before initial dwell; no pending action survives. */
  Pan(160,28);SetCursorPos(479,128);Command(106);Pump(200);SetCursorPos(320,128);Pump(700);Pan(-1,0);Check("CANCEL_INITIAL",pan[0]==160&&pan[1]==28);Command(107);
  /* External origin update must arm a fresh initial dwell at the new view. */
  Pan(160,28);SetCursorPos(479,128);Command(106);Check("WAIT_FIRST",WaitPan(168,28,4000));Pan(80,28);SetCursorPos(399,128);Pump(200);Pan(-1,0);Check("EXTERNAL_FRESH_DWELL",pan[0]==80&&pan[1]==28);Check("EXTERNAL_TARGET",WaitPan(88,28,4000));Command(107);Snap(617,0,407,128);
  Command(104);Pan(160,28);SetCursorPos(479,128);Command(106);Check("SOFT_EDGE",WaitPan(168,28,5000));Command(107);statsProc(stats);Check("SOFT_MODE",stats[0]==0&&stats[2]==0);Snap(619,0,487,128);
  Command(105);Pan(160,28);Mode(2);SetCursorPos(479,128);Command(106);Check("FAULT_EDGE",WaitPan(168,28,5000));Command(107);statsProc(stats);Check("FAULT_FALLBACK",stats[0]==0&&stats[2]==0&&stats[3]==4);Snap(618,0,487,128);Command(105);
  DialogTest();
  Command(107);Pan(160,28);Command(102);Command(110);Check("KEY_ORIGIN",pan[0]==168&&pan[1]==32);
  if(VerifyHelper("keyboard-up-focus")){SetWindowPos(helper,HWND_TOP,180,40,0,0,SWP_NOSIZE);SetActiveWindow(helper);SetFocus(helper);}Marker("C:\\XYKEY.TXT");Pump(8000);Pan(-1,0);Check("RAW_UP",pan[0]==168&&pan[1]==28);Snap(513,0,188,48);
  Command(103);Command(104);if(VerifyHelper("keyboard-quit-focus")){SetActiveWindow(helper);SetFocus(helper);}Marker("C:\\XYQUIT.TXT");Pump(8000);Check("RAW_QUIT",!IsWindow(helper)&&NoOverviewWindow());
 }else{
  if(!EdgeLeg(160,28,-1,-1,0,0,620,1))return;
  if(!EdgeLeg(160,28,1,-1,320,0,621,1))return;
  if(!EdgeLeg(160,28,-1,1,0,56,622,1))return;
  if(!EdgeLeg(160,28,1,1,320,56,623,1))return;
  Command(108);start=GetTickCount();while(IsWindow(helper)&&(DWORD)(GetTickCount()-start)<5000L)Pump(100);Check("MENU_QUIT",!IsWindow(helper));
 }
 Pan(-1,0);statsProc(stats);Check("HELPER_RESET",pan[0]==0&&pan[1]==0&&stats[0]==0);Snap(run==1?517:901,0,50,50);
}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR command,int show) {
 HINSTANCE display;WNDCLASS wc;FARPROC thunk;HDC dc;HFILE f;int x,y,i;unsigned char am[64],xm[64];DWORD a,b;
  instanceUI=instance;f=_lopen("C:\\XYOVIEW.TXT",OF_READ);overviewSelectorPresent=f!=HFILE_ERROR;overviewOnly=0;
  if(f!=HFILE_ERROR){char selector[9];overviewOnly=_lread(f,selector,9)==8 && !memcmp(selector,"OVERVIEW",8);_lclose(f);}
 f=_lopen("C:\\XYRUN.TXT",OF_READ);run=f==HFILE_ERROR?1:2;if(f!=HFILE_ERROR)_lclose(f);
 if(run==1){f=_lcreat("C:\\XYRUN.TXT",0);_lwrite(f,"1",1);_lclose(f);logFile=_lcreat("C:\\XY.LOG",0);}else{logFile=_lopen("C:\\XY.LOG",OF_WRITE);_llseek(logFile,0L,2);}
 wsprintf(line,"START run=%d overviewOnly=%d free=%lu largest=%lu\r\n",run,overviewOnly,GetFreeSpace(0),GlobalCompact(0L));Log(line);
  Check("OVERVIEW_SELECTOR",overviewSelectorPresent&&overviewOnly);if(!overviewSelectorPresent||!overviewOnly)goto done;
  Log("FOCUSED_OVERVIEW_BEGIN selector=XYOVIEW.TXT bytes=8\r\n");
 Check("GEOMETRY",GetSystemMetrics(0)==640 && GetSystemMetrics(1)==256);
 display=GetModuleHandle("DISPLAY");rowsProc=(ROWS)GetProcAddress(display,(LPSTR)108L);statsProc=(STATS)GetProcAddress(display,(LPSTR)106L);
 Check("EXPORTS",rowsProc!=0 && statsProc!=0);if(!rowsProc || !statsProc)goto done;
 Pan(-1,0);Check("INITIAL",pan[0]==0 && pan[1]==0 && pan[4]==640 && pan[5]==256);statsProc(stats);Check("DEFAULT_SOFTWARE",stats[0]==0);
 memset(&wc,0,sizeof(wc));thunk=MakeProcInstance((FARPROC)Wnd,instance);wc.lpfnWndProc=(WNDPROC)thunk;wc.hInstance=instance;wc.lpszClassName="XYQA";wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);RegisterClass(&wc);
 memset(am,255,sizeof(am));memset(xm,0,sizeof(xm));for(i=0;i<8;i++){am[i*4]=0;xm[i*4]=(unsigned char)(0x80>>i);}
 cursor=CreateCursor(instance,0,0,32,16,am,xm);active=0;
 mainWnd=CreateWindow("XYQA","PRIVATE sustained-edge proof",WS_POPUP,0,0,640,256,0,0,instance,0);Check("WINDOW",mainWnd!=0);ShowWindow(mainWnd,SW_SHOW);UpdateWindow(mainWnd);SetCursor(0);
 dc=GetDC(mainWnd);ReleaseDC(mainWnd,dc);Snap(run==1?0:900,0,400,120);
 UI();
  RestartCheck();
 SetCursor(0);Mode(0);Pan(0,0);DestroyWindow(mainWnd);DestroyCursor(cursor);UnregisterClass("XYQA",instance);FreeProcInstance(thunk);
done:
  if(enumProcInstance){FreeProcInstance(enumProcInstance);enumProcInstance=0;}
 wsprintf(line,"END run=%d FAILURES=%d free=%lu largest=%lu\r\n",run,failures,GetFreeSpace(0),GlobalCompact(0L));Log(line);_lclose(logFile);ExitWindows(0,0);return 0;
}
