/* Native 8086 / Win16 isolated white-box tests. Production source is unchanged. */
#define WinMain OriginalWinMain
#include "SUBJECT.C"
#undef WinMain
static HFILE utlog;
static int utpass,utfail;
static void utline(char *s) { _lwrite(utlog,(LPSTR)s,lstrlen(s));_lwrite(utlog,"\r\n",2); }
static void utcheck(char *s,int ok) { if(ok){utpass++;_lwrite(utlog,"PASS=",5);}else{utfail++;_lwrite(utlog,"FAIL=",5);}utline(s); }
static void utvalue(char *s,long v) { char b[16];_lwrite(utlog,(LPSTR)s,lstrlen(s));num(b,v);utline(b); }
static void utfix(unsigned char *b) { unsigned s=checksum(b);b[10]=(unsigned char)s;b[11]=(unsigned char)(s>>8); }
static void utmake(unsigned char *b,long v,unsigned c) { int i;b[0]='T';b[1]='C';b[2]='C';b[3]=1;for(i=4;i<8;i++){b[i]=(unsigned char)(v&255);v>>=8;}b[8]=(unsigned char)c;b[9]=(unsigned char)(c>>8);utfix(b);b[12]=77; }
static int utwrite(unsigned char *b,int n) { HFILE f;int k,r;f=_lcreat(savepath,0);if(f==HFILE_ERROR)return 0;k=_lwrite(f,(LPSTR)b,n);r=_lclose(f);return k==n&&r==0; }
static void utinvalid(HWND w,char *name,unsigned char *b,int n) { int written;cookies=4321;cps=7;written=utwrite(b,n);loadgame(w);utcheck(name,written&&cookies==4321&&cps==7&&!lstrcmp(status,"Invalid save")); }
static HWND utdialog;
static int utdialogseen;
void FAR PASCAL UTDlgTimer(HWND w,UINT m,UINT id,DWORD tick) {
 HWND d,ok;RECT r,cr,br;POINT pt;HDC dc;TEXTMETRIC tm;
 d=GetLastActivePopup(w);if(d==w||!d)return;utdialog=d;utdialogseen=1;KillTimer(w,2);
 GetWindowRect(d,&r);GetClientRect(d,&cr);ok=GetDlgItem(d,IDOK);
 utcheck("about-native-dialog-created",IsWindow(d));
 utcheck("about-exact-client-148x136",cr.right==148&&cr.bottom==136);
 utcheck("about-within-physical-screen",r.left>=0&&r.right<=GetSystemMetrics(SM_CXSCREEN)&&r.top>=0&&r.bottom<=GetSystemMetrics(SM_CYSCREEN));
 utcheck("about-native-ok-created",ok!=NULL&&IsWindow(ok));
 if(ok){GetWindowRect(ok,&br);pt.x=br.left;pt.y=br.top;ScreenToClient(d,&pt);utcheck("about-ok-geometry",pt.x==52&&pt.y==110&&br.right-br.left==40&&br.bottom-br.top==18);}
 dc=GetDC(d);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));GetTextMetrics(dc,&tm);ReleaseDC(d,dc);
 utcheck("about-text-no-row-overlap",tm.tmHeight<=12);utcheck("about-text-clears-ok",4+7*12+tm.tmHeight<=110);utcheck("about-text-width-fits",4+17*tm.tmAveCharWidth<=148);
 SendMessage(d,WM_COMMAND,IDOK,0L);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;RECT r;unsigned char b[13];int i,n;HFILE f;DWORD start;FARPROC dp;char name[40],digits[12];
 instance=inst;utlog=_lcreat("C:\\COOKIEUT.LOG",0);if(utlog==HFILE_ERROR)return 9;
 utline("HARNESS=COOKIE_NATIVE_WIN16");utvalue("SCREEN_WIDTH=",GetSystemMetrics(SM_CXSCREEN));utvalue("SCREEN_HEIGHT=",GetSystemMetrics(SM_CYSCREEN));utvalue("WIN_FLAGS=",GetWinFlags());
 utcheck("windows-real-mode",!(GetWinFlags()&WF_PMODE));
 wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="CookieUT";
 utcheck("native-window-class",RegisterClass(&wc)!=0);
 w=CreateWindow("CookieUT","Cookie UT",WS_OVERLAPPEDWINDOW|WS_CLIPCHILDREN,0,0,160,200,NULL,NULL,inst,NULL);
 utcheck("native-window-created",w!=NULL);if(!w)goto done;
 ShowWindow(w,SW_SHOWMAXIMIZED);UpdateWindow(w);KillTimer(w,1);GetClientRect(w,&r);
 utvalue("CLIENT_WIDTH=",r.right);utvalue("CLIENT_HEIGHT=",r.bottom);
 utcheck("native-buy-control-created",buy!=NULL&&IsWindow(buy));
 SendMessage(w,WM_COMMAND,NEW,0L);utcheck("new-game-zero",cookies==0&&cps==0);utcheck("buy-enabled-under-cost",IsWindowEnabled(buy));
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(0,0));utcheck("outside-click-rejected",cookies==0);
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(cookie.left+1,cookie.top+1));utcheck("bounding-corner-rejected",cookies==0);
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(cookie.left+27,cookie.top+27));utcheck("center-click-accepted",cookies==1);
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(cookie.left+55,cookie.top+27));utcheck("beyond-radius-rejected",cookies==1);
 SendMessage(w,WM_KEYDOWN,VK_SPACE,0L);utcheck("space-key-click",cookies==2);
 cookies=25;cps=0;refresh(w);utcheck("buy-enabled-at-cost",IsWindowEnabled(buy));
 SendMessage(w,WM_COMMAND,BUY,0L);utcheck("buy-cost-and-cps",cookies==15&&cps==1);
 SendMessage(w,WM_KEYDOWN,'U',0L);utcheck("upgrade-key-cost-and-cps",cookies==5&&cps==2);
 utcheck("buy-stays-enabled-below-cost",IsWindowEnabled(buy));SendMessage(w,WM_COMMAND,BUY,0L);utcheck("insufficient-buy-preserves-and-explains",cookies==5&&cps==2&&!lstrcmp(status,"Need 10 cookies"));
 cookies=100;cps=MAXCPS;refresh(w);utcheck("buy-enabled-at-cps-cap",IsWindowEnabled(buy));SendMessage(w,WM_COMMAND,BUY,0L);utcheck("cps-cap-preserves-money-and-explains",cookies==100&&cps==MAXCPS&&!lstrcmp(status,"CPS limit"));
 cookies=MAXCOOK;SendMessage(w,WM_KEYDOWN,VK_SPACE,0L);utcheck("click-saturates",cookies==MAXCOOK);
 cookies=10;cps=3;SendMessage(w,WM_TIMER,1,0L);utcheck("timer-adds-cps",cookies==13);
 SendMessage(w,WM_TIMER,2,0L);utcheck("unrelated-timer-ignored",cookies==13);
 cookies=MAXCOOK-2;SendMessage(w,WM_TIMER,1,0L);utcheck("timer-saturates",cookies==MAXCOOK);SendMessage(w,WM_TIMER,1,0L);utcheck("timer-remains-saturated",cookies==MAXCOOK);
 cookies=17;cps=0;SendMessage(w,WM_TIMER,1,0L);utcheck("zero-cps-stable",cookies==17);
 lstrcpy(savepath,"C:\\COOKIEUT.SAV");cookies=123456;cps=321;savegame(w);utcheck("save-native-write-success",!lstrcmp(status,"Saved"));
 f=_lopen(savepath,OF_READ);n=f==HFILE_ERROR?-1:_lread(f,(LPSTR)b,13);if(f!=HFILE_ERROR)_lclose(f);utcheck("save-exact-twelve-bytes",n==12);utcheck("save-version-signature",n==12&&b[0]=='T'&&b[1]=='C'&&b[2]=='C'&&b[3]==1);utcheck("save-native-checksum",n==12&&checksum(b)==((unsigned)b[10]|((unsigned)b[11]<<8)));
 cookies=7;cps=2;loadgame(w);utcheck("save-load-roundtrip",cookies==123456&&cps==321&&!lstrcmp(status,"Loaded"));
 utmake(b,MAXCOOK,MAXCPS);utcheck("maximum-fixture-written",utwrite(b,12));loadgame(w);utcheck("maximum-state-loads",cookies==MAXCOOK&&cps==MAXCPS);
 utmake(b,0,0);utcheck("zero-fixture-written",utwrite(b,12));loadgame(w);utcheck("zero-state-loads",cookies==0&&cps==0);
 for(i=0;i<12;i++){utmake(b,123456,321);b[i]^=1;lstrcpy(name,"single-byte-corruption-");num(digits,(long)i);lstrcat(name,digits);utinvalid(w,name,b,12);}
 for(i=0;i<12;i++){utmake(b,123456,321);lstrcpy(name,"truncated-save-");num(digits,(long)i);lstrcat(name,digits);utinvalid(w,name,b,i);}
 utmake(b,123456,321);utinvalid(w,"extra-byte-save",b,13);
 utmake(b,123456,321);b[0]='X';utfix(b);utinvalid(w,"bad-signature-valid-checksum",b,12);
 utmake(b,123456,321);b[3]=2;utfix(b);utinvalid(w,"bad-version-valid-checksum",b,12);
 utmake(b,MAXCOOK+1,321);utinvalid(w,"cookies-above-cap",b,12);
 utmake(b,2147483647L,321);utinvalid(w,"cookies-positive-long-max",b,12);
 utmake(b,-1L,321);utinvalid(w,"cookies-negative",b,12);
 utmake(b,123456,MAXCPS+1);utinvalid(w,"cps-above-cap",b,12);
 utmake(b,123456,65535U);utinvalid(w,"cps-unsigned-max",b,12);
 lstrcpy(savepath,"C:\\UTABSENT\\NONE.SAV");cookies=9876;cps=54;loadgame(w);utcheck("missing-save-preserves",cookies==9876&&cps==54&&!lstrcmp(status,"Cannot read save"));savegame(w);utcheck("failed-save-reports-error",cookies==9876&&cps==54&&!lstrcmp(status,"Save failed"));
 SendMessage(w,WM_COMMAND,NEW,0L);utcheck("new-game-resets-loaded-state",cookies==0&&cps==0&&!lstrcmp(status,"New game"));
 cookies=0;cps=1;i=SetTimer(w,1,100,NULL);utcheck("native-timer-created",i!=0);start=GetTickCount();
 if(i){while(cookies<3&&GetTickCount()-start<5000L){if(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}}KillTimer(w,1);utcheck("native-timer-messages-delivered",cookies>=3);}
 dp=MakeProcInstance((FARPROC)UTDlgTimer,instance);utcheck("about-probe-callback-created",dp!=NULL);
 if(dp){i=SetTimer(w,2,100,(TIMERPROC)dp);utcheck("about-probe-timer-created",i!=0);if(i){about(w);KillTimer(w,2);utcheck("about-probe-ran",utdialogseen);utcheck("about-native-ok-closes-dialog",utdialogseen&&!IsWindow(utdialog)&&!aboutOpen);}FreeProcInstance(dp);}
 DestroyWindow(w);
 done:utvalue("PASS_COUNT=",utpass);utvalue("FAIL_COUNT=",utfail);utline("COMPLETE=1");_lclose(utlog);return utfail?1:0;
}
