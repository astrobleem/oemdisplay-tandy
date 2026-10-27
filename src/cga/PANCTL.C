/* CGAPAN viewport owner: the only client of the driver's 5860h/5861h escapes.
 * Windows sees a 320x200 desktop; this moves the 160x100 CGA viewport over it.
 * Ctrl+Alt+arrows pan, Home returns to the origin, End exposes the active
 * window's bottom/right, Ctrl+Alt+S opens the shared panning settings; the
 * pointer scrolls at the viewport edge after a dwell, and a new active window
 * or focused control is brought into view.
 *
 * Commands arrive through PANKEY.DLL, which retains them while the machine is
 * busy. Input handlers only queue a target; the pan itself runs from the
 * timer. Without the DLL the owner falls back to polling the keys.
 * It exits at once unless the driver reports exactly this geometry, and never
 * runs beside another panning owner (CGACTL exits at 320x200x16 by itself).
 */
#define WINVER 0x0300
#include <windows.h>
#include "PANSET.H"
#include "PANDLG.H"
#include "PANKEY.H"
#include "PANOWN.H"
#include "PANTGT.H"
#define ESC_XY 0x5860
#define ESC_MODE 0x5861
#define VIEW_W 160
#define VIEW_H 100
#define LOGICAL_W 320
#define LOGICAL_H 200
#define STEP_MIN 8
#define EDGE_X 8
#define EDGE_Y 5
#define EDGE_ZONE 2
#define KEY_REPEAT 200L
#define DEF_STEP 40
#define DEF_DWELL 400
#define PAN_ENTRY
static HWND mainWindow;
static HANDLE instance;
static int closing;
static WORD wakeMessage,settingsMessage;
static HWND lastActive,lastFocus;
static int left,top,live;
static int pending,pendX,pendY,wantSettings;
static int edgeArmed,edgeKey;
static int stepX=DEF_STEP,stepY=25,dwell=DEF_DWELL,edgeOn=1,follow=1;
static POINT lastPoint;
static DWORD edgeSince;
static int Clamp(int n,int low,int high)
{return n<low?low:n>high?high:n;}
/* Bounded copy: lstrcpyn is a Windows 3.1 call. */
static void Copy(char *dst,const char FAR *src,int cap)
{
 int i;
 for(i=0;i<cap-1 && src[i];i++)dst[i]=src[i];
 dst[i]=0;
}
static int Query(void)
{
 HDC dc;int in[2],out[6],ok;
 in[0]=-1;in[1]=0;
 dc=GetDC(NULL);ok=Escape(dc,ESC_XY,4,(LPSTR)in,(LPSTR)out)>0;ReleaseDC(NULL,dc);
 if(!ok || out[2]!=VIEW_W || out[3]!=VIEW_H || out[4]!=LOGICAL_W || out[5]!=LOGICAL_H)return live=0;
 left=out[0];top=out[1];return live=1;
}
/* Move the viewport; return the pan actually applied through *dx,*dy. */
static int Pan(int x,int y,int *dx,int *dy)
{
 HDC dc;int in[2],out[6],oldx=left,oldy=top;
 x=Clamp(x,0,LOGICAL_W-VIEW_W)&~7;y=Clamp(y,0,LOGICAL_H-VIEW_H);
 if(dx)*dx=0;if(dy)*dy=0;
 if(x==left && y==top)return 0;
 in[0]=x;in[1]=y;
 dc=GetDC(NULL);Escape(dc,ESC_XY,4,(LPSTR)in,(LPSTR)out);ReleaseDC(NULL,dc);
 if(!Query())return 0;
 if(dx)*dx=left-oldx;if(dy)*dy=top-oldy;
 return left!=oldx || top!=oldy;
}
/* Keep the pointer at the same place on the screen while the view moves. */
static void CarryPointer(int dx,int dy)
{
 POINT p;
 if(!dx && !dy)return;
 GetCursorPos(&p);
 SetCursorPos(Clamp(p.x+dx,0,LOGICAL_W-1),Clamp(p.y+dy,0,LOGICAL_H-1));
 GetCursorPos(&lastPoint);        /* our own move is not the user's */
}
static int Fit(int lo,int hi,int view,int cur)
{
 if(hi-lo>view)return lo;
 if(lo<cur)return lo;
 if(hi>cur+view)return hi-view;
 return cur;
}
/* Bring a window or control into view; put the pointer inside if it is not. */
static void Reveal(HWND w,int margin)
{
 RECT r;POINT p;int dx,dy,x;
 if(!w || !IsWindow(w) || w==mainWindow || !IsWindowVisible(w) || IsIconic(w))return;
 GetWindowRect(w,&r);
 if(r.right<=r.left || r.bottom<=r.top)return;
 x=Fit(r.left-margin,r.right+margin,VIEW_W,left);
 /* A right-edge reveal rounds up; rounding down could clip seven pixels. */
 if(x>left)x=(x+7)&~7;
 if(Pan(x,Fit(r.top-margin,r.bottom+margin,VIEW_H,top),&dx,&dy))
  edgeArmed=0;
 GetCursorPos(&p);
 if(p.x<left || p.x>=left+VIEW_W || p.y<top || p.y>=top+VIEW_H){
  SetCursorPos(Clamp((r.left+r.right)/2,left,left+VIEW_W-1),Clamp((r.top+r.bottom)/2,top,top+VIEW_H-1));
  GetCursorPos(&lastPoint);       /* our own move is not the user's */
 }
}
static HWND Active(void)
{
 HWND w=GetActiveWindow();
 if(!w || w==mainWindow || !IsWindowVisible(w) || IsIconic(w))return 0;
 return w;
}
/* The pointer is the user's own view: never leave it where it cannot be seen. */
static void FollowPointer(DWORD now)
{
 POINT p;int moved,dx,dy,key=0,sx=0,sy=0;
 GetCursorPos(&p);moved=p.x!=lastPoint.x || p.y!=lastPoint.y;lastPoint=p;
 if(moved)edgeArmed=1;
 if(moved && (p.x<left || p.x>=left+VIEW_W || p.y<top || p.y>=top+VIEW_H)){
  Pan(p.x-VIEW_W/2,p.y-VIEW_H/2,&dx,&dy);return;
 }
 if(!edgeOn || !edgeArmed)return;
 if(p.x<left+EDGE_ZONE && left>0){sx=-EDGE_X;key|=1;}
 else if(p.x>=left+VIEW_W-EDGE_ZONE && left<LOGICAL_W-VIEW_W){sx=EDGE_X;key|=2;}
 if(p.y<top+EDGE_ZONE && top>0){sy=-EDGE_Y;key|=4;}
 else if(p.y>=top+VIEW_H-EDGE_ZONE && top<LOGICAL_H-VIEW_H){sy=EDGE_Y;key|=8;}
 if(!key){edgeKey=0;return;}
 if(key!=edgeKey){edgeKey=key;edgeSince=now;return;}
 if(now-edgeSince<(DWORD)dwell)return;
 if(Pan(left+sx,top+sy,&dx,&dy))CarryPointer(dx,dy);
}
/* Shared panning settings: this owner describes itself to PANSET/PANDLGC and
 * keeps its own engine. The model names the XTPan and XYPan sections; CGAPAN
 * keeps its keys together in [CGAPan] with its own defaults. */
static int StoreGet(void *ctx,const char *section,const char *key,int def)
{
 (void)ctx;(void)section;
 if(!lstrcmp((LPSTR)key,(LPSTR)PS_KEY_STEP))def=DEF_STEP;
 else if(!lstrcmp((LPSTR)key,(LPSTR)PS_KEY_DWELL))def=DEF_DWELL;
 else if(!lstrcmp((LPSTR)key,(LPSTR)PS_KEY_FOLLOW))def=1;
 else if(!lstrcmp((LPSTR)key,(LPSTR)PS_KEY_EDGEON))def=1;
 return GetProfileInt("CGAPan",(LPSTR)key,def);
}
static int StorePut(void *ctx,const char *section,const char *key,int value)
{
 char text[12];
 (void)ctx;(void)section;
 wsprintf(text,"%d",value);
 return WriteProfileString("CGAPan",(LPSTR)key,text)!=0;
}
/* A multiple of 8 across; down is five eighths of it (40 across, 25 down). */
static int StepAcross(int step)
{
 step=(step+4)&~7;
 return Clamp(step,STEP_MIN,LOGICAL_W-VIEW_W);
}
static void UseSettings(const PANSET *s)
{
 stepX=StepAcross(s->step);stepY=(stepX*5+4)/8;
 dwell=s->dwell;follow=s->follow!=0;edgeOn=s->edgeOn!=0;edgeKey=0;
}
static int OpQuery(void *ctx,PANCAPS *c,PANSET *s)
{
 (void)ctx;
 if(!Query()){c->backend=PS_BACK_NONE;return 0;}
 c->backend=PS_BACK_XY;
 c->caps=PS_CAP_STEP|PS_CAP_DWELL|PS_CAP_FOLLOW|PS_CAP_EDGEON|PS_CAP_HOME;
 c->viewX=left;c->viewY=top;c->viewW=VIEW_W;c->viewH=VIEW_H;
 c->workW=LOGICAL_W;c->workH=LOGICAL_H;
 PanSetDefaults(PS_BACK_XY,s);
 s->step=stepX;s->dwell=dwell;s->follow=follow;s->edgeOn=edgeOn;
 return 1;
}
static int OpApply(void *ctx,const PANSET *want,PANSET *actual,char *note,int cap)
{
 (void)ctx;
 *actual=*want;
 actual->step=StepAcross(want->step);
 UseSettings(actual);
 if(actual->step!=want->step)Copy(note,"Step rounded to a multiple of 8.",cap);
 return PS_OK;
}
static int OpHome(void *ctx)
{
 int dx,dy;
 (void)ctx;
 pending=0;Pan(0,0,&dx,&dy);
 return Query();
}
static PANHOST host={{0,OpQuery,OpApply,OpHome},{0,StoreGet,StorePut},
 "Panning settings","Software viewport"};
static void LoadSettings(void)
{
 PANCAPS c;PANSET s;PANSTORE st;
 if(!OpQuery(0,&c,&s))return;
 st=host.store;PanSetLoad(&c,&s,&st);UseSettings(&s);
}
static void DrainKeys(void)
{
 int cmd,ex=0,ey=0;HWND active;RECT frame;PANTARGET target;
 PanTargetInit(&target,left,top,160,100,stepX,stepY,8,1);
 while((cmd=PanInputNext())!=0){
  if(cmd==PK_SETTINGS){wantSettings=1;continue;}
  if(cmd==PK_END){
   active=Active();if(!active)continue;GetWindowRect(active,&frame);
   ex=frame.right-VIEW_W;ey=frame.bottom-VIEW_H;
  }
  (void)PanTargetCommand(&target,cmd,ex,ey);
 }
 if(target.moved){pendX=target.x;pendY=target.y;pending=1;}
}
long FAR PASCAL PAN_ENTRY WndProc(HWND w,unsigned m,UINT wp,LONG lp)
{
 int dx,dy,moved=0;DWORD now;HWND a,f;
 if(m==wakeMessage)return 0;
 if(m==settingsMessage){wantSettings=1;return 0;}
 if(m==WM_TIMER){
  if(closing){if(PanInputStop())DestroyWindow(w);return 0;}
  if(!Query())return 0;
  DrainKeys();
  now=GetTickCount();
  /* The pan runs here, never in the input path. */
  if(pending){
   pending=0;
   if(Pan(pendX,pendY,&dx,&dy)){CarryPointer(dx,dy);edgeArmed=0;}
   moved=1;
  }
  if(wantSettings){wantSettings=0;PanDlgOpen(instance,&host);}
  if(!moved){
   a=Active();f=GetFocus();
   if(a && a!=lastActive){lastActive=a;lastFocus=f;if(follow)Reveal(a,0);}
   else if(f && f!=lastFocus){lastFocus=f;if(follow)Reveal(f,4);}
   else FollowPointer(now);
  }
  PanDlgTrack();
  return 0;
 }
 if(m==WM_CLOSE){closing=1;pending=wantSettings=0;PanDlgClose();
  if(PanInputStop())DestroyWindow(w);return 0;}
 /* A cancelled session end must leave the viewport owner running. */
 if(m==WM_ENDSESSION && !wp)return 0;
 if(m==WM_ENDSESSION || m==WM_DESTROY){
  PanDlgClose();
  (void)PanInputStop();
  if(m==WM_DESTROY){KillTimer(w,1);PostQuitMessage(0);return 0;}
 }
 return DefWindowProc(w,m,wp,lp);
}
static void StartKeys(void)
{
 PANBIND map[PK_BIND_MAX];int n=PanInputDefaults(map,PK_X|PK_Y);
 (void)PanInputStart(mainWindow,wakeMessage,map,n);
}
int PASCAL WinMain(HANDLE hi,HANDLE previous,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;HDC dc;HWND other;int in[1],wide,high,colors,mode,settings;
 char line[24];
 (void)show;
 instance=hi;
 Copy(line,cmd,sizeof(line));settings=PanCmdParse(line)==PS_CMD_SETTINGS;
 settingsMessage=PanOwnerMessage(PN_CGA);
 if(PanOwnerRoute(settings))return 0;
 /* A second copy only asks the running owner for its settings. */
 other=FindWindow("CGAPan",0);
 if(other || previous){
  if(other && settings)PostMessage(other,settingsMessage,0,0L);
  return 0;
 }
 dc=GetDC(NULL);wide=GetDeviceCaps(dc,HORZRES);high=GetDeviceCaps(dc,VERTRES);
 colors=GetDeviceCaps(dc,NUMCOLORS);
 in[0]=0;mode=Escape(dc,ESC_MODE,2,(LPSTR)in,NULL);ReleaseDC(NULL,dc);
 /* Only the CGAPAN driver: 320x200x16 whose escapes answer for this geometry. */
 if(wide!=LOGICAL_W || high!=LOGICAL_H || colors!=16 || mode<=0 || !Query())return 0;
 /* One owner: no other panning client may run beside this one. */
 if(FindWindow("XTPan",0) || FindWindow("XYOverviewControl",0) || FindWindow("CGASlide",0))return 0;
 SetMessageQueue(32);       /* a larger queue retains more while busy */
 wakeMessage=RegisterWindowMessage(PK_WAKE);
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=hi;
 wc.hIcon=0;wc.hCursor=0;wc.hbrBackground=0;wc.lpszMenuName=0;wc.lpszClassName="CGAPan";
 if(!RegisterClass(&wc))return 1;
 mainWindow=CreateWindow("CGAPan","CGA viewport",WS_POPUP,0,0,0,0,0,0,hi,0);
 if(!mainWindow)return 1;
 if(!SetTimer(mainWindow,1,100,0)){DestroyWindow(mainWindow);return 1;}
 LoadSettings();
 StartKeys();
 if(settings)wantSettings=1;
 GetCursorPos(&lastPoint);
 while(GetMessage(&msg,0,0,0)){
  if(PanDlgMessage(&msg))continue;
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
 return msg.wParam;
}
