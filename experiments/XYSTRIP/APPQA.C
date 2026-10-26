/* Native Paintbrush repaint/pan probe for the installed local candidate. */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
typedef int (FAR PASCAL *ROWS)(LPSTR,unsigned,unsigned);
typedef int (FAR PASCAL *STATS)(unsigned FAR *);
static ROWS rows;
static STATS stats;
static char buffer[3840],line[256];
static HFILE logfile;
static int failures;
static int view[6];
static void Log(LPSTR s){_lwrite(logfile,s,lstrlen(s));_lclose(logfile);logfile=_lopen("C:\\APPQA.LOG",OF_WRITE);_llseek(logfile,0L,2);}
static void Check(LPSTR s,int ok){wsprintf(line,"CHECK %s=%d\r\n",s,ok!=0);Log(line);if(!ok)failures++;}
static void Pump(DWORD ms){DWORD a;MSG m;a=GetTickCount();while(GetTickCount()-a<ms)while(PeekMessage(&m,0,0,0,PM_REMOVE)){TranslateMessage(&m);DispatchMessage(&m);}}
static int Pan(int x,int y){HDC d;int in[2],ok;in[0]=x;in[1]=y;d=GetDC(0);ok=Escape(d,0x5860,4,(LPSTR)in,(LPSTR)view)>0;ReleaseDC(0,d);return ok;}
static void Mode(int m){HDC d;d=GetDC(0);Check("MODE",Escape(d,0x5861,2,(LPSTR)&m,0)>0);ReleaseDC(0,d);}
static HWND FindPaint(void){HWND w;char name[128];HINSTANCE owner;
 w=GetWindow(GetDesktopWindow(),GW_CHILD);while(w){owner=GetWindowWord(w,GWW_HINSTANCE);name[0]=0;
  if(owner)GetModuleFileName(owner,name,sizeof(name));AnsiUpper(name);
  if(strstr(name,"PBRUSH.EXE") && IsWindowVisible(w))return w;w=GetWindow(w,GW_HWNDNEXT);}return 0;}
static void Snap(int id){HFILE f;char name[24];char FAR *video;unsigned first,n,count,off,st[8];
 Pump(100);SetCursor(0);Check("QUERY",Pan(-1,0));stats(st);
 wsprintf(name,"C:\\A%03d.BIN",id);f=_lcreat(name,0);Check("SHADOW_FILE",f!=HFILE_ERROR);
 if(f!=HFILE_ERROR){for(first=0;first<256;first+=12){count=256-first;if(count>12)count=12;n=rows(buffer,first,count);Check("ROWS",n==count*320);Check("SHADOW_WRITE",_lwrite(f,buffer,n)==n);}_lclose(f);}
 wsprintf(name,"C:\\B%03d.BIN",id);f=_lcreat(name,0);Check("VRAM_FILE",f!=HFILE_ERROR);video=(char FAR *)MAKELONG(0,0xb800);
 if(f!=HFILE_ERROR){for(off=0;off<32768U;off+=8192U)Check("VRAM_WRITE",_lwrite(f,video+off,8192)==8192);_lclose(f);}
 wsprintf(line,"FRAME id=%d x=%d y=%d head=%u enabled=%u\r\n",id,view[0],view[1],st[2],st[0]);Log(line);}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR cmd,int show){HINSTANCE display;HWND paint;RECT r;int i,ok;DWORD a,b;unsigned st[8];char title[128];
 (void)instance;(void)previous;(void)cmd;(void)show;logfile=_lcreat("C:\\APPQA.LOG",0);if(logfile==HFILE_ERROR)return 1;
 display=GetModuleHandle("DISPLAY");rows=(ROWS)GetProcAddress(display,(LPSTR)108L);stats=(STATS)GetProcAddress(display,(LPSTR)106L);
 Check("EXPORTS",rows!=0 && stats!=0);Check("GEOMETRY",GetSystemMetrics(0)==640 && GetSystemMetrics(1)==256);if(!rows||!stats)goto done;
 Check("APP_LAUNCH",WinExec("C:\\WINDOWS\\PBRUSH.EXE C:\\PANAPP.BMP",SW_SHOWNORMAL)>=32);
 paint=0;for(i=0;i<20 && !paint;i++){Pump(250);paint=FindPaint();}Check("PBRUSH_WINDOW",paint!=0);if(!paint)goto done;
 SendMessage(paint,WM_SYSCOMMAND,SC_MAXIMIZE,0L);Pump(300);GetWindowText(paint,title,sizeof(title));GetWindowRect(paint,&r);
 AnsiUpper(title);Check("FILE_LOADED",strstr(title,"PANAPP")!=0);
 wsprintf(line,"APP title=%s rect=%d,%d,%d,%d\r\n",(LPSTR)title,r.left,r.top,r.right,r.bottom);Log(line);
 Mode(1);Check("HOME",Pan(0,0));Snap(0);
 a=GetTickCount();ok=Pan(16,8);b=GetTickCount();Check("PAN",ok);stats(st);
 wsprintf(line,"MOVE from=0,0 to=%d,%d total_ms=%lu bytes=%u reason=%u\r\n",view[0],view[1],b-a,st[7],st[3]);Log(line);
 Check("STAGED",view[0]==16 && view[1]==8 && st[7]==2816 && st[3]==0);Snap(1);
 InvalidateRect(paint,0,TRUE);Check("REPAINT_PENDING",GetUpdateRect(paint,&r,FALSE));
 UpdateWindow(paint);Check("REPAINT_COMPLETE",!GetUpdateRect(paint,&r,FALSE));Snap(2);
 Check("RETURN_HOME",Pan(0,0));Snap(3);
 SendMessage(paint,WM_CLOSE,0,0L);Pump(300);Check("PBRUSH_CLOSED",FindPaint()==0);Mode(0);Pan(0,0);
done:wsprintf(line,"END FAILURES=%d\r\n",failures);Log(line);_lclose(logfile);ExitWindows(0,0);return 0;}
