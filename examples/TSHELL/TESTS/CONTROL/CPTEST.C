#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>
#include "WINDOWS.H"
#include "../../TSCP.C"
static int present,created,enabled,exists,winresult,pathlen,menuok;
static int posts,launches,notices,restores,active,postok,captionok;
static UINT state,lastcommand,queried;
static UINT nativeids[]={0,8,7,2,3,5,6,10,4,1,9,11,0,51};
static int nativecount,queries;
static int keymodule=1,keyexport=1,keyspeed=0,keyqueries;
static int rows;static UINT rowflags[12],rowids[12];static char rownames[12][48];
int AppendMenu(HMENU m,UINT flags,UINT id,const char *name)
{(void)m;assert(rows<12);rowflags[rows]=flags;rowids[rows]=id;
 if(name)strcpy(rownames[rows],name);
 rows++;return 1;}
static int FAR PASCAL queryspeed(int value)
{assert(value==-1);keyqueries++;return keyspeed;}
HANDLE GetModuleHandle(const char *name)
{assert(!strcmp(name,"KEYBOARD"));return keymodule?7:0;}
FARPROC GetProcAddress(HANDLE h,const char *name)
{assert(h==7&&!strcmp(name,"SetSpeed"));return keyexport?queryspeed:NULL;}
HWND FindWindow(const char *name,const char *title)
{assert(!strcmp(name,"CtlPanelClass"));assert(title==NULL);return present?2:0;}
UINT GetWindowsDirectory(char *p,int n)
{assert(n==128);strcpy(p,"C:\\WINDOWS");return pathlen;}
char *lstrcat(char *a,const char *b){return strcat(a,b);}
int OpenFile(char *p,OFSTRUCT *of,UINT flags)
{(void)of;assert(!strcmp(p,"C:\\WINDOWS\\CONTROL.EXE"));assert(flags==OF_EXIST);return exists?1:HFILE_ERROR;}
UINT WinExec(char *p,int show)
{assert(!strcmp(p,"C:\\WINDOWS\\CONTROL.EXE"));assert(show==SW_SHOWNORMAL);
 launches++;if(created)present=1;return winresult;}
int wsprintf(char *p,const char *format,...)
{int n;va_list a;va_start(a,format);n=vsprintf(p,format,a);va_end(a);return n;}
BOOL IsWindowEnabled(HWND w){return w==3?1:enabled;}
HWND GetLastActivePopup(HWND w){assert(w==2);return 3;}
int BringWindowToTop(HWND w){assert(w==2||w==3);return 1;}
HWND SetActiveWindow(HWND w){active=w;return w;}
int ShowWindow(HWND w,int show){assert(w==2&&show==SW_RESTORE);restores++;return 1;}
HMENU GetMenu(HWND w){assert(w==2);return menuok?4:0;}
HMENU GetSubMenu(HMENU m,int i){assert(i==0);return m?5:0;}
UINT GetMenuState(HMENU m,UINT id,UINT flags)
{assert(m==5&&flags==MF_BYPOSITION);assert(id<(UINT)nativecount);queries++;
 queried=id<14?nativeids[id]:999;return id==12?MF_SEPARATOR:state;}
int GetMenuItemCount(HMENU m){assert(m==5);return nativecount;}
UINT GetMenuItemID(HMENU m,int pos)
{assert(m==5&&pos>=0&&pos<nativecount);return pos<14?nativeids[pos]:999;}
int GetMenuString(HMENU m,UINT id,char *p,int n,UINT flags)
{int i;assert(m==5&&n==48&&flags==MF_BYPOSITION);assert(id<14);
 for(i=0;i<CP_COUNT;i++)if(cpCommands[i]==nativeids[id])break;
 assert(i<CP_COUNT);strcpy(p,captionok?cpNames[i]:"Unexpected command");return (int)strlen(p);}
int lstrcmpi(const char *a,const char *b){return strcmp(a,b);}
BOOL PostMessage(HWND w,UINT m,WPARAM wp,LPARAM lp)
{assert(w==2&&m==WM_COMMAND&&lp==0);lastcommand=wp;posts++;return postok;}
void TinyNotice(HWND w,HINSTANCE h,char *title,char *text)
{assert(w==1&&h==1&&!strcmp(title,"Settings"));assert(text[0]);notices++;active=1;}
static void reset(void)
{present=0;created=enabled=exists=menuok=postok=captionok=1;winresult=33;pathlen=10;
 keymodule=keyexport=1;keyspeed=keyqueries=0;
 posts=launches=notices=restores=active=queries=0;nativecount=14;state=0;lastcommand=queried=999;}
int main(void)
{
 int i;UINT expected[]={0,8,7,2,3,5,6,4,1,9};
 TSControlMenu(1);assert(rows==12&&rowids[0]==CP_OPEN);
 for(i=0;i<CP_COUNT;i++){assert(rowids[i+2]==(UINT)(CP_FIRST+i));assert(!strcmp(rownames[i+2],cpNames[i]));}
 for(i=0;i<CP_COUNT;i++){
  reset();TSControlPanel(1,1,i);assert(launches==1&&posts==1&&!notices&&active==2);
  assert(lastcommand==expected[i]&&queried==expected[i]);
  TSControlPanel(1,1,i);assert(launches==1&&posts==2);
 }
 reset();TSControlPanel(1,1,-1);assert(launches==1&&!posts&&!notices&&active==2);
 reset();exists=0;TSControlPanel(1,1,0);assert(!launches&&!posts&&notices==1);
 reset();pathlen=0;TSControlPanel(1,1,0);assert(!launches&&!posts&&notices==1);
 reset();pathlen=128;TSControlPanel(1,1,0);assert(!launches&&!posts&&notices==1);
 reset();winresult=8;TSControlPanel(1,1,0);assert(launches==1&&!posts&&notices==1);
 reset();created=0;TSControlPanel(1,1,0);assert(launches==1&&!posts&&notices==1);
 reset();present=1;enabled=0;TSControlPanel(1,1,0);assert(!launches&&!posts&&notices==1&&active==3);
 reset();menuok=0;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();state=0xffff;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();state=MF_GRAYED;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();state=MF_DISABLED;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();state=MF_POPUP;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();state=MF_SEPARATOR;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();captionok=0;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();postok=0;TSControlPanel(1,1,0);assert(posts==1&&notices==1);
 /* ID zero is both Color and the trailing separator. The position guard
    must select Color and must never use ambiguous command lookup. */
 reset();TSControlPanel(1,1,0);assert(posts==1&&lastcommand==0&&queries==1);
 reset();state=MF_SEPARATOR;TSControlPanel(1,1,0);assert(!posts&&notices==1);
 reset();nativecount=0;TSControlPanel(1,1,0);assert(!posts&&notices==1&&!queries);
 reset();nativecount=-1;TSControlPanel(1,1,0);assert(!posts&&notices==1&&!queries);
 reset();nativecount=33;TSControlPanel(1,1,0);assert(!posts&&notices==1&&!queries);
 reset();nativecount=32;captionok=0;TSControlPanel(1,1,0);assert(!posts&&notices==1&&queries==32);
 reset();nativecount=1;TSControlPanel(1,1,9);assert(!posts&&notices==1&&queries==1);
 reset();TSControlPanel(1,1,-2);TSControlPanel(1,1,10);assert(!launches&&!posts&&!notices);
 /* Only the driver's read-only -1 query decides keyboard support. */
 reset();assert(TSKeyboardAvailable()&&keyqueries==1);
 reset();keyspeed=31;assert(TSKeyboardAvailable()&&keyqueries==1);
 reset();keyspeed=-1;assert(!TSKeyboardAvailable()&&keyqueries==1);
 reset();keymodule=0;assert(!TSKeyboardAvailable()&&!keyqueries);
 reset();keyexport=0;assert(!TSKeyboardAvailable()&&!keyqueries);
 reset();keyspeed=-1;rows=0;TSControlMenu(1);
 assert(rows==12&&rowflags[7]==MF_GRAYED);
 for(i=0;i<12;i++)if(i!=7)assert(!(rowflags[i]&MF_GRAYED));
 reset();rows=0;TSControlMenu(1);assert(!(rowflags[7]&MF_GRAYED));
 reset();keyspeed=-1;TSControlPanel(1,1,5);assert(launches==1&&!posts&&notices==1);
 reset();keymodule=0;TSControlPanel(1,1,5);assert(launches==1&&!posts&&notices==1);
 reset();keyexport=0;TSControlPanel(1,1,5);assert(launches==1&&!posts&&notices==1);
 reset();keyspeed=-1;TSControlPanel(1,1,-1);assert(launches==1&&!posts&&!notices);
 puts("PASS: keyboard capability, 10 applet routes, duplicate zero ID/separator, menu bounds, reuse and failure guards");return 0;
}
