/* CGAPAN viewport owner: the only client of the driver's 5860h/5861h escapes.
 * Windows sees a 320x200 desktop; this moves the 160x100 CGA viewport over it.
 * Ctrl+Alt+arrows pan, Home returns to the origin, End exposes the active
 * window's bottom/right; the pointer scrolls at the viewport edge after a
 * dwell, and a new active window or focused control is brought into view.
 * It exits at once unless the driver reports exactly this geometry, and never
 * runs beside another panning owner (CGACTL exits at 320x200x16 by itself).
 */
#define WINVER 0x0300
#include <windows.h>
#define ESC_XY 0x5860
#define ESC_MODE 0x5861
#define VIEW_W 160
#define VIEW_H 100
#define LOGICAL_W 320
#define LOGICAL_H 200
#define STEP_X 40
#define STEP_Y 25
#define EDGE_X 8
#define EDGE_Y 5
#define EDGE_ZONE 2
#define EDGE_DWELL 400L
#define KEY_REPEAT 200L
#ifdef __WATCOMC__
#define PAN_ENTRY __export
#else
#define PAN_ENTRY
#endif
static HWND mainWindow;
static HWND lastActive,lastFocus;
static int left,top,live;
static int edgeArmed,edgeKey;
static POINT lastPoint;
static DWORD edgeSince,lastKey;
static int held;
static int Clamp(int n,int low,int high)
{return n<low?low:n>high?high:n;}
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
 RECT r;POINT p;int dx,dy;
 if(!w || !IsWindow(w) || w==mainWindow || !IsWindowVisible(w) || IsIconic(w))return;
 GetWindowRect(w,&r);
 if(r.right<=r.left || r.bottom<=r.top)return;
 if(Pan(Fit(r.left-margin,r.right+margin,VIEW_W,left),Fit(r.top-margin,r.bottom+margin,VIEW_H,top),&dx,&dy))
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
static void KeyPan(int key)
{
 HWND w;RECT r;int dx,dy,x=left,y=top;
 if(key==VK_HOME){x=0;y=0;}
 else if(key==VK_END){
  w=Active();if(!w)return;
  GetWindowRect(w,&r);x=r.right-VIEW_W;y=r.bottom-VIEW_H;
 }
 else if(key==VK_LEFT)x-=STEP_X;else if(key==VK_RIGHT)x+=STEP_X;
 else if(key==VK_UP)y-=STEP_Y;else if(key==VK_DOWN)y+=STEP_Y;
 if(Pan(x,y,&dx,&dy)){CarryPointer(dx,dy);edgeArmed=0;}
}
static int ChordKey(void)
{
 static int keys[6]={VK_HOME,VK_END,VK_LEFT,VK_RIGHT,VK_UP,VK_DOWN};
 static int pad[6]={VK_NUMPAD7,VK_NUMPAD1,VK_NUMPAD4,VK_NUMPAD6,VK_NUMPAD8,VK_NUMPAD2};
 int i;
 if(!(GetAsyncKeyState(VK_CONTROL)&0x8000) || !(GetAsyncKeyState(VK_MENU)&0x8000))return 0;
 for(i=0;i<6;i++)if(GetAsyncKeyState(keys[i])&0x8000)return keys[i];
 for(i=0;i<6;i++)if(GetAsyncKeyState(pad[i])&0x8000)return keys[i];
 return 0;
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
 if(!edgeArmed)return;
 if(p.x<left+EDGE_ZONE && left>0){sx=-EDGE_X;key|=1;}
 else if(p.x>=left+VIEW_W-EDGE_ZONE && left<LOGICAL_W-VIEW_W){sx=EDGE_X;key|=2;}
 if(p.y<top+EDGE_ZONE && top>0){sy=-EDGE_Y;key|=4;}
 else if(p.y>=top+VIEW_H-EDGE_ZONE && top<LOGICAL_H-VIEW_H){sy=EDGE_Y;key|=8;}
 if(!key){edgeKey=0;return;}
 if(key!=edgeKey){edgeKey=key;edgeSince=now;return;}
 if(now-edgeSince<EDGE_DWELL)return;
 if(Pan(left+sx,top+sy,&dx,&dy))CarryPointer(dx,dy);
}
long FAR PASCAL PAN_ENTRY WndProc(HWND w,unsigned m,UINT wp,LONG lp)
{
 int key;DWORD now;HWND a,f;
 if(m==WM_TIMER){
  if(!Query())return 0;
  now=GetTickCount();
  key=ChordKey();
  if(key && (key!=held || now-lastKey>=KEY_REPEAT)){KeyPan(key);lastKey=now;}
  held=key;
  if(key)return 0;
  a=Active();f=GetFocus();
  if(a && a!=lastActive){lastActive=a;lastFocus=f;Reveal(a,0);return 0;}
  if(f && f!=lastFocus){lastFocus=f;Reveal(f,4);return 0;}
  FollowPointer(now);
  return 0;
 }
 if(m==WM_CLOSE){DestroyWindow(w);return 0;}
 if(m==WM_DESTROY){KillTimer(w,1);PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE hi,HANDLE previous,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;HDC dc;int in[1],wide,high,colors,mode;
 (void)cmd;(void)show;
 if(previous)return 0;
 dc=GetDC(NULL);wide=GetDeviceCaps(dc,HORZRES);high=GetDeviceCaps(dc,VERTRES);
 colors=GetDeviceCaps(dc,NUMCOLORS);
 in[0]=0;mode=Escape(dc,ESC_MODE,2,(LPSTR)in,NULL);ReleaseDC(NULL,dc);
 /* Only the CGAPAN driver: 320x200x16 whose escapes answer for this geometry. */
 if(wide!=LOGICAL_W || high!=LOGICAL_H || colors!=16 || mode<=0 || !Query())return 0;
 /* One owner: no other panning client may run beside this one. */
 if(FindWindow("XTPan",0) || FindWindow("XYOverviewControl",0) || FindWindow("CGASlide",0))return 0;
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=hi;
 wc.hIcon=0;wc.hCursor=0;wc.hbrBackground=0;wc.lpszMenuName=0;wc.lpszClassName="CGAPan";
 if(!RegisterClass(&wc))return 1;
 mainWindow=CreateWindow("CGAPan","CGA viewport",WS_POPUP,0,0,0,0,0,0,hi,0);
 if(!mainWindow || !SetTimer(mainWindow,1,100,0))return 1;
 GetCursorPos(&lastPoint);
 while(GetMessage(&msg,0,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
