/* XTEyes: original Win16/8086 implementation, inspired by xeyes and WinEyes.
 * No WPF/WinEyes source is reused. See README.TXT and LICENSE.TXT. */
#define WINVER 0x0300
#include <windows.h>
#include "EYES.H"
static HDC eyeDC,pupilDC;
static HBITMAP eyeBM,pupilBM,oldEye,oldPupil;
static int margin;
static int rx,ry=23,px,py=4,cx[2],cy=28,pupilX[2],pupilY[2];
static int lastX=-30000,lastY=-30000;
static void bounds(RECT *r,int x,int y) {
 r->left=x-px;r->right=x+px+1;r->top=y-py;r->bottom=y+py+1;
}
/* L1 normalization stays inside an ellipse, without sqrt or floating point.
 * Clamp before arithmetic: all intermediate products fit signed 16 bits. */
static int offset(int delta,int other,int radius) {
 int a,b;
 if(delta>512)delta=512;if(delta< -512)delta=-512;
 if(other>512)other=512;if(other< -512)other=-512;
 a=delta<0?-delta:delta;b=other<0?-other:other;
 return delta*radius/(a+b+24);
}
static void track(HWND w) {
 POINT p;RECT r,s,screen;int i,x,y,dx,dy;HDC dc;
 if(IsIconic(w)||!IsWindowVisible(w))return;
 GetWindowRect(w,&r);SetRect(&screen,0,0,GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN));
 if(!IntersectRect(&s,&r,&screen))return;
 dc=GetDC(w);i=GetClipBox(dc,&r);ReleaseDC(w,dc);if(i==NULLREGION)return;
 GetCursorPos(&p);ScreenToClient(w,&p);
 if(p.x==lastX&&p.y==lastY)return;lastX=p.x;lastY=p.y;
 for(i=0;i<2;i++){
  dx=p.x-cx[i];dy=p.y-cy;
  x=cx[i]+offset(dx,dy,rx-px-4);y=cy+offset(dy,dx,ry-py-4);
  if(x==pupilX[i]&&y==pupilY[i])continue;
  bounds(&r,pupilX[i],pupilY[i]);
  pupilX[i]=x;pupilY[i]=y;
  dc=GetDC(w);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));
  BitBlt(dc,x-px,y-py,px*2+1,py*2+1,pupilDC,0,0,SRCCOPY);ReleaseDC(w,dc);
 }
}
long FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 PAINTSTRUCT ps;RECT r;HDC dc;int i;
 switch(m){
 case WM_CREATE:
  GetClientRect(w,&r);margin=(r.right-(4*rx+15))/2;cx[0]+=margin;cx[1]+=margin;pupilX[0]+=margin;pupilX[1]+=margin;
  AppendMenu(GetSystemMenu(w,FALSE),MF_SEPARATOR,0,NULL);
  AppendMenu(GetSystemMenu(w,FALSE),MF_STRING,100,"About XTEyes...");
  if(!SetTimer(w,1,125,NULL)){MessageBox(w,"No timer available.","XTEyes",MB_OK);return -1;}
  return 0;
 case WM_SYSCOMMAND:
  if(wp==100){MessageBox(w,"XTEyes 1.0\nWindows 3.0 / 8088\n\nInspired by xeyes and\nWinEyes (Michael Duerr).\nOriginal Win16 implementation.\nMIT license; see README.TXT.","About XTEyes",MB_OK);return 0;}break;
 case WM_TIMER:track(w);return 0;
 case WM_MOVE:lastX=-30000;track(w);return 0;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);GetClientRect(w,&r);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));
  BitBlt(dc,margin,0,4*rx+15,57,eyeDC,0,0,SRCCOPY);
  for(i=0;i<2;i++)BitBlt(dc,pupilX[i]-px,pupilY[i]-py,px*2+1,py*2+1,pupilDC,0,0,SRCCOPY);
  EndPaint(w,&ps);return 0;
 case WM_DESTROY:KillTimer(w,1);PostQuitMessage(0);return 0;
 }
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE h,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;RECT r;int sw;HDC dc;BYTE *eb,*pb;
 sw=GetSystemMetrics(SM_CXSCREEN);rx=sw<240?12:(sw<480?19:29);px=rx/4;
 eb=rx==12?eyes12:(rx==19?eyes19:eyes29);pb=rx==12?pupil12:(rx==19?pupil19:pupil29);
 eyeBM=CreateBitmap(4*rx+16,57,1,1,eb);pupilBM=CreateBitmap(px*2+1,9,1,1,pb);
 dc=GetDC(NULL);eyeDC=CreateCompatibleDC(dc);pupilDC=CreateCompatibleDC(dc);ReleaseDC(NULL,dc);
 if(!eyeBM||!pupilBM||!eyeDC||!pupilDC)goto cleanup;
 oldEye=SelectObject(eyeDC,eyeBM);oldPupil=SelectObject(pupilDC,pupilBM);
 cx[0]=rx+5;cx[1]=3*rx+10;pupilX[0]=cx[0];pupilX[1]=cx[1];pupilY[0]=pupilY[1]=cy;
 if(!prev){wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=h;wc.hIcon=LoadIcon(NULL,IDI_APPLICATION);wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="XTEyes";if(!RegisterClass(&wc))goto cleanup;}
 SetRect(&r,0,0,4*rx+15,57);AdjustWindowRect(&r,WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,FALSE);
 w=CreateWindow("XTEyes","XTEyes",WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,4,24,r.right-r.left,r.bottom-r.top,NULL,NULL,h,NULL);
 if(!w)goto cleanup;ShowWindow(w,show);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
cleanup:
 if(oldEye)SelectObject(eyeDC,oldEye);if(oldPupil)SelectObject(pupilDC,oldPupil);
 if(eyeDC)DeleteDC(eyeDC);if(pupilDC)DeleteDC(pupilDC);
 if(eyeBM)DeleteObject(eyeBM);if(pupilBM)DeleteObject(pupilBM);return 0;
}
