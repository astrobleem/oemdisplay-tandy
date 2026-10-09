/* Host fixture for actual TSHELL popup and deferred-dispatch functions. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned UINT;typedef unsigned short WORD;typedef int HWND;
typedef int HMENU;typedef int HDC;typedef int HFONT;
typedef struct {int top;} RECT;
typedef struct {int tmHeight;} TEXTMETRIC;
#define NULLMENU 0
#define MF_STRING 0
#define MF_SEPARATOR 0x800
#define MF_POPUP 0x10
#define MF_GRAYED 1
#define MF_BYPOSITION 0x400
#define SM_CYBORDER 1
#define SM_CYMENU 2
#define SYSTEM_FONT 3
#define TPM_LEFTBUTTON 0
#define WM_COMMAND 0x111
#define WM_USER 0x400
/* DEFINES */
static int width,shellMode,systemQueued,active,focus,holds,done,tracked;
static int nextmenu,failcreate,selectsettings,queued,alive[12],counts[12];
static int ys[12],trackmenus[12],dcok=1,metricok=1;
static UINT ids[12][20],flags[12][20];
static char paths[1][144]={{0}};static char *names[]={"Program Mgr"};
static void dispatch(HWND w,UINT m,UINT wp);
static void TSSaverHold(int h){holds+=h?1:-1;assert(holds>=0);}
static void TandyHoldMenuDone(int d){done=d;}
static void findapps(void){}
static int BringWindowToTop(HWND w){(void)w;return 1;}
static HWND SetActiveWindow(HWND w){active=w;return w;}
static HWND GetActiveWindow(void){return active;}
static HWND SetFocus(HWND w){focus=w;return w;}
static HMENU CreatePopupMenu(void){nextmenu++;if(nextmenu==failcreate)return 0;alive[nextmenu]=1;return nextmenu;}
static int AppendMenu(HMENU m,UINT f,UINT id,const char *s)
{int n=counts[m]++;(void)s;assert(n<20);ids[m][n]=id;flags[m][n]=f;return 1;}
static int GetMenuItemCount(HMENU m){return counts[m];}
static WORD GetMenuState(HMENU m,int i,UINT f){assert(f==MF_BYPOSITION);return (WORD)flags[m][i];}
static int GetSystemMetrics(int n){return n==SM_CYBORDER?1:12;}
static HDC GetDC(HWND w){(void)w;return dcok;}
static int GetStockObject(int n){assert(n==SYSTEM_FONT);return 1;}
static int SelectObject(HDC d,int o){(void)d;(void)o;return 1;}
static int GetTextMetrics(HDC d,TEXTMETRIC *t){(void)d;t->tmHeight=8;return metricok;}
static int ReleaseDC(HWND w,HDC d){(void)w;(void)d;return 1;}
static void GetWindowRect(HWND w,RECT *r){assert(w==1);r->top=178;}
static int PostMessage(HWND w,UINT m,UINT wp,long lp)
{assert(w==1&&m==OPENSYSTEM&&wp==0&&lp==0);queued++;return 1;}
static void TSControlMenu(HMENU m)
{int i;AppendMenu(m,MF_STRING,59,"Control Panel");AppendMenu(m,MF_SEPARATOR,0,0);
 for(i=0;i<10;i++)AppendMenu(m,MF_STRING,60+i,"Applet");}
static int TrackPopupMenu(HMENU m,UINT f,int x,int y,int reserved,HWND w,void *rect)
{assert(f==0&&x==0&&reserved==0&&w==1&&rect==0);trackmenus[tracked]=m;ys[tracked++]=y;
 if(selectsettings){selectsettings=0;dispatch(w,WM_COMMAND,SETTINGSMENU);assert(tracked==1);assert(alive[m]);}
 return 1;}
static int DestroyMenu(HMENU m)
{int i;assert(alive[m]);alive[m]=0;for(i=0;i<counts[m];i++)if(flags[m][i]&MF_POPUP)alive[ids[m][i]]=0;return 1;}
/* PRODUCTION */
static void dispatch(HWND w,UINT m,UINT wp)
{switch(m){
/* DISPATCH */
 default:break;}}
static void reset(int pixels)
{width=pixels;shellMode=systemQueued=active=focus=holds=done=tracked=0;
 nextmenu=failcreate=selectsettings=queued=0;dcok=metricok=1;
 memset(alive,0,sizeof(alive));memset(counts,0,sizeof(counts));}
static int finditem(HMENU m,UINT id)
{int i;for(i=0;i<counts[m];i++)if(ids[m][i]==id)return i;return -1;}
int main(void)
{
 int i,m;
 reset(160);selectsettings=1;popup(1);
 assert(tracked==1&&systemQueued==2&&queued==1&&!alive[1]&&!holds&&done==0);
 assert(finditem(1,SETTINGSMENU)>=0&&!(flags[1][finditem(1,SETTINGSMENU)]&MF_POPUP));
 dispatch(1,OPENSYSTEM,0);assert(tracked==2&&!systemQueued&&!holds&&done==1&&focus==1);
 m=trackmenus[1];assert(counts[m]==14&&ys[1]>=0&&ys[1]+popupheight(1,m)<=200);
 assert(finditem(m,SAVERSETUP)>=0&&finditem(m,CP_OPEN)>=0);
 for(i=0;i<10;i++)assert(finditem(m,CP_FIRST+i)>=0);
 reset(160);popup(1);assert(tracked==1&&!systemQueued&&!holds&&done==1);
 reset(160);dispatch(1,WM_COMMAND,SETTINGSMENU);active=9;dispatch(1,OPENSYSTEM,0);
 assert(!tracked&&!systemQueued&&done==1&&!holds);
 reset(160);failcreate=1;settingspopup(1);assert(!tracked&&!holds&&done==1);
 reset(640);popup(1);assert(tracked==1&&finditem(1,SETTINGSMENU)<0);
 assert(counts[3]==14&&(flags[1][4]&MF_POPUP));
 reset(320);popup(1);assert(nextmenu==3);
 reset(319);popup(1);assert(nextmenu==1&&finditem(1,SETTINGSMENU)>=0);
 reset(640);failcreate=3;popup(1);assert(tracked==1&&!holds&&done==1);
 reset(160);dcok=0;settingspopup(1);assert(!holds&&ys[0]>=0&&ys[0]+popupheight(1,1)<=200);
 puts("PASS: actual narrow/wide popup composition, deferred Settings dispatch, cancellation/focus guard, sizing and menu allocation failures");return 0;
}
