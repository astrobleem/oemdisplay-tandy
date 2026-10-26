/* Private focused Windows 3.0 real-mode driver integration probe. */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
typedef int (FAR PASCAL *ROWS)(LPSTR,unsigned,unsigned);
typedef int (FAR PASCAL *STATS)(unsigned FAR *);
static ROWS rowsProc;
static STATS statsProc;
static HFILE logFile;
static char buffer[3840],line[256];
static HWND mainWnd;
static HCURSOR cursor,active;
static int pan[6],failures;
static unsigned stats[8];
static void Log(LPSTR s) {
 _lwrite(logFile,s,lstrlen(s));_lclose(logFile);
 logFile=_lopen("C:\\PANQA.LOG",OF_WRITE);_llseek(logFile,0L,2);
}
static void Check(LPSTR s,int ok) {
 wsprintf(line,"CHECK %s=%d\r\n",s,ok!=0);Log(line);if(!ok)failures++;
}
static void Pump(DWORD ms) {
 DWORD start;MSG msg;start=GetTickCount();
 while((DWORD)(GetTickCount()-start)<ms)
  while(PeekMessage(&msg,0,0,0,PM_REMOVE)) {
   TranslateMessage(&msg);DispatchMessage(&msg);
  }
}
static int RawPan(int x,int y) {
 HDC dc;int in[2],ok;dc=GetDC(0);in[0]=x;in[1]=y;
 ok=Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)pan)>0;
 ReleaseDC(0,dc);return ok;
}
static void Pan(int x,int y) {
 Check("ESC_XY",RawPan(x,y));
}
static void Mode(int m) {
 HDC dc;dc=GetDC(0);Check("ESC_MODE",Escape(dc,0x5861,2,(LPSTR)&m,0)>0);ReleaseDC(0,dc);
}
static void Memory(LPSTR label) {
 wsprintf(line,"MEM %s free=%lu largest=%lu\r\n",label,GetFreeSpace(0),GlobalCompact(0L));Log(line);
}
static void Pattern(HDC dc) {
 HBRUSH b;HPEN p,old;RECT r;
 PatBlt(dc,0,0,640,256,BLACKNESS);
 b=CreateSolidBrush(RGB(170,0,0));r.left=80;r.top=32;r.right=240;r.bottom=224;
 FillRect(dc,&r,b);DeleteObject(b);
 b=CreateSolidBrush(RGB(0,170,0));r.left=400;r.top=180;r.right=600;r.bottom=252;
 FillRect(dc,&r,b);DeleteObject(b);
 p=CreatePen(PS_SOLID,1,RGB(255,255,255));old=SelectObject(dc,p);
 MoveTo(dc,0,0);LineTo(dc,639,255);MoveTo(dc,0,255);LineTo(dc,639,0);
 SelectObject(dc,old);DeleteObject(p);
 TextOut(dc,4,190,"BAND 199/200",12);TextOut(dc,340,234,"LOWER RIGHT",11);
}
static void Shadow(int id) {
 HFILE f;char name[24];unsigned first,count,n;int ok;
 wsprintf(name,"C:\\S%03d.BIN",id);f=_lcreat(name,0);ok=f!=HFILE_ERROR;
 if(ok) {
  for(first=0;first<256;first+=12) {
   count=256-first;if(count>12)count=12;
   n=rowsProc(buffer,first,count);
   if(n!=count*320 || _lwrite(f,buffer,n)!=n)ok=0;
  }
  _lclose(f);
 }
 Check("SHADOW_STREAM",ok);
}
static void Frame(int id,int visible,int shadowId) {
 HFILE f;char name[24];unsigned off;char FAR *video;POINT point;
 active=visible?cursor:0;SetCursor(active);Pump(70);SetCursor(active);
 GetCursorPos(&point);Pan(-1,0);statsProc(stats);
 wsprintf(name,"C:\\V%03d.BIN",id);f=_lcreat(name,0);
 Check("FRAME_FILE",f!=HFILE_ERROR);video=(char FAR *)MAKELONG(0,0xb800);
 if(f!=HFILE_ERROR) {
  for(off=0;off<32768U;off+=8192U)Check("FRAME_WRITE",_lwrite(f,video+off,8192)==8192);
  _lclose(f);
 }
 wsprintf(line,"FRAME id=%d shadow=%d x=%d y=%d head=%u enabled=%u cursor=%d cx=%d cy=%d\r\n",
  id,shadowId,pan[0],pan[1],stats[2],stats[0],visible,point.x,point.y);Log(line);
}
long FAR PASCAL __export Wnd(HWND w,UINT m,WPARAM a,LPARAM b) {
 PAINTSTRUCT ps;HDC dc;
 if(m==WM_SETCURSOR){SetCursor(active);return 1;}
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);Pattern(dc);EndPaint(w,&ps);return 0;}
 return DefWindowProc(w,m,a,b);
}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR command,int show) {
 HINSTANCE display;WNDCLASS wc;FARPROC thunk;HDC dc;HBRUSH brush;RECT r;
 unsigned char am[64],xm[64];int i,x,y,id,ok;DWORD a,b;
 static int targets[11][2]={{24,0},{0,0},{0,4},{0,0},{16,8},{16,24},
  {304,48},{320,56},{304,48},{999,999},{0,0}};
 (void)previous;(void)command;(void)show;
 logFile=_lcreat("C:\\PANQA.LOG",0);if(logFile==HFILE_ERROR)return 1;
 Memory("ENTRY");Check("REAL_MODE",(GetWinFlags()&WF_STANDARD)==0);
 Check("GEOMETRY",GetSystemMetrics(0)==640 && GetSystemMetrics(1)==256);
 display=GetModuleHandle("DISPLAY");
 rowsProc=(ROWS)GetProcAddress(display,(LPSTR)108L);
 statsProc=(STATS)GetProcAddress(display,(LPSTR)106L);
 Check("EXPORTS",rowsProc!=0 && statsProc!=0);if(!rowsProc || !statsProc)goto done;
 memset(&wc,0,sizeof(wc));thunk=MakeProcInstance((FARPROC)Wnd,instance);
 wc.lpfnWndProc=(WNDPROC)thunk;wc.hInstance=instance;wc.lpszClassName="StripQA";
 RegisterClass(&wc);memset(am,255,sizeof(am));memset(xm,0,sizeof(xm));
 for(i=0;i<8;i++){am[i*4]=0;xm[i*4]=(unsigned char)(0x80>>i);}
 cursor=CreateCursor(instance,0,0,32,16,am,xm);Check("CURSOR_ALLOC",cursor!=0);
 mainWnd=CreateWindow("StripQA","PRIVATE Tandy strip qualification",WS_POPUP,
  0,0,640,256,0,0,instance,0);Check("WINDOW",mainWnd!=0);
 ShowWindow(mainWnd,SW_SHOW);UpdateWindow(mainWnd);SetCursor(0);Pump(100);
 Pan(0,0);Mode(1);Memory("WARM");Shadow(0);Frame(0,0,0);
 for(i=0;i<11;i++) {
  x=targets[i][0];y=targets[i][1];if(x>320)x=320;if(y>56)y=56;
  SetCursorPos(x+160,y+80);active=cursor;SetCursor(active);Pump(70);
  a=GetTickCount();ok=RawPan(targets[i][0],targets[i][1]);b=GetTickCount();
  Check("ESC_XY",ok);
  statsProc(stats);
  wsprintf(line,"MOVE id=%d x=%d y=%d ms=%lu bytes=%u reason=%u hw=%u sw=%u\r\n",
   i,pan[0],pan[1],b-a,stats[7],stats[3],stats[4],stats[5]);Log(line);
  Check("PAN_POSITION",pan[0]==x && pan[1]==y);id=1+i*3;
  Frame(id,1,0);SetCursorPos(x+184,y+96);Frame(id+1,1,0);Frame(id+2,0,0);
 }
 /* Change the saved-under pixels while the real driver cursor is visible. */
 SetCursorPos(50,70);active=cursor;SetCursor(active);Pump(70);
 dc=GetDC(mainWnd);brush=CreateSolidBrush(RGB(0,0,255));
 r.left=32;r.top=44;r.right=108;r.bottom=92;FillRect(dc,&r,brush);
 DeleteObject(brush);ReleaseDC(mainWnd,dc);Shadow(1);Frame(40,0,1);
 Pan(16,8);Frame(41,1,1);Pan(0,0);Frame(42,0,1);
 Memory("AFTER_PANS");
 Mode(2);Pan(0,4);statsProc(stats);
 Check("FAULT_RECOVERY",stats[0]==0 && stats[3]==4 && stats[7]==32000);
 Frame(43,0,1);Mode(0);Pan(0,0);
 SetCursor(0);DestroyWindow(mainWnd);DestroyCursor(cursor);
 UnregisterClass("StripQA",instance);FreeProcInstance(thunk);Memory("CLOSED");
done:
 wsprintf(line,"END FAILURES=%d\r\n",failures);Log(line);_lclose(logFile);
 ExitWindows(0,0);return 0;
}
