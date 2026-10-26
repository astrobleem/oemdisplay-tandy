/* CGA100 access client of shared WDESK/WTPLACE; no second root tracker,
 * enumerator, saved-position implementation, bitmap or video-port owner.
 * Ctrl+Alt+arrows pan window positions; Home recovers, End exposes the active
 * frame's bottom/right. The unique CGA operation slides an existing visible
 * child group when its fixed client clips it (stock Control Panel icons).
 */
#define WINVER 0x0300
#include <windows.h>
#include "WDWIN.H"
#ifdef __WATCOMC__
#define CGA_ENTRY __export
#else
#define CGA_ENTRY
#endif
static HWND mainWindow;
static DWORD lastMove;
static int held;
static int Clamp(int n,int low,int high)
{return n<low?low:n>high?high:n;}
static int Limit(long n,int high)
{return n<0?0:n>high?high:(int)n;}
static HWND Active(void)
{
 HWND w=GetActiveWindow();char cls[32];LONG style;
 if(!w || w==mainWindow || !IsWindowVisible(w) || !IsWindowEnabled(w) || IsIconic(w))return 0;
 style=GetWindowLong(w,GWL_STYLE);
 if((style&WS_CHILD) || (style&WS_CAPTION)!=WS_CAPTION)return 0;
 cls[0]=0;if(!GetClassName(w,cls,sizeof(cls)))return 0;
 return !lstrcmp(cls,"Progman") || !lstrcmp(cls,"#32768") ? 0 : w;
}
static void SlideChildren(HWND w,int key)
{
 HWND child;RECT c,b;POINT origin;int first=1,minX=0,minY=0,maxX=0,maxY=0;
 int dx=0,dy=0,lo,hi,t;
 GetClientRect(w,&c);origin.x=origin.y=0;ClientToScreen(w,&origin);
 for(child=GetWindow(w,GW_CHILD);child;child=GetWindow(child,GW_HWNDNEXT)){
  if(!IsWindowVisible(child) || !(GetWindowLong(child,GWL_STYLE)&WS_CHILD))continue;
  GetWindowRect(child,&b);OffsetRect(&b,-origin.x,-origin.y);
  if(first){minX=b.left;maxX=b.right;minY=b.top;maxY=b.bottom;first=0;}
  else{if(b.left<minX)minX=b.left;if(b.right>maxX)maxX=b.right;
       if(b.top<minY)minY=b.top;if(b.bottom>maxY)maxY=b.bottom;}
 }
 if(first || minX < -1024 || minY < -1024 || maxX > 2048 || maxY > 2048 ||
    maxX-minX>1024 || maxY-minY>1024)return;
 if(minX<0 || maxX>c.right){
  lo=-minX;hi=c.right-maxX;if(lo>hi){t=lo;lo=hi;hi=t;}
  if(key==VK_HOME)dx=-minX;else if(key==VK_END)dx=c.right-maxX;
  else if(key==VK_LEFT)dx=-5;else if(key==VK_RIGHT)dx=5;
  dx=Clamp(dx,lo,hi);
 }
 if(minY<0 || maxY>c.bottom){
  lo=-minY;hi=c.bottom-maxY;if(lo>hi){t=lo;lo=hi;hi=t;}
  if(key==VK_HOME)dy=-minY;else if(key==VK_END)dy=c.bottom-maxY;
  else if(key==VK_UP)dy=-5;else if(key==VK_DOWN)dy=5;
  dy=Clamp(dy,lo,hi);
 }
 if(!dx && !dy)return;
 for(child=GetWindow(w,GW_CHILD);child;child=GetWindow(child,GW_HWNDNEXT)){
  if(!IsWindowVisible(child) || !(GetWindowLong(child,GWL_STYLE)&WS_CHILD))continue;
  GetWindowRect(child,&b);
  SetWindowPos(child,0,b.left-origin.x+dx,b.top-origin.y+dy,0,0,
               SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_NOREDRAW);
  InvalidateRect(child,0,TRUE);
 }
 InvalidateRect(w,0,TRUE);UpdateWindow(w);
}
static void Slide(int key)
{
 HWND w=Active();RECT r;int x,y,childKey=key;
 /* Window workspace movement and fixed-client movement share one chord. */
 if(key==VK_LEFT)childKey=VK_RIGHT;else if(key==VK_RIGHT)childKey=VK_LEFT;
 else if(key==VK_UP)childKey=VK_DOWN;else if(key==VK_DOWN)childKey=VK_UP;
 if(w)SlideChildren(w,childKey);
 if(key==VK_HOME){(void)WDWinHome();return;}
 if(key==VK_END){
  if(!w)return;
  GetWindowRect(w,&r);WDWinViewport(&x,&y);
  (void)WDWinPan(Limit((long)x+r.right-160,160),Limit((long)y+r.bottom-100,100));return;
 }
 if(key==VK_LEFT)(void)WDWinPanBy(-5,0);
 else if(key==VK_RIGHT)(void)WDWinPanBy(5,0);
 else if(key==VK_UP)(void)WDWinPanBy(0,-5);
 else if(key==VK_DOWN)(void)WDWinPanBy(0,5);
}
long FAR PASCAL CGA_ENTRY WndProc(HWND w,unsigned m,UINT wp,LONG lp)
{
 int keys[6],i,key=0;DWORD now;
 if(m==WM_TIMER){
  if(!(GetAsyncKeyState(VK_CONTROL)&0x8000) || !(GetAsyncKeyState(VK_MENU)&0x8000)){
   held=0;return 0;
  }
  keys[0]=VK_HOME;keys[1]=VK_END;keys[2]=VK_LEFT;keys[3]=VK_RIGHT;keys[4]=VK_UP;keys[5]=VK_DOWN;
  for(i=0;i<6;i++)if(GetAsyncKeyState(keys[i])&0x8000){key=keys[i];break;}
  if(!key){
   if(GetAsyncKeyState(VK_NUMPAD7)&0x8000)key=VK_HOME;
   else if(GetAsyncKeyState(VK_NUMPAD1)&0x8000)key=VK_END;
   else if(GetAsyncKeyState(VK_NUMPAD4)&0x8000)key=VK_LEFT;
   else if(GetAsyncKeyState(VK_NUMPAD6)&0x8000)key=VK_RIGHT;
   else if(GetAsyncKeyState(VK_NUMPAD8)&0x8000)key=VK_UP;
   else if(GetAsyncKeyState(VK_NUMPAD2)&0x8000)key=VK_DOWN;
  }
  now=GetTickCount();
  if(key && (key!=held || now-lastMove>=200L)){Slide(key);lastMove=now;}
  held=key;return 0;
 }
 if(m==WM_QUERYENDSESSION)return WDWinPrepareShutdown()>=0;
 if(m==WM_ENDSESSION){if(wp)(void)WDWinShutdown();return 0;}
 if(m==WM_CLOSE){if(WDWinShutdown()<0)return 0;DestroyWindow(w);return 0;}
 if(m==WM_DESTROY){(void)WDWinShutdown();KillTimer(w,1);PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE hi,HANDLE previous,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;HDC dc;int wide,high,colors,index;COLORREF black;
 (void)cmd;(void)show;
 if(previous)return 0;
 dc=GetDC(NULL);wide=GetDeviceCaps(dc,HORZRES);high=GetDeviceCaps(dc,VERTRES);
 colors=GetDeviceCaps(dc,NUMCOLORS);ReleaseDC(NULL,dc);
 /* Gray128 maps to the same white as the button face in reduced palettes.
  * Fix only the session's disabled-text color; no palette/renderer change
  * and no resident window or placement service in these normal modes. */
 if(high==200 && ((wide==320 && colors==4) || (wide==640 && colors==2))){
  index=COLOR_GRAYTEXT;black=RGB(0,0,0);SetSysColors(1,&index,&black);return 0;
 }
 if(wide!=160 || high!=100 || colors!=16)return 0;
 /* Existing panning owners never run concurrently with this fixed-mode client. */
 if(FindWindow("XTPan",0) || FindWindow("XYOverviewControl",0))return 0;
 if(WDWinInitView(320,200,160,100)<0)return 1;
 (void)WDWinExclude("Progman");
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=hi;
 wc.hIcon=0;wc.hCursor=0;wc.hbrBackground=0;wc.lpszMenuName=0;wc.lpszClassName="CGASlide";
 if(!RegisterClass(&wc)){(void)WDWinShutdown();return 1;}
 mainWindow=CreateWindow("CGASlide","CGA window access",WS_POPUP,0,0,0,0,0,0,hi,0);
 if(!mainWindow || !SetTimer(mainWindow,1,100,0)){(void)WDWinShutdown();return 1;}
 while(GetMessage(&msg,0,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
