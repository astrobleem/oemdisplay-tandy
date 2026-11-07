"""Compile the production popup tracker against a deterministic Win3 shim."""
from pathlib import Path
import argparse,subprocess,os
p=argparse.ArgumentParser();p.add_argument('--cc',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parent.parent;O=a.out.resolve();O.mkdir(exist_ok=True,parents=True)
def save(n,s):(O/n).write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
save('windows.h',r'''
#ifndef MENU_HOST
#define MENU_HOST
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define FAR
#define PASCAL
typedef unsigned UINT,WORD,WPARAM;
typedef long LONG,LPARAM;
typedef unsigned long DWORD;
typedef int HWND,HMENU,HDC,HFONT,HBRUSH,HINSTANCE,BOOL;
typedef struct {int x,y;} POINT;
typedef struct {int left,top,right,bottom;} RECT;
typedef struct {int tmHeight;} TEXTMETRIC;
typedef struct {RECT rcPaint;} PAINTSTRUCT;
typedef struct {HWND hwnd;UINT message;WPARAM wParam;LPARAM lParam;} MSG;
typedef struct {int style;LONG (*lpfnWndProc)(HWND,UINT,WPARAM,LPARAM);int cbClsExtra,cbWndExtra;HINSTANCE hInstance;int hIcon,hCursor;HBRUSH hbrBackground;char *lpszMenuName,*lpszClassName;} WNDCLASS;
#define FALSE 0
#define TRUE 1
#define LOWORD(x) ((unsigned)(x)&65535)
#define HIWORD(x) (((unsigned long)(x)>>16)&65535)
#define MF_POPUP 16
#define MF_GRAYED 1
#define MF_DISABLED 2
#define MF_SEPARATOR 0x800
#define MF_BYPOSITION 0x400
#define SYSTEM_FONT 13
#define BLACK_BRUSH 4
#define GRAY_BRUSH 2
#define COLOR_MENU 4
#define COLOR_MENUTEXT 7
#define COLOR_GRAYTEXT 17
#define COLOR_HIGHLIGHT 13
#define COLOR_HIGHLIGHTTEXT 14
#define TRANSPARENT 1
#define WM_PAINT 15
#define WM_MOUSEACTIVATE 33
#define MA_NOACTIVATE 3
#define WM_INITMENUPOPUP 279
#define WM_COMMAND 273
#define WM_KEYDOWN 256
#define WM_SYSKEYDOWN 260
#define WM_LBUTTONDOWN 513
#define WM_LBUTTONUP 514
#define WM_MOUSEMOVE 512
#define WM_RBUTTONDOWN 516
#define VK_ESCAPE 27
#define VK_LEFT 37
#define VK_RIGHT 39
#define VK_UP 38
#define VK_DOWN 40
#define VK_HOME 36
#define VK_END 35
#define VK_RETURN 13
#define VK_MENU 18
#define VK_TAB 9
#define GWW_HINSTANCE 0
#define WS_POPUP 0
#define WS_CLIPSIBLINGS 0x04000000L
#define SW_SHOWNOACTIVATE 4
#define SWP_NOMOVE 2
#define SWP_NOSIZE 1
#define SWP_NOACTIVATE 16
#define IDC_ARROW 32512
#define SM_CXSCREEN 0
#define SM_CYSCREEN 1
#define lstrlen strlen
#define lstrcpy strcpy
int GetMenuState(int,int,int),GetMenuString(int,int,char*,int,int);
int GetMenuItemCount(int),GetSubMenu(int,int),GetMenuItemID(int,int);
unsigned long GetTextExtent(int,char*,int);
int OffsetRect(RECT*,int,int),IntersectRect(RECT*,RECT*,RECT*),UnionRect(RECT*,RECT*,RECT*),GetUpdateRect(int,RECT*,int);
int CreateDC(char*,void*,void*,void*),DeleteDC(int),SelectClipRgn(int,void*);
int SaveDC(int),RestoreDC(int,int),SetViewportOrg(int,int,int);
int IntersectClipRect(int,int,int,int,int);
int ExcludeClipRect(int,int,int,int,int);
int GetClientRect(int,RECT*),CreateSolidBrush(int),GetSysColor(int);
int FillRect(int,RECT*,int),DeleteObject(int),FrameRect(int,RECT*,int);
int GetStockObject(int),SelectObject(int,int),SetBkMode(int,int);
int SetTextColor(int,int),TextOut(int,int,int,char*,int);
int BeginPaint(int,PAINTSTRUCT*),EndPaint(int,PAINTSTRUCT*);
long DefWindowProc(int,unsigned,unsigned,long);
int DestroyWindow(int),UpdateWindow(int),InvalidateRect(int,void*,int);
long SendMessage(int,unsigned,unsigned,long);
int GetDC(int),ReleaseDC(int,int),CreateWindow(char*,char*,long,int,int,int,int,int,int,int,void*);
int ShowWindow(int,int),SetWindowPos(int,int,int,int,int,int,int);
int PtInRect(RECT*,POINT),GetWindowWord(int,int),GetClassInfo(int,char*,WNDCLASS*);
int LoadCursor(int,int),RegisterClass(WNDCLASS*),GetTextMetrics(int,TEXTMETRIC*);
int GetSystemMetrics(int),SetCapture(int),GetMessage(MSG*,int,int,int);
int IsWindow(int),TranslateMessage(MSG*),DispatchMessage(MSG*),GetCapture(void);
int GetCursorPos(POINT*);
int ClientToScreen(int,POINT*),GetActiveWindow(void),ReleaseCapture(void);
int PostMessage(int,unsigned,unsigned,long),PostQuitMessage(int);
#endif
''')
save('MENUHOST.C',r'''
#include "windows.h"
typedef struct {int flags,id;char *name;} ITEM;
static ITEM root[]={{16,2,"&Programs"},{0,100,"&Back"}};
static ITEM group[]={{16,3,"Productivity tools"},{1,0,"Disabled"}};
static ITEM apps[]={{0,101,"Write a letter"},{0,102,"A && B"},{16,3,"More"},{0,103,"WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"}};
static ITEM *menus[]={0,root,group,apps};
static int counts[]={0,2,2,4};
static int sw=160,sh=200,fw=6,selectedfont,cap,posted,failed,drawn,queue[30],qcount,qpos;
static RECT rectangles[100];static int nextwindow=2;
static void ck(char *name,int ok){printf("CHECK %s=%d\n",name,ok!=0);if(!ok)failed++;}
int GetMenuState(int m,int i,int f){if(i<0||i>=counts[m])return -1;return menus[m][i].flags|((menus[m][i].flags&16)?(counts[menus[m][i].id]<<8):0);}
int GetMenuString(int m,int i,char *s,int n,int f){strncpy(s,menus[m][i].name,n);s[n-1]=0;return strlen(s);}
int GetMenuItemCount(int m){return counts[m];}
int GetSubMenu(int m,int i){return i>=0&&i<counts[m]&&(menus[m][i].flags&16)?menus[m][i].id:0;}
int GetMenuItemID(int m,int i){return menus[m][i].id;}
unsigned long GetTextExtent(int d,char *s,int n){int i,w=0;for(i=0;i<n;i++)w+=s[i]=='W'?fw+2:s[i]=='i'?2:fw;return w;}
int OffsetRect(RECT*r,int x,int y){r->left+=x;r->right+=x;r->top+=y;r->bottom+=y;return 1;}
int IntersectRect(RECT*r,RECT*a,RECT*b){r->left=a->left>b->left?a->left:b->left;r->right=a->right<b->right?a->right:b->right;r->top=a->top>b->top?a->top:b->top;r->bottom=a->bottom<b->bottom?a->bottom:b->bottom;return r->left<r->right&&r->top<r->bottom;}
int UnionRect(RECT*r,RECT*a,RECT*b){RECT t;t.left=a->left<b->left?a->left:b->left;t.right=a->right>b->right?a->right:b->right;t.top=a->top<b->top?a->top:b->top;t.bottom=a->bottom>b->bottom?a->bottom:b->bottom;*r=t;return 1;}
int GetUpdateRect(int w,RECT*r,int b){return 0;}
int CreateDC(char*a,void*b,void*c,void*d){return 1;}int DeleteDC(int d){return 1;}int SelectClipRgn(int d,void*r){return 1;}
int SaveDC(int d){return 1;}int RestoreDC(int d,int s){return 1;}int SetViewportOrg(int d,int x,int y){return 1;}int IntersectClipRect(int d,int l,int t,int r,int b){return 1;}
int ExcludeClipRect(int d,int l,int t,int r,int b){return 1;}
int GetClientRect(int w,RECT*r){*r=rectangles[w];r->right-=r->left;r->bottom-=r->top;r->left=r->top=0;return 1;}
int CreateSolidBrush(int c){return 1;}int GetSysColor(int c){return c;}
int FillRect(int d,RECT*r,int b){return 1;}int DeleteObject(int o){return 1;}int FrameRect(int d,RECT*r,int b){return 1;}
int GetStockObject(int n){return n;}int SelectObject(int d,int o){int p=selectedfont;selectedfont=o;return p;}int SetBkMode(int d,int m){return 1;}
int SetTextColor(int d,int c){return 1;}int TextOut(int d,int x,int y,char*s,int n){drawn++;return 1;}
int BeginPaint(int w,PAINTSTRUCT*p){return 1;}int EndPaint(int w,PAINTSTRUCT*p){return 1;}
long DefWindowProc(int w,unsigned m,unsigned p,long l){return 0;}
int DestroyWindow(int w){return 1;}int UpdateWindow(int w){return 1;}int InvalidateRect(int w,void*p,int b){return 1;}
long SendMessage(int w,unsigned m,unsigned p,long l){return 0;}
int GetDC(int w){return 1;}int ReleaseDC(int w,int d){return 1;}
int CreateWindow(char*c,char*t,long s,int x,int y,int w,int h,int o,int m,int i,void*p){int n=nextwindow++;rectangles[n].left=x;rectangles[n].top=y;rectangles[n].right=x+w;rectangles[n].bottom=y+h;return n;}
int ShowWindow(int w,int c){return 1;}int SetWindowPos(int w,int a,int x,int y,int b,int c,int f){return 1;}
int PtInRect(RECT*r,POINT p){return p.x>=r->left&&p.x<r->right&&p.y>=r->top&&p.y<r->bottom;}
int GetWindowWord(int w,int n){return 1;}int GetClassInfo(int i,char*c,WNDCLASS*w){return 1;}
int LoadCursor(int i,int c){return 1;}int RegisterClass(WNDCLASS*w){return 1;}int GetTextMetrics(int d,TEXTMETRIC*t){t->tmHeight=8;return 1;}
int GetSystemMetrics(int n){return n==0?sw:sh;}int SetCapture(int w){int o=cap;cap=w;return o;}
int GetMessage(MSG*m,int w,int a,int b){if(qpos==qcount)return 0;m->message=WM_KEYDOWN;m->wParam=queue[qpos++];if(m->wParam==(unsigned)-1){m->message=WM_MOUSEMOVE;m->hwnd=1;m->lParam=6+(3L<<16);}else if(m->wParam==(unsigned)-2||m->wParam==(unsigned)-3){m->message=m->wParam==(unsigned)-2?WM_LBUTTONDOWN:WM_LBUTTONUP;m->hwnd=1;m->lParam=60+(3L<<16);}return 1;}
int IsWindow(int w){return 1;}int TranslateMessage(MSG*m){return 1;}int DispatchMessage(MSG*m){return 1;}int GetCapture(void){return cap;}
int ClientToScreen(int w,POINT*p){p->x+=rectangles[w].left;p->y+=rectangles[w].top;return 1;}
int GetCursorPos(POINT*p){p->x=6;p->y=3;return 1;}
int GetActiveWindow(void){return 1;}int ReleaseCapture(void){cap=0;return 1;}
int PostMessage(int w,unsigned m,unsigned p,long l){posted=p;return 1;}int PostQuitMessage(int c){return 1;}
#include "TSMENU.C"
static void keys(int a,int b,int c,int d,int e,int f){queue[0]=a;queue[1]=b;queue[2]=c;queue[3]=d;queue[4]=e;queue[5]=f;qcount=6;qpos=0;posted=0;TSMenuTrack(1,0,0,1);}
int main(void){int widths[]={160,320,640},i,j,n,width;POINT point;char before[256];
 for(i=0;i<3;i++){
  sw=widths[i];screenW=sw;screenH=200;row=9;menuOwner=menuInstance=1;depth=0;nextwindow=2;
  ck("open_root",openmenu(1,sw-12,195));
  ck("root_right_bottom_clamped",levels[0].rect.right<=sw&&levels[0].rect.bottom<=200);
  selectrow(0,0);enter(1);selectrow(1,0);enter(1);
  ck("three_levels_preserved",depth==3&&levels[0].selected==0&&levels[1].selected==0);
  ck("full_label_stored",!strcmp(menus[3][0].name,"Write a letter"));
  label(&levels[2],0);fit(1,sw-18);ck("ordinary_label_full",!strcmp(fitted,"Write a letter"));
  label(&levels[2],1);ck("literal_ampersand",!strcmp(text,"A & B"));
  label(&levels[2],3);strcpy(before,text);fit(1,sw-18);
  ck("long_name_bounded_marked",extent(1,fitted)<=sw-18&&(extent(1,before)>sw-18 ? strstr(fitted,"...")!=0&&strcmp(before,fitted)!=0 : !strcmp(before,fitted)));
  for(j=0;j<10;j++){
   width=levels[depth-1].rect.right-levels[depth-1].rect.left;
   selectrow(depth-1,2);enter(1);
   ck("deep_width_not_divided",levels[depth-1].rect.right-levels[depth-1].rect.left==width);
   ck("deep_within_viewport",levels[depth-1].rect.left>=0&&levels[depth-1].rect.right<=sw&&levels[depth-1].rect.top>=0&&levels[depth-1].rect.bottom<=200);
  }
  point.x=levels[depth-1].rect.left+6;point.y=levels[depth-1].rect.top+3;
  ck("newest_overlap_hit",hit(point,&n)==depth-1&&n==0);
  trim(1);ck("parent_after_back",depth==1&&levels[0].selected==0);
  point.x=levels[0].rect.left+6;point.y=levels[0].rect.top+3;
  ck("parent_hit_restored",hit(point,&n)==0&&n==0);trim(0);
  keys(VK_RIGHT,-1,VK_RIGHT,VK_RETURN,VK_ESCAPE,VK_ESCAPE);
  ck("synthetic_motion_keeps_keyboard_child",posted==101);
  keys(VK_RIGHT,VK_RIGHT,VK_ESCAPE,VK_RIGHT,VK_RETURN,VK_ESCAPE);
  ck("keyboard_back_reenter_launch",posted==101&&depth==0&&!cap);
  keys(VK_RIGHT,VK_RIGHT,VK_LEFT,VK_LEFT,VK_DOWN,VK_RETURN);
  ck("keyboard_parent_selection",posted==100&&depth==0&&!cap);
  keys(VK_RIGHT,VK_RIGHT,VK_ESCAPE,VK_ESCAPE,VK_ESCAPE,VK_ESCAPE);
  ck("escape_all_no_command",posted==0&&depth==0&&!cap);
 }
 sw=160;group[0].flags=0;group[0].id=105;
 keys(-2,-3,VK_ESCAPE,VK_ESCAPE,VK_ESCAPE,VK_ESCAPE);
 ck("opening_release_not_clickthrough",posted==0&&!cap);
 keys(-2,-3,-2,-3,VK_ESCAPE,VK_ESCAPE);
 ck("next_child_click_activates",posted==105&&!cap);
 group[0].flags=16;group[0].id=3;
 fw=4;sw=160;screenW=160;depth=0;nextwindow=2;openmenu(1,0,0);ck("root_preselected_before_tracking",levels[0].selected==0);width=levels[0].rect.right;trim(0);
 fw=8;openmenu(1,0,0);ck("selected_font_width_changes_layout",levels[0].rect.right>width);trim(0);
 counts[1]=0;openmenu(1,0,0);ck("empty_root_no_selection",levels[0].selected==-1);trim(0);
 counts[1]=2;root[0].flags=MF_GRAYED;root[1].flags=MF_DISABLED;
 openmenu(1,0,0);ck("all_disabled_root_no_selection",levels[0].selected==-1);trim(0);
 root[1].flags=0;openmenu(1,0,0);ck("leading_disabled_selects_first_enabled",levels[0].selected==1);trim(0);
 root[0].flags=MF_SEPARATOR;openmenu(1,0,0);ck("leading_separator_selects_first_enabled",levels[0].selected==1);trim(0);
 root[0].flags=MF_POPUP;
 printf("FINAL failures=%d\n",failed);return failed?1:0;
}
''')
env=dict(os.environ,PATH=str(a.cc.parent)+os.pathsep+os.environ['PATH'])
subprocess.run([str(a.cc),'-std=c89','-Wall','-Wextra','-Wno-unused-parameter','-Wno-int-conversion','-I'+str(O),'-I'+str(R),'-x','c',str(O/'MENUHOST.C'),'-o',str(O/'MENUHOST.EXE')],env=env,check=True)
r=subprocess.run([str(O/'MENUHOST.EXE')],capture_output=True,text=True,env=env)
(O/'RESULT.LOG').write_text(r.stdout+r.stderr);print(r.stdout);r.check_returncode()
