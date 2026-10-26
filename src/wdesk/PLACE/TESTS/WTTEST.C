/* Actual placement service, bounded USER mocks. No native evidence here. */
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "WTPLACE.H"
static struct {int state;WORD task,instance;RECT normal;HWND previous;} win;
static int failRect,failMove,checks,failures,saved,visible,readCalls,writeCalls,gone;
static HWND active;
static int title,raiseGroup,failStack;
static HWND titlePrevious;
#define CHECK(x) do {checks++;if(!(x)){failures++;printf("FAIL line %d: %s\n",__LINE__,#x);}}while(0)
BOOL IsWindow(HWND h){return (h==2 || h==3 || h==5 || (h==4 && title)) && !gone;}
HTASK GetWindowTask(HWND h){(void)h;return win.task;}
WORD GetWindowWord(HWND h,int i){(void)h;(void)i;return win.instance;}
BOOL IsIconic(HWND h){(void)h;return win.state==WTP_ICONIC;}
BOOL IsZoomed(HWND h){(void)h;return win.state==WTP_ZOOMED;}
BOOL IsWindowVisible(HWND h){return h==5?0:h==3?1:visible;}
LONG GetWindowLong(HWND h,int i){(void)i;return (h==4 || h==5)?0:WS_CAPTION;}
HWND GetActiveWindow(void){return active;}
void GetWindowRect(HWND h,RECT *r){
 (void)h;if(failRect){gone=1;return;}
 if(win.state==WTP_NORMAL)*r=win.normal;
 else {r->left=1;r->top=180;r->right=31;r->bottom=200;}
}
HWND GetWindow(HWND h,int c){
 if(c==GW_OWNER)return (HWND)(h==4?2:0);
 CHECK(c==GW_HWNDPREV);return h==4?titlePrevious:h==5?3:h==3?0:win.previous;
}
HMODULE GetModuleHandle(LPCSTR s){CHECK(!strcmp(s,"USER"));return 1;}
static WORD getSaved(HWND h,LPRECT r,LPPOINT point){
 (void)h;readCalls++;
 if(r)*r=win.normal;
 if(point)point->x=point->y=-1;
 return (WORD)(win.state+1);
}
static void setSaved(HWND h,WORD show,LPRECT r,LPPOINT point){
 (void)h;(void)point;writeCalls++;CHECK(show==(visible?SW_SHOWNA:SW_HIDE));
 if(!failMove)win.normal=*r;
 if(title){titlePrevious=raiseGroup?0:win.previous;win.previous=4;}
}
FARPROC GetProcAddress(HMODULE m,LPCSTR s){
 CHECK(m==1);if(!saved)return 0;
 if(!strcmp(s,"GETINTERNALWINDOWPOS"))return (FARPROC)getSaved;
 CHECK(!strcmp(s,"SETINTERNALWINDOWPOS"));return (FARPROC)setSaved;
}
void SetWindowPos(HWND h,HWND after,int x,int y,int w,int ht,UINT f){
 int oldw,oldh;(void)h;(void)after;
 CHECK((f&SWP_NOACTIVATE)!=0);
 if(failMove)return;
 if(!(f&SWP_NOZORDER)){
  if(failStack)return;
  CHECK((f&(SWP_NOMOVE|SWP_NOSIZE))==(SWP_NOMOVE|SWP_NOSIZE));
  if(win.previous==4)titlePrevious=after;else win.previous=after;
 }
 if(f&SWP_NOMOVE)return;
 oldw=win.normal.right-win.normal.left;oldh=win.normal.bottom-win.normal.top;
 win.normal.left=(short)x;win.normal.top=(short)y;
 win.normal.right=(short)(x+((f&SWP_NOSIZE)?oldw:w));
 win.normal.bottom=(short)(y+((f&SWP_NOSIZE)?oldh:ht));
}
static void reset(void){
 memset(&win,0,sizeof(win));win.task=5;win.instance=6;win.previous=3;
 win.normal.left=-200;win.normal.top=-100;win.normal.right=-80;win.normal.bottom=-20;
 failRect=failMove=readCalls=writeCalls=gone=title=raiseGroup=failStack=0;saved=visible=1;active=3;titlePrevious=0;
}
int main(void){
 WTPLACEMENT p;RECT target;int state,hidden;
 for(state=WTP_NORMAL;state<=WTP_ZOOMED;state++)for(hidden=0;hidden<2;hidden++){
  reset();win.state=state;visible=!hidden;
  CHECK(WTPlaceAvailable());CHECK(WTPlaceInit(2,&p)==0);CHECK(p.flags==0);
  CHECK(WTPlaceGet(2,&p)==0);CHECK(p.state==state && (p.flags&WTP_KNOWN));
  CHECK(p.normal.left==-200 && p.normal.top==-100);
  CHECK((p.flags&WTP_SAVED)==(state==WTP_NORMAL?0:WTP_SAVED));
  target.left=20;target.top=30;target.right=target.bottom=0;
  CHECK(WTPlaceSetNormal(2,&p,&target,WTP_MOVE_ONLY)==0);
  CHECK(p.state==state && p.normal.left==20 && p.normal.top==30);
  CHECK(p.normal.right==140 && p.normal.bottom==110);
  CHECK(active==3 && win.previous==3 && visible==!hidden);
  target.left=25;target.top=35;target.right=100;target.bottom=90;
  CHECK(WTPlaceSetNormal(2,&p,&target,0)==0);
  CHECK(p.normal.left==25 && p.normal.right==100 && p.normal.bottom==90);
  failMove=1;target.left=30;CHECK(WTPlaceSetNormal(2,&p,&target,0)==WTP_E_MOVE);
  CHECK(p.normal.left==25 && p.state==state && active==3);
  win.task++;saved=0;CHECK(WTPlaceGet(2,&p)==0);
  CHECK((p.flags&WTP_KNOWN)==(state==WTP_NORMAL?WTP_KNOWN:0));
 }
 reset();saved=0;win.state=WTP_ICONIC;CHECK(!WTPlaceAvailable());
 CHECK(WTPlaceInit(2,&p)==0);CHECK(WTPlaceGet(2,&p)==0 && p.flags==0);
 CHECK(WTPlaceSetNormal(2,&p,&target,WTP_MOVE_ONLY)==WTP_E_UNSUPPORTED);
 CHECK(win.state==WTP_ICONIC && active==3 && !writeCalls);
 win.state=WTP_NORMAL;CHECK(WTPlaceGet(2,&p)==0);
 win.state=WTP_ICONIC;CHECK(WTPlaceGet(2,&p)==0);
 CHECK((p.flags&WTP_KNOWN) && !(p.flags&WTP_SAVED) && p.normal.left==-200);
 win.instance++;CHECK(WTPlaceGet(2,&p)==0 && p.flags==0);
 reset();CHECK(WTPlaceInit(2,&p)==0);failRect=1;
 CHECK(WTPlaceGet(2,&p)==WTP_E_WINDOW);
 gone=0;p.size=0;CHECK(WTPlaceGet(2,&p)==WTP_E_ARG);
 CHECK(WTPlaceInit(0,&p)==WTP_E_WINDOW && p.task==0 && p.instance==0);
 CHECK(WTPlaceInit(2,0)==WTP_E_ARG);CHECK(WTPlaceInit(2,&p)==0);
 target.left=10;target.right=10;target.top=20;target.bottom=30;
 CHECK(WTPlaceSetNormal(2,&p,&target,0)==WTP_E_ARG);
 CHECK(WTPlaceSetNormal(2,&p,&target,2)==WTP_E_ARG);
 win.state=WTP_ICONIC;CHECK(WTPlaceGet(2,&p)==0);
 target.left=32760;CHECK(WTPlaceSetNormal(2,&p,&target,WTP_MOVE_ONLY)==WTP_E_ARG);
 CHECK(!writeCalls && win.normal.left==-200);
 for(state=0;state<2;state++){
  reset();title=1;raiseGroup=state;win.state=WTP_ZOOMED;
  CHECK(WTPlaceInit(2,&p)==0);target.left=20;target.top=30;
  CHECK(WTPlaceSetNormal(2,&p,&target,WTP_MOVE_ONLY)==0);
  CHECK(win.previous==4 && titlePrevious==3 && p.state==WTP_ZOOMED && active==3);
 }
 reset();title=raiseGroup=1;win.state=WTP_ICONIC;win.previous=5;
 CHECK(WTPlaceInit(2,&p)==0);target.left=20;target.top=30;
 CHECK(WTPlaceSetNormal(2,&p,&target,WTP_MOVE_ONLY)==0);
 CHECK(win.previous==4 && titlePrevious==5 && p.state==WTP_ICONIC && active==3);
 reset();title=raiseGroup=failStack=1;win.state=WTP_ICONIC;
 CHECK(WTPlaceInit(2,&p)==0);target.left=20;target.top=30;
 CHECK(WTPlaceSetNormal(2,&p,&target,WTP_MOVE_ONLY)==WTP_E_MOVE);
 CHECK(p.state==WTP_ICONIC && p.normal.left==20 && active==3);
 printf("%d checks; %d failures; sizeof(WTPLACEMENT)=%u; host mocks only\n",checks,failures,(unsigned)sizeof(p));
 return failures?1:0;
}
