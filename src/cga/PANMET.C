#include <windows.h>
/* Private CGAPAN probe: developer instrumentation, never a consumer file.
 * One full-screen window on the 320x200 desktop. Space runs the next step and
 * logs "STEP n DONE"; the controller then captures VRAM. Escapes 5860h and
 * 5861h belong to the CGAPAN driver. */
#define ESC_XY 0x5860
#define ESC_MODE 0x5861
static HWND win;
static int step,focused;
static char line[256];
static COLORREF colors[16]={RGB(0,0,0),RGB(0,0,128),RGB(0,128,0),RGB(0,128,128),
 RGB(128,0,0),RGB(128,0,128),RGB(128,128,0),RGB(128,128,128),
 RGB(64,64,64),RGB(0,0,255),RGB(0,255,0),RGB(0,255,255),
 RGB(255,0,0),RGB(255,0,255),RGB(255,255,0),RGB(255,255,255)};
static void Log(LPSTR s)
{
 OFSTRUCT of;int f=OpenFile("C:\\PANMET.LOG",&of,OF_WRITE);
 if(f==-1)f=OpenFile("C:\\PANMET.LOG",&of,OF_CREATE|OF_WRITE);
 if(f==-1)return;
 _llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);
}
static int Esc(int code,int count,int FAR *in,int FAR *out)
{
 HDC dc=GetDC(win);int r=Escape(dc,code,count,(LPSTR)in,(LPSTR)out);
 ReleaseDC(win,dc);return r;
}
static int Pan(int x,int y)
{
 int in[2],out[6],r;
 in[0]=x;in[1]=y;
 r=Esc(ESC_XY,4,in,out);
 wsprintf(line,"PAN req=%d,%d ret=%d now=%d,%d view=%dx%d logical=%dx%d\r\n",x,y,r,out[0],out[1],out[2],out[3],out[4],out[5]);Log(line);
 return r;
}
static void Caps(void)
{
 HDC dc=GetDC(win);int in[2],out[6],code,r;
 wsprintf(line,"CAPS horz=%d vert=%d colors=%d bits=%d planes=%d dpi=%d,%d aspect=%d,%d size=%d,%d\r\n",
  GetDeviceCaps(dc,HORZRES),GetDeviceCaps(dc,VERTRES),GetDeviceCaps(dc,NUMCOLORS),GetDeviceCaps(dc,BITSPIXEL),
  GetDeviceCaps(dc,PLANES),GetDeviceCaps(dc,LOGPIXELSX),GetDeviceCaps(dc,LOGPIXELSY),
  GetDeviceCaps(dc,ASPECTX),GetDeviceCaps(dc,ASPECTY),GetDeviceCaps(dc,HORZSIZE),GetDeviceCaps(dc,VERTSIZE));Log(line);
 ReleaseDC(win,dc);
 wsprintf(line,"METRICS screen=%dx%d free=%08lx\r\n",GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),GetFreeSpace(0));Log(line);
 for(code=ESC_XY;code<=ESC_MODE;code++){
  in[0]=code;r=Esc(QUERYESCSUPPORT,2,in,NULL);
  wsprintf(line,"SUPPORT %04x=%d\r\n",code,r);Log(line);
 }
 in[0]=0;r=Esc(ESC_MODE,2,in,NULL);wsprintf(line,"MODE 0 ret=%d\r\n",r);Log(line);
 in[0]=1;r=Esc(ESC_MODE,2,in,NULL);wsprintf(line,"MODE 1 ret=%d\r\n",r);Log(line);
 in[0]=-1;in[1]=0;r=Esc(ESC_XY,4,in,out);
 wsprintf(line,"QUERY ret=%d now=%d,%d view=%dx%d logical=%dx%d\r\n",r,out[0],out[1],out[2],out[3],out[4],out[5]);Log(line);
}
/* 8x5 tiles of 40x40: every logical position has a unique tile and label. */
static void PaintPattern(HWND w)
{
 PAINTSTRUCT ps;HDC dc;HBRUSH brush;RECT r;int tx,ty,c;char label[8];
 dc=BeginPaint(w,&ps);SetBkMode(dc,TRANSPARENT);
 for(ty=0;ty<5;ty++)for(tx=0;tx<8;tx++){
  c=(tx+ty*3+1)&15;if(!c)c=15;
  SetRect(&r,tx*40,ty*40,tx*40+40,ty*40+40);
  brush=CreateSolidBrush(colors[c]);FillRect(dc,&r,brush);DeleteObject(brush);
  SetTextColor(dc,(c==15||c==14||c==11||c==10||c==7)?colors[0]:colors[15]);
  wsprintf(label,"%d%d",ty,tx);TextOut(dc,tx*40+3,ty*40+3,label,lstrlen(label));
 }
 SetPixel(dc,0,0,colors[15]);SetPixel(dc,319,0,colors[15]);
 SetPixel(dc,0,199,colors[15]);SetPixel(dc,319,199,colors[15]);
 EndPaint(w,&ps);
}
static void Offscreen(void)
{
 HDC dc=GetDC(win);HBRUSH b;RECT r;int i;
 for(i=0;i<5;i++){
  SetRect(&r,200+i*20,120+(i&1)*30,220+i*20,150+(i&1)*30);
  b=CreateSolidBrush(colors[1+i*3]);FillRect(dc,&r,b);DeleteObject(b);
 }
 SetBkMode(dc,TRANSPARENT);SetTextColor(dc,colors[15]);TextOut(dc,205,125,"OFFSCREEN",9);
 wsprintf(line,"OFFSCREEN pixel(210,135)=%08lx\r\n",GetPixel(dc,210,135));Log(line);
 ReleaseDC(win,dc);
}
static void Crossing(void)
{
 HDC dc=GetDC(win);HBRUSH b;RECT r;
 /* Source straddles x=160; destination overlaps the source. */
 BitBlt(dc,140,30,80,40,dc,100,30,SRCCOPY);
 SetRect(&r,130,80,190,130);b=CreateSolidBrush(colors[12]);FillRect(dc,&r,b);DeleteObject(b);
 SetBkMode(dc,TRANSPARENT);SetTextColor(dc,colors[15]);TextOut(dc,140,100,"EDGE",4);
 wsprintf(line,"CROSS pixel(150,90)=%08lx pixel(170,90)=%08lx\r\n",GetPixel(dc,150,90),GetPixel(dc,170,90));Log(line);
 ReleaseDC(win,dc);
}
static void Timing(void)
{
 DWORD begin=GetTickCount(),end;int i,home[2],far_corner[2];
 home[0]=0;home[1]=0;far_corner[0]=160;far_corner[1]=100;
 for(i=0;i<20;i++)Esc(ESC_XY,4,(i&1)?home:far_corner,NULL);
 end=GetTickCount();
 wsprintf(line,"TIMING 20 full pans ms=%lu\r\n",end-begin);Log(line);
}
static void CursorAt(int x,int y)
{
 POINT p;HWND at;
 SetCursorPos(x,y);GetCursorPos(&p);at=WindowFromPoint(p);
 wsprintf(line,"CURSOR set=%d,%d get=%d,%d window=%s\r\n",x,y,p.x,p.y,(at==win)?(LPSTR)"probe":(LPSTR)"other");Log(line);
}
static void Run(void)
{
 switch(step){
 case 1:Pan(160,0);break;
 case 2:Pan(0,100);break;
 case 3:Pan(160,100);break;
 case 4:Pan(80,50);break;
 case 5:Pan(999,999);break;
 case 6:Pan(13,7);break;
 case 7:Pan(0,0);break;
 case 8:Offscreen();break;
 case 9:Pan(160,100);break;
 case 10:Pan(0,0);Crossing();break;
 case 11:Pan(160,0);break;
 case 12:Timing();Pan(0,0);break;
 case 13:ShowCursor(TRUE);CursorAt(10,10);break;
 case 14:CursorAt(300,10);break;
 case 15:Pan(160,0);break;
 case 16:ShowCursor(FALSE);Log("PANMET EXIT\r\n");DestroyWindow(win);return;
 }
 wsprintf(line,"STEP %d DONE free=%08lx\r\n",step,GetFreeSpace(0));Log(line);
}
long FAR PASCAL WndProc(HWND w,WORD m,WORD wp,LONG lp)
{
 switch(m){
 case WM_PAINT:PaintPattern(w);return 0L;
 case WM_CHAR:if(wp==' '){step++;Run();}return 0L;
 case WM_TIMER:
  /* The shell starts after load= programs and takes the activation. */
  if(GetActiveWindow()!=w)SetActiveWindow(w);
  if(GetFocus()!=w)SetFocus(w);
  if(!focused && GetActiveWindow()==w && GetFocus()==w){focused=1;Log("FOCUS held\r\n");}
  return 0L;
 case WM_DESTROY:PostQuitMessage(0);return 0L;
 }
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE inst,HANDLE prev,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;
 if(!prev){
  wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;
  wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);
  wc.hbrBackground=GetStockObject(BLACK_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="PanMet";
  if(!RegisterClass(&wc))return 1;
 }
 win=CreateWindow("PanMet","PANMET",WS_POPUP|WS_VISIBLE,0,0,320,200,NULL,NULL,inst,NULL);
 if(!win)return 1;
 ShowCursor(FALSE);
 ShowWindow(win,SW_SHOW);UpdateWindow(win);SetFocus(win);SetTimer(win,1,500,NULL);
 Log("PANMET START\r\n");Caps();Log("STEP 0 DONE\r\n");
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
