/* Windows 3.0 / 8086 global input observation. No launch or UI in hook. */
#define WINVER 0x0300
#ifdef TSINPUT_HOST
#include "TESTS/WINSTUB.H"
#else
#include <windows.h>
#endif
#include "TSINPUT.H"

#define POLL_GAP 2000L
#define CLOCK_TOLERANCE 250L
/* Documented DOS read service (INT21/AH2C); never called in the hook. */
DWORD FAR PASCAL ReadDosClock(void);
static HINSTANCE library;
static HTASK owner;
static FARPROC recordProc, nextRecord;
static BOOL installed, seenInput, systemModal, needRelease;
static WORD mouseHeld, heldKeys;
static WORD mouseL, mouseH;
static BOOL haveMouse;
static BYTE keyHeld[256];
static DWORD generation, lastPoll, lastDos;

/* Called outside the hook only: install, timer gap, system-modal exit.
   The GetAsyncKeyState low-bit side effect is limited to these baselines. */
static void baseline(void)
{
    int key;
    POINT cursor;
    heldKeys = 0;
    for (key = 0; key < 256; ++key) {
        keyHeld[key] = (BYTE)(key >= 8 && (GetAsyncKeyState(key) & 0x8000) ? 1 : 0);
        if (keyHeld[key]) ++heldKeys;
    }
    mouseHeld = 0;
    if (GetKeyState(VK_LBUTTON) & 0x8000) mouseHeld |= 1;
    if (GetKeyState(VK_RBUTTON) & 0x8000) mouseHeld |= 2;
    if (GetKeyState(VK_MBUTTON) & 0x8000) mouseHeld |= 4;
    /* Win3 native coordinate probe verifies paramL=x, paramH=y. */
    GetCursorPos(&cursor);
    mouseL = (WORD)cursor.x;
    mouseH = (WORD)cursor.y;
    haveMouse = TRUE;
}

/* Fixed DLL data, never a pointer into the caller's stack/data segment. */
DWORD FAR PASCAL IdleRecord(int code, WORD wp, DWORD lp)
{
    LPEVENTMSG event;
    WORD key;
    if (code == HC_ACTION && installed && lp) {
        event = (LPEVENTMSG)lp;
        /* Compare the journal's own raw mouse fields, without assuming a
           newer EVENTMSG coordinate contract. Duplicate stationary moves
           are common after activation/capture changes. Always chain them. */
        if (event->message == WM_MOUSEMOVE) {
            if (haveMouse && event->paramL == mouseL && event->paramH == mouseH)
                return DefHookProc(code, wp, lp, (FARPROC FAR *)&nextRecord);
            mouseL = event->paramL;
            mouseH = event->paramH;
            haveMouse = TRUE;
        }
        if ((event->message >= WM_KEYFIRST && event->message <= WM_KEYLAST) ||
            (event->message >= WM_MOUSEFIRST && event->message <= WM_MOUSELAST)) {
            ++generation;
            if (!needRelease || event->message == WM_KEYUP ||
                event->message == WM_SYSKEYUP || event->message == WM_LBUTTONUP ||
                event->message == WM_RBUTTONUP || event->message == WM_MBUTTONUP) {
                seenInput = TRUE;
                needRelease = FALSE;
            }
            key = event->paramL & 255;
            switch (event->message) {
            case WM_KEYDOWN: case WM_SYSKEYDOWN:
                if (!keyHeld[key]) { keyHeld[key] = 1; ++heldKeys; }
                break;
            case WM_KEYUP: case WM_SYSKEYUP:
                if (keyHeld[key]) { keyHeld[key] = 0; --heldKeys; }
                break;
            case WM_LBUTTONDOWN: case WM_LBUTTONDBLCLK: mouseHeld |= 1; break;
            case WM_LBUTTONUP: mouseHeld &= ~1; break;
            case WM_RBUTTONDOWN: case WM_RBUTTONDBLCLK: mouseHeld |= 2; break;
            case WM_RBUTTONUP: mouseHeld &= ~2; break;
            case WM_MBUTTONDOWN: case WM_MBUTTONDBLCLK: mouseHeld |= 4; break;
            case WM_MBUTTONUP: mouseHeld &= ~4; break;
            }
        }
    }
    /* Includes negative codes, unknown codes, and every processed event. */
    return DefHookProc(code, wp, lp, (FARPROC FAR *)&nextRecord);
}

BOOL FAR PASCAL IdleInstall(void)
{
    if (installed) return owner == GetCurrentTask();
    recordProc = GetProcAddress(library, "IdleRecord");
    if (!recordProc) return FALSE;
    owner = GetCurrentTask();
    baseline();
    systemModal = GetSysModalWindow() != NULL;
    seenInput = FALSE;
    needRelease = FALSE;
    lastPoll = GetTickCount();
    lastDos = ReadDosClock();
    ++generation;
    installed = TRUE;
    /* NULL is a valid empty previous chain, not a documented failure. */
    nextRecord = SetWindowsHook(WH_JOURNALRECORD, recordProc);
    return TRUE;
}

static BOOL unhook(void)
{
    if (!installed) return TRUE;
    if (!UnhookWindowsHook(WH_JOURNALRECORD, recordProc)) return FALSE;
    installed = FALSE;
    owner = NULL;
    recordProc = nextRecord = NULL;
    mouseHeld = 0;
    seenInput = systemModal = needRelease = FALSE;
    ++generation;
    return TRUE;
}

BOOL FAR PASCAL IdleRemove(void)
{
    if (installed && owner != GetCurrentTask()) return FALSE;
    return unhook();
}

DWORD FAR PASCAL IdleGeneration(void)
{
    return generation;
}

BOOL FAR PASCAL IdleReady(void)
{
    DWORD now, dosNow, winElapsed, dosElapsed;
    BOOL blocked, modalNow;
    HWND active, windowOwner;
    char name[16];
    if (!installed || owner != GetCurrentTask()) return FALSE;
    now = GetTickCount();
    dosNow = ReadDosClock();
    /* Unsigned subtraction is valid across the roughly 49-day tick wrap. */
    winElapsed = (DWORD)(now - lastPoll);
    blocked = winElapsed > (DWORD)POLL_GAP;
    /* Win3 /R GetTickCount stops during DOS. DOS time does not. A backwards
       adjustment OR midnight rollover conservatively starts a new interval. */
    if (dosNow < lastDos) blocked = TRUE;
    else {
        dosElapsed = dosNow - lastDos;
        if (dosElapsed > winElapsed &&
            dosElapsed - winElapsed > (DWORD)CLOCK_TOLERANCE) blocked = TRUE;
    }
    lastPoll = now;
    lastDos = dosNow;
    modalNow = GetSysModalWindow() != NULL;
    if (blocked || (systemModal && !modalNow)) {
        baseline();
        seenInput = FALSE;
        needRelease = TRUE;
    }
    if (modalNow != systemModal) {
        systemModal = modalNow;
        seenInput = FALSE;
        needRelease = TRUE;
        blocked = TRUE;
    }
    if (!seenInput || systemModal || GetCapture())
        blocked = TRUE;
    active = GetActiveWindow();
    windowOwner = active ? GetWindow(active, GW_OWNER) : NULL;
    if (windowOwner && !IsWindowEnabled(windowOwner)) blocked = TRUE;
    if (active && GetClassName(active, name, sizeof(name)) &&
        name[0] == '#' && name[1] == '3' && name[2] == '2' &&
        name[3] == '7' && name[4] == '7' && name[5] == '0' && !name[6])
        blocked = TRUE;
    if (mouseHeld || heldKeys) blocked = TRUE;
    if (blocked) ++generation;
    return !blocked;
}

int FAR PASCAL LibMain(HINSTANCE instance, WORD ds, WORD heap, LPSTR cmd)
{
    library = instance;
    return 1;
}

int FAR PASCAL WEP(int systemExit)
{
    /* Best effort for abnormal owner termination; caller must first use
       IdleRemove and must NOT FreeLibrary after a failed removal. */
    unhook();
    return 1;
}
