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
 *     KeyTop (default Alt+PgDn / Alt+PgUp / Alt+F9. Not Shift: with Shift a
 *     keypad key (PgDn, Home on XT/Tandy keyboards) arrives as a digit or
 *     wrapped in transient "Shift up" codes. Not Ctrl+Alt: Ctrl+Alt+PgDn is
 *     the fullscreen hotkey of 86Box and other emulators. NumLock off.);
 *   - FollowActive: a newly activated window that is not wholly visible is
 *     brought into view with the smallest exact move (FollowTop; dialogs
 *     are centred on the 400-row desktop).
 * Settings: WIN.INI [XTPan]. Enabled=0 makes the helper exit at once.
 * "PANCFG SETTINGS" (or XTPAN /SETTINGS) opens the shared panning settings
 * window of the running helper (PANDLG.C); it adds no timer and no hook.
 * With any other display driver the escape is unsupported and the helper
 * exits quietly. C89, /G0 /Gw /AS.
 */
#include <windows.h>
#include "PANDLG.H"
#include "WDWIN.H"

#define XTPAN_ESC 0x5850
#define QUERYESC 8

static HWND hMain;
static int nStep, nDwell, nEdge, nMods, vkDown, vkUp, vkTop, bFollow;
static int nTop, nView = 200, nLogical = 400;
static int nEdgeDir;
static DWORD dwEdgeSince;
static int bKeyWasDown;
static int bLogKeys;
static DWORD dwSeen[3];         /* last time Ctrl, Alt, Shift was seen down */
static HWND hLastActive;
static char szLog[80];
static HANDLE hInstance;
static UINT uOpenMsg;
static PANHOST host;
static int bDesk, nDeskX, nDeskW, nDeskArrow;

static void DeskRefresh(void)
{
    WDWinViewport(&nDeskX, &nTop);
}

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
    int x, y;
    GetCursorPos(&pt);
    if (bDesk) {
        x = pt.x;y = pt.y;
        if (pt.x < 0) pt.x = 0;
        if (pt.x >= nDeskW) pt.x = nDeskW - 1;
        if (pt.y < 0) pt.y = 0;
        if (pt.y >= nView) pt.y = nView - 1;
        if (x != pt.x || y != pt.y) SetCursorPos(pt.x, pt.y);
        return;
    }
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
    if (bDesk) {
        (void)WDWinPan(nDeskX, want);
        DeskRefresh();
        return;
    }
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

/* A modifier counts if it was seen down within the last 250 ms: keyboard
 * paths that wrap grey navigation keys in transient "Shift up" codes, or a
 * modifier pressed one tick before the key, must not lose the press. */
static int Recent(int i, int now_down, DWORD now)
{
    if (now_down)
        dwSeen[i] = now;
    return dwSeen[i] && now - dwSeen[i] <= 250;
}

static void Keys(void)
{
    DWORD now = GetCurrentTime();
    int ctl = Hit(VK_CONTROL), alt = Hit(VK_MENU), sh = Hit(VK_SHIFT);
    int dn = Hit(vkDown), up = Hit(vkUp), tp = Hit(vkTop);
    int mods = (!(nMods & 1) || Recent(0, ctl, now)) && (!(nMods & 2) || Recent(1, alt, now)) &&
               (!(nMods & 4) || Recent(2, sh, now));
    int which = 0;
    if (bLogKeys && (ctl || alt || sh || dn || up || tp)) {
        char buf[64];
        wsprintf(buf, "KEYS t=%lu ctl=%d alt=%d sh=%d dn=%d up=%d tp=%d was=%d",
                 GetCurrentTime(), ctl, alt, sh, dn, up, tp, bKeyWasDown);
        LogLine(buf);
    }
    if (mods)
        which = dn ? 1 : up ? 2 : tp ? 3 : 0;
    if (which && !bKeyWasDown) {
        if (which == 1)
            PanTo(nTop + nStep, "key-down");
        else if (which == 2)
            PanTo(nTop - nStep, "key-up");
        else if (bDesk) {
            (void)WDWinHome();
            DeskRefresh();
        } else
            PanTo(0, "key-top");
        KeepPointer();
    }
    /* a key still held down does not repeat the pan */
    bKeyWasDown = which && Held(which == 1 ? vkDown : which == 2 ? vkUp : vkTop);
}

/* The viewport top that brings window rows [wtop, wbot) into view with the
 * smallest move: exact rows, not Steps (a 190-row window at rows 30..220
 * seen from top 0 needs top 20; whole 50-row steps would give 50 and then,
 * to show row 30, 0 again, leaving it cut off). A window taller than the
 * viewport shows its top (title bar). The result is clamped to the
 * desktop, so a window hanging off the desktop is shown as far as it can
 * be. Pure arithmetic: HOSTTEST.PY runs the same rule. */
static int FollowTop(int top, int view, int logical, int wtop, int wbot)
{
    int t = top;
    if (wbot - wtop > view)
        t = wtop;
    else if (wbot > t + view)
        t = wbot - view;
    else if (wtop < t)
        t = wtop;
    if (t > logical - view)
        t = logical - view;
    if (t < 0)
        t = 0;
    return t;
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
    /* re-read the viewport: another program may have panned (Control
       escape), and the fit must start from the top really shown */
    PanEscape(-1);
    GetWindowRect(h, &r);
    if (r.top >= nTop && r.bottom <= nTop + nView)
        return;
    t = FollowTop(nTop, nView, nLogical, r.top, r.bottom);
    PanTo(t, "follow");
    KeepPointer();
}

static void FrameTick(void)
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

/* One existing timer, one selected engine. The framebuffer timer above is
 * left intact, including the exact softpan sync_helper transformation. */
static void Tick(void)
{
    POINT pt;
    int dx = 0, dy = 0, dir, arrows;
    DWORD now;
    if (!bDesk) { FrameTick(); return; }
    DeskRefresh();
    (void)WDWinPan(nDeskX, nTop); /* reconcile restores/open/close, no new timer */
    Keys();
    arrows = Held(VK_CONTROL) && Held(VK_MENU);
    if (arrows) {
        dx = Held(VK_RIGHT) - Held(VK_LEFT);
        dy = Held(VK_DOWN) - Held(VK_UP);
    }
    if ((dx || dy) && !nDeskArrow) {
        (void)WDWinPanBy(dx * nStep, dy * nStep);
        DeskRefresh();
    }
    nDeskArrow = dx || dy;
    KeepPointer();GetCursorPos(&pt);dx = dy = 0;
    if (pt.x < nEdge && nDeskX > 0) dx = -1;
    else if (pt.x >= nDeskW - nEdge && nDeskX < 2048 - nDeskW) dx = 1;
    if (pt.y < nEdge && nTop > 0) dy = -1;
    else if (pt.y >= nView - nEdge && nTop < 2048 - nView) dy = 1;
    dir = dx + 3 * dy;now = GetCurrentTime();
    if (dir != nEdgeDir) { nEdgeDir = dir;dwEdgeSince = now;return; }
    if (dir && now - dwEdgeSince >= (DWORD)nDwell) {
        (void)WDWinPanBy(dx * nStep, dy * nStep);DeskRefresh();dwEdgeSince = now;
    }
}

/* Settings window glue: the dialog edits what Tick() already uses. */
/* The command line is far; PANSET takes near strings. */
static void CopyArg(char *d, LPSTR s, int cap)
{
    int i = 0;
    while (s[i] && i < cap - 1) {
        d[i] = s[i];
        i++;
    }
    d[i] = 0;
}

static int IniGet(void *ctx, const char *sec, const char *key, int def)
{
    return (int)GetProfileInt(sec, key, def);
}

static int IniPut(void *ctx, const char *sec, const char *key, int value)
{
    char buf[12];
    wsprintf(buf, "%d", value);
    return WriteProfileString(sec, key, buf);
}

static int XtQuery(void *ctx, PANCAPS *c, PANSET *s)
{
    if (!bDesk && PanEscape(-1) < 0) {
        c->backend = PS_BACK_NONE;
        c->caps = 0;
        return 0;
    }
    c->backend = PS_BACK_VERT;
    c->caps = PanCapsFor(PS_BACK_VERT, 0);
    if (bDesk) {
        DeskRefresh();
        host.backend = WDWinDropped() ? "Window limit: close windows or use Home" :
                                        "Window workspace (24 windows)";
        c->caps = (c->caps & ~(PS_CAP_SOFT | PS_CAP_FOLLOW)) |
                  PS_CAP_MODE | PS_CAP_DESK;
    }
    c->viewX = bDesk ? nDeskX : 0;
    c->viewY = nTop;
    c->viewW = c->workW = GetSystemMetrics(SM_CXSCREEN);
    c->viewH = nView;
    c->workH = nLogical;
    if (bDesk) c->workW = 2048;
    PanSetDefaults(PS_BACK_VERT, s);
    s->step = nStep;
    s->dwell = nDwell;
    s->edge = nEdge;
    s->follow = bFollow != 0;
    if (bDesk) s->mode = PS_MODE_DESK;
    return 1;
}

static int XtApply(void *ctx, const PANSET *w, PANSET *actual, char *note, int cap)
{
    if (bDesk && w->mode != PS_MODE_DESK)
        return PS_E_APPLY;
    if (!bDesk && PanEscape(-1) < 0)
        return PS_E_LOST;
    nStep = w->step;
    nDwell = w->dwell;
    nEdge = w->edge;
    bFollow = w->follow;
    /* a pending edge dwell was timed with the old band and delay */
    nEdgeDir = 0;
    dwEdgeSince = GetCurrentTime();
    PanSetDefaults(PS_BACK_VERT, actual);
    actual->step = nStep;
    actual->dwell = nDwell;
    actual->edge = nEdge;
    actual->follow = bFollow;
    if (bDesk) actual->mode = PS_MODE_DESK;
    note[0] = 0;
    return PS_OK;
}

static int XtHome(void *ctx)
{
    if (bDesk) {
        int ok = WDWinHome() >= 0;
        DeskRefresh();KeepPointer();return ok;
    }
    if (PanEscape(-1) < 0)
        return 0;
    PanTo(0, "home");
    KeepPointer();
    return PanEscape(-1) >= 0 && nTop == 0;
}

static void OpenSettings(void)
{
    PanDlgOpen(hInstance, &host);
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    if (uOpenMsg && msg == uOpenMsg) {
        OpenSettings();
        return 0;
    }
    switch (msg) {
    case WM_QUERYENDSESSION:
        return !bDesk || WDWinPrepareShutdown() >= 0;
    case WM_ENDSESSION:
        if (wParam && bDesk) (void)WDWinShutdown();
        return 0;
    case WM_CLOSE:
        if (bDesk && WDWinShutdown() < 0) {
            MessageBox(hwnd, "Windows could not finish recovering a window. Use Home before closing the workspace.",
                       "Window workspace", MB_OK | MB_ICONEXCLAMATION);
            return 0;
        }
        DestroyWindow(hwnd);return 0;
    case WM_TIMER:
        Tick();
        PanDlgTrack();
        return 0;
    case WM_DESTROY:
        if (bDesk) (void)WDWinShutdown();
        PanDlgClose();
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
    char buf[96], arg[24];
    int settings;
    HWND hOwner;

    /* One owner: a second copy only asks the first to open its settings. */
    CopyArg(arg, lpCmd, sizeof(arg));
    settings = PanCmdParse(arg) == PS_CMD_SETTINGS;
    uOpenMsg = RegisterWindowMessage(PS_MSG_VERT);
    /* A fixed display can use either helper's linked window workspace.
     * Forward to its existing owner before starting a second tracker. */
    hOwner = FindWindow("XYOverviewControl", NULL);
    if (hOwner) {
        if (settings)
            PostMessage(hOwner, RegisterWindowMessage(PS_MSG_XY), 0, 0L);
        return 0;
    }
    switch (PanOwnerStart(hPrev != 0, settings)) {
    case PS_OWN_FORWARD:
        hOwner = FindWindow("XTPan", NULL);
        if (hOwner)
            PostMessage(hOwner, uOpenMsg, 0, 0L);
        return 0;
    case PS_OWN_EXIT:
        return 0;
    }
    if (!GetProfileInt("XTPan", "Enabled", 1))
        return 0;
    nStep = GetProfileInt("XTPan", "Step", 50);
    nDwell = GetProfileInt("XTPan", "Dwell", 400);
    nEdge = GetProfileInt("XTPan", "Edge", 3);
    nMods = GetProfileInt("XTPan", "KeyMods", 2);
    vkDown = GetProfileInt("XTPan", "KeyDown", VK_NEXT);
    vkUp = GetProfileInt("XTPan", "KeyUp", VK_PRIOR);
    vkTop = GetProfileInt("XTPan", "KeyTop", VK_F9);
    bFollow = GetProfileInt("XTPan", "FollowActive", 1);
    bLogKeys = GetProfileInt("XTPan", "LogKeys", 0);
    GetProfileString("XTPan", "LogFile", "", szLog, sizeof(szLog));
    if (nStep < 8)
        nStep = 8;
    if (nEdge < 1)
        nEdge = 1;

    if (ScreenEscape(QUERYESC, sizeof(int), (LPSTR)&esc, NULL) <= 0 || PanEscape(-1) < 0) {
        LogLine("START no XTPAN driver: helper exits");
        /* Explicit Settings is the opt-in entry on a fixed graphics mode.
         * Never treat the larger logical screen of a pan driver as visible. */
        nDeskW = GetSystemMetrics(SM_CXSCREEN);
        nView = GetSystemMetrics(SM_CYSCREEN);
        if (!settings) return 0;
        if ((nDeskW != 320 && nDeskW != 640) || nView != 200 ||
            WDWinInit(2048, 2048) != WD_OK) {
            MessageBox(NULL, "Window workspace needs a fixed 320x200 or 640x200 display.",
                       "Panning settings", MB_OK | MB_ICONINFORMATION);
            return 0;
        }
        bDesk = 1;nLogical = 2048;nTop = 0;
        if (nStep > 2048) nStep = 2048;
        if (nEdge > nView / 2) nEdge = nView / 2;
        if (nDwell < 0) nDwell = 0;
        if (nDwell > 10000) nDwell = 10000;
        (void)WDWinExclude((LPCSTR)"Progman");
        (void)WDWinExclude((LPCSTR)"TandyStart");
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
    hInstance = hInst;
    host.ops.query = XtQuery;
    host.ops.apply = XtApply;
    host.ops.home = XtHome;
    host.store.get = IniGet;
    host.store.put = IniPut;
    host.title = "XTPAN panning settings";
    host.backend = bDesk ? "Window workspace (24 windows)" : "Vertical software pan";
    if (settings)
        PostMessage(hMain, uOpenMsg, 0, 0L);
    while (GetMessage(&msg, NULL, 0, 0)) {
        if (PanDlgMessage(&msg))
            continue;
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return msg.wParam;
}
