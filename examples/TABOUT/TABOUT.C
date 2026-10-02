/* About This Tandy: Windows 3.0, 8086, no hardware probes. */
#define WINVER 0x0300
#include <windows.h>
#define SYS 101
#define DISP 102
#define MEM 103
#define REFRESH 104
static HINSTANCE instance;
static HWND buttons[4];
static int page;
static DWORD version,flags,freebytes;
static int width,height,colors,planes,bits;
static char lines[8][24];
static void num(char *s,DWORD v) { char b[12];int n=0,i=0;do{b[n++]=(char)('0'+v%10);v/=10;}while(v);while(n)s[i++]=b[--n];s[i]=0; }
static void value(int line,char *prefix,DWORD v) { char b[12];num(b,v);lstrcpy(lines[line],prefix);lstrcat(lines[line],b); }
static void sample(HWND w) { HDC dc;version=GetVersion();flags=GetWinFlags();freebytes=GetFreeSpace(0);dc=GetDC(w);width=GetDeviceCaps(dc,HORZRES);height=GetDeviceCaps(dc,VERTRES);colors=GetDeviceCaps(dc,NUMCOLORS);planes=GetDeviceCaps(dc,PLANES);bits=GetDeviceCaps(dc,BITSPIXEL);ReleaseDC(w,dc); }
static char *cpu(DWORD f) { if(f&WF_CPU486)return "80486 family";if(f&WF_CPU386)return "80386 family";if(f&WF_CPU286)return "80286 family";if(f&WF_CPU186)return "80186/80188";if(f&WF_CPU086)return "8086/8088";return "Unknown family"; }
static void compose(void) { int i;char b[12];for(i=0;i<8;i++)lines[i][0]=0;
 if(page==0){lstrcpy(lines[0],"About This Tandy");value(1,"Windows ",LOBYTE(LOWORD(version)));lstrcat(lines[1],".");num(b,HIBYTE(LOWORD(version)));if(HIBYTE(LOWORD(version))<10)lstrcat(lines[1],"0");lstrcat(lines[1],b);
 lstrcpy(lines[2],flags&WF_ENHANCED?"386 enhanced mode":flags&WF_PMODE?"Standard mode":"Real mode");lstrcpy(lines[3],"CPU (Windows):");lstrcpy(lines[4],cpu(flags));lstrcpy(lines[5],"Model: unknown");lstrcpy(lines[6],"No hardware probe");}
 if(page==1){lstrcpy(lines[0],"Display (GDI)");value(1,"Width: ",(DWORD)width);value(2,"Height: ",(DWORD)height);if(colors<0)lstrcpy(lines[3],"Colors: >32767");else value(3,"Colors: ",(DWORD)colors);value(4,"DDB planes: ",(DWORD)planes);value(5,"Bits/plane: ",(DWORD)bits);lstrcpy(lines[6],"Colors = NUMCOLORS");}
 if(page==2){lstrcpy(lines[0],"Memory (Windows)");lstrcpy(lines[1],"Free global heap:");value(2,"",freebytes/1024L);lstrcat(lines[2]," KiB");lstrcpy(lines[3],"Available to Win.");lstrcpy(lines[4],"Not installed RAM");lstrcpy(lines[5],"Refresh to update");lstrcpy(lines[6],"1 KiB = 1024 bytes");}}
static void redraw(HWND w) { RECT r;compose();GetClientRect(w,&r);r.top=26;r.bottom=126;InvalidateRect(w,&r,TRUE); }
static int key(HWND w,WPARAM k) { int i;if(k=='S'||k=='D'||k=='M'||k=='R'){SendMessage(w,WM_COMMAND,k=='S'?SYS:k=='D'?DISP:k=='M'?MEM:REFRESH,0L);return 1;}if(k==VK_LEFT||k==VK_RIGHT){page=(page+(k==VK_RIGHT?1:2))%3;redraw(w);return 1;}if(k==VK_TAB){for(i=0;i<4&&GetFocus()!=buttons[i];i++);i=i==4?(GetKeyState(VK_SHIFT)<0?3:0):(i+(GetKeyState(VK_SHIFT)<0?3:1))%4;SetFocus(buttons[i]);return 1;}if(k==VK_ESCAPE){DestroyWindow(w);return 1;}return 0; }
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc;PAINTSTRUCT ps;int i,x;RECT r;
 switch(m){case WM_CREATE:
 for(i=0;i<4;i++){buttons[i]=CreateWindow("BUTTON",i==0?"Sys":i==1?"Disp":i==2?"Mem":"Refresh",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,0,0,40,20,w,(HMENU)(SYS+i),instance,NULL);if(!buttons[i])return -1L;SendMessage(buttons[i],WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);}sample(w);compose();return 0;
 case WM_SIZE:GetClientRect(w,&r);x=(r.right-148)/2;if(x<0)x=0;for(i=0;i<3;i++)MoveWindow(buttons[i],x+i*50,2,48,20,TRUE);MoveWindow(buttons[3],x,130,148,20,TRUE);return 0;
 case WM_COMMAND:if(wp>=SYS&&wp<=MEM)page=wp-SYS;else if(wp==REFRESH)sample(w);else break;redraw(w);return 0;
 case WM_KEYDOWN:if(key(w,wp))return 0;break;
 case WM_PAINT:dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(0,0,0));GetClientRect(w,&r);x=(r.right-148)/2;if(x<0)x=0;for(i=0;i<8;i++)TextOut(dc,x+2,28+i*12,lines[i],lstrlen(lines[i]));TextOut(dc,x+2,154,"S D M R / Esc",13);EndPaint(w,&ps);return 0;
 case WM_DESTROY:PostQuitMessage(0);return 0; }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;instance=inst;
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="TandyAbout";if(!RegisterClass(&wc))return 1;}
 w=CreateWindow("TandyAbout","About Tandy",WS_OVERLAPPEDWINDOW|WS_CLIPCHILDREN,0,0,160,200,NULL,NULL,inst,NULL);if(!w)return 2;ShowWindow(w,SW_SHOWMAXIMIZED);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){if(msg.message==WM_KEYDOWN&&key(w,msg.wParam))continue;TranslateMessage(&msg);DispatchMessage(&msg);}return msg.wParam;
}
