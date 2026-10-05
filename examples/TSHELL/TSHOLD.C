/* Optional Tandy Hold shortcut. All window activation stays in this task. */
#define WINVER 0x0300
#include <windows.h>
#include "TSHOLD.H"
#include "TSBOOT.H"
#include "TSSAVER.H"
#include "TNOTICE.H"
typedef BOOL (FAR PASCAL *HOLDINSTALL)(HWND,WORD,BOOL);
typedef BOOL (FAR PASCAL *HOLDREMOVE)(void);
typedef BOOL (FAR PASCAL *HOLDPOLICY)(HWND,BOOL);
typedef BOOL (FAR PASCAL *HOLDTAKE)(HWND,DWORD);
static HINSTANCE module;
static HWND target,previousActive,previousFocus;
static HTASK previousTask,previousFocusTask;
static int menuPending;
static HOLDINSTALL install;
static HOLDREMOVE removeHook;
static HOLDPOLICY policy;
static HOLDTAKE take;
static int holding,stopping,closing,closeTries;

void TandyHoldRefresh(void)
{
 if(module && policy && target)
  policy(target,!holding && !stopping && !closing && !TandyBootBusy());
}
void TandyHoldBlock(int enter)
{
 if(enter)++holding;else if(holding)--holding;
 TandyHoldRefresh();
}
void TandyHoldShutdown(int pending)
{
 stopping=pending!=0;TandyHoldRefresh();
}
static int release(void)
{
 if(!module)return 1;
 if(policy && target)policy(target,FALSE);
 if(removeHook && !removeHook())return 0;
 FreeLibrary(module);module=0;install=NULL;removeHook=NULL;policy=NULL;take=NULL;
 return 1;
}
static int compatibleKeyboard(void)
{
 HMODULE keyboard;char path[144],*base,*p;int n;
 keyboard=GetModuleHandle("KEYBOARD");if(!keyboard)return 0;
 n=GetModuleFileName(keyboard,path,sizeof(path));
 if(n<=0 || n>=sizeof(path)-1)return 0;
 path[n]=0;base=path;
 for(p=path;*p;p++)if(*p=='\\' || *p==':')base=p+1;
 /* Inspect the loaded driver, not an INI selection awaiting the next boot.
    The compatible kit's latched classification keeps modifier breaks paired.
    This is a profile/name gate; it is not a binary-integrity verification. */
 return !lstrcmpi(base,"TNDYK3.DRV");
}
void TandyHoldBegin(HWND owner,HINSTANCE instance)
{
 char path[144],config[144];OFSTRUCT of;int n;
 if(module || target || (GetWinFlags()&WF_PMODE))return;
 /* Same Tandy ROM marker used by the existing PSG applications. No remap
    is installed on another machine, even if it runs a copy of this shell. */
 if(*(unsigned char FAR *)0xfc000000UL!=0x21)return;
 n=GetWindowsDirectory(config,sizeof(config));
 if(!n || n>=sizeof(config)-12)return;
 lstrcat(config,"\\TSHELL.INI");
 if(!GetPrivateProfileInt("Keyboard","HoldStart",compatibleKeyboard(),config))return;
 n=GetWindowsDirectory(path,sizeof(path));if(!n || n>=sizeof(path)-13)return;
 lstrcat(path,"\\TSINPUT.DLL");
 if(OpenFile(path,&of,OF_EXIST)==HFILE_ERROR)goto missing;
 module=LoadLibrary(path);if((UINT)module<32){module=0;goto missing;}
 install=(HOLDINSTALL)GetProcAddress(module,"HoldInstall");
 removeHook=(HOLDREMOVE)GetProcAddress(module,"HoldRemove");
 policy=(HOLDPOLICY)GetProcAddress(module,"HoldPolicy");
 take=(HOLDTAKE)GetProcAddress(module,"HoldTake");
 if(!install || !removeHook || !policy || !take){release();goto missing;}
 target=owner;
 if(!install(owner,HOLD_START,!holding && !stopping && !TandyBootBusy())){
  release();target=NULL;
  TinyNotice(owner,instance,"Hold","Hold unavailable.\nUse Start.");return;
 }
 TandyHoldRefresh();return;
missing:
 TinyNotice(owner,instance,"Hold","Update TSINPUT.\nHold is off.");
}
static int canOpen(HWND owner)
{
 HWND active,parent;char name[16];
 if(owner!=target || holding || stopping || closing || TandyBootBusy() ||
    TSSaverShortcutBusy() || !IsWindowEnabled(owner) || GetCapture() ||
    GetSysModalWindow() || GetModuleHandle("TEXIT"))return 0;
 if(FindWindow("TandyMatrixSaver",NULL) || FindWindow("TandyMazeSaver",NULL) ||
    FindWindow("TandyStarfieldSaver",NULL))return 0;
 active=GetActiveWindow();parent=active?GetWindow(active,GW_OWNER):NULL;
 if(parent && !IsWindowEnabled(parent))return 0;
 if(active && GetClassName(active,name,sizeof(name)) && !lstrcmp(name,"#32770"))return 0;
 return 1;
}
int TandyHoldRequest(HWND owner,DWORD token)
{
 if(!module || !take || !take(owner,token) || menuPending || !canOpen(owner))return 0;
 previousActive=GetActiveWindow();previousFocus=GetFocus();
 previousTask=previousActive?GetWindowTask(previousActive):NULL;
 previousFocusTask=previousFocus?GetWindowTask(previousFocus):NULL;
 menuPending=1;return 1;
}
void TandyHoldAction(void)
{ previousActive=previousFocus=NULL;previousTask=previousFocusTask=NULL;menuPending=0; }
void TandyHoldMenuDone(int complete)
{
 HWND active,focus;HTASK task,focusTask;
 if(!complete)return;
 active=previousActive;focus=previousFocus;task=previousTask;focusTask=previousFocusTask;TandyHoldAction();
 /* Never take focus back from an app the user selected or activated. */
 if(!active || active==target || GetActiveWindow()!=target ||
    !IsWindow(active) || GetWindowTask(active)!=task || !IsWindowVisible(active) || !IsWindowEnabled(active))return;
 BringWindowToTop(active);SetActiveWindow(active);
 if(GetActiveWindow()==active && GetWindowTask(active)==task &&
    focus && IsWindow(focus) && GetWindowTask(focus)==focusTask && (focus==active || IsChild(active,focus)) &&
    IsWindowVisible(focus) && IsWindowEnabled(focus))SetFocus(focus);
}
int TandyHoldClose(HWND owner)
{
 closing=1;TandyHoldAction();TandyHoldRefresh();
 if(release())return 1;
 if(!SetTimer(owner,HOLD_CLOSE_TIMER,55,NULL))return 1;
 closeTries=0;return 0;
}
int TandyHoldCloseTick(HWND owner)
{
 if(!closing)return 0;
 /* A held key may finish its swallowed gesture before normal bar teardown.
    Detach failure never frees live hook code or keeps a visible bar stuck. */
 if(release() || ++closeTries>=20){KillTimer(owner,HOLD_CLOSE_TIMER);return 1;}
 return 0;
}
void TandyHoldStop(HWND owner)
{
 closing=1;KillTimer(owner,HOLD_CLOSE_TIMER);TandyHoldAction();TandyHoldRefresh();
 release();target=NULL;
 /* An explicit LoadLibrary reference is deliberately retained on failure.
    The disabled DLL cannot post; WEP handles final Windows shutdown. */
}
