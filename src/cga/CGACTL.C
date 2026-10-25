/* CGA100 window access. No rendering, video ports, hooks or geometry switch.
 * Ctrl+Alt+arrows slide the foreground window by five pixels; Home restores
 * its top/left, End exposes its bottom/right. Only explicit chords act.
 * Direct visible child bounds repair a fixed window initially capped by USER
 * (the stock Control Panel icon grid is wider than its capped client).
 */
#define WINVER 0x0300
#include <windows.h>
static HWND mainWindow,target;
static HINSTANCE instance;
static DWORD lastMove;
static int held;
static int Clamp(int n,int low,int high)
{return n<low?low:n>high?high:n;}
BOOL FAR PASCAL __export Pick(HWND w,LPARAM unused)
{
 LONG style;char cls[32],title[2];
 if(w==mainWindow || !IsWindowVisible(w) || !IsWindowEnabled(w) || IsIconic(w))return TRUE;
 style=GetWindowLong(w,GWL_STYLE);
 if((style&WS_CHILD) || (style&WS_CAPTION)!=WS_CAPTION)return TRUE;
 if(!GetWindowText(w,title,sizeof(title)))return TRUE;
 GetClassName(w,cls,sizeof(cls));
 if(!lstrcmp(cls,"Progman") || !lstrcmp(cls,"#32768"))return TRUE;
 target=w;return FALSE;
}
static void FitChildren(HWND w)
{
 HWND child;RECT r,c,b;POINT origin;int needX,needY;
 if(GetWindowLong(w,GWL_STYLE)&WS_THICKFRAME)return;
 GetWindowRect(w,&r);GetClientRect(w,&c);origin.x=origin.y=0;ClientToScreen(w,&origin);
 needX=c.right;needY=c.bottom;
 for(child=GetWindow(w,GW_CHILD);child;child=GetWindow(child,GW_HWNDNEXT)){
  if(!IsWindowVisible(child) || !(GetWindowLong(child,GWL_STYLE)&WS_CHILD))continue;
  GetWindowRect(child,&b);
  if(b.right-origin.x>needX)needX=b.right-origin.x;
  if(b.bottom-origin.y>needY)needY=b.bottom-origin.y;
 }
 if(needX>1024 || needY>1024)return;
 if(needX>c.right || needY>c.bottom)
  SetWindowPos(w,0,0,0,r.right-r.left+needX-c.right,r.bottom-r.top+needY-c.bottom,
               SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);
}
static void Slide(int key)
{
 FARPROC callback;RECT r;int x,y,w,h,loX,hiX,loY,hiY;
 target=0;callback=MakeProcInstance((FARPROC)Pick,instance);
 if(!callback)return;
 EnumWindows((WNDENUMPROC)callback,0L);FreeProcInstance(callback);
 if(!target)return;
 FitChildren(target);GetWindowRect(target,&r);
 w=r.right-r.left;h=r.bottom-r.top;x=r.left;y=r.top;
 loX=160-w;hiX=loX;if(loX>0)loX=0;else hiX=0;
 loY=100-h;hiY=loY;if(loY>0)loY=0;else hiY=0;
 if(key==VK_HOME){x=0;y=0;}
 else if(key==VK_END){x=loX;y=loY;}
 else if(key==VK_LEFT)x-=5;
 else if(key==VK_RIGHT)x+=5;
 else if(key==VK_UP)y-=5;
 else if(key==VK_DOWN)y+=5;
 x=Clamp(x,loX,hiX);y=Clamp(y,loY,hiY);
 SetWindowPos(target,0,x,y,0,0,SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE);
}
long FAR PASCAL __export WndProc(HWND w,unsigned m,WORD wp,LONG lp)
{
 int keys[6],i,key=0;DWORD now;
 if(m==WM_TIMER){
  if(!(GetAsyncKeyState(VK_CONTROL)&0x8000) || !(GetAsyncKeyState(VK_MENU)&0x8000)){
   held=0;return 0;
  }
  keys[0]=VK_HOME;keys[1]=VK_END;keys[2]=VK_LEFT;keys[3]=VK_RIGHT;keys[4]=VK_UP;keys[5]=VK_DOWN;
  for(i=0;i<6;i++)if(GetAsyncKeyState(keys[i])&0x8000){key=keys[i];break;}
  now=GetTickCount();
  if(key && (key!=held || now-lastMove>=200L)){Slide(key);lastMove=now;}
  held=key;return 0;
 }
 if(m==WM_DESTROY){KillTimer(w,1);PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE hi,HANDLE previous,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;HDC dc;int ok;
 if(previous)return 0;
 dc=GetDC(NULL);ok=GetDeviceCaps(dc,HORZRES)==160 && GetDeviceCaps(dc,VERTRES)==100 && GetDeviceCaps(dc,NUMCOLORS)==16;ReleaseDC(NULL,dc);
 if(!ok)return 0;
 instance=hi;wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=hi;
 wc.hIcon=0;wc.hCursor=0;wc.hbrBackground=0;wc.lpszMenuName=0;wc.lpszClassName="CGASlide";
 if(!RegisterClass(&wc))return 1;
 mainWindow=CreateWindow("CGASlide","CGA window access",WS_POPUP,0,0,0,0,0,0,hi,0);
 if(!mainWindow || !SetTimer(mainWindow,1,100,0))return 1;
 while(GetMessage(&msg,0,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
