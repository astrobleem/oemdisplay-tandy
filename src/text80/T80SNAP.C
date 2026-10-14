/* T80SNAP.C - text buffer snapshots for the TEXT80 tests (Windows 3.0
 * real mode; C89, /G0 /Gw /AS). Started by WIN.INI load= on test disks only.
 *
 * Every 55 ms (task time, a WM_TIMER) it checks Scroll Lock with
 * GetAsyncKeyState. Each press appends one record to SNAPS.BIN beside
 * T80SNAP.EXE:
 *   16-byte header: 'T8', record number, columns, rows, pointer x, y (screen
 *   pixels, GetCursorPos), viewport top (escape 5850h, 0 without panning),
 *   flags (bit 0: the pointer was visible when the second copy was taken)
 *   then the text buffer at B800:0000 twice (columns*rows words each): first
 *   with the pointer hidden (ShowCursor(FALSE)), then shown again.
 * The driver draws the pointer as the hot spot's cell with attribute XOR
 * 77h, so the two copies must differ in exactly that cell (T80CHK.PY).
 * Columns and rows come from the BIOS data area (40:4Ah, 40:84h + 1).
 */
#include <windows.h>

#define XTPAN_ESC 0x5850
#define QUERYESC 8

static char szFile[128];
static HWND hWnd;
static WORD wRecord;
static int bWas;

static int Rows(void)
{
    BYTE FAR *bda = (BYTE FAR *)MAKELONG(0, 0x40);
    int r = bda[0x84] + 1;
    return (r >= 25 && r <= 50) ? r : 25;
}

static int Cols(void)
{
    BYTE FAR *bda = (BYTE FAR *)MAKELONG(0, 0x40);
    return bda[0x4A] == 40 ? 40 : 80;
}

static int Top(void)
{
    HDC hdc = GetDC(NULL);
    int esc = XTPAN_ESC, q = -1, out[3], r = 0;
    out[0] = 0;
    if (hdc) {
        if (Escape(hdc, QUERYESC, sizeof(int), (LPSTR)&esc, NULL) > 0)
            r = Escape(hdc, XTPAN_ESC, sizeof(int), (LPSTR)&q, (LPSTR)out) > 0;
        ReleaseDC(NULL, hdc);
    }
    return r ? out[0] : 0;
}

static void Snap(void)
{
    WORD hdr[8];
    POINT pt;
    int fh, n;
    OFSTRUCT of;
    WORD FAR *vb = (WORD FAR *)MAKELONG(0, 0xB800);
    static WORD buf[80 * 50];
    int i;
    n = Cols() * Rows();
    GetCursorPos(&pt);
    hdr[0] = 0x3854;                        /* 'T8' */
    hdr[1] = ++wRecord;
    hdr[2] = Cols();
    hdr[3] = Rows();
    hdr[4] = pt.x;
    hdr[5] = pt.y;
    hdr[6] = Top();
    fh = OpenFile(szFile, &of, OF_WRITE);
    if (fh == -1)
        fh = OpenFile(szFile, &of, OF_CREATE | OF_WRITE);
    if (fh == -1)
        return;
    _llseek(fh, 0L, 2);
    i = ShowCursor(FALSE);
    hdr[7] = i >= -1;                       /* was visible before hiding */
    _lwrite(fh, (LPSTR)hdr, sizeof(hdr));
    for (i = 0; i < n; i++)
        buf[i] = vb[i];
    ShowCursor(TRUE);
    _lwrite(fh, (LPSTR)buf, n * 2);
    for (i = 0; i < n; i++)
        buf[i] = vb[i];
    _lwrite(fh, (LPSTR)buf, n * 2);
    _lclose(fh);
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    int down;
    switch (msg) {
    case WM_TIMER:
        down = (GetAsyncKeyState(VK_SCROLL) & 0x8001) != 0;
        if (down && !bWas)
            Snap();
        bWas = (GetAsyncKeyState(VK_SCROLL) & 0x8000) != 0;
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

int PASCAL WinMain(HANDLE hI, HANDLE hPrev, LPSTR lpCmd, int nShow)
{
    WNDCLASS wc;
    MSG msg;
    int n;
    if (hPrev)
        return 0;
    n = GetModuleFileName(hI, szFile, sizeof(szFile) - 12);
    while (n > 0 && szFile[n - 1] != '\\' && szFile[n - 1] != ':')
        n--;
    lstrcpy(szFile + n, "SNAPS.BIN");
    wc.style = 0;
    wc.lpfnWndProc = WndProc;
    wc.cbClsExtra = 0;
    wc.cbWndExtra = 0;
    wc.hInstance = hI;
    wc.hIcon = NULL;
    wc.hCursor = NULL;
    wc.hbrBackground = NULL;
    wc.lpszMenuName = NULL;
    wc.lpszClassName = "T80Snap";
    if (!RegisterClass(&wc))
        return 0;
    hWnd = CreateWindow("T80Snap", "T80SNAP", WS_POPUP, 0, 0, 0, 0, NULL, NULL, hI, NULL);
    if (!hWnd || !SetTimer(hWnd, 1, 55, NULL))
        return 0;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return 0;
}
