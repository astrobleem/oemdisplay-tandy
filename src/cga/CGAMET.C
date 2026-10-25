#include <windows.h>
static HWND hidden,last;
static int ticks;
static char line[256];
static HWND pattern;
static HCURSOR testcursor,oldcursor;
static int cursorphase;
static BYTE cmask[128],xmask[128];
static void Log(LPSTR s)
{
 OFSTRUCT of;int f=OpenFile("C:\\CGAMET.LOG",&of,OF_WRITE);
 if(f==-1)f=OpenFile("C:\\CGAMET.LOG",&of,OF_CREATE|OF_WRITE);
 if(f==-1)return;
 _llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);
}
static void Font(HDC dc,int stock,LPSTR name)
{
 HFONT old;TEXTMETRIC tm;
 old=SelectObject(dc,GetStockObject(stock));GetTextMetrics(dc,&tm);
 wsprintf(line,"FONT %s height=%d ascent=%d ave=%d max=%d weight=%d\r\n",name,tm.tmHeight,tm.tmAscent,tm.tmAveCharWidth,tm.tmMaxCharWidth,tm.tmWeight);Log(line);
 SelectObject(dc,old);
}
static void FontProbe(HDC dc)
{
 HFONT f,old;TEXTMETRIC tm;char face[40],value[100];int h,bold,n;
 GetProfileString("fonts","Helv 3x5 (CGA100)","MISSING",value,sizeof(value));
 wsprintf(line,"PROFILE CG1HELV=%s\r\n",(LPSTR)value);Log(line);
 for(n=0;n<2;n++){
  if(n){
   wsprintf(line,"ADDFONT Helv=%d Courier=%d\r\n",AddFontResource("C:\\WINDOWS\\SYSTEM\\CG1HELV.FON"),AddFontResource("C:\\WINDOWS\\SYSTEM\\CG1COUR.FON"));Log(line);
  }
  for(h=4;h<=8;h++)for(bold=0;bold<2;bold++){
   f=CreateFont(h,0,0,0,bold?700:400,0,0,0,ANSI_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,DEFAULT_QUALITY,VARIABLE_PITCH|FF_SWISS,"Helv");
   old=SelectObject(dc,f);GetTextMetrics(dc,&tm);GetTextFace(dc,sizeof(face),face);
   wsprintf(line,"MAP added=%d request=%d weight=%d face=%s height=%d ave=%d pitch=%d\r\n",n,h,bold?700:400,(LPSTR)face,tm.tmHeight,tm.tmAveCharWidth,tm.tmPitchAndFamily);Log(line);
   SelectObject(dc,old);DeleteObject(f);
  }
 }
}
static COLORREF colors[16]={RGB(0,0,0),RGB(0,0,128),RGB(0,128,0),RGB(0,128,128),
 RGB(128,0,0),RGB(128,0,128),RGB(128,128,0),RGB(128,128,128),
 RGB(64,64,64),RGB(0,0,255),RGB(0,255,0),RGB(0,255,255),
 RGB(255,0,0),RGB(255,0,255),RGB(255,255,0),RGB(255,255,255)};
static void PaintPattern(HWND w)
{
 PAINTSTRUCT ps;HDC dc,mem;HBITMAP bmp,old;HBRUSH brush;RECT r;
 int x,y,c,wide=GetSystemMetrics(SM_CXSCREEN),high=GetSystemMetrics(SM_CYSCREEN);
 DWORD begin=GetTickCount(),elapsed;COLORREF got[16],lastpixel;
 dc=BeginPaint(w,&ps);
 for(c=0;c<16;c++){
  SetRect(&r,c*wide/16,0,(c+1)*wide/16,high);
  brush=CreateSolidBrush(colors[c]);FillRect(dc,&r,brush);DeleteObject(brush);
  got[c]=GetPixel(dc,(2*c+1)*wide/32,high/2);
 }
 mem=CreateCompatibleDC(dc);bmp=CreateCompatibleBitmap(dc,32,16);old=SelectObject(mem,bmp);
 for(y=0;y<4;y++)for(x=0;x<16;x++)SetPixel(mem,x,y,colors[(x+y)&15]);
 BitBlt(dc,1,1,16,4,mem,0,0,SRCCOPY);
 for(y=0;y<16;y++)for(x=0;x<16;x++){
  SetPixel(mem,2*x,y,colors[y]);SetPixel(mem,2*x+1,y,colors[x]);
 }
 BitBlt(dc,65,30,32,16,mem,0,0,SRCCOPY);
 SelectObject(mem,old);DeleteObject(bmp);DeleteDC(mem);
 SetPixel(dc,wide-1,high-1,colors[4]);
 lastpixel=GetPixel(dc,wide-1,high-1);EndPaint(w,&ps);elapsed=GetTickCount()-begin;
 for(c=0;c<16;c++){wsprintf(line,"BAR %d RGB=%08lx\r\n",c,got[c]);Log(line);}
 wsprintf(line,"DRAW width=%d height=%d last=%08lx ms=%lu\r\n",wide,high,lastpixel,elapsed);Log(line);Log("PATTERN READY\r\n");
}
static void CursorStep(void)
{
 int i,wide=GetSystemMetrics(SM_CXSCREEN),high=GetSystemMetrics(SM_CYSCREEN);
 if(!pattern)return;
 if(!cursorphase){
  for(i=0;i<128;i++){cmask[i]=0xaa;xmask[i]=0x66;}
  testcursor=CreateCursor(GetWindowWord(hidden,GWW_HINSTANCE),1,1,32,32,(LPSTR)cmask,(LPSTR)xmask);
  wsprintf(line,"CURSOR created=%04x size=32,32 hotspot=1,1\r\n",testcursor);Log(line);
  if(!testcursor){Log("CURSOR FAIL\r\n");return;}
  oldcursor=SetCursor(testcursor);SetCursorPos(2,2);ShowCursor(TRUE);
 }else if(cursorphase==1)SetCursorPos(wide-1,high-1);
 else if(cursorphase==2)SetCursorPos(0,high-1);
 else if(cursorphase==3)SetCursorPos(wide-1,0);
 else if(cursorphase==4){ShowCursor(FALSE);SetCursor(oldcursor);DestroyCursor(testcursor);}
 wsprintf(line,"CURSOR phase=%d\r\n",++cursorphase);Log(line);
}
static void Tree(HWND w,int depth)
{
 char cls[40],title[70];RECT r;HWND child;int n=0;HFONT f;LOGFONT lf;
 for(;w && n++<60;w=GetWindow(w,GW_HWNDNEXT)){
  if(!IsWindowVisible(w)||w==hidden)continue;
  GetClassName(w,cls,sizeof(cls));GetWindowText(w,title,sizeof(title));GetWindowRect(w,&r);
  wsprintf(line,"W %d %04x %s [%d,%d,%d,%d] %s\r\n",depth,w,(LPSTR)cls,r.left,r.top,r.right,r.bottom,(LPSTR)title);Log(line);
  if(depth<2){
   f=(HFONT)SendMessage(w,WM_GETFONT,0,0L);
   if(f&&GetObject(f,sizeof(lf),(LPSTR)&lf)){
    wsprintf(line,"LF %04x h=%d w=%d weight=%d face=%s\r\n",w,lf.lfHeight,lf.lfWidth,lf.lfWeight,(LPSTR)lf.lfFaceName);Log(line);
   }
  }
  child=GetWindow(w,GW_CHILD);if(child&&depth<4)Tree(child,depth+1);
 }
}
long FAR PASCAL WndProc(HWND w,unsigned m,WORD wp,LONG lp)
{
 HWND active;
 if(m==WM_PAINT&&w==pattern){PaintPattern(w);return 0;}
 if(m==WM_TIMER){
  active=GetActiveWindow();
  if(GetAsyncKeyState(VK_F9)&1){
   if(pattern){DestroyWindow(pattern);pattern=NULL;ShowCursor(TRUE);Log("PATTERN CLOSED\r\n");}
   else{ShowCursor(FALSE);cursorphase=0;pattern=CreateWindow("CGAMET","CGA GDI",WS_POPUP|WS_VISIBLE,0,0,GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),NULL,NULL,GetWindowWord(hidden,GWW_HINSTANCE),NULL);UpdateWindow(pattern);}
  }
  if(GetAsyncKeyState(VK_F8)&1)CursorStep();
  if(active!=last||(GetAsyncKeyState(VK_SCROLL)&1)){
   last=active;Log("SNAP\r\n");Tree(GetWindow(GetDesktopWindow(),GW_CHILD),0);
  }
  return 0;
 }
 if(m==WM_DESTROY&&w==hidden){PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE hi,HANDLE prev,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;HDC dc;
 if(prev)return 0;
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=hi;
 wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="CGAMET";
 if(!RegisterClass(&wc))return 1;
 hidden=CreateWindow("CGAMET","CGA metrics",WS_POPUP,0,0,0,0,NULL,NULL,hi,NULL);
 dc=GetDC(NULL);wsprintf(line,"CAPS width=%d height=%d colors=%d dpi=%d,%d caption=%d menu=%d scroll=%d,%d\r\n",GetDeviceCaps(dc,HORZRES),GetDeviceCaps(dc,VERTRES),GetDeviceCaps(dc,NUMCOLORS),GetDeviceCaps(dc,LOGPIXELSX),GetDeviceCaps(dc,LOGPIXELSY),GetSystemMetrics(SM_CYCAPTION),GetSystemMetrics(SM_CYMENU),GetSystemMetrics(SM_CXVSCROLL),GetSystemMetrics(SM_CYHSCROLL));Log(line);
 Font(dc,SYSTEM_FONT,"SYSTEM");Font(dc,SYSTEM_FIXED_FONT,"FIXED");Font(dc,OEM_FIXED_FONT,"OEM");
 Font(dc,ANSI_VAR_FONT,"ANSI_VAR");
 if(cmd[0]=='F')FontProbe(dc);
 ReleaseDC(NULL,dc);
 SetTimer(hidden,1,1000,NULL);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 return msg.wParam;
}
