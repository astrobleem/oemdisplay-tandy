/* Tiny 8086 / Windows 3.0 native usability benchmark. */
#define WINVER 0x0300
#include <windows.h>
#define MAXCOOK 999999L
#define MAXCPS 999
#define BUY 20
#define NEW 101
#define SAVE 102
#define LOAD 103
#define QUIT 104
#define ABOUT 105
static HINSTANCE instance;
static HWND buy;
static long cookies;
static unsigned cps;
static RECT cookie;
static char status[24]="Click cookie!";
static char savepath[144];
static int aboutOpen;
static void note(HWND w,char *s) { RECT r; lstrcpy(status,s); GetClientRect(w,&r);r.top=119;r.bottom=133;InvalidateRect(w,&r,TRUE); }
static void add(void) { if(cookies<MAXCOOK) ++cookies; }
static void num(char *s,long v) { char b[12]; int n=0,i=0; do { b[n++]=(char)('0'+v%10);v/=10; }while(v);while(n)s[i++]=b[--n];s[i]=0; }
static void label(HDC dc,int x,int y,char *s) { TextOut(dc,x,y,s,lstrlen(s)); }
static void refresh(HWND w) { RECT r; GetClientRect(w,&r);r.bottom=29;InvalidateRect(w,&r,TRUE); }
static unsigned checksum(unsigned char *b) { unsigned s=0x436b;int i;for(i=0;i<10;i++)s=(s<<1)^b[i]^(s>>15);return s; }
static void savegame(HWND w) {
 unsigned char b[12]; unsigned s; HFILE f; int i; long v=cookies;
 b[0]='T';b[1]='C';b[2]='C';b[3]=1;
 for(i=4;i<8;i++){b[i]=(unsigned char)(v&255);v>>=8;}
 b[8]=(unsigned char)cps;b[9]=(unsigned char)(cps>>8);s=checksum(b);b[10]=(unsigned char)s;b[11]=(unsigned char)(s>>8);
 f=_lcreat(savepath,0);if(f==HFILE_ERROR){note(w,"Save failed");return;}
 i=_lwrite(f,(LPSTR)b,12);if(_lclose(f)!=0)i=0;note(w,i==12?"Saved":"Save failed");
}
static void loadgame(HWND w) {
 unsigned char b[13]; HFILE f; int n; long v; unsigned c,s;
 f=_lopen(savepath,OF_READ);if(f==HFILE_ERROR){note(w,"Cannot read save");return;}
 n=_lread(f,(LPSTR)b,13);_lclose(f);
 if(n!=12 || b[0]!='T'||b[1]!='C'||b[2]!='C'||b[3]!=1){note(w,"Invalid save");return;}
 v=(long)b[4]|((long)b[5]<<8)|((long)b[6]<<16)|((long)b[7]<<24);c=b[8]|((unsigned)b[9]<<8);s=b[10]|((unsigned)b[11]<<8);
 if(v<0||v>MAXCOOK||c>MAXCPS||s!=checksum(b)){note(w,"Invalid save");return;}
 cookies=v;cps=c;note(w,"Loaded");refresh(w);
}
BOOL FAR PASCAL AboutProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc; PAINTSTRUCT ps; RECT r,cr; int i,ww,hh;
 static char *lines[]={"Tandy Cookie","Clicker Benchmark","","A tiny Win16","usability test","for the Tandy","1000 display","driver."};
 if(m==WM_INITDIALOG){GetWindowRect(w,&r);GetClientRect(w,&cr);ww=148+r.right-r.left-cr.right;hh=136+r.bottom-r.top-cr.bottom;SetWindowPos(w,NULL,(GetSystemMetrics(SM_CXSCREEN)-ww)/2,10,ww,hh,SWP_NOZORDER);MoveWindow(GetDlgItem(w,IDOK),52,110,40,18,TRUE);SendMessage(GetDlgItem(w,IDOK),WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);return TRUE;}
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(dc,TRANSPARENT);for(i=0;i<8;i++)label(dc,4,4+i*12,lines[i]);EndPaint(w,&ps);return TRUE;}
 if(m==WM_COMMAND&&(wp==IDOK||wp==IDCANCEL)){EndDialog(w,1);return TRUE;}
 if(m==WM_CLOSE){EndDialog(w,1);return TRUE;}return FALSE;
}
/* Windows 3.0 packed dialog template, generated in memory: one native OK. */
static void word(BYTE FAR **p,unsigned v){*(*p)++=(BYTE)v;*(*p)++=(BYTE)(v>>8);}
static void dword(BYTE FAR **p,DWORD v){word(p,(unsigned)v);word(p,(unsigned)(v>>16));}
static void about(HWND w) {
 HGLOBAL h; BYTE FAR *p; FARPROC proc; DWORD units=GetDialogBaseUnits();
 int bx=LOWORD(units),by=HIWORD(units); char *s;
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,256);if(!h){note(w,"No dialog memory");return;}
 p=(BYTE FAR *)GlobalLock(h);if(!p){GlobalFree(h);note(w,"No dialog memory");return;}
 dword(&p,WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME);*p++=1;
 word(&p,0);word(&p,0);word(&p,148*4/bx);word(&p,122*8/by);
 *p++=0;*p++=0;s="About";while(*s)*p++=*s++;*p++=0;
 word(&p,52*4/bx);word(&p,98*8/by);word(&p,40*4/bx);word(&p,18*8/by);word(&p,IDOK);
 dword(&p,WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON);*p++=0x80;*p++='O';*p++='K';*p++=0;*p++=0;
 GlobalUnlock(h);proc=MakeProcInstance((FARPROC)AboutProc,instance);if(!proc){GlobalFree(h);note(w,"No dialog memory");return;}aboutOpen=1;if(DialogBoxIndirect(instance,h,w,(DLGPROC)proc)==-1)note(w,"Dialog failed");aboutOpen=0;FreeProcInstance(proc);GlobalFree(h);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc; PAINTSTRUCT ps; RECT r; HBRUSH brush,old; char text[32],digits[12]; int x,y,cx,cy,dx,dy;
 switch(m){
 case WM_CREATE:
  buy=CreateWindow("BUTTON","Buy +1 CPS (10)",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,2,2,140,20,w,(HMENU)BUY,instance,NULL);
  if(!buy)return -1L;
  SendMessage(buy,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  if(!SetTimer(w,1,1000,NULL))lstrcpy(status,"Timer failed");return 0;
 case WM_SIZE:
  GetClientRect(w,&r);cx=r.right;cy=r.bottom;
  cookie.left=cx/2-27;cookie.right=cx/2+27;cookie.top=31;cookie.bottom=85;
  MoveWindow(buy,(cx-144)/2,94,144,20,TRUE);refresh(w);return 0;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(0,0,0));
  num(digits,cookies);lstrcpy(text,"Cookies:");lstrcat(text,digits);label(dc,3,3,text);
  num(digits,(long)cps);lstrcpy(text,"CPS:");lstrcat(text,digits);label(dc,3,15,text);
  brush=CreateSolidBrush(RGB(255,255,0));old=SelectObject(dc,brush);Ellipse(dc,cookie.left,cookie.top,cookie.right,cookie.bottom);SelectObject(dc,GetStockObject(BLACK_BRUSH));
  x=cookie.left;y=cookie.top;Ellipse(dc,x+12,y+12,x+17,y+17);Ellipse(dc,x+32,y+11,x+37,y+16);Ellipse(dc,x+23,y+26,x+29,y+32);Ellipse(dc,x+11,y+35,x+16,y+40);Ellipse(dc,x+35,y+36,x+40,y+41);
  SelectObject(dc,old);DeleteObject(brush);label(dc,3,121,status);label(dc,3,134,"Space=click U=buy");EndPaint(w,&ps);return 0;
 case WM_LBUTTONDOWN:
  x=(int)LOWORD(lp);y=(int)HIWORD(lp);dx=x-(cookie.left+27);dy=y-(cookie.top+27);
  if(dx>=-27&&dx<=27&&dy>=-27&&dy<=27&&dx*dx+dy*dy<=729){add();note(w,"Click!");refresh(w);}SetFocus(w);return 0;
 case WM_KEYDOWN:if(wp==VK_SPACE){add();note(w,"Click!");refresh(w);return 0;}if(wp=='U'){SendMessage(w,WM_COMMAND,BUY,0L);return 0;}break;
 case WM_TIMER:if(wp==1&&cps){if(cookies>MAXCOOK-(long)cps)cookies=MAXCOOK;else cookies+=cps;refresh(w);}return 0;
 case WM_COMMAND:
  switch(wp){case BUY:if(cookies>=10&&cps<MAXCPS){cookies-=10;++cps;note(w,"Upgrade bought");refresh(w);}else note(w,cps>=MAXCPS?"CPS limit":"Need 10 cookies");SetFocus(w);break;
  case NEW:cookies=0;cps=0;note(w,"New game");refresh(w);break;
  case SAVE:savegame(w);break;case LOAD:loadgame(w);break;case ABOUT:about(w);break;case QUIT:DestroyWindow(w);break;}return 0;
 case WM_DESTROY:KillTimer(w,1);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc; HWND w; MSG msg; HMENU menu,game,help; int i,n;
 instance=inst;GetModuleFileName(inst,savepath,sizeof(savepath));n=lstrlen(savepath);for(i=n-1;i>=0&&savepath[i]!='\\'&&savepath[i]!=':';i--);savepath[i+1]=0;lstrcat(savepath,"COOKIE.SAV");
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="CookieBench";if(!RegisterClass(&wc))return 1;}
 menu=CreateMenu();game=CreatePopupMenu();help=CreatePopupMenu();
 AppendMenu(game,MF_STRING,NEW,"&New");AppendMenu(game,MF_STRING,SAVE,"&Save");AppendMenu(game,MF_STRING,LOAD,"&Load");AppendMenu(game,MF_SEPARATOR,0,NULL);AppendMenu(game,MF_STRING,QUIT,"E&xit");AppendMenu(help,MF_STRING,ABOUT,"&About");AppendMenu(menu,MF_POPUP,(UINT)game,"&Game");AppendMenu(menu,MF_POPUP,(UINT)help,"&Help");
 w=CreateWindow("CookieBench","Cookie",WS_OVERLAPPEDWINDOW|WS_CLIPCHILDREN,0,0,160,200,NULL,menu,inst,NULL);if(!w)return 2;ShowWindow(w,SW_SHOWMAXIMIZED);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return msg.wParam;
}
