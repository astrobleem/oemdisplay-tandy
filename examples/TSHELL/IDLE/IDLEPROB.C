/* Native Windows 3.0 probe; not shipped or loaded by TSHELL. */
#define WINVER 0x0300
#include <windows.h>
#include "TSINPUT.H"
static HINSTANCE dll;
static IDLEBOOLPROC installHook, removeHook, readyHook;
static IDLEGENPROC generationHook;
static DWORD started;
static unsigned ownerKeys, ownerMouse, ticks;
static int lastControl;

static void logLine(LPSTR line)
{
    HFILE file = _lopen("C:\\IDLE.LOG", 1);
    if (file == HFILE_ERROR) file = _lcreat("C:\\IDLE.LOG", 0);
    if (file != HFILE_ERROR) {
        _llseek(file, 0L, 2); _lwrite(file, line, lstrlen(line)); _lclose(file);
    }
}
static BOOL loadHook(void)
{
    char line[128];
    dll = LoadLibrary("TSINPUT.DLL");
    if (dll < 32) { logLine("LOAD FAILED\r\n"); return FALSE; }
    installHook = (IDLEBOOLPROC)GetProcAddress(dll, "IdleInstall");
    removeHook = (IDLEBOOLPROC)GetProcAddress(dll, "IdleRemove");
    readyHook = (IDLEBOOLPROC)GetProcAddress(dll, "IdleReady");
    generationHook = (IDLEGENPROC)GetProcAddress(dll, "IdleGeneration");
    if (!installHook || !removeHook || !readyHook || !generationHook) {
        logLine("EXPORT FAILED\r\n"); FreeLibrary(dll); dll = NULL; return FALSE;
    }
    wsprintf(line, "INSTALL %d DUPLICATE %d\r\n", installHook(), installHook());
    logLine(line);
    return TRUE;
}
static BOOL unloadHook(void)
{
    if (!dll) return TRUE;
    if (!removeHook()) { logLine("REMOVE FAILED; RETAINING DLL\r\n"); return FALSE; }
    FreeLibrary(dll); dll = NULL; logLine("REMOVED AND UNLOADED\r\n");
    return TRUE;
}
LONG FAR PASCAL ProbeProc(HWND w, UINT msg, WPARAM wp, LPARAM lp)
{
    char line[160], cls[32];
    HWND active;
    BOOL ready;
    int control, held;
    DWORD before;
    POINT cursor;
    HFILE controlFile;
    char controlChar;
    switch (msg) {
    case WM_KEYDOWN: case WM_SYSKEYDOWN: ++ownerKeys; break;
    case WM_MOUSEMOVE: ++ownerMouse; break;
    case WM_TIMER:
        ++ticks;
        control = 0;
        controlFile = _lopen("C:\\IDLECTRL.TXT", 0);
        if (controlFile != HFILE_ERROR) {
            if (_lread(controlFile, &controlChar, 1) == 1) control = controlChar - '0';
            _lclose(controlFile);
        }
        if (control != lastControl) {
            lastControl = control;
            if (control == 1) {
                before = GetTickCount();
                while ((DWORD)(GetTickCount() - before) < 6100L) ;
                logLine("SIMULATED TIMER GAP\r\n");
            } else if (control == 2) {
                if (unloadHook()) loadHook();
            } else if (control == 3) {
                /* Deliberate abnormal unload tests the WEP fallback. */
                FreeLibrary(dll); dll = NULL;
                logLine("WEP UNLOAD\r\n"); loadHook();
            } else if (control == 4) {
                DestroyWindow(w); return 0;
            } else if (control == 5) {
                MessageBox(w, "Idle probe system-modal test", "Probe", MB_OK | MB_SYSTEMMODAL);
            } else if (control == 6) {
                wsprintf(line, "DOS EXEC %u\r\n", WinExec("C:\\DOSWAIT.COM", SW_SHOWNORMAL));
                logLine(line);
            }
        }
        ready = readyHook();
        cls[0] = 0;
        active = GetActiveWindow();
        if (active) GetClassName(active, cls, sizeof(cls));
        for (held=8; held < 256; ++held) if (GetAsyncKeyState(held) & 0x8000) break;
        GetCursorPos(&cursor);
        wsprintf(line, "CURSOR %d %d\r\n", cursor.x, cursor.y); logLine(line);
        wsprintf(line, "T %u MS %lu GEN %lu READY %d OWNERKEY %u OWNERMOUSE %u ACTIVE %s CAP %u SYS %u HELD %u MOUSE %u\r\n",
            ticks, GetTickCount() - started, generationHook(), ready,
            ownerKeys, ownerMouse, (LPSTR)cls, GetCapture(), GetSysModalWindow(), held,
            (GetKeyState(VK_LBUTTON) | GetKeyState(VK_RBUTTON) | GetKeyState(VK_MBUTTON)) & 0x8000);
        logLine(line);
        return 0;
    case WM_DESTROY:
        KillTimer(w, 1); unloadHook(); PostQuitMessage(0); return 0;
    }
    return DefWindowProc(w, msg, wp, lp);
}
int PASCAL WinMain(HINSTANCE inst, HINSTANCE prev, LPSTR cmd, int show)
{
    WNDCLASS c;
    HWND w;
    MSG msg;
    if (!loadHook()) return 1;
    c.style = 0; c.lpfnWndProc = ProbeProc; c.cbClsExtra = c.cbWndExtra = 0;
    c.hInstance = inst; c.hIcon = NULL; c.hCursor = NULL;
    c.hbrBackground = NULL; c.lpszMenuName = NULL; c.lpszClassName = "IdleProbe";
    if (!RegisterClass(&c)) { unloadHook(); return 2; }
    w = CreateWindow("IdleProbe", "IdleProbe", WS_OVERLAPPED,
        0, 0, 100, 50, NULL, NULL, inst, NULL);
    if (!w) { unloadHook(); return 3; }
    started = GetTickCount();
    if (!SetTimer(w, 1, 1000, NULL)) { DestroyWindow(w); return 4; }
    logLine("PROBE START; HIDDEN OWNER; LAUNCH NOTEPAD\r\n");
    WinExec("NOTEPAD.EXE", SW_SHOWNORMAL);
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg); DispatchMessage(&msg);
    }
    return 0;
}
