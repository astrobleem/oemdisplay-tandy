/* Main-task saver policy. The separate fixed DLL only observes global input. */
#define WINVER 0x0300
#include <windows.h>
#include "TSBOOT.H"
#include "TSSAVER.H"
#include "TNOTICE.H"
#include "PROGMENU.H"
#include "SVCORE.H"
typedef BOOL (FAR PASCAL *IDLEBOOL)(void);
typedef DWORD (FAR PASCAL *IDLECOUNT)(void);
static HINSTANCE hookModule, ownInstance;
static IDLEBOOL idleInstall,idleRemove,idleReady;
static IDLECOUNT idleGeneration;
static SVSTATE state;
static DWORD delay;
static int enabled, holding, stopping, inTick;
static char saver[128];

static void reset(void)
{ SvReset(&state,GetTickCount(),idleGeneration?idleGeneration():0L); }
static int knownAudio(void)
{
    return TandyBootBusy() || GetModuleHandle("TCHIME") ||
        GetModuleHandle("XPCHIME") || GetModuleHandle("TEXIT") ||
        FindWindow("TandyPSGTest",NULL) ||
        FindWindow("TandyAutomaticMouth",NULL) ||
        FindWindow("TandyMiniMIDI",NULL) || FindWindow("TandyJoyMIDI",NULL);
}
static void closeSaver(void)
{
    HWND w=FindWindow("TandyMatrixSaver",NULL);
    if (w) PostMessage(w,WM_CLOSE,0,0L);
}
static void releaseHook(void)
{
    if (!hookModule) return;
    /* An unhook failure must never leave a live callback in freed code. */
    if (!idleRemove || idleRemove()) {
        FreeLibrary(hookModule); hookModule=0;
        idleInstall=idleRemove=idleReady=NULL; idleGeneration=NULL;
    }
}
void TSSaverStop(HWND w)
{
    enabled=0; KillTimer(w,SAVER_TIMER); closeSaver(); releaseHook();
}
void TSSaverHold(int enter)
{
    if (enter) ++holding;
    else if (holding) --holding;
    reset();
}
void TSSaverShutdown(int pending)
{
    stopping=pending; reset(); if(pending)closeSaver();
}
static int seconds(char *s)
{
    int n=0,i=0;
    while(s[i]>='0'&&s[i]<='9') {
        if(i==4)return 0;
        n=n*10+s[i++]-'0';
    }
    return !s[i]&&n>=10&&n<=3600?n:0;
}
static int absolute(char *s)
{
    int i,n=lstrlen(s);
    if(n<4||n>122||s[1]!=':'||s[2]!='\\')return 0;
    if(!((s[0]>='A'&&s[0]<='Z')||(s[0]>='a'&&s[0]<='z')))return 0;
    for(i=0;i<n;++i)
        if(s[i]==' '||s[i]=='\t'||s[i]=='"'||s[i]=='/'||s[i]=='*'||s[i]=='?')return 0;
    return 1;
}
void TSSaverBegin(HWND w,HINSTANCE instance)
{
    char ini[144],dll[144],number[12]; int n,secs; OFSTRUCT of;
    if(enabled||hookModule)return;
    ownInstance=instance;
    GetWindowsDirectory(ini,sizeof(ini));lstrcat(ini,"\\TSHELL.INI");
    if(!GetPrivateProfileInt("ScreenSaver","Enabled",0,ini))return;
    GetPrivateProfileString("ScreenSaver","IdleSeconds","300",number,sizeof(number),ini);
    secs=seconds(number);
    n=GetPrivateProfileString("ScreenSaver","Program","C:\\TSTART\\MATRIX.EXE",saver,sizeof(saver),ini);
    if(!secs||!n||n>=sizeof(saver)-1||!absolute(saver)) {
        TinyNotice(w,instance,"Saver","Bad saver setup.\nSee TSHELL.INI.");return;
    }
    if(OpenFile(saver,&of,OF_EXIST)==HFILE_ERROR) {
        TinyNotice(w,instance,"Saver","Matrix missing.\nSaver disabled.");return;
    }
    lstrcat(saver," /S"); delay=(DWORD)secs*1000L;
    GetWindowsDirectory(dll,sizeof(dll));lstrcat(dll,"\\TSINPUT.DLL");
    /* Win3's loader opens an oversized system dialog for a missing DLL. */
    if(OpenFile(dll,&of,OF_EXIST)==HFILE_ERROR) {
        TinyNotice(w,instance,"Saver","TSINPUT missing.\nSaver disabled.");return;
    }
    hookModule=LoadLibrary(dll);
    if((UINT)hookModule<32) { hookModule=0; goto failed; }
    idleInstall=(IDLEBOOL)GetProcAddress(hookModule,"IdleInstall");
    idleRemove=(IDLEBOOL)GetProcAddress(hookModule,"IdleRemove");
    idleReady=(IDLEBOOL)GetProcAddress(hookModule,"IdleReady");
    idleGeneration=(IDLECOUNT)GetProcAddress(hookModule,"IdleGeneration");
    if(!idleInstall||!idleRemove||!idleReady||!idleGeneration)goto failed;
    if(!idleInstall())goto failed;
    reset(); enabled=1;
    if(SetTimer(w,SAVER_TIMER,1000,NULL))return;
failed:
    TSSaverStop(w);
    TinyNotice(w,instance,"Saver","Idle hook failed.\nSaver disabled.");
}
void TSSaverTick(HWND w)
{
    BOOL ready; DWORD gen; UINT result;
    if(!enabled||inTick)return;
    inTick=1;
    ready=idleReady(); gen=idleGeneration();
    if(holding||stopping||!IsWindowEnabled(w)||knownAudio()||GetModuleHandle("MATRIX"))ready=FALSE;
    if(SvDue(&state,GetTickCount(),gen,delay,ready)) {
        ++holding;
        result=PmLaunchShow(w,saver,SW_SHOWNORMAL);
        /* WinExec may yield while loading; do not keep a saver over new input. */
        if(idleGeneration() != gen) closeSaver();
        --holding; reset();
        if(result<32) {
            TSSaverStop(w);
            TinyNotice(w,ownInstance,"Saver","Matrix failed.\nSaver disabled.");
        }
    }
    inTick=0;
}
