#define WINVER 0x0300
#include <windows.h>
static int step;static HWND eyes;static HFILE logf;static HWND cover;
static void logline(LPSTR s){logf=_lopen("C:\\EYES.LOG",OF_WRITE);_llseek(logf,0L,2);_lwrite(logf,s,lstrlen(s));_lclose(logf);}
long FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){
 RECT r;POINT p;
 if(m==WM_TIMER){
  switch(step++){
  case 0:WinExec("C:\\WINDOWS\\XTEYES.EXE",SW_SHOWNORMAL);break;
  case 1:eyes=FindWindow("XTEyes",NULL);if(!eyes){logline("FAIL launch\r\n");DestroyWindow(w);break;}logline("PASS launch\r\n");SetCursorPos(0,0);break;
  case 2:logline("left-top\r\n");break;
  case 3:SetCursorPos(GetSystemMetrics(SM_CXSCREEN)-1,199);break;
  case 4:logline("right-bottom\r\n");break;
  case 5:GetClientRect(eyes,&r);p.x=r.right/2;p.y=28;ClientToScreen(eyes,&p);SetCursorPos(p.x,p.y);break;
  case 6:logline("cursor-over-eyes\r\n");break;
  case 7:cover=CreateWindow("QA","Cover",WS_POPUP|WS_VISIBLE,0,20,GetSystemMetrics(SM_CXSCREEN),95,NULL,NULL,GetWindowWord(w,GWW_HINSTANCE),NULL);break;
  case 8:logline("covered\r\n");break;
  case 9:DestroyWindow(cover);SetCursorPos(0,199);break;
  case 10:logline("uncovered\r\n");break;
  case 11:SetWindowPos(eyes,NULL,15,70,0,0,SWP_NOSIZE|SWP_NOZORDER);break;
  case 12:logline("moved\r\n");break;
  case 13:ShowWindow(eyes,SW_MINIMIZE);break;
  case 14:logline("minimized\r\n");break;
  case 15:ShowWindow(eyes,SW_RESTORE);break;
  case 16:logline("restored\r\n");break;
  case 17:SendMessage(eyes,WM_CLOSE,0,0L);break;
  case 18:logline(FindWindow("XTEyes",NULL)?"FAIL close\r\n":"PASS close\r\n");break;
  case 19:WinExec("C:\\WINDOWS\\XTEYES.EXE",SW_SHOWNORMAL);break;
  case 20:eyes=FindWindow("XTEyes",NULL);logline(eyes?"PASS reopen\r\n":"FAIL reopen\r\n");break;
  case 21:if(eyes)SendMessage(eyes,WM_CLOSE,0,0L);logline("DONE\r\n");DestroyWindow(w);break;
  }return 0;
 }
 if(m==WM_DESTROY&&w!=cover){KillTimer(w,1);PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE h,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG m;
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=h;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(GRAY_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="QA";RegisterClass(&wc);
 logf=_lcreat("C:\\EYES.LOG",0);_lclose(logf);w=CreateWindow("QA","QA",WS_OVERLAPPED,0,0,10,10,NULL,NULL,h,NULL);SetTimer(w,1,2500,NULL);
 while(GetMessage(&m,NULL,0,0)){TranslateMessage(&m);DispatchMessage(&m);}return 0;}
