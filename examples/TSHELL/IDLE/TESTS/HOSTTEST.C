#include <assert.h>
#include <stdio.h>
#include <string.h>
#define TSINPUT_HOST
#include "../TSINPUT.C"
static unsigned installs, removals, chains, asyncCalls;
static BOOL removeOK = 1, exportOK = 1;
static HTASK task = (HTASK)1;
static DWORD tick = 10;
static DWORD dosTick = 10;
static HWND capture, modal;
static HWND windowOwner;
static BOOL windowEnabled=TRUE;
static char *activeName = "Notepad";
static int held[256], mouse[8];
static FARPROC chainExpected;
static void prior(void) {}
DWORD DefHookProc(int code, WORD wp, DWORD lp, FARPROC *next) {
    (void)code; (void)wp; (void)lp;
    ++chains; assert(*next == chainExpected); return 0x789;
}
HTASK GetCurrentTask(void) { return task; }
FARPROC GetProcAddress(HINSTANCE h, LPSTR name) {
    assert(h == (HINSTANCE)123); assert(!strcmp(name,"IdleRecord"));
    return exportOK ? (FARPROC)IdleRecord : NULL;
}
DWORD GetTickCount(void) { return tick; }
DWORD ReadDosClock(void) { return dosTick; }
FARPROC SetWindowsHook(int type, FARPROC fn) {
    assert(type == WH_JOURNALRECORD); assert(fn == (FARPROC)IdleRecord);
    ++installs; return chainExpected;
}
BOOL UnhookWindowsHook(int type, FARPROC fn) {
    assert(type == WH_JOURNALRECORD); assert(fn == (FARPROC)IdleRecord);
    ++removals; return removeOK;
}
HWND GetSysModalWindow(void) { return modal; }
HWND GetCapture(void) { return capture; }
HWND GetActiveWindow(void) { return (HWND)1; }
int GetClassName(HWND h, LPSTR dst, int count) {
    (void)h; strncpy(dst, activeName, count); return strlen(activeName);
}
int GetKeyState(int key) { assert(key < 8); return mouse[key]; }
int GetAsyncKeyState(int key) { assert(key >= 8 && key < 256); ++asyncCalls; return held[key]; }
void GetCursorPos(POINT *p) { p->x=320; p->y=100; }
HWND GetWindow(HWND w, WORD kind) { (void)w; assert(kind==GW_OWNER); return windowOwner; }
BOOL IsWindowEnabled(HWND w) { assert(w==windowOwner); return windowEnabled; }
static void event(WORD msg) {
    EVENTMSG e; e.message = msg; e.paramL = 65; e.paramH = 0;
    assert(IdleRecord(HC_ACTION, 0, (DWORD)&e) == 0x789);
}
int main(void) {
    DWORD gen;
    LibMain((HINSTANCE)123,0,0,NULL);
    assert(!IdleReady()); assert(IdleRemove());
    exportOK=0; assert(!IdleInstall()); assert(!installs); exportOK=1;
    assert(IdleInstall()); assert(installs==1); assert(IdleInstall()); assert(installs==1);
    gen=IdleGeneration(); assert(!IdleReady()); assert(IdleGeneration()==gen+1);
    {
        EVENTMSG e; e.message=WM_MOUSEMOVE; e.paramL=320; e.paramH=100;
        gen=IdleGeneration(); IdleRecord(HC_ACTION,0,(DWORD)&e);
        assert(IdleGeneration()==gen); assert(!seenInput);
    }
    /* Foreign task cannot steal ownership, duplicate hook, or remove it. */
    task=(HTASK)2; assert(!IdleInstall()); assert(!IdleRemove()); assert(!IdleReady());
    assert(installs==1 && removals==0); task=(HTASK)1;
    /* Negative/unknown codes must chain unchanged without touching lParam. */
    gen=IdleGeneration(); assert(IdleRecord(-1,1,(DWORD)1)==0x789);
    assert(IdleRecord(99,1,(DWORD)1)==0x789); assert(IdleGeneration()==gen);
    event(WM_KEYDOWN); assert(!IdleReady());
    event(WM_KEYDOWN); assert(heldKeys==1); event(WM_KEYUP);
    assert(IdleReady()); gen=IdleGeneration();
    event(0x1234); assert(IdleGeneration()==gen);
    event(WM_MOUSEMOVE); assert(IdleGeneration()==gen+1);
    event(WM_MOUSEMOVE); assert(IdleGeneration()==gen+1);
    event(WM_LBUTTONDOWN); assert(!IdleReady());
    event(WM_LBUTTONUP); assert(IdleReady());
    event(WM_RBUTTONDBLCLK); assert(!IdleReady()); event(WM_RBUTTONUP); assert(IdleReady());
    event(WM_MBUTTONDOWN); assert(!IdleReady()); event(WM_MBUTTONUP); assert(IdleReady());
    /* Ordinary polls do not consume ANY GetAsyncKeyState low bits. */
    assert(asyncCalls==248); held[255]=1; assert(IdleReady()); assert(asyncCalls==248); held[255]=0;
    capture=(HWND)1; assert(!IdleReady()); capture=NULL; assert(IdleReady());
    modal=(HWND)1; assert(!IdleReady()); modal=NULL; assert(!IdleReady());
    event(WM_KEYDOWN); assert(!IdleReady()); event(WM_KEYUP); assert(IdleReady());
    activeName="#32770"; assert(!IdleReady()); activeName="Notepad"; assert(IdleReady());
    windowOwner=(HWND)2; windowEnabled=FALSE; assert(!IdleReady());
    windowEnabled=TRUE; assert(IdleReady()); windowOwner=NULL;
    /* Header-only later hook codes are ignored, but still chained. */
    gen=IdleGeneration(); IdleRecord(HC_SYSMODALON,0,0); IdleRecord(HC_SYSMODALOFF,0,0);
    assert(IdleGeneration()==gen);
    tick += 2000; assert(IdleReady()); gen=IdleGeneration();
    tick += 2001; assert(!IdleReady()); assert(IdleGeneration()==gen+1);
    tick += 1000; assert(!IdleReady()); event(WM_MOUSEMOVE); assert(!IdleReady());
    event(WM_LBUTTONDOWN); event(WM_LBUTTONUP); assert(IdleReady());
    lastPoll=(DWORD)-500; tick=100; assert(IdleReady());
    /* Independent DOS time catches suspended Windows ticks. */
    dosTick += 250; assert(IdleReady());
    dosTick += 251; assert(!IdleReady());
    event(WM_KEYDOWN); event(WM_KEYUP); assert(IdleReady());
    dosTick += 12000; assert(!IdleReady());
    event(WM_KEYUP); assert(IdleReady());
    /* Backwards clock changes and midnight reset conservatively. */
    --dosTick; assert(!IdleReady()); event(WM_KEYUP); assert(IdleReady());
    lastDos=86399990; dosTick=10; assert(!IdleReady());
    event(WM_KEYUP); assert(IdleReady());
    removeOK=0; assert(!IdleRemove()); assert(installed && owner==task && recordProc);
    removeOK=1; assert(IdleRemove()); assert(!installed && !owner && !recordProc);
    assert(IdleRemove());
    /* Nonempty previous chain is retained; WEP uses no owner-task check. */
    held[65]=0x8000; mouse[VK_LBUTTON]=0x8000;
    chainExpected=prior; assert(IdleInstall()); event(WM_MOUSEMOVE); assert(!IdleReady());
    event(WM_LBUTTONUP); assert(!IdleReady()); event(WM_KEYUP); assert(IdleReady());
    assert(nextRecord==prior); task=(HTASK)2; WEP(0); assert(!installed);
    printf("PASS: ownership, duplicate suppression, hook chaining, held input, modal/capture guards, poll gap, tick wrap, DOS suspension, midnight/backward clocks, remove failure, WEP (%u chained callbacks)\n",chains);
    return 0;
}
