/* Original MIT test-only Win16 driver for an actual DOS guard test.
 * MSC6 /AS /G0 /Gw; initial shell only in a disposable private fixture.
 */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HFILE logfile;
static DWORD started;
static int phase;
static void record(char *name,unsigned value)
{ char line[80];unsigned n;n=(unsigned)wsprintf(line,"%s=%u\r\n",(LPSTR)name,value);_lwrite(logfile,line,n); }
long FAR PASCAL WindowProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp)
{
 HFILE child;unsigned result,n;char output[1024];
 if(msg==WM_TIMER){
  if(!phase){
   phase=1;record("WINEXEC_REQUEST",1);
   result=WinExec("C:\\DOSGUARD.EXE WINDOWS",SW_SHOW);record("WINEXEC_RESULT",result);
   if(result<32){record("LAUNCH_FAILED",1);DestroyWindow(hwnd);return 0L;}
  }
  child=_lopen("C:\\DOSDONE.OK",OF_READ);
  if(child!=HFILE_ERROR){_lclose(child);record("DOS_RETURNED_TO_WINDOWS",1);DestroyWindow(hwnd);return 0L;}
  child=_lopen("C:\\DOSGUARD.LOG",OF_READ);
  if(child!=HFILE_ERROR){n=_lread(child,output,sizeof(output)-1);_lclose(child);if(n<sizeof(output)){output[n]=0;if(strstr(output,"STOP: guard not proved")){record("DOS_GUARD_FAILED",1);DestroyWindow(hwnd);return 0L;}}}
  if(GetTickCount()-started>40000UL){record("WAIT_EXPIRED",1);DestroyWindow(hwnd);return 0L;}
  return 0L;
 }
 if(msg==WM_DESTROY){KillTimer(hwnd,1);record("WINAPP_EXIT",1);_lclose(logfile);PostQuitMessage(0);return 0L;}
 return DefWindowProc(hwnd,msg,wp,lp);
}
int PASCAL WinMain(HINSTANCE current,HINSTANCE prior,LPSTR args,int show)
{
 WNDCLASS wc;HWND hwnd;MSG msg;DWORD flags;
 (void)args;(void)show;logfile=_lcreat("C:\\WINGUARD.LOG",0);if(logfile==HFILE_ERROR)return 1;
 flags=GetWinFlags();record("FLAGS_HIGH",(unsigned)(flags>>16));record("FLAGS_LOW",(unsigned)flags);
 if(!prior){memset(&wc,0,sizeof(wc));wc.lpfnWndProc=WindowProc;wc.hInstance=current;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszClassName="XTWINGUARD";if(!RegisterClass(&wc)){_lclose(logfile);return 2;}}
 hwnd=CreateWindow("XTWINGUARD","Native DOS guard test",WS_OVERLAPPEDWINDOW,0,0,240,100,NULL,NULL,current,NULL);
 if(!hwnd){_lclose(logfile);return 3;}ShowWindow(hwnd,SW_SHOW);UpdateWindow(hwnd);started=GetTickCount();
 if(!SetTimer(hwnd,1,1000,NULL)){DestroyWindow(hwnd);return 4;}
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return msg.wParam;
}
