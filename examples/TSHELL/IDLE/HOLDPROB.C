/* Native cross-task Hold probe, deliberately excluded from runtime package. */
#define WINVER 0x0300
#include <windows.h>
#include "TSINPUT.H"
#define REQUEST (WM_USER+9)
static HINSTANCE dll;
static HOLDINSTALLPROC installHold;
static IDLEBOOLPROC removeHold, installIdle, removeIdle, readyIdle;
static IDLEGENPROC generation;
static HOLDPOLICYPROC policy;
static HOLDTAKEPROC take;
static HWND ownerWindow;
static BOOL sink, peeking, exiting, idleOn;
static int control;
static unsigned requests, accepted, received;
static void logLine(LPSTR text)
{
    HFILE f=_lopen("C:\\HOLD.LOG",1);
    if (f==HFILE_ERROR) f=_lcreat("C:\\HOLD.LOG",0);
    if (f!=HFILE_ERROR) {
        _llseek(f,0L,2); _lwrite(f,text,lstrlen(text)); _lclose(f);
    }
}
static BOOL loadHook(void)
{
    char line[96];
    dll=LoadLibrary("TSINPUT.DLL");
    if (dll<32) { logLine("LOAD FAILED\r\n"); dll=NULL; return FALSE; }
    installHold=(HOLDINSTALLPROC)GetProcAddress(dll,"HoldInstall");
    removeHold=(IDLEBOOLPROC)GetProcAddress(dll,"HoldRemove");
    policy=(HOLDPOLICYPROC)GetProcAddress(dll,"HoldPolicy");
    take=(HOLDTAKEPROC)GetProcAddress(dll,"HoldTake");
    installIdle=(IDLEBOOLPROC)GetProcAddress(dll,"IdleInstall");
    removeIdle=(IDLEBOOLPROC)GetProcAddress(dll,"IdleRemove");
    readyIdle=(IDLEBOOLPROC)GetProcAddress(dll,"IdleReady");
    generation=(IDLEGENPROC)GetProcAddress(dll,"IdleGeneration");
    if (!installHold || !removeHold || !policy || !take || !installIdle ||
        !removeIdle || !readyIdle || !generation) { logLine("EXPORT FAILED\r\n"); return FALSE; }
    wsprintf(line,"HOLD INSTALL %u OWNER %u TASK %u\r\n",installHold(ownerWindow,REQUEST,TRUE),ownerWindow,GetCurrentTask());
    logLine(line); return TRUE;
}
static BOOL unloadHook(void)
{
    if (!dll) return TRUE;
    if (idleOn && !removeIdle()) { logLine("IDLE REMOVE DEFERRED\r\n"); return FALSE; }
    idleOn=FALSE;
    if (!removeHold()) { logLine("HOLD REMOVE DEFERRED\r\n"); return FALSE; }
    FreeLibrary(dll); dll=NULL; logLine("HOLD REMOVED UNLOADED\r\n"); return TRUE;
}
static void readControl(HWND w)
{
    HFILE f;
    char ch, line[128];
    int c=0;
    DWORD start;
    f=_lopen("C:\\HOLCTRL.TXT",0);
    if (f!=HFILE_ERROR) { if (_lread(f,&ch,1)==1) c=ch; _lclose(f); }
    if (c==control) return;
    control=c;
    wsprintf(line,"CONTROL %c %s T%lu\r\n",c,sink?(LPSTR)"SINK":(LPSTR)"OWNER",GetTickCount()); logLine(line);
    if (sink) {
        if (c=='P') { peeking=TRUE; logLine("PEEK MODE\r\n"); }
        if (c=='N') { peeking=FALSE; logLine("GET MODE\r\n"); }
        if (c=='M') MessageBox(w,"External application dialog. Hold must pass through.","HoldProbe dialog",MB_OK);
        if (c=='S') MessageBox(w,"System modal. Hold must pass through.","HoldProbe system",MB_OK|MB_SYSTEMMODAL);
        if (c=='B') {
            logLine("BUSY START\r\n"); start=GetTickCount();
            while ((DWORD)(GetTickCount()-start)<3500L) ;
            logLine("BUSY END\r\n");
        }
        if (c=='4') DestroyWindow(w);
        return;
    }
    if (c=='1') { policy(w,FALSE); logLine("POLICY BLOCK\r\n"); }
    if (c=='2') { policy(w,TRUE); logLine("POLICY ALLOW\r\n"); }
    if (c=='3') { if (unloadHook()) loadHook(); }
    if (c=='I') { idleOn=installIdle(); logLine("IDLE INSTALL\r\n"); }
    if (c=='J') { if(removeIdle()) idleOn=FALSE; logLine("IDLE REMOVE\r\n"); }
    if (c=='4') { exiting=TRUE; if(unloadHook()) DestroyWindow(w); }
}
LONG FAR PASCAL ProbeProc(HWND w, UINT msg, WPARAM wp, LPARAM lp)
{
    char line[160];
    BOOL okay;
    PAINTSTRUCT paint;
    HDC dc;
    switch (msg) {
    case WM_KEYDOWN: case WM_KEYUP: case WM_SYSKEYDOWN: case WM_SYSKEYUP:
        ++received;
        wsprintf(line,"RECV %s MSG%04X VK%04X LP%08lX T%lu\r\n",sink?(LPSTR)"SINK":(LPSTR)"OWNER",msg,wp,lp,GetTickCount());
        logLine(line); break;
    case REQUEST:
        ++requests; okay=take(w,(DWORD)lp); if (okay) ++accepted;
        wsprintf(line,"REQUEST %u TOKEN%lu TAKE%u AGAIN%u ACTIVE%u T%lu\r\n",requests,(DWORD)lp,okay,take(w,(DWORD)lp),GetActiveWindow(),GetTickCount());
        logLine(line); return 0;
    case WM_TIMER:
        readControl(w);
        if (!sink && exiting && dll && unloadHook()) DestroyWindow(w);
        if (!sink && dll && idleOn) {
            okay=readyIdle();
            wsprintf(line,"IDLE READY%u GEN%lu T%lu\r\n",okay,generation(),GetTickCount()); logLine(line);
        }
        return 0;
    case WM_PAINT:
        dc=BeginPaint(w,&paint);
        TextOut(dc,10,10,"Hold input receiver",19);
        TextOut(dc,10,30,"Plain Hold should not appear in receiver log.",43);
        EndPaint(w,&paint); return 0;
    case WM_CLOSE:
        if (!sink && !unloadHook()) { exiting=TRUE; return 0; }
        DestroyWindow(w); return 0;
    case WM_DESTROY:
        KillTimer(w,1); PostQuitMessage(0); return 0;
    }
    return DefWindowProc(w,msg,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
    WNDCLASS c;
    HWND w;
    MSG msg, preview;
    char line[128];
    int result;
    sink=cmd && cmd[0]=='s';
    c.style=0; c.lpfnWndProc=ProbeProc; c.cbClsExtra=c.cbWndExtra=0;
    c.hInstance=inst; c.hIcon=NULL; c.hCursor=LoadCursor(NULL,IDC_ARROW);
    c.hbrBackground=(HBRUSH)(COLOR_WINDOW+1); c.lpszMenuName=NULL;
    c.lpszClassName=sink?(LPSTR)"HoldSink":(LPSTR)"HoldOwner";
    if(!RegisterClass(&c)) return 1;
    w=CreateWindow(c.lpszClassName,sink?(LPSTR)"Hold receiver":(LPSTR)"Hold owner",WS_OVERLAPPEDWINDOW,
        10,10,600,180,NULL,NULL,inst,NULL);
    if(!w) return 2;
    if(sink) { ShowWindow(w,SW_SHOWNORMAL); UpdateWindow(w); }
    else { ownerWindow=w; if(!loadHook()) return 3; WinExec("C:\\WINDOWS\\HOLDPROB.EXE sink",SW_SHOWNORMAL); }
    SetTimer(w,1,250,NULL);
    wsprintf(line,"START %s HWND%u TASK%u\r\n",sink?(LPSTR)"SINK":(LPSTR)"OWNER",w,GetCurrentTask());logLine(line);
    while(TRUE) {
        if(peeking) {
            if(!PeekMessage(&preview,NULL,0,0,PM_NOREMOVE)) { WaitMessage(); continue; }
            if(preview.message>=WM_KEYFIRST && preview.message<=WM_KEYLAST) {
                wsprintf(line,"PEEK MSG%04X VK%04X LP%08lX\r\n",preview.message,preview.wParam,preview.lParam);logLine(line);
            }
        }
        result=GetMessage(&msg,NULL,0,0);
        if(!result) break;
        TranslateMessage(&msg); DispatchMessage(&msg);
    }
    return 0;
}
