/* THE BRIGHTER TOMORROW INITIATIVE. Windows 3.0 / 8088. */
#define WINVER 0x0300
#include <windows.h>
#include "ENGINE.H"
#define FIRST 100
static HINSTANCE instance;
static HWND buttons[3];
static GAME game;
static int cx,cy,fw,fh,bodytop,buttony,buttonh;
static char *names[3]={"PRODUCTIVITY","MORALE","BRIGHTNESS"};
static void number(char *s,int n) {
 char tmp[6];int i=0,j=0;
 if(n<0){s[j++]='-';n=-n;}
 do{tmp[i++]=(char)('0'+n%10);n/=10;}while(n);
 while(i)s[j++]=tmp[--i];s[j]=0;
}
static void text(HDC dc,int x,int y,char *s) {TextOut(dc,x,y,s,lstrlen(s));}
static void line(HDC dc,int x,int y,int xx,int yy) {MoveTo(dc,x,y);LineTo(dc,xx,yy);}
static void UpdateButtons(HWND w) {
 int i,n;char *s;
 n=game.phase==PLAYING?events[game.event].count:(game.phase==RECEIPT?1:2);
 for(i=0;i<3;++i) {
  if(i<n) {
   s=game.phase==PLAYING?events[game.event].choice[i].label:
     (game.phase==RECEIPT?"Continue":(i==0?"Restart":"Exit"));
   SetWindowText(buttons[i],s);ShowWindow(buttons[i],SW_SHOW);
  } else ShowWindow(buttons[i],SW_HIDE);
 }
 SetFocus(buttons[0]);InvalidateRect(w,NULL,TRUE);
}
static void Layout(HWND w) {
 HDC dc;TEXTMETRIC tm;RECT r;int i,left,width;
 dc=GetDC(w);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
 GetTextMetrics(dc,&tm);ReleaseDC(w,dc);fw=tm.tmAveCharWidth;fh=tm.tmHeight;
 GetClientRect(w,&r);cx=r.right;cy=r.bottom;
 buttonh=fh+7;buttony=cy-3*(buttonh+2)-2;
 left=4;width=cx-8;if(width>240){width=240;left=(cx-width)/2;}
 for(i=0;i<3;++i)MoveWindow(buttons[i],left,buttony+i*(buttonh+2),width,buttonh,TRUE);
 bodytop=3*fh+8+3*(fh+2)+fh+4;
}
static void Act(HWND w,int n) {
 if(game.phase==PLAYING) {if(!Choose(&game,n))return;}
 else if(game.phase==RECEIPT) {if(n!=0)return;ContinueGame(&game);}
 else if(n==0)ResetGame(&game);
 else if(n==1){DestroyWindow(w);return;}else return;
 UpdateButtons(w);
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp) {
 HDC dc;PAINTSTRUCT ps;RECT r;int i,y,gx,gw,fill;char s[80],n[8];char *body;
 switch(m) {
 case WM_CREATE:
  for(i=0;i<3;++i){
   buttons[i]=CreateWindow("BUTTON","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,
       0,0,1,1,w,(HMENU)(FIRST+i),instance,NULL);
   if(!buttons[i])return -1L;
   SendMessage(buttons[i],WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
  }
  Layout(w);UpdateButtons(w);return 0;
 case WM_SIZE: Layout(w);InvalidateRect(w,NULL,TRUE);return 0;
 case WM_COMMAND:
  if(wp>=FIRST&&wp<FIRST+3&&HIWORD(lp)==BN_CLICKED)Act(w,(int)wp-FIRST);
  return 0;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
  SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(0,0,0));
  /* A 20-pixel rising sun: line art only, no bitmap or color dependency. */
  SelectObject(dc,GetStockObject(BLACK_PEN));SelectObject(dc,GetStockObject(WHITE_BRUSH));
  Ellipse(dc,7,8,21,22);r.left=4;r.top=16;r.right=24;r.bottom=24;
  FillRect(dc,&r,GetStockObject(WHITE_BRUSH));line(dc,3,16,25,16);
  line(dc,14,2,14,6);line(dc,3,7,7,10);line(dc,21,9,25,6);
  text(dc,29,1,"BRIGHTER");text(dc,29,fh+1,"TOMORROW");text(dc,29,2*fh+1,"INITIATIVE");
  y=3*fh+8;
  for(i=0;i<3;++i) {
   lstrcpy(s,names[i]);lstrcat(s,":");number(n,game.value[i]);
   while(lstrlen(s)<13)lstrcat(s," ");lstrcat(s,n);lstrcat(s,"%");
   text(dc,4,y,s);
   gx=4+18*fw;gw=cx-gx-5;if(gw>100)gw=100;
   if(gw>12){Rectangle(dc,gx,y+1,gx+gw,y+fh-1);fill=(gw-4)*game.value[i]/100;
    r.left=gx+2;r.top=y+3;r.right=gx+2+fill;r.bottom=y+fh-3;
    if(fill>0&&r.bottom>r.top)FillRect(dc,&r,GetStockObject(BLACK_BRUSH));}
   y+=fh+2;
  }
  line(dc,3,y,cx-3,y);y+=3;
  if(game.phase< SUCCESS) {
   lstrcpy(s,game.phase==PLAYING?"NOTICE ":"RECORDED ");number(n,game.event+1);
   lstrcat(s,n);lstrcat(s,"/5");
   body=game.phase==PLAYING?events[game.event].text:events[game.event].choice[game.picked].receipt;
  } else {
   lstrcpy(s,game.phase==SUCCESS?"TARGETS ACHIEVED":"REVIEW COMPLETE");
   body=game.phase==SUCCESS?"TOMORROW HAS BEEN\nBRIGHTENED. YOUR\nPARTICIPATION WAS\nALWAYS VOLUNTARY.":"YOUR PARTICIPATION\nIN TOMORROW HAS\nBEEN DISCONTINUED.\nHAVE A BRIGHT DAY.";
  }
  text(dc,4,y,s);r.left=4;r.top=bodytop;r.right=cx-4;r.bottom=buttony-2;
  DrawText(dc,body,-1,&r,DT_LEFT|DT_NOPREFIX);
  EndPaint(w,&ps);return 0;
 case WM_CLOSE:DestroyWindow(w);return 0;
 case WM_DESTROY:PostQuitMessage(0);return 0;
 }
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show) {
 WNDCLASS wc;HWND w;MSG msg;int sw,sh,width,i;
 instance=inst;ResetGame(&game);
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;
 wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;
 wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);
 wc.lpszMenuName=NULL;wc.lpszClassName="BrighterTomorrow";
 if(!RegisterClass(&wc))return 1;}
 sw=GetSystemMetrics(SM_CXSCREEN);sh=GetSystemMetrics(SM_CYSCREEN);width=sw;if(width>360)width=360;
 w=CreateWindow("BrighterTomorrow",sw<300?"BRIGHTER":"BRIGHTER TOMORROW INITIATIVE",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_CLIPCHILDREN,
 (sw-width)/2,0,width,sh>240?240:sh,NULL,NULL,inst,NULL);
 if(!w)return 2;ShowWindow(w,SW_SHOW);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)) {
  if(msg.message==WM_KEYDOWN&&msg.wParam==VK_RETURN) {
   if(!(HIWORD(msg.lParam)&0x4000))
    for(i=0;i<3;++i)if(GetFocus()==buttons[i]){Act(w,i);break;}
  }
  else if(msg.message==WM_KEYDOWN&&msg.wParam>='1'&&msg.wParam<='3') {
   if(game.phase==PLAYING && !(HIWORD(msg.lParam)&0x4000))Act(w,(int)msg.wParam-'1');
  }
  else if(!IsDialogMessage(w,&msg)){TranslateMessage(&msg);DispatchMessage(&msg);}
 }
 return msg.wParam;
}
