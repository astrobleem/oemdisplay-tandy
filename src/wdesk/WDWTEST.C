/* Actual WDWIN + placement service, with bounded USER mocks. No native claim. */
#include <stdio.h>
#include <string.h>
#include "WDWIN.H"
#include "WTPLACE.H"
#define MAX 40
static struct {RECT normal;int state,visible,changes;LONG style;WORD task;HWND owner;} os[MAX+1];
static HWND order[MAX],active=2;
static unsigned count,checks,failed;
static int failMove,failRestore,autoOwned,failSaved,failGet;
static struct {HWND h;int x,y;UINT flags;} batch[WD_MAXWIN];
static unsigned nbatch;
#define CHECK(x) do {checks++;if(!(x)){failed++;printf("FAIL %d: %s\n",__LINE__,#x);}}while(0)
BOOL IsWindow(HWND h){return h>=1 && h<=MAX;}
HTASK GetWindowTask(HWND h){return os[h].task;}
HWND GetActiveWindow(void){return active;}
HMODULE GetModuleHandle(LPCSTR s){CHECK(!strcmp(s,"USER"));return 1;}
static WORD getSaved(HWND h,LPRECT r,LPPOINT p){
 if(failGet && h==2)return 0;
 if(r)*r=os[h].normal;
 if(p)p->x=p->y=-1;
 return (WORD)(os[h].state+1);
}
static void setSaved(HWND h,WORD show,LPRECT r,LPPOINT p){
 (void)p;CHECK(show==(os[h].visible?SW_SHOWNA:SW_HIDE));
 if(!failSaved)os[h].normal=*r;
}
FARPROC GetProcAddress(HMODULE m,LPCSTR s){
 CHECK(m==1);if(!strcmp(s,"GETINTERNALWINDOWPOS"))return (FARPROC)getSaved;
 CHECK(!strcmp(s,"SETINTERNALWINDOWPOS"));return (FARPROC)setSaved;
}
WORD GetWindowWord(HWND h,int i){(void)h;(void)i;return 7;}
BOOL IsIconic(HWND h){return os[h].state==WTP_ICONIC;}
BOOL IsZoomed(HWND h){return os[h].state==WTP_ZOOMED;}
void GetWindowRect(HWND h,RECT *r){
 if(os[h].state==WTP_NORMAL)*r=os[h].normal;
 else {r->left=5;r->top=180;r->right=35;r->bottom=200;}
}
HWND GetDesktopWindow(void){return 1000;}
HWND GetWindow(HWND h,int c){
 unsigned i;
 if(c==GW_CHILD)return count?order[0]:0;
 if(c==GW_OWNER)return os[h].owner;
 for(i=0;i<count;i++)if(order[i]==h){
  if(c==GW_HWNDPREV)return i?order[i-1]:0;
  if(c==GW_HWNDNEXT)return i+1<count?order[i+1]:0;
 }
 return 0;
}
BOOL ShowWindow(HWND h,int c){CHECK(c==SW_SHOWNOACTIVATE);if(!failRestore)os[h].state=WTP_NORMAL;return 1;}
BOOL IsWindowVisible(HWND h){return os[h].visible;}
LONG GetWindowLong(HWND h,int i){(void)i;return os[h].style;}
HTASK GetCurrentTask(void){return 1;}
int GetClassName(HWND h,char *s,int n){(void)h;if(n<4)return 0;strcpy(s,"App");return 3;}
int GetSystemMetrics(int i){return i==SM_CXSCREEN?640:i==SM_CYSCREEN?256:16;}
void SetWindowPos(HWND h,HWND after,int x,int y,int w,int ht,UINT flags){
 int width,height,dx,dy;unsigned i;(void)after;(void)w;(void)ht;
 CHECK((flags&SWP_NOACTIVATE)!=0);
 if(failMove)return;
 width=os[h].normal.right-os[h].normal.left;height=os[h].normal.bottom-os[h].normal.top;
 if(!(flags&SWP_NOMOVE)){
  dx=x-os[h].normal.left;dy=y-os[h].normal.top;
  if(dx || dy)os[h].changes++;
  os[h].normal.left=(short)x;os[h].normal.top=(short)y;
  os[h].normal.right=(short)(x+width);os[h].normal.bottom=(short)(y+height);
  if(autoOwned)for(i=1;i<=MAX;i++)if(os[i].owner==h && os[i].state==WTP_NORMAL){
   os[i].normal.left=(short)(os[i].normal.left+dx);os[i].normal.right=(short)(os[i].normal.right+dx);
   os[i].normal.top=(short)(os[i].normal.top+dy);os[i].normal.bottom=(short)(os[i].normal.bottom+dy);
   if(dx || dy)os[i].changes++;
  }
 }
}
HDWP BeginDeferWindowPos(int n){CHECK(n<=WD_MAXWIN);nbatch=0;return 1;}
HDWP DeferWindowPos(HDWP d,HWND h,HWND a,int x,int y,int w,int ht,UINT f){
 (void)a;(void)w;(void)ht;CHECK(nbatch<WD_MAXWIN);
 batch[nbatch].h=h;batch[nbatch].x=x;batch[nbatch].y=y;batch[nbatch++].flags=f;return d;
}
void EndDeferWindowPos(HDWP d){unsigned i;(void)d;
 for(i=0;i<nbatch;i++)SetWindowPos(batch[i].h,0,batch[i].x,batch[i].y,0,0,batch[i].flags);
}
static void reset(void){
 unsigned i;memset(os,0,sizeof(os));count=3;failMove=failRestore=autoOwned=failSaved=failGet=0;active=2;
 for(i=1;i<=MAX;i++){
  os[i].normal.left=10;os[i].normal.top=20;os[i].normal.right=130;os[i].normal.bottom=100;
  os[i].visible=1;os[i].style=WS_CAPTION;os[i].task=(WORD)(i==1?1:2);order[i-1]=(HWND)i;
 }
 CHECK(WDWinInitView(2048,2048,320,200)==0);
}
int main(void){
 int x,y;unsigned i;
 reset();CHECK(WDWinPan(100,80)==2);CHECK(os[2].normal.left==-90);
 os[2].state=WTP_ICONIC;os[3].state=WTP_ZOOMED;
 CHECK(WDWinShutdown()==0);CHECK(os[2].state==WTP_ICONIC && os[3].state==WTP_ZOOMED);
 CHECK(os[2].normal.left==10 && os[2].normal.top==20);
 CHECK(os[3].normal.left==10 && active==2);CHECK(WDWinShutdown()==0);
 reset();os[2].state=WTP_ICONIC;os[2].normal.left=-500;os[2].normal.top=-300;
 os[2].normal.right=-380;os[2].normal.bottom=-220;
 CHECK(WDWinHome()>=0);CHECK(os[2].normal.left>=-80 && os[2].normal.top==0);
 CHECK(WDWinShutdown()==0);
 reset();failMove=1;CHECK(WDWinPan(100,80)==WD_E_MOVE);CHECK(os[2].normal.left==10);
 failMove=0;CHECK(WDWinPan(100,80)==2);CHECK(os[2].normal.left==-90 && os[2].normal.top==-60);
 os[2].state=WTP_ICONIC;failSaved=1;CHECK(WDWinShutdown()==WD_E_MOVE);
 WDWinViewport(&x,&y);CHECK(x==0 && y==0);
 failSaved=0;CHECK(WDWinShutdown()==0);CHECK(os[2].normal.left==10 && os[2].normal.top==20);
 reset();CHECK(WDWinPan(100,80)==2);
 /* New foreground windows must not evict previously moved tail windows. */
 count=MAX;for(i=0;i<MAX-3;i++)order[i]=(HWND)(i+4);
 order[MAX-3]=1;order[MAX-2]=2;order[MAX-1]=3;
 CHECK(WDWinPan(120,100)==WD_E_FULL);CHECK(WDWinDropped()==MAX-1-WD_MAXWIN);
 CHECK(WDWinHome()>=0);CHECK(os[2].normal.left==10 && os[2].normal.top==20);
 CHECK(os[3].normal.left==10 && os[3].normal.top==20);
 CHECK(WDWinShutdown()==0);
 reset();os[3].style=0;CHECK(WDWinPan(100,80)==1);CHECK(os[3].normal.left==10);
 CHECK(WDWinShutdown()==0);CHECK(active==2);
 reset();os[2].state=WTP_ICONIC;CHECK(WDWinShutdown()==0);CHECK(os[2].state==WTP_ICONIC);
 reset();CHECK(WDWinPan(100,80)==2);os[2].state=WTP_ICONIC;
 CHECK(WDWinPan(0,0)>=0);CHECK(WDWinShutdown()==0);
 CHECK(os[2].state==WTP_ICONIC && os[2].normal.left==10);
 for(i=0;i<2;i++){
  reset();autoOwned=(int)i;os[3].owner=2;
  os[3].normal.left=40;os[3].normal.top=50;os[3].normal.right=160;os[3].normal.bottom=130;
  order[0]=3;order[1]=2;order[2]=1;
  CHECK(WDWinPan(100,80)==2);
  CHECK(os[3].normal.left-os[2].normal.left==30);
  CHECK(os[3].normal.top-os[2].normal.top==30);
  CHECK(os[2].changes==1 && os[3].changes==1);
  CHECK(WDWinPrepareShutdown()>=0);
  CHECK(WDWinPan(20,20)==2); /* another app cancelled end-session */
  CHECK(WDWinShutdown()==0);
 }
 for(i=0;i<2;i++){
  reset();autoOwned=(int)i;os[3].owner=2;
  os[2].normal.left=400;os[2].normal.right=520;
  os[3].normal.left=-80;os[3].normal.right=40;
  CHECK(WDWinHome()>=0);
  CHECK(os[2].normal.left==280 && os[3].normal.left==-80);
  CHECK(WDWinShutdown()==0);
 }
 reset();CHECK(WDWinPan(100,80)==2);os[2].style=0;
 CHECK(WDWinShutdown()==0);CHECK(os[2].normal.left==10 && os[2].normal.top==20);
 reset();CHECK(WDWinPan(100,80)==2);CHECK(WDWinExclude("App")==0);
 CHECK(WDWinShutdown()==0);CHECK(os[2].normal.left==10 && os[2].normal.top==20);
 reset();CHECK(WDWinPan(100,80)==2);os[2].task=3;os[2].style=0;
 os[2].normal.left=300;os[2].normal.right=420;os[2].changes=0;
 CHECK(WDWinHome()>=0);CHECK(os[2].normal.left==300 && os[2].changes==0);
 CHECK(WDWinShutdown()==0);
 reset();os[2].state=WTP_ICONIC;os[2].visible=0;
 os[2].normal.left=-500;os[2].normal.right=-380;
 CHECK(WDWinReconcile()==0); /* known before hiding is not required for a saved rectangle */
 os[2].visible=1;CHECK(WDWinReconcile()==0);os[2].visible=0;
 CHECK(WDWinHome()>=0);CHECK(!os[2].visible && os[2].state==WTP_ICONIC);
 CHECK(os[2].normal.left>=-80 && active==2);CHECK(WDWinShutdown()==0);
 reset();os[2].state=WTP_ICONIC;failGet=1;
 os[2].normal.left=-500;os[2].normal.right=-380;
 CHECK(WDWinHome()==WD_E_MOVE);CHECK(os[2].normal.left==-500 && os[2].state==WTP_ICONIC);
 failGet=0;CHECK(WDWinHome()>=0);CHECK(os[2].normal.left>=-80);
 CHECK(WDWinShutdown()==0);
 printf("%u adapter checks; %u failures; USER mocks only\n",checks,failed);
 return failed?1:0;
}
