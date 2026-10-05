#include <assert.h>
#include <stdio.h>
#include <string.h>
#define TSINPUT_HOST
#include "../TSINPUT.C"
#define TARGET ((HWND)10)
#define FOCUS ((HWND)20)
#define MESSAGE (WM_USER+9)
#define MAKE ((DWORD)0x00460001L)
#define REPEAT ((DWORD)0x40460001L)
#define BREAK ((DWORD)0xc0460001L)
static HTASK task=(HTASK)1, focusTask=(HTASK)2;
static HWND active=FOCUS, cap, modal, disabledOwner;
static BOOL valid=TRUE, enabled=TRUE, postOK=TRUE;
static int state[256];
static DWORD tick=100, postedToken, postedAt;
static unsigned installs[3], removes[3], posts, chains, peeks, asyncs;
static unsigned queued;
static int missingExport, failKeyRemove, failRecordRemove, reenterRemove, reenterPolicy, reenterTake, reenterPeek;
static char *className="Notepad";
static int chainResult=0;
static char *moduleName="", *windowClass="";
static void priorKey(void) {}
static void priorRecord(void) {}
DWORD DefHookProc(int code, WORD wp, DWORD lp, FARPROC *next)
{
    HTASK saved;
    (void)code; (void)wp; (void)lp;
    ++chains;
    assert(next == &nextHoldKey || next == &nextHoldRecord || next == &nextRecord);
    if (next==&nextHoldKey) assert(*next == priorKey);
    else assert(*next == priorRecord);
    if (reenterRemove && next==&nextHoldKey) {
        reenterRemove=0; saved=task; task=(HTASK)1;
        assert(holdDepth); assert(!HoldRemove());
        assert(holdKeyLive && holdKeyProc);
        task=saved;
    }
    if (reenterTake && next==&nextHoldKey) {
        reenterTake=0; saved=task; task=(HTASK)1;
        assert(holdDepth && holdPending && !HoldTake(TARGET,holdPending));
        task=saved;
    }
    if (reenterPolicy && next==&nextHoldKey) {
        reenterPolicy=0; saved=task; task=(HTASK)1;
        assert(HoldPolicy(TARGET,FALSE)); assert(HoldPolicy(TARGET,TRUE));
        task=saved;
    }
    return (DWORD)chainResult;
}
HINSTANCE GetModuleHandle(LPSTR name) { return !strcmp(name,moduleName)?(HINSTANCE)100:NULL; }
HWND FindWindow(LPSTR name, LPSTR title) { (void)title; return !strcmp(name,windowClass)?(HWND)100:NULL; }
HTASK GetCurrentTask(void) { return task; }
FARPROC GetProcAddress(HINSTANCE h, LPSTR name)
{
    assert(h==(HINSTANCE)123);
    if (missingExport) return NULL;
    if (!strcmp(name,"HoldKeyboard")) return (FARPROC)HoldKeyboard;
    if (!strcmp(name,"HoldRecord")) return (FARPROC)HoldRecord;
    assert(!strcmp(name,"IdleRecord")); return (FARPROC)IdleRecord;
}
DWORD GetTickCount(void) { return tick; }
DWORD ReadDosClock(void) { return tick; }
FARPROC SetWindowsHook(int type, FARPROC fn)
{
    assert(type==WH_KEYBOARD || type==WH_JOURNALRECORD);
    assert(fn==(FARPROC)HoldKeyboard || fn==(FARPROC)HoldRecord || fn==(FARPROC)IdleRecord);
    ++installs[type]; return type==WH_KEYBOARD ? priorKey : priorRecord;
}
BOOL UnhookWindowsHook(int type, FARPROC fn)
{
    assert(type==WH_KEYBOARD || type==WH_JOURNALRECORD);
    assert(fn==(FARPROC)HoldKeyboard || fn==(FARPROC)HoldRecord || fn==(FARPROC)IdleRecord);
    ++removes[type]; return !(type==WH_KEYBOARD ? failKeyRemove : failRecordRemove);
}
HWND GetSysModalWindow(void) { return modal; }
HWND GetCapture(void) { return cap; }
HWND GetActiveWindow(void) { return active; }
int GetClassName(HWND h, LPSTR dst, int count)
{
    assert(h==active); strncpy(dst,className,count); return strlen(className);
}
int GetKeyState(int key) { assert(key>=0 && key<256); return state[key]; }
int GetAsyncKeyState(int key) { ++asyncs; return GetKeyState(key); }
void GetCursorPos(POINT *p) { p->x=320; p->y=100; }
HWND GetWindow(HWND h, WORD kind) { assert(h==active && kind==GW_OWNER); return disabledOwner; }
BOOL IsWindowEnabled(HWND h) { assert(h==disabledOwner); return enabled; }
BOOL IsWindow(HWND h) { return h && (h!=TARGET || valid); }
HTASK GetWindowTask(HWND h) { return h==TARGET ? (HTASK)1 : focusTask; }
BOOL PostMessage(HWND h, WORD msg, WORD wp, DWORD lp)
{
    assert(h==TARGET && msg==MESSAGE && wp==0 && lp);
    ++posts; postedToken=lp; postedAt=tick; if (postOK) ++queued;
    return postOK;
}
BOOL PeekMessage(MSG *m, HWND h, WORD lo, WORD hi, WORD flags)
{
    (void)m; ++peeks;
    assert(h==TARGET && lo==MESSAGE && hi==MESSAGE && flags==PM_REMOVE);
    if (reenterPeek) {
        reenterPeek=0; assert(holdRemoving && !holdKeyLive && !holdRecordLive);
        assert(!HoldRemove()); assert(!HoldInstall(TARGET,MESSAGE,TRUE));
    }
    if (!queued) return FALSE;
    --queued; return TRUE;
}
static void raw(WORD msg, WORD key, WORD hi)
{
    EVENTMSG e; e.message=msg; e.paramL=key; e.paramH=hi; e.time=tick;
    assert(HoldRecord(HC_ACTION,0,(DWORD)&e)==(DWORD)chainResult);
}
static int key(WORD vk, DWORD bits)
{
    int result; HTASK old=task; task=(HTASK)2;
    result=HoldKeyboard(HC_ACTION,vk,bits); task=old; return result;
}
static int step(WORD vk, DWORD bits)
{
    raw((bits&0x80000000L)?WM_KEYUP:WM_KEYDOWN,vk,0);
    return key(vk,bits);
}
static void install(void)
{
    task=(HTASK)1; active=FOCUS; focusTask=(HTASK)2; className="Notepad";
    cap=modal=disabledOwner=NULL; valid=enabled=postOK=TRUE;
    memset(state,0,sizeof(state)); tick+=100; chainResult=0;
    assert(HoldInstall(TARGET,MESSAGE,TRUE));
}
static void removeHooks(void)
{
    task=(HTASK)1; assert(HoldRemove()); assert(!holdKeyLive && !holdRecordLive);
    assert(!holdOwner && !holdTarget && !holdPending && !queued);
}
static DWORD tap(void)
{
    unsigned count=posts; assert(step(VK_SCROLL,MAKE)==1);
    tick+=55; assert(step(VK_SCROLL,BREAK)==1); assert(posts==count+1);
    return postedToken;
}
int main(void)
{
    DWORD token, newer; unsigned before, calls;
    LibMain((HINSTANCE)123,0,0,NULL);
    assert(HoldRemove()); assert(!HoldPolicy(TARGET,TRUE)); assert(!HoldTake(TARGET,1));
    assert(!HoldInstall(NULL,MESSAGE,TRUE)); assert(!HoldInstall(TARGET,WM_USER-1,TRUE));
    task=(HTASK)2; assert(!HoldInstall(TARGET,MESSAGE,TRUE)); task=(HTASK)1;
    missingExport=1; assert(!HoldInstall(TARGET,MESSAGE,TRUE)); missingExport=0;
    assert(!holdKeyLive && !holdRecordLive);
    install(); before=installs[WH_KEYBOARD]; assert(HoldInstall(TARGET,MESSAGE,FALSE));
    assert(installs[WH_KEYBOARD]==before && holdAllowed);
    assert(!HoldInstall(TARGET,MESSAGE+1,TRUE));
    task=(HTASK)2; assert(!HoldInstall(TARGET,MESSAGE,TRUE)); assert(!HoldRemove());
    assert(!HoldPolicy(TARGET,FALSE)); task=(HTASK)1;
    chainResult=0x789; before=holdGesture; calls=chains;
    assert(HoldKeyboard(-1,VK_SCROLL,MAKE)==0x789);
    assert(HoldKeyboard(99,VK_SCROLL,MAKE)==0x789);
    assert(HoldRecord(-1,0,1)==0x789); assert(HoldRecord(99,0,1)==0x789);
    assert(holdGesture==before && chains==calls+4); chainResult=0;
    /* NOREMOVE is repeatable and state-free on make and owned break. */
    raw(WM_KEYDOWN,VK_SCROLL,0); before=posts;
    assert(HoldKeyboard(HC_NOREMOVE,VK_SCROLL,MAKE)==0);
    assert(HoldKeyboard(HC_NOREMOVE,VK_SCROLL,MAKE)==0);
    assert(holdGesture==HOLD_NONE && !holdPending && posts==before);
    assert(key(VK_SCROLL,MAKE)==1); assert(holdGesture==HOLD_OWNED);
    assert(step(VK_SCROLL,REPEAT)==1); assert(step(VK_SCROLL,REPEAT)==1);
    raw(WM_KEYUP,VK_SCROLL,0);
    assert(HoldKeyboard(HC_NOREMOVE,VK_SCROLL,BREAK)==0);
    assert(holdGesture==HOLD_OWNED && posts==before);
    assert(key(VK_SCROLL,BREAK)==1); assert(posts==before+1);
    token=postedToken; assert(!HoldTake(TARGET,token+1));
    task=(HTASK)2; assert(!HoldTake(TARGET,token)); task=(HTASK)1;
    assert(!HoldTake((HWND)30,token)); assert(HoldTake(TARGET,token));
    assert(!HoldTake(TARGET,token)); assert(step(VK_SCROLL,BREAK)==0);
    assert(asyncs==1); /* install only; callbacks never consume async low bits */
    /* Non-target scan, extended Scroll, VK_CANCEL and unrelated keys pass. */
    assert(step(VK_SCROLL,0x00450001L)==0); assert(step(VK_SCROLL,0xc0450001L)==0);
    assert(step(VK_SCROLL,MAKE|0x01000000L)==0); assert(step(VK_SCROLL,BREAK|0x01000000L)==0);
    assert(step(VK_CANCEL,MAKE)==0); assert(step(VK_CANCEL,BREAK)==0);
    assert(step(65,0x001e0001L)==0); assert(step(65,0xc01e0001L)==0);
    before=posts; assert(step(VK_SCROLL,REPEAT)==0); assert(step(VK_SCROLL,BREAK)==0);
    assert(posts==before);
    /* Held modifiers, including an ALT context bit, pass the whole gesture. */
    state[VK_SHIFT]=0x8000; assert(step(VK_SCROLL,MAKE)==0);
    state[VK_SHIFT]=0; step(VK_SHIFT,0xc02a0001L); assert(step(VK_SCROLL,BREAK)==0);
    state[VK_CONTROL]=0x8000; assert(step(VK_SCROLL,MAKE)==0); state[VK_CONTROL]=0;
    assert(step(VK_SCROLL,BREAK)==0);
    state[VK_MENU]=0x8000; assert(step(VK_SCROLL,MAKE)==0); state[VK_MENU]=0;
    assert(step(VK_SCROLL,BREAK)==0);
    assert(step(VK_SCROLL,MAKE|0x20000000L)==0); assert(step(VK_SCROLL,BREAK)==0);
    /* Modifier transitions cancel but preserve swallowed-down/up balance. */
    before=posts; assert(step(VK_SCROLL,MAKE)==1); state[VK_CONTROL]=0x8000;
    assert(step(VK_CONTROL,0x001d0001L)==0); state[VK_CONTROL]=0;
    assert(step(VK_CONTROL,0xc01d0001L)==0); assert(step(VK_SCROLL,REPEAT)==1);
    assert(step(VK_SCROLL,BREAK)==1); assert(posts==before);
    assert(step(VK_SCROLL,MAKE)==1); state[VK_CONTROL]=0x8000;
    assert(step(VK_CONTROL,0x001d0001L)==0); assert(step(VK_SCROLL,BREAK)==1);
    assert(holdGesture==HOLD_NONE); state[VK_CONTROL]=0;
    assert(step(VK_CONTROL,0xc01d0001L)==0); assert(posts==before);
    /* Old drivers' remapped CtrlBreak release is passed and unsticks state. */
    assert(step(VK_SCROLL,MAKE)==1); assert(step(VK_CANCEL,BREAK)==0);
    assert(holdGesture==HOLD_NONE && !holdRawDown && posts==before);
    /* Both journal and dequeue ordering cancel other-input interruptions. */
    assert(step(VK_SCROLL,MAKE)==1); raw(WM_KEYDOWN,65,0);
    assert(step(VK_SCROLL,BREAK)==1); assert(posts==before);
    raw(WM_KEYDOWN,VK_SCROLL,0); raw(WM_KEYDOWN,65,0);
    assert(key(VK_SCROLL,MAKE)==0); assert(step(VK_SCROLL,BREAK)==0);
    assert(step(VK_SCROLL,MAKE)==1); raw(WM_MOUSEMOVE,320,100);
    assert(step(VK_SCROLL,BREAK)==1); assert(posts==before+1); before=posts;
    assert(step(VK_SCROLL,MAKE)==1); raw(WM_MOUSEMOVE,321,100);
    assert(step(VK_SCROLL,BREAK)==1); assert(posts==before);
    assert(step(VK_SCROLL,MAKE)==1); raw(WM_LBUTTONDOWN,321,100);
    raw(WM_LBUTTONUP,321,100); assert(step(VK_SCROLL,BREAK)==1); assert(posts==before);
    /* Owner policy invalidates both held and already-posted gestures. */
    assert(step(VK_SCROLL,MAKE)==1); assert(HoldPolicy(TARGET,FALSE));
    assert(HoldPolicy(TARGET,TRUE)); assert(step(VK_SCROLL,BREAK)==1); assert(posts==before);
    token=tap(); assert(HoldPolicy(TARGET,FALSE)); assert(HoldPolicy(TARGET,TRUE));
    assert(!HoldTake(TARGET,token)); token=tap(); newer=tap();
    assert(token!=newer && !HoldTake(TARGET,token) && HoldTake(TARGET,newer));
    token=tap(); raw(WM_KEYDOWN,65,0); assert(!HoldTake(TARGET,token));
    /* Queued event age and queued request age are bounded independently. */
    raw(WM_KEYDOWN,VK_SCROLL,0); tick+=1001; assert(key(VK_SCROLL,MAKE)==0);
    assert(step(VK_SCROLL,BREAK)==0);
    before=posts; assert(step(VK_SCROLL,MAKE)==1); raw(WM_KEYUP,VK_SCROLL,0);
    tick+=1001; assert(key(VK_SCROLL,BREAK)==1); assert(posts==before);
    token=tap(); tick=postedAt+1000; assert(HoldTake(TARGET,token));
    token=tap(); tick=postedAt+1001; assert(!HoldTake(TARGET,token));
    tick=(DWORD)-100; token=tap(); tick=10; assert(HoldTake(TARGET,token));
    /* Initial ineligible context passes both halves, even after dismissal. */
    cap=(HWND)30; assert(step(VK_SCROLL,MAKE)==0); cap=NULL;
    assert(step(VK_SCROLL,BREAK)==0);
    modal=(HWND)30; assert(step(VK_SCROLL,MAKE)==0); modal=NULL;
    assert(step(VK_SCROLL,BREAK)==0);
    className="#32770"; assert(step(VK_SCROLL,MAKE)==0); className="Notepad";
    assert(step(VK_SCROLL,BREAK)==0);
    disabledOwner=(HWND)30; enabled=FALSE; assert(step(VK_SCROLL,MAKE)==0);
    enabled=TRUE; disabledOwner=NULL; assert(step(VK_SCROLL,BREAK)==0);
    moduleName="MAZE"; assert(step(VK_SCROLL,MAKE)==0); assert(step(VK_SCROLL,BREAK)==0);
    windowClass="TandyMaze"; token=tap(); assert(HoldTake(TARGET,token));
    moduleName=windowClass="";
    moduleName="MATRIX"; assert(step(VK_SCROLL,MAKE)==0); assert(step(VK_SCROLL,BREAK)==0);
    moduleName="TEXIT"; assert(step(VK_SCROLL,MAKE)==0); assert(step(VK_SCROLL,BREAK)==0);
    moduleName=""; windowClass="TandyStarfieldSaver";
    assert(step(VK_SCROLL,MAKE)==0); assert(step(VK_SCROLL,BREAK)==0); windowClass="";
    state[VK_LBUTTON]=0x8000; assert(step(VK_SCROLL,MAKE)==0);
    state[VK_LBUTTON]=0; assert(step(VK_SCROLL,BREAK)==0);
    assert(step(VK_SCROLL,MAKE)==1); active=(HWND)30; before=posts;
    assert(step(VK_SCROLL,BREAK)==1); assert(posts==before); active=FOCUS;
    token=tap(); active=(HWND)30; assert(!HoldTake(TARGET,token)); active=FOCUS;
    token=tap(); focusTask=(HTASK)3; assert(!HoldTake(TARGET,token)); focusTask=(HTASK)2;
    token=tap(); valid=FALSE; assert(!HoldTake(TARGET,token)); valid=TRUE;
    postOK=FALSE; tap(); assert(!holdPending); postOK=TRUE;
    /* Removal retains fixed callbacks while a swallowed make needs its up. */
    assert(step(VK_SCROLL,MAKE)==1); assert(!HoldRemove());
    assert(holdStopping && !holdAllowed && holdKeyLive && holdRecordLive);
    assert(!HoldInstall(TARGET,MESSAGE,TRUE)); assert(!HoldPolicy(TARGET,TRUE));
    before=posts; assert(step(VK_SCROLL,BREAK)==1); assert(posts==before); removeHooks();
    /* Reentrant remove from the chained hook cannot detach executing code. */
    install(); reenterRemove=1; assert(step(65,0x001e0001L)==0);
    assert(!reenterRemove && holdStopping); removeHooks();
    install(); assert(step(VK_SCROLL,MAKE)==1); reenterPolicy=1;
    before=posts; assert(step(VK_SCROLL,BREAK)==1); assert(posts==before+1);
    assert(!HoldTake(TARGET,postedToken)); removeHooks();
    install(); before=posts; chainResult=1;
    assert(step(VK_SCROLL,MAKE)==1); chainResult=0;
    assert(step(VK_SCROLL,BREAK)==1); assert(posts==before); removeHooks();
    install(); assert(step(VK_SCROLL,MAKE)==1); chainResult=1;
    assert(step(VK_SCROLL,BREAK)==1); assert(!holdPending); chainResult=0; removeHooks();
    install(); assert(step(VK_SCROLL,MAKE)==1); reenterTake=1;
    assert(step(VK_SCROLL,BREAK)==1); assert(!holdPending && !reenterTake); removeHooks();
    install(); token=tap(); reenterPeek=1; removeHooks();
    assert(!reenterPeek && !holdRemoving); install(); removeHooks();
    /* Each failed unhook retains its exact function and chain pointer. */
    install(); failKeyRemove=1; assert(!HoldRemove());
    assert(holdKeyLive && holdRecordLive && holdKeyProc && nextHoldKey==priorKey);
    failKeyRemove=0; failRecordRemove=1; assert(!HoldRemove());
    assert(!holdKeyLive && holdRecordLive && holdRecordProc && nextHoldRecord==priorRecord);
    failRecordRemove=0; removeHooks();
    /* IdleRemove and IdleInstall do not change independent Hold ownership. */
    install(); assert(IdleInstall()); assert(installed && holdKeyLive);
    assert(IdleRemove()); assert(!installed && holdKeyLive && holdRecordLive);
    token=tap(); assert(HoldTake(TARGET,token)); assert(IdleInstall()); removeHooks();
    assert(installed); assert(IdleRemove());
    /* WEP is abnormal best effort and must detach even an owned down. */
    install(); assert(step(VK_SCROLL,MAKE)==1); task=(HTASK)2; WEP(0);
    assert(!holdKeyLive && !holdRecordLive); task=(HTASK)1;
    install(); assert(step(VK_SCROLL,MAKE)==1); before=peeks; WEP(0);
    assert(!holdKeyLive && !holdRecordLive && peeks==before);
    printf("PASS: Hold ownership, chaining, NOREMOVE, make/repeat/break, modifiers, input cancellation, modal guards, tokens, expiry, deferred removal, reentry, partial failures, idle independence and WEP (%u callbacks, %u post attempts)\n",chains,posts);
    return 0;
}
