/* TGCLOG.EXE - TEST TOOL: record the Clipboard and free memory (MIT).
 *
 * Not part of the packet. A Clipboard viewer for the grabber tests: every
 * time the Clipboard changes it writes C:\TGCLOG\Cnnn.BIN (nnn = 001, 002,
 * ...) with the CF_BITMAP it then holds, as GetBitmapBits returns it:
 *   word width, height, widthbytes, planes, bitspixel; then the bits
 * and appends to C:\TGCLOG\LOG.TXT one line
 *   CLIP nnn formats=<CF_ numbers> bitmap=<w>x<h>x<planes>x<bits>|none
 *        [text=yes] free=<n>
 * and, when the Clipboard holds OEM text, C:\TGCLOG\Cnnn.TXT with it.
 * Every 3 seconds it also appends "MEM <ticks> free=<n> big=<n>" when
 * GetFreeSpace(0) or the largest free block (GlobalCompact(0)) changed.
 * The test harness reads both through mtools. C, small model, 8086.
 */
#include <windows.h>

#define WM_TGCHECK (WM_USER + 1)

static HWND hwndNext;
static int nClip;
static DWORD lastFree = 0xFFFFFFFFL, lastBig = 0xFFFFFFFFL;
static char szLog[] = "C:\\TGCLOG\\LOG.TXT";

long FAR PASCAL WndProc(HWND, unsigned, WORD, LONG);

static void LogLine(LPSTR s)
{
    OFSTRUCT of;
    int fh = OpenFile(szLog, &of, OF_WRITE);
    if (fh == -1)
        fh = OpenFile(szLog, &of, OF_CREATE | OF_WRITE);
    if (fh == -1)
        return;
    _llseek(fh, 0L, 2);
    _lwrite(fh, s, lstrlen(s));
    _lclose(fh);
}

static void LogMem(int always)
{
    char line[80];
    DWORD fr = GetFreeSpace(0), big = GlobalCompact(0L);
    if (!always && fr == lastFree && big == lastBig)
        return;
    lastFree = fr;
    lastBig = big;
    wsprintf(line, "MEM %lu free=%lu big=%lu\r\n", GetTickCount(), fr, big);
    LogLine(line);
}

static void Record(HWND hwnd)
{
    char name[32], line[200], *p;
    WORD fmt, hdr[5];
    HBITMAP hbm;
    BITMAP bm;
    HANDLE hBits;
    LPSTR lp;
    DWORD size;
    OFSTRUCT of;
    int fh;

    if (!OpenClipboard(hwnd))
        return;
    nClip++;
    wsprintf(line, "CLIP %03d formats=", nClip);
    p = line + lstrlen(line);
    for (fmt = EnumClipboardFormats(0); fmt && p < line + 120; fmt = EnumClipboardFormats(fmt)) {
        wsprintf(p, "%u,", fmt);
        p += lstrlen(p);
    }
    hbm = GetClipboardData(CF_BITMAP);
    if (hbm && GetObject(hbm, sizeof(bm), (LPSTR)&bm)) {
        size = (DWORD)bm.bmWidthBytes * bm.bmHeight * bm.bmPlanes;
        hBits = GlobalAlloc(GMEM_MOVEABLE, size);
        if (hBits) {
            lp = GlobalLock(hBits);
            if (GetBitmapBits(hbm, size, lp) == (LONG)size) {
                wsprintf(name, "C:\\TGCLOG\\C%03d.BIN", nClip);
                fh = OpenFile(name, &of, OF_CREATE | OF_WRITE);
                if (fh != -1) {
                    hdr[0] = bm.bmWidth; hdr[1] = bm.bmHeight; hdr[2] = bm.bmWidthBytes;
                    hdr[3] = bm.bmPlanes; hdr[4] = bm.bmBitsPixel;
                    _lwrite(fh, (LPSTR)hdr, sizeof(hdr));
                    _lwrite(fh, lp, (WORD)size);
                    _lclose(fh);
                }
            }
            GlobalUnlock(hBits);
            GlobalFree(hBits);
        }
        wsprintf(p, " bitmap=%dx%dx%dx%d", bm.bmWidth, bm.bmHeight, (int)bm.bmPlanes, (int)bm.bmBitsPixel);
    } else
        lstrcpy(p, " bitmap=none");
    p += lstrlen(p);
    hBits = GetClipboardData(CF_OEMTEXT);
    if (hBits && (lp = GlobalLock(hBits)) != NULL) {
        wsprintf(name, "C:\\TGCLOG\\C%03d.TXT", nClip);
        fh = OpenFile(name, &of, OF_CREATE | OF_WRITE);
        if (fh != -1) {
            _lwrite(fh, lp, lstrlen(lp));
            _lclose(fh);
        }
        GlobalUnlock(hBits);
        lstrcpy(p, " text=yes");
    }
    CloseClipboard();
    p += lstrlen(p);
    wsprintf(p, " free=%lu\r\n", GetFreeSpace(0));
    LogLine(line);
}

long FAR PASCAL WndProc(HWND hwnd, unsigned msg, WORD wParam, LONG lParam)
{
    switch (msg) {
    case WM_CREATE:
        hwndNext = SetClipboardViewer(hwnd);
        SetTimer(hwnd, 1, 3000, NULL);
        LogLine("START\r\n");
        LogMem(1);
        return 0;
    case WM_TIMER:
        LogMem(0);
        return 0;
    case WM_CHANGECBCHAIN:
        if ((HWND)wParam == hwndNext)
            hwndNext = (HWND)LOWORD(lParam);
        else if (hwndNext)
            SendMessage(hwndNext, msg, wParam, lParam);
        return 0;
    case WM_DRAWCLIPBOARD:
        if (hwndNext)
            SendMessage(hwndNext, msg, wParam, lParam);
        PostMessage(hwnd, WM_TGCHECK, 0, 0L);
        return 0;
    case WM_TGCHECK:
        Record(hwnd);
        return 0;
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        ChangeClipboardChain(hwnd, hwndNext);
        LogLine("END\r\n");
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

int PASCAL WinMain(HANDLE hInst, HANDLE hPrev, LPSTR lpCmd, int nShow)
{
    WNDCLASS wc;
    MSG msg;
    HWND hwnd;

    if (hPrev)
        return 0;
    wc.style = 0;
    wc.lpfnWndProc = WndProc;
    wc.cbClsExtra = 0;
    wc.cbWndExtra = 0;
    wc.hInstance = hInst;
    wc.hIcon = NULL;
    wc.hCursor = NULL;
    wc.hbrBackground = NULL;
    wc.lpszMenuName = NULL;
    wc.lpszClassName = "TGClog";
    if (!RegisterClass(&wc))
        return 0;
    hwnd = CreateWindow("TGClog", "TGCLOG", WS_OVERLAPPED, 0, 0, 0, 0,
                        NULL, NULL, hInst, NULL);
    if (!hwnd)
        return 0;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return msg.wParam;
}
