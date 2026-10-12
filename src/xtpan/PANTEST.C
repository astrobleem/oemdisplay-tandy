/* PANTEST.C - test fixture for the XTPAN panned desktop (Windows 3.0 real
 * mode, C89, /G0 /Gw /AS). Every mode appends lines to C:\XTPAN\PANTEST.LOG
 * so that clicks, moves, menu commands, selections and timings are checked
 * from what Windows reports, not from pictures alone. All modes log
 * GetFreeSpace(0) when they start.
 *
 *   PANTEST PATTERN [HIDE]  borderless 320x400 window at (0,0) filled with a
 *       known pattern: colour index c(x,y) = ((y+off)/8 + x/32) mod 16, and
 *       in the rightmost 32 columns 12 + ((y+off)/8)/16 mod 4, so every
 *       8-row band of the 400 rows is unique. HIDE hides the pointer.
 *       Keys: S = ScrollWindow up 56 rows (screen-to-screen copy, the
 *       exposed strip repainted with off += 56); R = repaint all; P = log
 *       the pointer position, viewport top and offset; Q = quit.
 *       Clicks are logged in desktop coordinates.
 *   PANTEST DIALOG   a modal dialog about 300 pixels tall (DialogBoxIndirect)
 *       with buttons "Top" near its top and "Bottom" near its bottom.
 *   PANTEST OVERLAP  two overlapping captioned windows across row 200,
 *       solid red (A) and blue (B); clicks and activations are logged.
 *   PANTEST MOVE     one captioned window at (40,140), 200x100; every
 *       WM_MOVE is logged (for dragging across the viewport boundary).
 *   PANTEST MENU     a captioned window at y=230 with a menu bar; menu
 *       commands are logged.
 *   PANTEST EDIT     a multi-line edit control with 30 numbered lines from
 *       y=100 down; the selection is logged whenever it changes.
 *   PANTEST BENCH    timed drawing inside rows 0-199 (fills and text).
 *   PANTEST PANBENCH 40 pans through the driver escape, timed.
 */
#include <windows.h>

#define XTPAN_ESC 0x5850
#define IDB_TOP 101
#define IDB_BOTTOM 102

static HANDLE hInst;
static HWND hMain;
static int nMode;
static int nOff;
static HBRUSH hbr[16];
static char szLogName[] = "C:\\XTPAN\\PANTEST.LOG";
static WORD wLastSelLo, wLastSelHi;
static HWND hEdit;

static DWORD rgb16[16] = {
    RGB(0, 0, 0), RGB(0x80, 0, 0), RGB(0, 0x80, 0), RGB(0x80, 0x80, 0),
    RGB(0, 0, 0x80), RGB(0x80, 0, 0x80), RGB(0, 0x80, 0x80), RGB(0x80, 0x80, 0x80),
    RGB(0x40, 0x40, 0x40), RGB(0xFF, 0, 0), RGB(0, 0xFF, 0), RGB(0xFF, 0xFF, 0),
    RGB(0, 0, 0xFF), RGB(0xFF, 0, 0xFF), RGB(0, 0xFF, 0xFF), RGB(0xFF, 0xFF, 0xFF)
};

static void LogLine(LPSTR text)
{
    int fh;
    OFSTRUCT of;
    fh = OpenFile(szLogName, &of, OF_WRITE);
    if (fh == -1)
        fh = OpenFile(szLogName, &of, OF_CREATE | OF_WRITE);
    if (fh == -1)
        return;
    _llseek(fh, 0L, 2);
    _lwrite(fh, text, lstrlen(text));
    _lwrite(fh, "\r\n", 2);
    _lclose(fh);
}

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

static int PanTop(void)
{
    int q = -1, out[3];
    out[0] = 0;
    if (ScreenEscape(XTPAN_ESC, sizeof(int), (LPSTR)&q, (LPSTR)out) <= 0)
        return -1;
    return out[0];
}

static int Colour(int x, int y)
{
    int band = (y + nOff) >> 3;
    if (x >= 288)
        return 12 + ((band >> 4) & 3);
    return (band + (x >> 5)) & 15;
}

static void PaintPattern(HDC hdc, RECT FAR *rc)
{
    int y, x;
    RECT r;
    for (y = rc->top & ~7; y < rc->bottom; y += 8) {
        for (x = rc->left & ~31; x < rc->right; x += 32) {
            r.left = x;
            r.right = x + 32;
            r.top = y;
            r.bottom = y + 8;
            /* bands are offset by nOff, which is a multiple of 8 */
            FillRect(hdc, &r, hbr[Colour(x, y)]);
        }
    }
}

static void LogClick(LPSTR what, HWND hwnd, LONG lParam)
{
    char buf[96];
    POINT pt, cur;
    pt.x = LOWORD(lParam);
    pt.y = HIWORD(lParam);
    ClientToScreen(hwnd, &pt);
    GetCursorPos(&cur);
    wsprintf(buf, "%s x=%d y=%d cursor=%d,%d top=%d", what, pt.x, pt.y, cur.x, cur.y, PanTop());
    LogLine(buf);
}

/* All drawing stays inside the 320x200 screen of the unchanged driver, so
 * both drivers do the same work (text crossing the bottom of a 200-row
 * screen makes the unchanged driver flush the whole screen). */
static void Bench(HWND hwnd)
{
    HDC hdc = GetDC(hwnd);
    DWORD t0, t1, t2, t3;
    int i;
    RECT r;
    char buf[120];
    t0 = GetCurrentTime();
    for (i = 0; i < 400; i++) {
        r.left = (i * 7) % 280;
        r.top = (i * 13) % 180;
        r.right = r.left + 40;
        r.bottom = r.top + 20;
        FillRect(hdc, &r, hbr[i & 15]);
    }
    t1 = GetCurrentTime();
    SetBkColor(hdc, RGB(0xFF, 0xFF, 0xFF));
    for (i = 0; i < 200; i++)
        TextOut(hdc, (i * 5) % 160, (i * 9) % 150, "Bench text 0123", 15);
    t2 = GetCurrentTime();
    GetClientRect(hwnd, &r);
    r.bottom = 150;
    for (i = 0; i < 50; i++)
        ScrollWindow(hwnd, 0, -8, &r, &r);
    ValidateRect(hwnd, NULL);
    t3 = GetCurrentTime();
    ReleaseDC(hwnd, hdc);
    wsprintf(buf, "BENCH fills400 ms=%lu text200 ms=%lu scroll50 ms=%lu", t1 - t0, t2 - t1, t3 - t2);
    LogLine(buf);
}

static void PanBench(void)
{
    int i, want, out[3];
    DWORD t0, t1;
    char buf[96];
    if (PanTop() < 0) {
        LogLine("PANBENCH no XTPAN driver");
        return;
    }
    t0 = GetCurrentTime();
    for (i = 0; i < 40; i++) {
        want = (i & 1) ? 0 : 200;
        ScreenEscape(XTPAN_ESC, sizeof(int), (LPSTR)&want, (LPSTR)out);
    }
    t1 = GetCurrentTime();
    wsprintf(buf, "PANBENCH pans=40 alternating 0/200 ms=%lu", t1 - t0);
    LogLine(buf);
    t0 = GetCurrentTime();
    for (i = 0; i < 40; i++) {
        want = (i & 1) ? 0 : 50;
        ScreenEscape(XTPAN_ESC, sizeof(int), (LPSTR)&want, (LPSTR)out);
    }
    t1 = GetCurrentTime();
    wsprintf(buf, "PANBENCH pans=40 alternating 0/50 ms=%lu", t1 - t0);
    LogLine(buf);
}

BOOL FAR PASCAL DlgProc(HWND hdlg, unsigned msg, WORD wParam, LONG lParam)
{
    char buf[64];
    RECT r;
    if (msg == WM_INITDIALOG) {
        GetWindowRect(hdlg, &r);
        wsprintf(buf, "DIALOG rect=%d,%d,%d,%d", r.left, r.top, r.right, r.bottom);
        LogLine(buf);
        GetWindowRect(GetDlgItem(hdlg, IDB_TOP), &r);
        wsprintf(buf, "DLGITEM Top rect=%d,%d,%d,%d", r.left, r.top, r.right, r.bottom);
        LogLine(buf);
        GetWindowRect(GetDlgItem(hdlg, IDB_BOTTOM), &r);
        wsprintf(buf, "DLGITEM Bottom rect=%d,%d,%d,%d", r.left, r.top, r.right, r.bottom);
        LogLine(buf);
        return TRUE;
    }
    if (msg == WM_COMMAND && wParam == IDCANCEL) {
        LogLine("DIALOG cancelled");
        EndDialog(hdlg, 0);
        return TRUE;
    }
    if (msg == WM_COMMAND && (wParam == IDB_TOP || wParam == IDB_BOTTOM)) {
        GetWindowRect(GetDlgItem(hdlg, wParam), &r);
        wsprintf(buf, "BUTTON %s rect=%d,%d,%d,%d top=%d", (LPSTR)(wParam == IDB_TOP ? "Top" : "Bottom"),
                 r.left, r.top, r.right, r.bottom, PanTop());
        LogLine(buf);
        if (wParam == IDB_BOTTOM)
            EndDialog(hdlg, 1);
        return TRUE;
    }
    return FALSE;
}

/* Windows 3.0 dialog template in memory: header, then items. */
static LPSTR PutWord(LPSTR p, WORD w) { *(WORD FAR *)p = w; return p + 2; }
static LPSTR PutLong(LPSTR p, DWORD d) { *(DWORD FAR *)p = d; return p + 4; }
static LPSTR PutStr(LPSTR p, LPSTR s) { while ((*p++ = *s++) != 0) ; return p; }

static LPSTR PutItem(LPSTR p, int x, int y, int cx, int cy, int id, LPSTR text)
{
    p = PutWord(p, x);
    p = PutWord(p, y);
    p = PutWord(p, cx);
    p = PutWord(p, cy);
    p = PutWord(p, id);
    p = PutLong(p, WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON);
    *p++ = (char)0x80;          /* button class */
    p = PutStr(p, text);
    *p++ = 0;                   /* no creation data */
    return p;
}

static void TallDialog(HWND owner)
{
    HANDLE h;
    LPSTR p;
    FARPROC proc;
    LONG units = GetDialogBaseUnits();
    int cy = HIWORD(units), cyDlg, topDlg;
    /* about 300 pixels tall, from pixel row 50 */
    cyDlg = (int)((300L * 8) / cy);
    topDlg = (int)((50L * 8) / cy);
    h = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, 256);
    p = GlobalLock(h);
    p = PutLong(p, WS_POPUP | WS_VISIBLE | WS_CAPTION | DS_MODALFRAME);
    *p++ = 2;
    p = PutWord(p, 4);
    p = PutWord(p, topDlg);
    p = PutWord(p, 140);
    p = PutWord(p, cyDlg);
    *p++ = 0;                   /* no menu */
    *p++ = 0;                   /* default class */
    p = PutStr(p, "Tall dialog");
    p = PutItem(p, 10, 6, 50, 14, IDB_TOP, "Top");
    p = PutItem(p, 10, cyDlg - 26, 50, 14, IDB_BOTTOM, "Bottom");
    GlobalUnlock(h);
    proc = MakeProcInstance((FARPROC)DlgProc, hInst);
    DialogBoxIndirect(hInst, h, owner, proc);
    FreeProcInstance(proc);
    GlobalFree(h);
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    PAINTSTRUCT ps;
    char buf[96];
    RECT r;
    DWORD sel;

    switch (msg) {
    case WM_PAINT:
        BeginPaint(hwnd, &ps);
        if (nMode == 0)
            PaintPattern(ps.hdc, &ps.rcPaint);
        else if (nMode == 2) {
            GetClientRect(hwnd, &r);
            FillRect(ps.hdc, &r, hbr[GetWindowWord(hwnd, 0) ? 12 : 9]);
        }
        EndPaint(hwnd, &ps);
        return 0;
    case WM_CHAR:
        if (nMode == 0 && (wParam == 's' || wParam == 'S')) {
            nOff += 56;
            ScrollWindow(hwnd, 0, -56, NULL, NULL);
            UpdateWindow(hwnd);
            wsprintf(buf, "SCROLL off=%d top=%d", nOff, PanTop());
            LogLine(buf);
            return 0;
        }
        if (wParam == 'p' || wParam == 'P') {
            POINT cur;
            GetCursorPos(&cur);
            wsprintf(buf, "CURSOR x=%d y=%d top=%d off=%d", cur.x, cur.y, PanTop(), nOff);
            LogLine(buf);
            return 0;
        }
        if (nMode == 0 && (wParam == 'r' || wParam == 'R')) {
            InvalidateRect(hwnd, NULL, FALSE);
            return 0;
        }
        if (wParam == 'q' || wParam == 'Q') {
            DestroyWindow(hwnd);
            return 0;
        }
        break;
    case WM_LBUTTONDOWN:
        if (nMode == 2)
            LogClick(GetWindowWord(hwnd, 0) ? "CLICK B" : "CLICK A", hwnd, lParam);
        else
            LogClick("CLICK", hwnd, lParam);
        return 0;
    case WM_ACTIVATE:
        if (nMode == 2 && wParam) {
            wsprintf(buf, "ACTIVATE %s", (LPSTR)(GetWindowWord(hwnd, 0) ? "B" : "A"));
            LogLine(buf);
        }
        break;
    case WM_MOVE:
        if (nMode == 3) {
            GetWindowRect(hwnd, &r);
            wsprintf(buf, "MOVE window=%d,%d,%d,%d top=%d", r.left, r.top, r.right, r.bottom, PanTop());
            LogLine(buf);
        }
        break;
    case WM_COMMAND:
        if (nMode == 4) {
            wsprintf(buf, "COMMAND %d top=%d", wParam, PanTop());
            LogLine(buf);
            return 0;
        }
        break;
    case WM_TIMER:
        if (nMode == 5 && hEdit) {
            sel = SendMessage(hEdit, EM_GETSEL, 0, 0L);
            if (LOWORD(sel) != wLastSelLo || HIWORD(sel) != wLastSelHi) {
                wLastSelLo = LOWORD(sel);
                wLastSelHi = HIWORD(sel);
                wsprintf(buf, "SELECT %u %u top=%d", wLastSelLo, wLastSelHi, PanTop());
                LogLine(buf);
            }
        }
        return 0;
    case WM_DESTROY:
        if (hwnd == hMain)
            PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

static HWND Make(LPSTR title, DWORD style, int x, int y, int cx, int cy, HMENU menu)
{
    return CreateWindow("PanTest", title, style, x, y, cx, cy, NULL, menu, hInst, NULL);
}

static int Is(LPSTR cmd, LPSTR word)
{
    while (*word) {
        if ((*cmd | 0x20) != (*word | 0x20))
            return 0;
        cmd++;
        word++;
    }
    return *cmd == 0 || *cmd == ' ';
}

int PASCAL WinMain(HANDLE hI, HANDLE hPrev, LPSTR lpCmd, int nShow)
{
    WNDCLASS wc;
    MSG msg;
    int i;
    char buf[200];
    HMENU hMenu, hPop;
    HWND hB;
    DWORD style = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_VISIBLE;

    hInst = hI;
    for (i = 0; i < 16; i++)
        hbr[i] = CreateSolidBrush(rgb16[i]);
    wsprintf(buf, "START cmd=%s free=%lu top=%d", lpCmd, GetFreeSpace(0), PanTop());
    LogLine(buf);
    {
        HDC hdc = GetDC(NULL);
        TEXTMETRIC tm;
        GetTextMetrics(hdc, &tm);
        ReleaseDC(NULL, hdc);
        wsprintf(buf, "METRICS screen=%dx%d cycaption=%d cymenu=%d cyframe=%d tmheight=%d tmextlead=%d",
                 GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN),
                 GetSystemMetrics(SM_CYCAPTION), GetSystemMetrics(SM_CYMENU),
                 GetSystemMetrics(SM_CYFRAME), tm.tmHeight, tm.tmExternalLeading);
        LogLine(buf);
    }

    if (!hPrev) {
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = WndProc;
        wc.cbClsExtra = 0;
        wc.cbWndExtra = 2;
        wc.hInstance = hI;
        wc.hIcon = NULL;
        wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        wc.hbrBackground = GetStockObject(WHITE_BRUSH);
        wc.lpszMenuName = NULL;
        wc.lpszClassName = "PanTest";
        if (!RegisterClass(&wc))
            return 0;
    }

    if (Is(lpCmd, "BENCH")) {
        nMode = 6;
        hMain = Make("Bench", style, 0, 0, 320, 180, NULL);
        UpdateWindow(hMain);
        Bench(hMain);
        DestroyWindow(hMain);
    } else if (Is(lpCmd, "PANBENCH")) {
        PanBench();
        return 0;
    } else if (Is(lpCmd, "DIALOG")) {
        nMode = 1;
        TallDialog(NULL);
        return 0;
    } else if (Is(lpCmd, "OVERLAP")) {
        nMode = 2;
        hMain = Make("A", style, 0, 120, 200, 160, NULL);
        SetWindowWord(hMain, 0, 0);
        hB = Make("B", style, 100, 180, 200, 150, NULL);
        SetWindowWord(hB, 0, 1);
        InvalidateRect(hMain, NULL, TRUE);
        InvalidateRect(hB, NULL, TRUE);
    } else if (Is(lpCmd, "MOVE")) {
        nMode = 3;
        hMain = Make("Move me", style, 40, 140, 200, 100, NULL);
    } else if (Is(lpCmd, "MENU")) {
        nMode = 4;
        hMenu = CreateMenu();
        hPop = CreateMenu();
        AppendMenu(hPop, MF_STRING, 201, "Alpha");
        AppendMenu(hPop, MF_STRING, 202, "Beta");
        AppendMenu(hPop, MF_STRING, 203, "Gamma");
        AppendMenu(hPop, MF_STRING, 204, "Delta");
        AppendMenu(hPop, MF_STRING, 205, "Epsilon");
        AppendMenu(hMenu, MF_POPUP, hPop, "Pick");
        hMain = Make("Menu below 200", style, 0, 230, 240, 100, hMenu);
        {
            RECT wr;
            POINT o;
            GetWindowRect(hMain, &wr);
            o.x = 0;
            o.y = 0;
            ClientToScreen(hMain, &o);
            wsprintf(buf, "MENUWIN rect=%d,%d,%d,%d client=%d,%d", wr.left, wr.top, wr.right, wr.bottom, o.x, o.y);
            LogLine(buf);
        }
    } else if (Is(lpCmd, "EDIT")) {
        nMode = 5;
        hMain = Make("Edit across 200", style, 0, 100, 320, 270, NULL);
        hEdit = CreateWindow("edit", NULL, WS_CHILD | WS_VISIBLE | ES_MULTILINE,
                             0, 0, 312, 240, hMain, (HMENU)1, hI, NULL);
        {
            POINT o;
            o.x = 0;
            o.y = 0;
            ClientToScreen(hEdit, &o);
            wsprintf(buf, "EDITORG x=%d y=%d", o.x, o.y);
            LogLine(buf);
        }
        buf[0] = 0;
        for (i = 1; i <= 30; i++) {
            wsprintf(buf + lstrlen(buf), "Line %02d\r\n", i);
            if (lstrlen(buf) > 180) {
                SendMessage(hEdit, EM_SETSEL, 0, MAKELONG(32767, 32767));
                SendMessage(hEdit, EM_REPLACESEL, 0, (LONG)(LPSTR)buf);
                buf[0] = 0;
            }
        }
        SendMessage(hEdit, EM_SETSEL, 0, MAKELONG(32767, 32767));
        SendMessage(hEdit, EM_REPLACESEL, 0, (LONG)(LPSTR)buf);
        SendMessage(hEdit, EM_SETSEL, 0, MAKELONG(0, 0));
        SetFocus(hEdit);
        SetTimer(hMain, 1, 300, NULL);
    } else {
        nMode = 0;
        hMain = CreateWindow("PanTest", NULL, WS_POPUP | WS_VISIBLE, 0, 0, 320, 400,
                             NULL, NULL, hI, NULL);
        if (Is(lpCmd, "PATTERN HIDE"))
            ShowCursor(FALSE);
    }
    if (!hMain)
        return 0;
    UpdateWindow(hMain);
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    for (i = 0; i < 16; i++)
        DeleteObject(hbr[i]);
    return msg.wParam;
}
