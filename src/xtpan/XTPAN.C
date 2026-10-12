/* XTPAN.C - task-time panning helper for XTPAN.DRV (Windows 3.0 real mode).
 *
 * The driver presents a 320x400 desktop through a 320x200 viewport and pans
 * only when asked through its Control escape (XTPAN_ESC). This helper asks,
 * from an ordinary timer message, so no redraw ever runs in the mouse or
 * timer interrupt:
 *   - edge dwell: the pointer rests in the bottom (top) edge band of the
 *     viewport for Dwell ms -> one Step down (up); repeats while it stays;
 *   - the pointer outside the viewport (fast motion) -> pan at once, in
 *     whole Steps, so the pointer and the click target are always visible;
 *   - keys (polled with GetAsyncKeyState): KeyMods + KeyDown / KeyUp /
 *     KeyTop (default Ctrl+Alt+PgDn / PgUp / Home);
 *   - FollowActive: a newly activated window that is not wholly visible is
 *     brought into view (dialogs are centred on the 400-row desktop).
 * Settings: WIN.INI [XTPan]. Enabled=0 makes the helper exit at once.
 * With any other display driver the escape is unsupported and the helper
 * exits quietly. C89, /G0 /Gw /AS.
 */
#include <windows.h>

#define XTPAN_ESC 0x5850
#define QUERYESC 8

static HWND hMain;
static int nStep, nDwell, nEdge, nMods, vkDown, vkUp, vkTop, bFollow;
static int nTop, nView = 200, nLogical = 400;
static int nEdgeDir;
static DWORD dwEdgeSince;
static int bKeyWasDown;
static HWND hLastActive;
static char szLog[80];

static void LogLine(LPSTR text)
{
    int fh;
    OFSTRUCT of;
    if (!szLog[0])
        return;
    fh = OpenFile(szLog, &of, OF_WRITE);
    if (fh == -1)
        fh = OpenFile(szLog, &of, OF_CREATE | OF_WRITE);
    if (fh == -1)
        return;
    _llseek(fh, 0L, 2);
    _lwrite(fh, text, lstrlen(text));
    _lwrite(fh, "\r\n", 2);
    _lclose(fh);
}

/* Windows 3.0 has only five cached DCs: take the screen DC per call. */
static int ScreenEscape(int esc, int cb, LPSTR in, LPSTR out)
{
    HDC hdc = GetDC(NULL);
    int r;
    if (!hdc)
        return 0;
    r = Escape(hdc, esc, cb, in, out);
    ReleaseDC(NULL, hdc);
    return r;
}

static int PanEscape(int want)
{
    int out[3];
    out[0] = nTop;
    out[1] = nView;
    out[2] = nLogical;
    if (ScreenEscape(XTPAN_ESC, sizeof(int), (LPSTR)&want, (LPSTR)out) <= 0)
        return -1;
    nTop = out[0];
    nView = out[1];
    nLogical = out[2];
    return nTop;
}

/* After a pan the pointer did not cause (keys, follow), keep the pointer
 * inside the viewport so that what is clicked is always what is shown. */
static void KeepPointer(void)
{
    POINT pt;
    GetCursorPos(&pt);
    if (pt.y < nTop)
        SetCursorPos(pt.x, nTop + nEdge);
    else if (pt.y >= nTop + nView)
        SetCursorPos(pt.x, nTop + nView - 1 - nEdge);
}

static void PanTo(int want, LPSTR why)
{
    char buf[96];
    int from = nTop;
    DWORD t0, t1;
    if (want < 0)
        want = 0;
    if (want > nLogical - nView)
        want = nLogical - nView;
    if (want == nTop)
        return;
    t0 = GetCurrentTime();
    PanEscape(want);
    t1 = GetCurrentTime();
    wsprintf(buf, "PAN %d %d %s t=%lu ms=%lu", from, nTop, why, t0, t1 - t0);
    LogLine(buf);
}

static int StepDown(int y)      /* smallest top in Steps that shows row y */
{
    int t = nTop;
    while (y >= t + nView)
        t += nStep;
    return t;
}

static int StepUp(int y)
{
    int t = nTop;
    while (y < t)
        t -= nStep;
    return t;
}

/* Bit 15: down now; bit 0: pressed since the previous call. A short tap
 * between two 55 ms ticks shows only in bit 0. Every key is read on every
 * tick so that bit 0 never carries over from an older press. */
static int Hit(int vk)
{
    return (GetAsyncKeyState(vk) & 0x8001) != 0;
}

static int Held(int vk)
{
    return (GetAsyncKeyState(vk) & 0x8000) != 0;
}

static void Keys(void)
{
    int ctl = Hit(VK_CONTROL), alt = Hit(VK_MENU), sh = Hit(VK_SHIFT);
    int dn = Hit(vkDown), up = Hit(vkUp), tp = Hit(vkTop);
    int mods = (!(nMods & 1) || ctl) && (!(nMods & 2) || alt) && (!(nMods & 4) || sh);
    int which = 0;
    if (mods)
        which = dn ? 1 : up ? 2 : tp ? 3 : 0;
    if (which && !bKeyWasDown) {
        if (which == 1)
            PanTo(nTop + nStep, "key-down");
        else if (which == 2)
            PanTo(nTop - nStep, "key-up");
        else
            PanTo(0, "key-top");
        KeepPointer();
    }
    /* a key still held down does not repeat the pan */
    bKeyWasDown = which && Held(which == 1 ? vkDown : which == 2 ? vkUp : vkTop);
}

static void Follow(void)
{
    HWND h = GetActiveWindow();
    RECT r;
    int t;
    if (h == hLastActive)
        return;
    hLastActive = h;
    if (!h || !bFollow || IsIconic(h))
        return;
    GetWindowRect(h, &r);
    if (r.top >= nTop && r.bottom <= nTop + nView)
        return;
    t = nTop;
    if (r.bottom - r.top <= nView) {
        while (r.bottom > t + nView)
            t += nStep;
        while (r.top < t)
            t -= nStep;
    } else {
        t = (r.top / nStep) * nStep;
    }
    PanTo(t, "follow");
    KeepPointer();
}

static void Tick(void)
{
    POINT pt;
    int dir = 0;
    DWORD now = GetCurrentTime();
    Keys();
    Follow();
    GetCursorPos(&pt);
    if (pt.y >= nTop + nView) {
        PanTo(StepDown(pt.y), "outside");
        nEdgeDir = 0;
        return;
    }
    if (pt.y < nTop) {
        PanTo(StepUp(pt.y), "outside");
        nEdgeDir = 0;
        return;
    }
    if (pt.y >= nTop + nView - nEdge && nTop < nLogical - nView)
        dir = 1;
    else if (pt.y < nTop + nEdge && nTop > 0)
        dir = -1;
    if (dir != nEdgeDir) {
        nEdgeDir = dir;
        dwEdgeSince = now;
        return;
    }
    if (dir && now - dwEdgeSince >= (DWORD)nDwell) {
        PanTo(nTop + dir * nStep, dir > 0 ? "dwell-down" : "dwell-up");
        dwEdgeSince = now;
    }
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    switch (msg) {
    case WM_TIMER:
        Tick();
        return 0;
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

int PASCAL WinMain(HANDLE hInst, HANDLE hPrev, LPSTR lpCmd, int nShow)
{
    WNDCLASS wc;
    MSG msg;
    int esc = XTPAN_ESC;
    char buf[96];

    if (hPrev)
        return 0;
    if (!GetProfileInt("XTPan", "Enabled", 1))
        return 0;
    nStep = GetProfileInt("XTPan", "Step", 50);
    nDwell = GetProfileInt("XTPan", "Dwell", 400);
    nEdge = GetProfileInt("XTPan", "Edge", 3);
    nMods = GetProfileInt("XTPan", "KeyMods", 3);
    vkDown = GetProfileInt("XTPan", "KeyDown", VK_NEXT);
    vkUp = GetProfileInt("XTPan", "KeyUp", VK_PRIOR);
    vkTop = GetProfileInt("XTPan", "KeyTop", VK_HOME);
    bFollow = GetProfileInt("XTPan", "FollowActive", 1);
    GetProfileString("XTPan", "LogFile", "", szLog, sizeof(szLog));
    if (nStep < 8)
        nStep = 8;
    if (nEdge < 1)
        nEdge = 1;

    if (ScreenEscape(QUERYESC, sizeof(int), (LPSTR)&esc, NULL) <= 0 || PanEscape(-1) < 0) {
        LogLine("START no XTPAN driver: helper exits");
        return 0;
    }
    wsprintf(buf, "START top=%d view=%d logical=%d step=%d dwell=%d edge=%d free=%lu",
             nTop, nView, nLogical, nStep, nDwell, nEdge, GetFreeSpace(0));
    LogLine(buf);

    wc.style = 0;
    wc.lpfnWndProc = WndProc;
    wc.cbClsExtra = 0;
    wc.cbWndExtra = 0;
    wc.hInstance = hInst;
    wc.hIcon = NULL;
    wc.hCursor = NULL;
    wc.hbrBackground = NULL;
    wc.lpszMenuName = NULL;
    wc.lpszClassName = "XTPan";
    if (!RegisterClass(&wc))
        return 0;
    hMain = CreateWindow("XTPan", "XTPan", WS_POPUP, 0, 0, 0, 0, NULL, NULL, hInst, NULL);
    if (!hMain || !SetTimer(hMain, 1, 55, NULL))
        return 0;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return msg.wParam;
}
