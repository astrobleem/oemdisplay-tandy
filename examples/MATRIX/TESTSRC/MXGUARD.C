#define WINVER 0x0300
#include <windows.h>
static HINSTANCE instance;
static HWND edit,button,win;
static int waiting,seen,launches,dupMode,dupPhase;
static DWORD dupStarted;
static HWND ordinary;
static void logtext(char *s){HFILE f=_lopen("C:\\GUARD.LOG",OF_WRITE);if(f==HFILE_ERROR)f=_lcreat("C:\\GUARD.LOG",0);if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);}}
static void arm(void){SetWindowText(edit,"UNCHANGED");SetFocus(edit);SetTimer(win,2,1200,NULL);logtext("ARMED\r\n");}
LONG FAR PASCAL GuardProc(HWND w,UINT m,WPARAM wp,LPARAM lp){HDC dc;PAINTSTRUCT ps;RECT r;char b[200],text[80];HWND s;
 switch(m){case WM_CREATE:win=w;edit=CreateWindow("EDIT","UNCHANGED",WS_CHILD|WS_VISIBLE|WS_BORDER|ES_AUTOHSCROLL,4,25,145,18,w,1,instance,NULL);button=CreateWindow("BUTTON","Arm /S (F5)",WS_CHILD|WS_VISIBLE|BS_PUSHBUTTON,4,55,145,20,w,2,instance,NULL);SetTimer(w,1,110,NULL);return 0;
 case WM_PAINT:dc=BeginPaint(w,&ps);GetClientRect(w,&r);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));TextOut(dc,4,4,"MATRIX INPUT GUARD",18);TextOut(dc,4,90,"Text must stay UNCHANGED.",25);TextOut(dc,4,110,"F5: delayed /S; F6: normal.",27);EndPaint(w,&ps);return 0;
 case WM_COMMAND:if(wp==2){arm();return 0;}return 0;
 case WM_TIMER:
  if(dupMode&&wp==1){
   if(!dupPhase){WinExec("C:\\MATRIX.EXE",SW_SHOWNORMAL);dupPhase=1;}
   else if(dupPhase==1&&(ordinary=FindWindow("TandyMatrix",NULL))){WinExec("C:\\MATRIX.EXE /S",SW_SHOWNORMAL);dupStarted=GetTickCount();dupPhase=2;}
   else if(dupPhase==2&&GetTickCount()-dupStarted>550UL){wsprintf(b,"DUP ordinary_alive=%d saver_absent=%d ordinary_active=%d\r\n",IsWindow(ordinary),FindWindow("TandyMatrixSaver",NULL)==NULL,GetActiveWindow()==ordinary);logtext(b);PostMessage(ordinary,WM_CLOSE,0,0L);dupPhase=3;}
   else if(dupPhase==3&&!IsWindow(ordinary)){logtext("DUP DONE\r\n");DestroyWindow(w);}
   return 0;
  }
  if(wp==2){KillTimer(w,2);seen=0;waiting=1;launches++;SetFocus(edit);wsprintf(b,"LAUNCH %d result=%u\r\n",launches,WinExec("C:\\MATRIX.EXE /S",SW_SHOWNORMAL));logtext(b);return 0;}
  s=FindWindow("TandyMatrixSaver",NULL);if(s&&!seen){seen=1;logtext("SAVER READY\r\n");}
  if(waiting&&seen&&!s){waiting=0;GetWindowText(edit,text,sizeof(text));wsprintf(b,"RETURN text=%s focus_ok=%d active_ok=%d capture_released=%d\r\n",(LPSTR)text,GetFocus()==edit,GetActiveWindow()==w,GetCapture()==NULL);logtext(b);InvalidateRect(w,NULL,FALSE);}return 0;
 case WM_CLOSE:DestroyWindow(w);return 0;
 case WM_DESTROY:KillTimer(w,1);KillTimer(w,2);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE i,HINSTANCE p,LPSTR c,int sh){WNDCLASS wc;MSG msg;HFILE f;instance=i;dupMode=c[0]=='/'&&(c[1]=='D'||c[1]=='d');f=_lcreat("C:\\GUARD.LOG",0);if(f!=HFILE_ERROR)_lclose(f);if(!p){wc.style=0;wc.lpfnWndProc=GuardProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=i;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="MatrixInputGuard";if(!RegisterClass(&wc))return 1;}win=CreateWindow("MatrixInputGuard","Matrix Input Guard",WS_POPUP,0,0,GetSystemMetrics(SM_CXSCREEN),200,NULL,NULL,i,NULL);ShowWindow(win,SW_SHOW);UpdateWindow(win);SetFocus(edit);while(GetMessage(&msg,NULL,0,0)){if(msg.message==WM_KEYDOWN&&msg.wParam==VK_F5)arm();else if(msg.message==WM_KEYDOWN&&msg.wParam==VK_F6){WinExec("C:\\MATRIX.EXE",SW_SHOWNORMAL);}else{TranslateMessage(&msg);DispatchMessage(&msg);}}return msg.wParam;}
