#define WINVER 0x0300
#include <windows.h>
#include "PHYSICS.H"
static int ox,oy=17,paused,lmask,rmask;
static HDC board;
static HBITMAP boardbits,oldbits;
static void line(HDC d,int x,int y,int xx,int yy){MoveTo(d,ox+x,oy+y);LineTo(d,ox+xx,oy+yy);}
static void text(HDC d,int x,int y,char *s){TextOut(d,x,y,s,lstrlen(s));}
static void number(char *s,long n){char t[12];int i=0,j=0;do{t[i++]=(char)('0'+n%10);n/=10;}while(n);while(i)s[j++]=t[--i];s[j]=0;}
static void setup(HDC d){
 SelectObject(d,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(d,TRANSPARENT);
 SetTextColor(d,RGB(255,255,255));SetBkColor(d,RGB(0,0,0));
 SelectObject(d,GetStockObject(WHITE_PEN));SelectObject(d,GetStockObject(BLACK_BRUSH));
}
static void table(HDC d){int i;
 setup(d);line(d,5,132,5,5);line(d,5,5,139,5);line(d,139,5,139,132);
 line(d,5,85,33,113);line(d,139,85,111,113);
 for(i=0;i<3;++i){Ellipse(d,ox+bumpx[i]-8,oy+bumpy[i]-8,ox+bumpx[i]+9,oy+bumpy[i]+9);Ellipse(d,ox+bumpx[i]-3,oy+bumpy[i]-3,ox+bumpx[i]+4,oy+bumpy[i]+4);}
 text(d,ox,oy+138,"Z / flip Space go");
}
static void freeboard(void){if(board){SelectObject(board,oldbits);DeleteDC(board);DeleteObject(boardbits);board=NULL;boardbits=NULL;}}
static void cache(HWND w,HDC d){RECT r;
 if(board)return;GetClientRect(w,&r);board=CreateCompatibleDC(d);if(!board)return;
 boardbits=CreateCompatibleBitmap(d,r.right,r.bottom);
 if(!boardbits){DeleteDC(board);board=NULL;return;}
 oldbits=SelectObject(board,boardbits);
 if(!oldbits){DeleteDC(board);DeleteObject(boardbits);board=NULL;boardbits=NULL;return;}
 if(!PatBlt(board,0,0,r.right,r.bottom,BLACKNESS)){freeboard();return;}
 table(board);
}
static void paint(HWND w,HDC d,RECT *r){char s[32],n[12];
 cache(w,d);
 if(!board||!BitBlt(d,r->left,r->top,r->right-r->left,r->bottom-r->top,board,r->left,r->top,SRCCOPY)){PatBlt(d,r->left,r->top,r->right-r->left,r->bottom-r->top,BLACKNESS);table(d);}
 setup(d);
 if(r->top<17){number(n,score);lstrcpy(s,"S:");lstrcat(s,n);text(d,ox+1,1,s);
  number(n,(long)balls);lstrcpy(s,"B:");lstrcat(s,n);text(d,ox+112,1,s);}
 if(r->bottom>oy+98&&r->top<oy+127){
  line(d,33,113,63,121-la*4);line(d,33,114,63,122-la*4);
  line(d,111,113,81,121-ra*4);line(d,111,114,81,122-ra*4);}
 /* Tiny square ball: two-dimensional GDI primitive, no ellipse scan conversion. */
 PatBlt(d,ox+bx/Q-2,oy+by/Q-2,5,5,WHITENESS);
 if(!live&&r->bottom>oy+90&&r->top<oy+105)text(d,ox+16,oy+90,balls?"SPACE launch":"SPACE new game");
 if(paused&&r->bottom>oy+80&&r->top<oy+95)text(d,ox+32,oy+80,"P: resume");
}
static void dirty(HWND w,int x,int y){RECT r;r.left=ox+x/Q-5;r.right=r.left+11;r.top=oy+y/Q-5;r.bottom=r.top+11;InvalidateRect(w,&r,TRUE);}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){
 HDC d;PAINTSTRUCT ps;RECT r;int x,y,l,rr,b;long sc;
 switch(m){
 case WM_CREATE:reset();if(!SetTimer(w,1,55,NULL))return -1L;return 0;
 case WM_SIZE:freeboard();GetClientRect(w,&r);ox=(r.right-144)/2;InvalidateRect(w,NULL,FALSE);return 0;
 case WM_ERASEBKGND:return 1L;
 case WM_PAINT:d=BeginPaint(w,&ps);paint(w,d,&ps.rcPaint);EndPaint(w,&ps);return 0;
 case WM_KEYDOWN:
  if(wp=='Z')lmask|=1;if(wp==VK_LEFT)lmask|=2;
  if(wp==191)rmask|=1;if(wp==VK_RIGHT)rmask|=2;
  leftkey=lmask!=0;rightkey=rmask!=0;
  if(wp==VK_SPACE&&!live){if(!balls){reset();lmask=rmask=0;}launch();InvalidateRect(w,NULL,TRUE);}
  if(wp=='P'&&!(lp&0x40000000L)){paused=!paused;InvalidateRect(w,NULL,TRUE);}
  return 0;
 case WM_KEYUP:
  if(wp=='Z')lmask&=~1;if(wp==VK_LEFT)lmask&=~2;
  if(wp==191)rmask&=~1;if(wp==VK_RIGHT)rmask&=~2;
  leftkey=lmask!=0;rightkey=rmask!=0;return 0;
 case WM_KILLFOCUS:lmask=rmask=leftkey=rightkey=0;paused=1;InvalidateRect(w,NULL,TRUE);return 0;
 case WM_TIMER:
  if(paused||IsIconic(w))return 0;
  x=bx;y=by;l=la;rr=ra;b=balls;sc=score;step();
  if(x!=bx||y!=by){dirty(w,x,y);dirty(w,bx,by);}
  if(l!=la||rr!=ra){r.left=ox+26;r.right=ox+118;r.top=oy+98;r.bottom=oy+127;InvalidateRect(w,&r,TRUE);}
  if(sc!=score){r.left=0;r.right=ox+112;r.top=0;r.bottom=17;InvalidateRect(w,&r,TRUE);}
  if(b!=balls)InvalidateRect(w,NULL,TRUE);return 0;
 case WM_DESTROY:freeboard();KillTimer(w,1);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG msg;int width=156,height=198;
 if(!prev){wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(BLACK_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="TinyPinball";if(!RegisterClass(&wc))return 1;}
 w=CreateWindow("TinyPinball","Pinball",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,(GetSystemMetrics(SM_CXSCREEN)-width)/2,0,width,height,NULL,NULL,inst,NULL);
 if(!w)return 2;ShowWindow(w,show);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return (int)msg.wParam;
}
