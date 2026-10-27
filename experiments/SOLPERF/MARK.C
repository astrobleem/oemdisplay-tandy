#include <windows.h>
#include <dos.h>
struct STATE {DWORD magic,phase,start_bios,start_ms,return_bios,return_ms,end_bios,end_ms;WORD rc,width,height,colors;short left,top,right,bottom;};
static volatile struct STATE state;static DWORD waitstart;static int started;
static DWORD bios(void){return *(DWORD FAR *)0x0040006cL;}
static void logline(char *s){HFILE f=_lcreat("C:\\SOLMARK.LOG",0);if(f!=HFILE_ERROR){_lwrite(f,s,lstrlen(s));_lclose(f);}}
long FAR PASCAL WndProc(HWND w,UINT m,WPARAM p,LPARAM l){HWND game;RECT r;
 if(m==WM_TIMER){
  if(!started && GetTickCount()>60000L){started=1;state.start_bios=bios();state.start_ms=GetTickCount();state.phase=1;state.rc=WinExec("C:\\WINDOWS\\SOL.EXE",SW_SHOWNORMAL);state.return_bios=bios();state.return_ms=GetTickCount();state.phase=2;}
  else if(state.phase==2){game=FindWindow(NULL,"Solitaire");if(game && IsWindowVisible(game) && !GetUpdateRect(game,&r,FALSE)){state.end_bios=bios();state.end_ms=GetTickCount();GetWindowRect(game,&r);state.left=r.left;state.top=r.top;state.right=r.right;state.bottom=r.bottom;state.phase=3;}}
  return 0;}
 return DefWindowProc(w,m,p,l);}
int PASCAL WinMain(HINSTANCE i,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG msg;char s[200];HDC dc;void FAR *ptr;
 LockData(0);state.magic=0x534f4c32L;dc=GetDC(0);state.width=GetDeviceCaps(dc,HORZRES);state.height=GetDeviceCaps(dc,VERTRES);state.colors=GetDeviceCaps(dc,NUMCOLORS);ReleaseDC(0,dc);ptr=(void FAR *)&state;
 wsprintf(s,"SEG %u OFFSET %u SIZE %u VERSION %lu WIDTH %u HEIGHT %u COLORS %u\r\n",FP_SEG(ptr),FP_OFF(ptr),sizeof(state),GetVersion(),state.width,state.height,state.colors);logline(s);
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=i;wc.hIcon=0;wc.hCursor=0;wc.hbrBackground=0;wc.lpszMenuName=0;wc.lpszClassName="SolMark";if(!RegisterClass(&wc))return 1;w=CreateWindow("SolMark","SolMark",WS_POPUP,0,0,0,0,0,0,i,0);waitstart=GetTickCount();SetTimer(w,1,55,0);while(GetMessage(&msg,0,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return 0;}
