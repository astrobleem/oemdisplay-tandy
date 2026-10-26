#define WINVER 0x0300
#include <windows.h>
#include <string.h>
#include "PANDLG.H"
#include "WDWIN.H"
#define ESC_XY 0x5860
#define ESC_MODE 0x5861
#define LEFT 101
#define RIGHT 102
#define HOME 103
#define SOFT 104
#define HARD 105
#define EDGEON 106
#define EDGEOFF 107
#define QUIT 108
#define UP 109
#define DOWN 110
#define FOLLOWON 111
#define FOLLOWOFF 112
#define REPEAT100 113
#define REPEAT200 114
#define REPEAT500 115
#define RECOVER 116
#define SETTINGS 117
#define XY_LOG_LINE_CAP 112
#define XY_PAINT_LINE_CAP 128
#define XY_CLASS_NAME "XYOverviewControl"
#define XY_WINDOW_TITLE "XY overview"
#define MAP_LEFT 8
#define MAP_TOP 58
#define MAP_WIDTH 160
#define MAP_HEIGHT 64
typedef int (FAR PASCAL *STATS)(unsigned FAR *);
static HWND window;
static HWND homeButton;
static HWND recoverButton;
static HDC display;
static HINSTANCE instanceHandle;
static STATS statsProc;
static HFILE logFile=HFILE_ERROR;
static char logPath[128];
static int left,top,hardware,edge,follow,live,closing,logCount;
static int viewWidth,viewHeight,logicalWidth,logicalHeight;
static int directionX,directionY,latch[10];
static DWORD since;
static int edgeRepeating,edgeRepeat=100,edgePresent,edgeDirty,timerSeen,edgePolled;
static int dragging,dragAnchorX,dragAnchorY,previewLeft,previewTop,dragOriginX,dragOriginY;
static int recoveryMoved,recoveryFailed;
static unsigned recoveryVisited;
static int driverWarning;
static UINT openMsg;
static PANHOST panHost;
static int windowOnly;
static char recoveryStatus[48]="Recovery is manual";
static int keys[10]={VK_LEFT,VK_RIGHT,VK_UP,VK_DOWN,VK_HOME,'H','E','F','Q','R'};
static void DriverLost(LPSTR why);
static void CancelMapDrag(void);
static void EnablePanControls(int enabled);
static void RecoverWindows(void);
static void KeepControlVisible(void);
static void MapInvalidate(void);
static void MapTarget(int mx,int my,int *x,int *y);
static void BeginMapDrag(int mx,int my);
static void DrawOverview(HDC dc);
static int Pan(int x,int y);
static int XyHome(void *c);
static void Log(LPSTR event,int a,int b,int c,int d) {
 char line[XY_LOG_LINE_CAP];
 if(logFile==HFILE_ERROR || logCount>=512)return;
 wsprintf(line,"%s tick=%lu a=%d b=%d c=%d d=%d\r\n",(LPSTR)event,GetTickCount(),a,b,c,d);
 _lwrite(logFile,line,lstrlen(line));logCount++;
}
static int OpenLog(HINSTANCE module) {
 int n,i,lastSlash;
 OFSTRUCT existing;
 n=GetModuleFileName(module,logPath,sizeof(logPath));
 if(n<=0 || n>=128)return 0;
 logPath[sizeof(logPath)-1]=0;lastSlash=-1;
 for(i=0;logPath[i];i++)if(logPath[i]=='\\' || logPath[i]=='/')lastSlash=i;
 if(lastSlash<0)return 0;
 logPath[lastSlash+1]=0;lstrcat(logPath,"XYCTL.LOG");
 /* Existing logs are opened and sought to EOF; only a proven-missing path is created. */
 logFile=_lopen(logPath,OF_WRITE);
 if(logFile==HFILE_ERROR){
  if(OpenFile(logPath,&existing,OF_EXIST)!=HFILE_ERROR)return 0;
  logFile=_lcreat(logPath,0);
 }else if(_llseek(logFile,0L,2)<0){_lclose(logFile);logFile=HFILE_ERROR;return 0;}
 return logFile!=HFILE_ERROR;
}
static void ResetEdge(void) {
 directionX=directionY=0;edgeRepeating=0;
}
static void PaintEdge(void) {
 if(edgeDirty && !closing){edgeDirty=0;InvalidateRect(window,0,FALSE);}
}
static void MapInvalidate(void) {
 RECT r;
 if(!window)return;
 r.left=MAP_LEFT-2;r.top=MAP_TOP-2;r.right=MAP_LEFT+MAP_WIDTH+2;r.bottom=MAP_TOP+MAP_HEIGHT+2;
 InvalidateRect(window,&r,FALSE);
}
static void CancelMapDrag(void) {
 if(!dragging)return;
 dragging=0;
 if(GetCapture()==window)ReleaseCapture();
 MapInvalidate();
}
static void EnablePanControls(int enabled) {
 HMENU menu;UINT flag;
 if(!window)return;
 flag=MF_BYCOMMAND|(enabled?MF_ENABLED:MF_GRAYED);menu=GetMenu(window);
 if(menu){
  EnableMenuItem(menu,LEFT,flag);EnableMenuItem(menu,RIGHT,flag);
  EnableMenuItem(menu,UP,flag);EnableMenuItem(menu,DOWN,flag);
  EnableMenuItem(menu,HOME,flag);EnableMenuItem(menu,RECOVER,flag);
  EnableMenuItem(menu,SOFT,flag);EnableMenuItem(menu,HARD,flag);
  EnableMenuItem(menu,EDGEON,flag);EnableMenuItem(menu,EDGEOFF,flag);
  EnableMenuItem(menu,FOLLOWON,flag);EnableMenuItem(menu,FOLLOWOFF,flag);
  EnableMenuItem(menu,REPEAT100,flag);EnableMenuItem(menu,REPEAT200,flag);EnableMenuItem(menu,REPEAT500,flag);
  DrawMenuBar(window);
 }
 if(homeButton)EnableWindow(homeButton,enabled);
 if(recoverButton)EnableWindow(recoverButton,enabled);
}
static void DriverLost(LPSTR why) {
 if(!live && driverWarning)return;
 live=edge=follow=0;ResetEdge();CancelMapDrag();EnablePanControls(0);
 lstrcpy(recoveryStatus,"Driver unavailable");
 Log(why,0,0,0,0);InvalidateRect(window,0,FALSE);
 if(!driverWarning && !closing){
  driverWarning=1;
  MessageBox(window, "The display driver no longer reports the supported panning geometry. Pan and recovery controls are disabled.", "XY overview", MB_OK|MB_ICONEXCLAMATION);
 }
}
static void KeepControlVisible(void) {
 RECT r;int x,y;
 if(!window || closing)return;
 x=(windowOnly?0:left)+4;y=(windowOnly?0:top)+2;GetWindowRect(window,&r);
 if(r.left!=x || r.top!=y)SetWindowPos(window,0,x,y,0,0,SWP_NOZORDER|SWP_NOACTIVATE|SWP_NOSIZE);
}
static int Query(void) {
 int in[2],out[6],ok;unsigned st[8];
 if(windowOnly){
  WDWinViewport(&left,&top);logicalWidth=logicalHeight=2048;
  viewWidth=GetSystemMetrics(SM_CXSCREEN);viewHeight=GetSystemMetrics(SM_CYSCREEN);
  hardware=0;KeepControlVisible();return 1;
 }
 in[0]=-1;in[1]=0;
 ok=Escape(display,ESC_XY,4,(LPSTR)in,(LPSTR)out)>0;
 if(!ok || out[0]<0 || out[0]>320 || (out[0]&7) || out[1]<0 || out[1]>56 || (out[1]&3) || out[2]!=320 || out[3]!=200 || out[4]!=640 || out[5]!=256)return 0;
 if(left!=out[0] || top!=out[1]){ResetEdge();edgeDirty=1;}
 left=out[0];top=out[1];viewWidth=out[2];viewHeight=out[3];logicalWidth=out[4];logicalHeight=out[5];
 KeepControlVisible();
 if(statsProc){statsProc(st);if(hardware!=(st[0]!=0)){ResetEdge();edgeDirty=1;}hardware=st[0]!=0;}
 return 1;
}
static int MapClamp(long value,int extent,int view,int step) {
 long limit;
 limit=(long)extent-(long)view;
 if(value<0)value=0;if(value>limit)value=limit;
 value=(value/(long)step)*(long)step;
 return (int)value;
}
static void MapTarget(int mx,int my,int *x,int *y) {
 long logicalX,logicalY;
 if(mx<MAP_LEFT)mx=MAP_LEFT;if(mx>=MAP_LEFT+MAP_WIDTH)mx=MAP_LEFT+MAP_WIDTH-1;
 if(my<MAP_TOP)my=MAP_TOP;if(my>=MAP_TOP+MAP_HEIGHT)my=MAP_TOP+MAP_HEIGHT-1;
 logicalX=(long)(mx-MAP_LEFT)*(long)logicalWidth/(long)MAP_WIDTH-dragAnchorX;
 logicalY=(long)(my-MAP_TOP)*(long)logicalHeight/(long)MAP_HEIGHT-dragAnchorY;
 *x=MapClamp(logicalX,logicalWidth,viewWidth,8);
 *y=MapClamp(logicalY,logicalHeight,viewHeight,4);
}
static void BeginMapDrag(int mx,int my) {
 int vx,vy,vw,vh,pointX,pointY;
 if(!live || mx<MAP_LEFT || mx>=MAP_LEFT+MAP_WIDTH || my<MAP_TOP || my>=MAP_TOP+MAP_HEIGHT)return;
 if(!Query()){DriverLost("MAP_QUERY");return;}
 vx=MAP_LEFT+(int)((long)left*MAP_WIDTH/logicalWidth);
 vy=MAP_TOP+(int)((long)top*MAP_HEIGHT/logicalHeight);
 vw=(int)((long)viewWidth*MAP_WIDTH/logicalWidth);
 vh=(int)((long)viewHeight*MAP_HEIGHT/logicalHeight);
 if(mx>=vx && mx<vx+vw && my>=vy && my<vy+vh){
  pointX=(int)((long)(mx-MAP_LEFT)*logicalWidth/MAP_WIDTH);
  pointY=(int)((long)(my-MAP_TOP)*logicalHeight/MAP_HEIGHT);
  dragAnchorX=pointX-left;dragAnchorY=pointY-top;
 }else{dragAnchorX=viewWidth/2;dragAnchorY=viewHeight/2;}
 if(dragAnchorX<0)dragAnchorX=0;if(dragAnchorX>=viewWidth)dragAnchorX=viewWidth-1;
 if(dragAnchorY<0)dragAnchorY=0;if(dragAnchorY>=viewHeight)dragAnchorY=viewHeight-1;
 previewLeft=left;previewTop=top;dragOriginX=left;dragOriginY=top;dragging=1;
 SetFocus(window);SetCapture(window);MapTarget(mx,my,&previewLeft,&previewTop);MapInvalidate();
}
static void DrawOverview(HDC dc) {
 RECT desk,view;HBRUSH oldBrush;int x,y;
 desk.left=MAP_LEFT;desk.top=MAP_TOP;desk.right=MAP_LEFT+MAP_WIDTH;desk.bottom=MAP_TOP+MAP_HEIGHT;
 oldBrush=(HBRUSH)SelectObject(dc,GetStockObject(NULL_BRUSH));
 Rectangle(dc,desk.left,desk.top,desk.right,desk.bottom);
 if(live){
  x=dragging?previewLeft:left;y=dragging?previewTop:top;
  view.left=MAP_LEFT+(int)((long)x*MAP_WIDTH/logicalWidth);
  view.top=MAP_TOP+(int)((long)y*MAP_HEIGHT/logicalHeight);
  view.right=view.left+(int)((long)viewWidth*MAP_WIDTH/logicalWidth);
  view.bottom=view.top+(int)((long)viewHeight*MAP_HEIGHT/logicalHeight);
  if(dragging)DrawFocusRect(dc,&view);else Rectangle(dc,view.left,view.top,view.right,view.bottom);
 }else{
  TextOut(dc,MAP_LEFT+4,MAP_TOP+24,"UNAVAILABLE",11);
 }
 SelectObject(dc,oldBrush);
}
BOOL FAR PASCAL __export RecoverOne(HWND hwnd,LPARAM data) {
 LONG style;RECT r;char cls[32],title[64];int width,caption,overlapX,overlapY,needX,needY,minX,maxX,minY,maxY,x,y;
 recoveryVisited++;
 if(hwnd==window || !IsWindowVisible(hwnd) || IsIconic(hwnd) || IsZoomed(hwnd))return 1;
 style=GetWindowLong(hwnd,GWL_STYLE);
 if((style&WS_CHILD) || (style&WS_CAPTION)!=WS_CAPTION)return 1;
 if(GetWindowText(hwnd,title,sizeof(title))<=0 || !title[0])return 1;
 GetClassName(hwnd,cls,sizeof(cls));
 if(!lstrcmp(cls,"Progman") || !lstrcmp(cls,"#32768") || !lstrcmp(cls,"Shell_TrayWnd") ||
    !lstrcmp(cls,"WorkerW") || !lstrcmp(cls,"DDEMLMom"))return 1;
 GetWindowRect(hwnd,&r);
 width=r.right-r.left;caption=GetSystemMetrics(SM_CYCAPTION)+2*GetSystemMetrics(SM_CYFRAME);
 if(caption<1)caption=18;if(caption>r.bottom-r.top)caption=r.bottom-r.top;
 if(width<1 || caption<1)return 1;
 overlapX=(r.right<logicalWidth?r.right:logicalWidth)-(r.left>0?r.left:0);
 overlapY=((r.top+caption)<logicalHeight?(r.top+caption):logicalHeight)-(r.top>0?r.top:0);
 needX=width<24?width:24;needY=caption<8?caption:8;
 if(overlapX>=needX && overlapY>=needY)return 1;
 minX=left;maxX=left+viewWidth-(width<viewWidth?width:viewWidth);if(maxX<minX)maxX=minX;
 minY=top;maxY=top+viewHeight-(caption<viewHeight?caption:viewHeight);if(maxY<minY)maxY=minY;
 x=r.left;y=r.top;if(x<minX)x=minX;if(x>maxX)x=maxX;if(y<minY)y=minY;if(y>maxY)y=maxY;
 if(x==r.left && y==r.top)return 1;
 if(SetWindowPos(hwnd,0,x,y,0,0,SWP_NOZORDER|SWP_NOACTIVATE|SWP_NOSIZE))recoveryMoved++;
 else recoveryFailed++;
 return 1;
}
static void RecoverWindows(void) {
 FARPROC recoverProc;int enumResult;
 if(!live)return;
 if(windowOnly){
  recoveryMoved=WDWinHome();Query();
  lstrcpy(recoveryStatus,recoveryMoved<0?"Home could not finish":"Windows recovered");
  InvalidateRect(window,0,FALSE);return;
 }
 CancelMapDrag();
 if(!Pan(0,0))return;
 if(!Query()){DriverLost("RECOVER_QUERY");return;}
 recoveryMoved=recoveryFailed=0;recoveryVisited=0;enumResult=0;Log("RECOVER_ENUM_BEGIN",left,top,0,0);
 recoverProc=MakeProcInstance((FARPROC)RecoverOne,instanceHandle);
 if(!recoverProc){recoveryFailed=1;Log("RECOVER_ENUM_THUNK_FAIL",0,0,0,0);}
 else{enumResult=EnumWindows((WNDENUMPROC)recoverProc,0L);FreeProcInstance(recoverProc);if(!enumResult){recoveryFailed++;Log("RECOVER_ENUM_FAIL",0,0,0,0);}}
 Log("RECOVER_ENUM_END",enumResult,recoveryVisited,recoveryMoved,recoveryFailed);
 wsprintf(recoveryStatus,"Moved %d; failed %d",recoveryMoved,recoveryFailed);
 Log("RECOVERY",recoveryMoved,recoveryFailed,left,top);InvalidateRect(window,0,FALSE);
}
static int Pan(int x,int y) {
 int in[2],out[6],oldX,oldY,keep,maxX,maxY;POINT p;unsigned st[8];
 if(dragging)CancelMapDrag();ResetEdge();if(!live)return 0;
 if(windowOnly){
  oldX=left;oldY=top;keep=WDWinPan(x,y)>=0;Query();
  Log("WINDOW_PAN",oldX,oldY,left,top);InvalidateRect(window,0,FALSE);return keep;
 }
 if(!Query()){DriverLost("PAN_QUERY");return 0;}
 maxX=logicalWidth-viewWidth;maxY=logicalHeight-viewHeight;
 if(x<0)x=0;if(x>maxX)x=maxX;if(y<0)y=0;if(y>maxY)y=maxY;
 x&=0xfff8;y&=0xfffc;oldX=left;oldY=top;
 if(x==oldX && y==oldY)return 1;
 GetCursorPos(&p);keep=p.x>=oldX && p.x<oldX+320 && p.y>=oldY && p.y<oldY+200;
 in[0]=x;in[1]=y;
 if(Escape(display,ESC_XY,4,(LPSTR)in,(LPSTR)out)<=0) {DriverLost("PAN_ESCAPE");Log("ERROR",x,y,0,0);return 0;}
 if(!Query()){DriverLost("PAN_QUERY");Log("ERROR",x,y,0,0);return 0;}
 if(keep){
  /* Present may take time: preserve the latest pointer, not the old sample. */
  GetCursorPos(&p);
  if(p.x<oldX)p.x=oldX;if(p.x>oldX+319)p.x=oldX+319;
  if(p.y<oldY)p.y=oldY;if(p.y>oldY+199)p.y=oldY+199;
  SetCursorPos(p.x+left-oldX,p.y+top-oldY);
 }
 Log("PAN",oldX,oldY,left,top);
 if(statsProc){statsProc(st);Log("PSTAT",st[2],st[3],st[7],st[0]);}
 if(edgePresent)edgeDirty=1;else{edgeDirty=0;InvalidateRect(window,0,FALSE);}return 1;
}
static void Mode(int value) {
 int ok;if(!live || windowOnly || (value!=0 && value!=1))return;ResetEdge();
 ok=Escape(display,ESC_MODE,2,(LPSTR)&value,0)>0;
 if(!ok){Log("MODE",value,hardware,0,0);DriverLost("MODE_ESCAPE");return;}
 if(!Query()){Log("MODE",value,hardware,0,0);DriverLost("MODE_QUERY");return;}
 Log("MODE",value,hardware,1,0);InvalidateRect(window,0,FALSE);
}
static void Cleanup(void) {
 int modeResult,panResult,confirmed,value,in[2],out[6];
 if(windowOnly){Log("WINDOW_STOP",WDWinShutdown(),0,0,0);return;}
 /* Always request the existing software/home shutdown state through the driver. */
 value=0;in[0]=in[1]=0;
 modeResult=Escape(display,ESC_MODE,2,(LPSTR)&value,0);
 panResult=Escape(display,ESC_XY,4,(LPSTR)in,(LPSTR)out);
 confirmed=Query();Log("STOP",modeResult,panResult,confirmed,hardware);
 Log("STOP_ORIGIN",left,top,live,0);
}
static int Stop(void) {
 if(closing)return 1;
 if(windowOnly && WDWinShutdown()<0)return 0;
 CancelMapDrag();closing=1;PanDlgClose();edge=follow=0;ResetEdge();KillTimer(window,1);Cleanup();live=0;return 1;
}
static int Press(int key,int i) {
 int down;down=(GetAsyncKeyState(key)&0x8000)!=0;
 if(!down){latch[i]=0;return 0;}if(latch[i])return 0;latch[i]=1;return 1;
}
static void KeyAction(int i) {
 Log("KEY",i,left,top,0);
 switch(i){
 case 0:Pan(left-8,top);break;case 1:Pan(left+8,top);break;
 case 2:Pan(left,top-4);break;case 3:Pan(left,top+4);break;
 case 4:XyHome(0);break;case 5:Mode(!hardware);break;
 case 6:edge=!edge;edgePolled=0;ResetEdge();Log("EDGE",edge,500,0,0);InvalidateRect(window,0,FALSE);break;
 case 7:if(!windowOnly){follow=!follow;ResetEdge();Log("FOLLOW",follow,0,0,0);InvalidateRect(window,0,FALSE);}break;
 case 8:PostMessage(window,WM_CLOSE,0,0L);break;
 case 9:RecoverWindows();break;
 }
}
static int KeyMessage(int key,LPARAM flags) {
 int i;if(!(GetKeyState(VK_CONTROL)&0x8000) || !(GetKeyState(VK_MENU)&0x8000))return 0;
 for(i=0;i<10;i++)if(keys[i]==key){
  if(!(flags&0x40000000L) && !closing){
   latch[i]=1; /* A held key must not fire again if focus changes. */
   if(i==8)KeyAction(i);
   else if(live && Query())KeyAction(i);
  }return 1;
 }return 0;
}
static void Keyboard(void) {
 int k[10],chord,i,controlDown,altDown;
 /* Focused commands use queued messages so a short press survives paint.
    The timer remains a best-effort background chord path, never both. */
 if(GetActiveWindow()==window)return;
 controlDown=(GetAsyncKeyState(VK_CONTROL)&0x8000)!=0;altDown=(GetAsyncKeyState(VK_MENU)&0x8000)!=0;chord=controlDown && altDown;
 for(i=0;i<10;i++)k[i]=Press(keys[i],i);
 if(!chord)return;
 if(k[8]){KeyAction(8);return;}
 if(k[9]){RecoverWindows();return;}
 if(k[4])XyHome(0);
 else if(k[0]||k[1]||k[2]||k[3])Pan(left+(k[1]-k[0])*8,top+(k[3]-k[2])*4);
 else if(k[5])Mode(!hardware);
 else if(k[6]){edge=!edge;edgePolled=0;ResetEdge();Log("EDGE",edge,500,0,0);InvalidateRect(window,0,FALSE);}
 else if(k[7] && !windowOnly){follow=!follow;ResetEdge();Log("FOLLOW",follow,0,0,0);InvalidateRect(window,0,FALSE);}
}
static void Edge(void) {
 POINT p;int dx,dy,mx,my,px,py,ok,wasHardware;DWORD now,elapsed,wait;
 if(!edge || !live || closing){ResetEdge();PaintEdge();return;}
 GetCursorPos(&p);if(!edgePolled){edgePolled=1;Log("EDGE_SAMPLE",left,top,p.x,p.y);}px=p.x-left;py=p.y-top;dx=dy=0;
 /* Keep raw direction stable when one axis reaches its viewport limit. */
 if(windowOnly){px=p.x;py=p.y;}
 if(px<=0)dx=-1;else if(px>=viewWidth-1)dx=1;
 if(py<=0)dy=-1;else if(py>=viewHeight-1)dy=1;
 mx=(dx<0 && left>0) || (dx>0 && left<logicalWidth-viewWidth)?dx:0;
 my=(dy<0 && top>0) || (dy>0 && top<logicalHeight-viewHeight)?dy:0;
 if(!mx && !my){ResetEdge();PaintEdge();return;}
 now=GetTickCount();
 if(dx!=directionX || dy!=directionY){directionX=dx;directionY=dy;edgeRepeating=0;since=now;Log("ARM",dx,dy,px,py);PaintEdge();return;}
 wait=edgeRepeating?(DWORD)edgeRepeat:500L;
 elapsed=now-since;if(elapsed<wait)return;
 /* Clamp both overshoots and confirm the pointer before using this origin. */
 if(px<0)px=0;if(px>=viewWidth)px=viewWidth-1;if(py<0)py=0;if(py>=viewHeight)py=viewHeight-1;
 SetCursorPos((windowOnly?0:left)+px,(windowOnly?0:top)+py);GetCursorPos(&p);
 if(p.x!=(windowOnly?0:left)+px || p.y!=(windowOnly?0:top)+py){ResetEdge();PaintEdge();return;}
 Log("EFIRE",left,top,mx,my);Log("DWELL",(int)elapsed,px,py,(int)wait);
 wasHardware=hardware;edgePresent=1;ok=Pan(left+mx*8,top+my*4);edgePresent=0;
 if(ok && live && edge && !(wasHardware && !hardware)){
  directionX=dx;directionY=dy;edgeRepeating=1;
  /* One pan per timer callback; no catch-up, including after slow redraw. */
  since=GetTickCount();
 }else{edgeDirty=1;PaintEdge();}
}
static int Fit(int origin,int low,int high,int extent,int step,int limit) {
 int result;result=origin;
 if(high-low>extent || low<origin)result=low&~(step-1);
 else if(high>origin+extent)result=(high-extent+step-1)&~(step-1);
 if(result<0)result=0;if(result>limit)result=limit;return result;
}
static int Follow(void) {
 HWND active;RECT r;char name[32];int x,y;
 if(!follow || !live || closing || windowOnly)return 0;active=GetActiveWindow();
 if(!active || active==window || !IsWindowVisible(active) || IsIconic(active))return 0;
 GetClassName(active,name,sizeof(name));
 if(lstrcmp(name,"#32770")!=0)return 0;
 GetWindowRect(active,&r);x=Fit(left,r.left,r.right,320,8,320);y=Fit(top,r.top,r.bottom,200,4,56);
 if(x!=left || y!=top){Log("DIALOG",r.left,r.top,r.right,r.bottom);Pan(x,y);}
 return 1; /* Active dialog following owns the viewport, even after it fits. */
}
/* Shared settings window glue: it edits the engine variables the timer already uses. */
static void CopyArg(char *d,LPSTR s,int cap) {
 int i=0;while(s[i] && i<cap-1){d[i]=s[i];i++;}d[i]=0;
}
static int IniGet(void *c,const char *s,const char *k,int d) {
 return (int)GetProfileInt(s,k,d);
}
static int IniPut(void *c,const char *s,const char *k,int v) {
 char b[12];wsprintf(b,"%d",v);return WriteProfileString(s,k,b);
}
static int XyQuery(void *c,PANCAPS *cp,PANSET *s) {
 if(!live || !Query()){cp->backend=PS_BACK_NONE;cp->caps=0;return 0;}
 cp->backend=PS_BACK_XY;cp->caps=PanCapsFor(PS_BACK_XY,statsProc!=0);
 if(windowOnly){cp->caps=(cp->caps&~(PS_CAP_SOFT|PS_CAP_HARD|PS_CAP_FOLLOWD))|PS_CAP_MODE|PS_CAP_DESK;
  panHost.backend=WDWinDropped()?"Window limit: close windows or use Home":"Window workspace (24 windows)";}
 cp->viewX=left;cp->viewY=top;cp->viewW=viewWidth;cp->viewH=viewHeight;cp->workW=logicalWidth;cp->workH=logicalHeight;
 PanSetDefaults(PS_BACK_XY,s);s->edgeOn=edge;s->repeat=edgeRepeat;s->followDlg=follow;s->mode=windowOnly?PS_MODE_DESK:hardware;return 1;
}
static int WindowApply(const PANSET *w,PANSET *a) {
 if(w->mode!=PS_MODE_DESK)return PS_E_APPLY;
 edge=w->edgeOn;edgeRepeat=w->repeat;ResetEdge();*a=*w;a->mode=PS_MODE_DESK;return PS_OK;
}
static int XyApply(void *c,const PANSET *w,PANSET *a,char *note,int cap) {
 int want;
 if(!live || !Query())return PS_E_LOST;
 if(windowOnly){note[0]=0;return WindowApply(w,a);}
 if(w->mode!=PS_MODE_SOFT && w->mode!=PS_MODE_HARD)return PS_E_APPLY;
 want=w->mode;note[0]=0;
 /* Mode is only touched when it can be read back; the result is what the driver reports. */
 if(statsProc && want!=hardware){Mode(want);if(!live)return PS_E_LOST;}
 edge=w->edgeOn;edgePolled=0;edgeRepeat=w->repeat;follow=w->followDlg;ResetEdge();
 Log("EDGE",edge,500,0,0);Log("RATE",edgeRepeat,500,0,0);Log("FOLLOW",follow,0,0,0);
 PanSetDefaults(PS_BACK_XY,a);a->edgeOn=edge;a->repeat=edgeRepeat;a->followDlg=follow;a->mode=hardware;
 if(statsProc && want!=hardware)if(cap>=48)lstrcpy(note,want?"Hardware pan not granted; running software.":"Software pan not granted; running hardware.");
 InvalidateRect(window,0,FALSE);return PS_OK;
}
static int XyHome(void *c) {
 if(windowOnly){int ok=WDWinHome()>=0;Query();InvalidateRect(window,0,FALSE);return ok;}
 return live && Pan(0,0);
}
static void OpenSettings(void) {
 PanDlgOpen(instanceHandle,&panHost);
}
static HMENU Menu(void) {
 HMENU bar,p,m,e,w;bar=CreateMenu();p=CreatePopupMenu();m=CreatePopupMenu();e=CreatePopupMenu();w=CreatePopupMenu();
 AppendMenu(p,MF_STRING,LEFT,"&Left 8");AppendMenu(p,MF_STRING,RIGHT,"&Right 8");AppendMenu(p,MF_STRING,UP,"&Up 4");AppendMenu(p,MF_STRING,DOWN,"&Down 4");AppendMenu(p,MF_STRING,HOME,"&Home");AppendMenu(p,MF_STRING,QUIT,"E&xit");
 if(windowOnly)AppendMenu(m,MF_STRING|MF_CHECKED,SETTINGS,"Window workspace");
 else{AppendMenu(m,MF_STRING,SOFT,"&Software");AppendMenu(m,MF_STRING,HARD,"&Hardware");}
 AppendMenu(e,MF_STRING,EDGEON,"Edge &on");AppendMenu(e,MF_STRING,EDGEOFF,"Edge o&ff");
 if(!windowOnly){AppendMenu(e,MF_STRING,FOLLOWON,"Dialog follow on");AppendMenu(e,MF_STRING,FOLLOWOFF,"Dialog follow off");}
 AppendMenu(e,MF_STRING,SETTINGS,"Panning &settings...");AppendMenu(e,MF_STRING,REPEAT100,"Repeat &100ms");AppendMenu(e,MF_STRING,REPEAT200,"Repeat &200ms");AppendMenu(e,MF_STRING,REPEAT500,"Repeat &500ms");
 AppendMenu(w,MF_STRING,RECOVER,"&Bring windows back");
 AppendMenu(bar,MF_POPUP,(UINT)p,"&Pan");AppendMenu(bar,MF_POPUP,(UINT)m,"&Mode");AppendMenu(bar,MF_POPUP,(UINT)e,"&Options");AppendMenu(bar,MF_POPUP,(UINT)w,"&Windows");return bar;
}
long FAR PASCAL __export Wnd(HWND w,UINT msg,WPARAM a,LPARAM b) {
 PAINTSTRUCT ps;HDC dc;char line[XY_PAINT_LINE_CAP];
 if(openMsg && msg==openMsg){OpenSettings();return 0;}
 switch(msg){
 case WM_CREATE:
  homeButton=CreateWindow("BUTTON","Home",WS_CHILD|WS_VISIBLE|BS_PUSHBUTTON,176,52,112,22,w,(HMENU)HOME,instanceHandle,0);
  recoverButton=CreateWindow("BUTTON","Recover windows",WS_CHILD|WS_VISIBLE|BS_PUSHBUTTON,176,78,112,22,w,(HMENU)RECOVER,instanceHandle,0);
  SetTimer(w,1,100,0);EnablePanControls(live);return 0;
 case WM_LBUTTONDOWN:Log("MAP_DOWN",(int)w,(int)(short)LOWORD(b),(int)(short)HIWORD(b),0);BeginMapDrag((int)(short)LOWORD(b),(int)(short)HIWORD(b));return 0;
 case WM_MOUSEMOVE:
  if(dragging && GetCapture()==w){Log("MAP_MOVE",(int)w,(int)(short)LOWORD(b),(int)(short)HIWORD(b),0);MapTarget((int)(short)LOWORD(b),(int)(short)HIWORD(b),&previewLeft,&previewTop);MapInvalidate();return 0;}
  break;
 case WM_LBUTTONUP:
  Log("MAP_UP",(int)w,(int)(short)LOWORD(b),(int)(short)HIWORD(b),dragging);
  if(dragging){int targetX,targetY,originX,originY;
   MapTarget((int)(short)LOWORD(b),(int)(short)HIWORD(b),&targetX,&targetY);originX=dragOriginX;originY=dragOriginY;
   if(!Query()){DriverLost("MAP_RELEASE_QUERY");return 0;}
   if(left!=originX || top!=originY){
    Log("MAP_DRAG_EXTERNAL",originX,originY,left,top);CancelMapDrag();return 0;
   }
   dragging=0;if(GetCapture()==w)ReleaseCapture();MapInvalidate();Pan(targetX,targetY);return 0;
  }
  return 0;
 case WM_CANCELMODE:CancelMapDrag();return 0;
 case WM_KILLFOCUS:CancelMapDrag();break;
 case WM_KEYDOWN:case WM_SYSKEYDOWN:
  if(a==VK_ESCAPE && dragging){CancelMapDrag();return 0;}
  if(KeyMessage(a,b))return 0;break;
 case WM_TIMER:if(!closing && live){int oldX,oldY;if(!timerSeen){timerSeen=1;Log("TIMER_START",left,top,edge,0);}oldX=left;oldY=top;if(!Query()){DriverLost("QUERY_ERROR");return 0;}if(windowOnly)(void)WDWinPan(left,top);if(dragging){if(GetCapture()!=w || oldX!=left || oldY!=top)CancelMapDrag();return 0;}Keyboard();if(Follow()){ResetEdge();PaintEdge();}else Edge();PanDlgTrack();}return 0;
 case WM_COMMAND:
  if(a==RECOVER)Log("RECOVER_ENTRY",(int)w,(int)a,left,top);
  if(a!=QUIT && live && !Query()){DriverLost("COMMAND_QUERY");return 0;}
  switch(a){
   case LEFT:Pan(left-8,top);break;case RIGHT:Pan(left+8,top);break;case UP:Pan(left,top-4);break;case DOWN:Pan(left,top+4);break;
   case HOME:XyHome(0);break;case RECOVER:RecoverWindows();break;case SOFT:Mode(0);break;case HARD:Mode(1);break;
   case EDGEON:case EDGEOFF:edge=a==EDGEON;edgePolled=0;ResetEdge();Log("EDGE",edge,500,0,0);InvalidateRect(w,0,FALSE);break;
   case FOLLOWON:case FOLLOWOFF:follow=a==FOLLOWON;ResetEdge();Log("FOLLOW",follow,0,0,0);InvalidateRect(w,0,FALSE);break;
   case REPEAT100:case REPEAT200:case REPEAT500:edgeRepeat=a==REPEAT100?100:(a==REPEAT200?200:500);ResetEdge();Log("RATE",edgeRepeat,500,0,0);InvalidateRect(w,0,FALSE);break;
   case SETTINGS:OpenSettings();break;
   case QUIT:PostMessage(w,WM_CLOSE,0,0L);break;
  }return 0;
 case WM_PAINT:
  edgeDirty=0;
  dc=BeginPaint(w,&ps);wsprintf(line,"Desk %dx%d / View %dx%d",logicalWidth,logicalHeight,viewWidth,viewHeight);TextOut(dc,8,4,line,lstrlen(line));
  TextOut(dc,8,20,"Ctrl+Alt arrows; Home; R recover",lstrlen("Ctrl+Alt arrows; Home; R recover"));
  TextOut(dc,8,36,"Click/drag map; Esc cancels",lstrlen("Click/drag map; Esc cancels"));
  TextOut(dc,8,48,"Overview",lstrlen("Overview"));DrawOverview(dc);
  /* The status line has at most 14 visible characters in this 128-byte buffer. */
  wsprintf(line,"X%d Y%d %s",left,top,(LPSTR)(windowOnly?"WIN":hardware?"HW":"SW"));TextOut(dc,176,106,line,lstrlen(line));
  wsprintf(line,"Edge %d Follow %d",edge,follow);TextOut(dc,176,122,line,lstrlen(line));
  TextOut(dc,8,132,recoveryStatus,lstrlen(recoveryStatus));EndPaint(w,&ps);return 0;
 case WM_CLOSE:
  if(!Stop()){MessageBox(w,"Windows could not finish recovering a window. Use Home before closing the workspace.","Window workspace",MB_OK|MB_ICONEXCLAMATION);return 0;}DestroyWindow(w);return 0;
 case WM_QUERYENDSESSION:return !windowOnly || WDWinPrepareShutdown()>=0;
 case WM_ENDSESSION:if(a)Stop();return 0;
 case WM_DESTROY:Stop();PostQuitMessage(0);return 0;
 }return DefWindowProc(w,msg,a,b);
}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR command,int show) {
 WNDCLASS wc;FARPROC thunk;MSG msg;HINSTANCE driver;int value,settings;char arg[24];HWND owner;
 instanceHandle=instance;
 /* One owner: route a second launch to the first before any driver escape (an escape would reset its mode). */
 CopyArg(arg,command,sizeof(arg));settings=PanCmdParse(arg)==PS_CMD_SETTINGS;openMsg=RegisterWindowMessage(PS_MSG_XY);
 owner=FindWindow("XTPan",0);
 if(owner){if(settings)PostMessage(owner,RegisterWindowMessage(PS_MSG_VERT),0,0L);return 0;}
 switch(PanOwnerStart(previous!=0,settings)){
 case PS_OWN_FORWARD:owner=FindWindow(XY_CLASS_NAME,0);if(owner)PostMessage(owner,openMsg,0,0L);return 0;
 case PS_OWN_EXIT:owner=FindWindow(XY_CLASS_NAME,0);if(owner){if(IsIconic(owner))ShowWindow(owner,SW_RESTORE);BringWindowToTop(owner);}return 0;
 }
 display=GetDC(0);if(!display)return 1;driver=GetModuleHandle("DISPLAY");statsProc=(STATS)GetProcAddress(driver,(LPSTR)106L);
 if(GetDeviceCaps(display,HORZRES)!=640 || GetDeviceCaps(display,VERTRES)!=256 || !Query()){
  if(!settings || GetSystemMetrics(SM_CYSCREEN)!=200 ||
     (GetSystemMetrics(SM_CXSCREEN)!=320 && GetSystemMetrics(SM_CXSCREEN)!=640) ||
     WDWinInit(2048,2048)!=WD_OK){
   MessageBox(0,"Use the supported Tandy pan display, or open Settings on a fixed 320x200 or 640x200 display.","XY overview unavailable",MB_OK|MB_ICONEXCLAMATION);
   ReleaseDC(0,display);return 1;
  }
  windowOnly=1;statsProc=0;live=1;WDWinExclude("Progman");WDWinExclude("TandyStart");Query();
 }
 value=0;if(!windowOnly)live=Escape(display,ESC_MODE,2,(LPSTR)&value,0)>0;
 if(!live){MessageBox(0,"The display driver does not provide the XY panning control escape. No pan controls were started.","XY overview unavailable",MB_OK|MB_ICONEXCLAMATION);ReleaseDC(0,display);return 1;}
 if(!Query()){
  Cleanup();MessageBox(0,"The display driver stopped reporting the supported XY panning geometry. No pan controls were started.","XY overview unavailable",MB_OK|MB_ICONEXCLAMATION);
  live=0;ReleaseDC(0,display);return 1;
 }
 panHost.ops.query=XyQuery;panHost.ops.apply=XyApply;panHost.ops.home=XyHome;panHost.store.get=IniGet;panHost.store.put=IniPut;
 panHost.title="XY panning settings";panHost.backend=windowOnly?"Window workspace (24 windows)":"Tandy XY pan (HPXY)";
 {PANCAPS pc;PANSET ps;
  /* Saved edge/repeat/dialog settings only; the mode always starts in software. */
  pc.backend=PS_BACK_XY;pc.caps=PanCapsFor(PS_BACK_XY,statsProc!=0);PanSetLoad(&pc,&ps,&panHost.store);
  edge=ps.edgeOn;edgeRepeat=ps.repeat;follow=windowOnly?0:ps.followDlg;}
 OpenLog(instance);Log("START",left,top,hardware,0);Log("EDGE_E1",500,edgeRepeat,100,0);
 memset(&wc,0,sizeof(wc));thunk=MakeProcInstance((FARPROC)Wnd,instance);wc.lpfnWndProc=(WNDPROC)thunk;wc.hInstance=instance;wc.hCursor=LoadCursor(0,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);wc.lpszClassName=XY_CLASS_NAME;RegisterClass(&wc);
 window=CreateWindow(XY_CLASS_NAME,XY_WINDOW_TITLE,WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,left+4,top+2,312,196,0,Menu(),instance,0);
 if(!window){Cleanup();goto done;}ShowWindow(window,show);UpdateWindow(window);
 if(settings)PostMessage(window,openMsg,0,0L);
 while(GetMessage(&msg,0,0,0)){
  if(PanDlgMessage(&msg))continue;
  if(msg.message==WM_KEYDOWN && msg.wParam==VK_ESCAPE && dragging){CancelMapDrag();continue;}
  if(msg.message==WM_KEYDOWN && msg.wParam==VK_TAB && (msg.hwnd==window || msg.hwnd==homeButton || msg.hwnd==recoverButton)){
   int reverse;reverse=(GetKeyState(VK_SHIFT)&0x8000)!=0;
   if(!live)SetFocus(window);
   else if(msg.hwnd==homeButton)SetFocus(reverse?recoverButton:recoverButton);
   else if(msg.hwnd==recoverButton)SetFocus(reverse?homeButton:homeButton);
   else SetFocus(reverse?recoverButton:homeButton);
   continue;
  }
  if((msg.message==WM_KEYDOWN || msg.message==WM_SYSKEYDOWN) &&
     (msg.hwnd==window || msg.hwnd==homeButton || msg.hwnd==recoverButton) && KeyMessage(msg.wParam,msg.lParam))continue;
  if(msg.message==WM_KEYUP || msg.message==WM_SYSKEYUP){int i;for(i=0;i<10;i++)if(keys[i]==msg.wParam)latch[i]=0;}
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
done:
 if(logFile!=HFILE_ERROR)_lclose(logFile);FreeProcInstance(thunk);UnregisterClass(XY_CLASS_NAME,instance);ReleaseDC(0,display);return 0;
}
