/* Small Windows 3.0 REAL MODE / 8088 EX built-in joystick tester. */
#define WINVER 0x0300
#include <windows.h>
#include "JOYCORE.H"
#define PAUSE 101
#define VIEW 102
#define PULSE 1
static HINSTANCE instance;
static HWND mainWindow;
static unsigned char raw[JOY_SAMPLES];
static JOY_SAMPLE sample;
static JOY_CAL cal;
static int paused,rangeView,demo,automatic,failures,stage;
static unsigned polls,hardwarePolls,pausedPolls;
static DWORD beginTick,lastPaint,maxPollMs;
static HFILE logFile=HFILE_ERROR;
static char notice[19]="* presence unknown";
static void line(HDC dc,int y,char *s) {RECT r;r.left=4;r.right=148;r.top=y;r.bottom=y+16;ExtTextOut(dc,4,y,ETO_OPAQUE,&r,s,lstrlen(s),NULL);}
static void logText(char *s){if(logFile!=HFILE_ERROR){_lwrite(logFile,s,lstrlen(s));_lwrite(logFile,"\r\n",2);}}
static void check(char *s,int ok){char b[96];wsprintf(b,"%s %s",(LPSTR)(ok?"PASS":"FAIL"),(LPSTR)s);logText(b);if(!ok)failures++;}
static void redraw(void){if(mainWindow)InvalidateRect(mainWindow,NULL,FALSE);}
static void setNotice(char *s){lstrcpy(notice,s);redraw();}
static void makeDemo(unsigned step){unsigned i,a,t[4],bits;t[0]=20+step%100;t[1]=100-step%80;t[2]=30+step%60;t[3]=90-step%70;for(i=0;i<JOY_SAMPLES;i++){bits=0xf0;if(step&1)bits&=~0x10;for(a=0;a<4;a++)if(i<t[a])bits|=1<<a;raw[i]=(unsigned char)bits;}}
static void poll(void){DWORD t,dt;t=GetTickCount();if(demo)makeDemo(polls);else {joy_capture(raw);hardwarePolls++;}dt=GetTickCount()-t;if(dt>maxPollMs)maxPollMs=dt;joy_decode(raw,JOY_SAMPLES,&sample);joy_track(&cal,&sample);polls++;}
static void togglePause(void){paused=!paused;SetWindowText(GetDlgItem(mainWindow,PAUSE),paused?"&Run":"&Pause");setNotice(paused?"Paused":"* presence unknown");}
static void resetRange(void){joy_reset(&cal);joy_track(&cal,&sample);setNotice("Range reset");}
static void center(void){joy_center(&cal,&sample);setNotice(cal.centered==15?"Center stored":cal.centered?"Center partial":"No center timing");}
static void axisText(char *s,unsigned a){if(sample.timeout&(1u<<a))lstrcpy(s,"TMO");else wsprintf(s,"%03u",sample.axis[a]);}
static void paint(HWND w){
 HDC dc;PAINTSTRUCT ps;RECT clear;char b[64],x[8],y[8];unsigned p,a;int yy;char *signal;
 dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));SetBkColor(dc,RGB(255,255,255));SetTextColor(dc,RGB(0,0,0));
 clear.left=4;clear.right=148;clear.top=20;clear.bottom=116;FillRect(dc,&clear,GetStockObject(WHITE_BRUSH));
 line(dc,2,demo?"EXJOY DEMO":paused?"EXJOY PAUSED":"EXJOY 4Hz 0201h");
 if(!rangeView){
  for(p=0;p<2;p++){
   a=p*2;yy=20+(int)p*48;axisText(x,a);axisText(y,a+1);wsprintf(b,"%s X:%s Y:%s",(LPSTR)(p?"L":"R"),(LPSTR)x,(LPSTR)y);line(dc,yy,b);
   wsprintf(b,"B1:%s B2:%s",(LPSTR)((sample.buttons&(1<<a))?"DOWN":"up"),(LPSTR)((sample.buttons&(2<<a))?"DOWN":"up"));line(dc,yy+16,b);
   signal=(sample.timeout&(3<<a))?"timeout / unknown":(sample.timed&(3<<a))==(3<<a)?"timing seen *":"zero / unknown *";
   line(dc,yy+32,signal);
  }
 }else{
  for(a=0;a<4;a++){if(cal.centered&(1u<<a))wsprintf(x,"%03u",cal.center[a]);else lstrcpy(x,"---");if(cal.seen&(1u<<a))wsprintf(b,"%s %03u-%03u C%s",(LPSTR)(a==0?"RX":a==1?"RY":a==2?"LX":"LY"),cal.low[a],cal.high[a],(LPSTR)x);else wsprintf(b,"%s --- --- C%s",(LPSTR)(a==0?"RX":a==1?"RY":a==2?"LX":"LY"),(LPSTR)x);line(dc,20+(int)a*24,b);}
 }
 line(dc,118,notice);line(dc,158,"C center R reset");EndPaint(w,&ps);
}
static void button(HWND w,char *s,int x,int id){HWND b;b=CreateWindow("BUTTON",s,WS_CHILD|WS_VISIBLE|WS_TABSTOP,x,136,68,20,w,(HMENU)id,instance,NULL);if(b)SendMessage(b,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);}
static void testStep(void){char b[100];JOY_CAL t;unsigned a;
 if(stage==0){check("window and controls exist",mainWindow&&GetDlgItem(mainWindow,PAUSE)&&GetDlgItem(mainWindow,VIEW));check("running timer produced samples",polls>=3);check("pure demo performs no hardware I/O",demo&&hardwarePolls==0);center();check("manual center captured",cal.centered==15);t=cal;for(a=0;a<4;a++){t.low[a]=t.center[a]-5;t.high[a]=t.center[a]+5;check("Win16 normalization",joy_normal(&t,a,t.center[a])==50&&joy_normal(&t,a,t.high[a])==100);}stage++;}
 else if(stage==1){togglePause();pausedPolls=polls;check("pause state",paused);stage++;}
 else if(stage==2){check("pause stops polling",paused&&polls==pausedPolls);togglePause();SendMessage(mainWindow,WM_COMMAND,VIEW,0L);resetRange();check("range reset clears center",cal.centered==0&&cal.seen==15);stage++;}
 else if(stage==3){check("resumed polling",!paused&&polls>=4);wsprintf(b,"POLLS=%u HARDWARE_POLLS=%u MAX_POLL_MS=%lu",polls,hardwarePolls,maxPollMs);logText(b);PostMessage(mainWindow,WM_CLOSE,0,0L);stage++;}
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){DWORD now;RECT r;
 switch(m){
 case WM_CREATE:mainWindow=w;button(w,"&Pause",4,PAUSE);button(w,"&Range",76,VIEW);if(!GetDlgItem(w,PAUSE)||!GetDlgItem(w,VIEW))return -1;if(!SetTimer(w,PULSE,250,NULL))return -1;beginTick=GetTickCount();return 0;
 case WM_COMMAND:if(wp==PAUSE)togglePause();if(wp==VIEW){rangeView=!rangeView;SetWindowText(GetDlgItem(w,VIEW),rangeView?"&Live":"&Range");redraw();}return 0;
 case WM_TIMER:if(wp==PULSE){now=GetTickCount();if(!paused&&!IsIconic(w))poll();if(now-lastPaint>=500UL){r.left=4;r.right=148;r.top=20;r.bottom=116;InvalidateRect(w,&r,FALSE);lastPaint=now;}if(automatic&&now-beginTick>2000UL+(DWORD)stage*2000UL){if(automatic==1)testStep();else if(now-beginTick>8000UL){check("bounded real I/O returns",hardwarePolls>0);PostMessage(w,WM_CLOSE,0,0L);}}}return 0;
 case WM_PAINT:paint(w);return 0;
 case WM_QUERYENDSESSION:return TRUE;
 case WM_CLOSE:DestroyWindow(w);return 0;
 case WM_DESTROY:KillTimer(w,PULSE);mainWindow=0;PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE previous,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG msg;char b[96];int result=0;
 if(previous){w=FindWindow("TandyEXJOY",NULL);if(w){ShowWindow(w,SW_RESTORE);BringWindowToTop(w);}return 0;}
 if(GetWinFlags()&WF_PMODE){MessageBox(NULL,"Use Windows 3.0 real mode on a Tandy 1000 EX.","EXJOY",MB_OK);return 1;}
 instance=inst;demo=lstrcmp(cmd,"/demo")==0||lstrcmp(cmd,"/test")==0;automatic=lstrcmp(cmd,"/test")==0?1:lstrcmp(cmd,"/porttest")==0?2:0;
 if(automatic)logFile=_lcreat("C:\\EXJOY.LOG",0);
 joy_reset(&cal);joy_decode(raw,0,&sample);
 wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="TandyEXJOY";
 if(!RegisterClass(&wc))return 2;
 w=CreateWindow("TandyEXJOY","EX Joystick",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX|WS_CLIPCHILDREN,0,0,156,200,NULL,NULL,inst,NULL);
 if(!w)return 3;ShowWindow(w,show);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){
  if(msg.message==WM_KEYDOWN){
   if(msg.wParam==VK_ESCAPE||msg.wParam=='Q'){PostMessage(w,WM_CLOSE,0,0L);continue;}
   if(msg.wParam=='P'){togglePause();continue;}if(msg.wParam=='R'){resetRange();continue;}if(msg.wParam=='C'){center();continue;}
   if(msg.wParam==VK_TAB){HWND next;next=GetNextDlgTabItem(w,GetFocus(),GetKeyState(VK_SHIFT)<0);if(next)SetFocus(next);continue;}
  }
  TranslateMessage(&msg);DispatchMessage(&msg);
 }
 if(automatic){check("window destroyed",mainWindow==0);wsprintf(b,"FINAL raw=%02X timed=%X early=%X timeout=%X buttons=%X",(unsigned)sample.last,(unsigned)sample.timed,(unsigned)sample.early,(unsigned)sample.timeout,(unsigned)sample.buttons);logText(b);wsprintf(b,"TOTAL_FAILURES=%d POLLS=%u HARDWARE_POLLS=%u MAX_POLL_MS=%lu",failures,polls,hardwarePolls,maxPollMs);logText(b);if(logFile!=HFILE_ERROR)_lclose(logFile);ExitWindows(0L,0);}return result?result:failures;
}
