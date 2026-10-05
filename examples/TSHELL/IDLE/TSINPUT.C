/* Windows 3.0 / 8086 global input observation. No launch or UI in hook. */
#define WINVER 0x0300
#ifdef TSINPUT_HOST
#include "tests/WINSTUB.H"
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

/* Hold-to-Start is independent of the saver/IdleInstall lifetime. The extra
   journal observer cancels gestures on mouse/other-key input even when the
   saver is disabled. Both callbacks and saved chain links remain fixed. */
#define HOLD_NONE 0
#define HOLD_OWNED 1
#define HOLD_PASS 2
#define HOLD_MAX_AGE 1000L
#define HOLD_SCAN 0x46
static HTASK holdOwner, holdFocusTask;
static HWND holdTarget, holdFocus;
static WORD holdMessage, holdGesture, holdDepth;
static WORD holdMouseL, holdMouseH;
static FARPROC holdKeyProc, holdRecordProc, nextHoldKey, nextHoldRecord;
static BOOL holdKeyLive, holdRecordLive, holdAllowed, holdStopping, holdRemoving;
static BOOL holdCanceled, holdRawDown, holdRawCanceled;
static DWORD holdSerial, holdPending, holdPosted, holdRawSerial, holdStartSerial;
static DWORD holdRawTime;

static void holdCancel(void)
{
    holdCanceled = TRUE;
    holdRawCanceled = TRUE;
    holdPending = 0;
}

static BOOL holdTargetValid(void)
{
    return holdTarget && IsWindow(holdTarget) &&
           GetWindowTask(holdTarget) == holdOwner;
}

/* GetKeyState observes the dequeued message's modifier context. Do not poll
   GetAsyncKeyState in either hook: its low bit is shared with other clients. */
static BOOL holdPlain(DWORD bits)
{
    return !(bits & 0x20000000L) &&
           !(GetKeyState(VK_SHIFT) & 0x8000) &&
           !(GetKeyState(VK_CONTROL) & 0x8000) &&
           !(GetKeyState(VK_MENU) & 0x8000) &&
           !(GetKeyState(VK_LBUTTON) & 0x8000) &&
           !(GetKeyState(VK_RBUTTON) & 0x8000) &&
           !(GetKeyState(VK_MBUTTON) & 0x8000);
}

static BOOL holdContext(void)
{
    HWND active, windowOwner;
    char name[16];
    if (!holdAllowed || holdStopping || !holdTargetValid() ||
        GetSysModalWindow() || GetCapture()) return FALSE;
    /* These are this suite's exact classes/modules, also checked by TSHELL.
       A loading saver has no capture/window yet: keep its wake key visible. */
    if (FindWindow("TandyMatrixSaver", NULL) || FindWindow("TandyMazeSaver", NULL) ||
        FindWindow("TandyStarfieldSaver", NULL) || GetModuleHandle("TEXIT") ||
        GetModuleHandle("MATRIX") ||
        (GetModuleHandle("MAZE") && !FindWindow("TandyMaze", NULL)) ||
        (GetModuleHandle("STARFLD") && !FindWindow("TandyStarfield", NULL))) return FALSE;
    active = GetActiveWindow();
    if (!active) return FALSE;
    windowOwner = GetWindow(active, GW_OWNER);
    if (windowOwner && !IsWindowEnabled(windowOwner)) return FALSE;
    if (GetClassName(active, name, sizeof(name)) &&
        name[0] == '#' && name[1] == '3' && name[2] == '2' &&
        name[3] == '7' && name[4] == '7' && name[5] == '0' && !name[6])
        return FALSE;
    return TRUE;
}

DWORD FAR PASCAL HoldRecord(int code, WORD wp, DWORD lp)
{
    LPEVENTMSG event;
    WORD key;
    DWORD result;
    ++holdDepth;
    if (code == HC_ACTION && holdRecordLive && lp) {
        event = (LPEVENTMSG)lp;
        if (event->message >= WM_KEYFIRST && event->message <= WM_KEYLAST) {
            key = event->paramL & 255;
            if (key == VK_SCROLL) {
                holdRawTime = event->time;
                if (event->message == WM_KEYDOWN || event->message == WM_SYSKEYDOWN) {
                    if (!holdRawDown) {
                        holdRawDown = TRUE;
                        holdRawCanceled = FALSE;
                        ++holdRawSerial;
                        /* A newer tap must not revive an older queued request. */
                        holdPending = 0;
                    }
                } else if (event->message == WM_KEYUP || event->message == WM_SYSKEYUP) {
                    holdRawDown = FALSE;
                }
            } else holdCancel();
        } else if (event->message == WM_MOUSEMOVE) {
            if (event->paramL != holdMouseL || event->paramH != holdMouseH) {
                holdMouseL = event->paramL;
                holdMouseH = event->paramH;
                holdCancel();
            }
        } else if (event->message >= WM_MOUSEFIRST && event->message <= WM_MOUSELAST) {
            holdCancel();
        }
    }
    result = DefHookProc(code, wp, lp, (FARPROC FAR *)&nextHoldRecord);
    --holdDepth;
    return result;
}

int FAR PASCAL HoldKeyboard(int code, WORD key, DWORD bits)
{
    BOOL matching, released, consume, candidate;
    HWND active;
    int result;
    ++holdDepth;
    consume = FALSE;
    if (code == HC_ACTION && holdKeyLive) {
        matching = key == VK_SCROLL && ((bits >> 16) & 255) == HOLD_SCAN &&
                   !(bits & 0x01000000L);
        released = (bits & 0x80000000L) != 0;
        if (matching) {
            /* Only removed events establish ownership. In native Win3 a
               nonzero HC_NOREMOVE return can suppress the later HC_ACTION,
               so previews must chain unchanged and do no work at all. */
            if (holdGesture == HOLD_OWNED) consume = TRUE;
            else if (holdGesture == HOLD_NONE && !released &&
                     !(bits & 0x40000000L)) {
                consume = holdRawDown && !holdRawCanceled &&
                          (DWORD)(GetTickCount() - holdRawTime) <= (DWORD)HOLD_MAX_AGE &&
                          holdPlain(bits) && holdContext();
            }
            if (code == HC_ACTION) {
                if (holdGesture == HOLD_NONE && !released) {
                    holdGesture = consume ? HOLD_OWNED : HOLD_PASS;
                    holdCanceled = !consume;
                    if (consume) {
                        holdFocus = GetActiveWindow();
                        holdFocusTask = holdFocus ? GetWindowTask(holdFocus) : NULL;
                        holdStartSerial = holdRawSerial;
                        if (!holdFocus || !holdFocusTask) holdCanceled = TRUE;
                    }
                }
                if (holdGesture == HOLD_OWNED) {
                    if (!holdPlain(bits) || !holdContext()) holdCancel();
                    if (released) {
                        active = GetActiveWindow();
                        candidate = !holdCanceled && !holdRawCanceled &&
                                    holdStartSerial == holdRawSerial &&
                                    (DWORD)(GetTickCount() - holdRawTime) <= (DWORD)HOLD_MAX_AGE &&
                                    active == holdFocus && active &&
                                    GetWindowTask(active) == holdFocusTask;
                        holdGesture = HOLD_NONE;
                        if (candidate) {
                            ++holdSerial;
                            if (!holdSerial) ++holdSerial;
                            holdPending = holdSerial;
                            holdPosted = holdRawTime;
                            if (!PostMessage(holdTarget, holdMessage, 0, holdPending))
                                holdPending = 0;
                        }
                    }
                } else if (released) holdGesture = HOLD_NONE;
            }
        } else if (code == HC_ACTION) {
            /* This includes VK_CANCEL/CtrlBreak and every modifier transition.
               Never consume them. Retain OWNED until matching Scroll release. */
            holdCancel();
            /* Some older drivers retranslate this physical key with current
               Ctrl state on break. Pass VK_CANCEL unchanged, but retire the
               old swallowed-Scroll ownership instead of leaving it stuck. */
            if (key == VK_CANCEL && ((bits >> 16) & 255) == HOLD_SCAN && released) {
                holdGesture = HOLD_NONE;
                holdRawDown = FALSE;
            }
        }
    }
    /* Even consumed keys reach every downstream filter. Preserve its result
       for unowned keys and all negative/unknown/no-remove pass-through calls. */
    result = (int)DefHookProc(code, key, bits, (FARPROC FAR *)&nextHoldKey);
    /* Respect an older filter that already handled this removed event.
       Keep OWNED balance, but do not run two actions for the same gesture. */
    if (code == HC_ACTION && result) holdCancel();
    --holdDepth;
    return consume ? 1 : result;
}

BOOL FAR PASCAL HoldInstall(HWND target, WORD message, BOOL allowed)
{
    POINT cursor;
    if (holdRemoving) return FALSE;
    if (holdKeyLive || holdRecordLive)
        return !holdStopping && holdKeyLive && holdRecordLive &&
               holdOwner == GetCurrentTask() && target == holdTarget &&
               message == holdMessage;
    if (!target || !IsWindow(target) || GetWindowTask(target) != GetCurrentTask() ||
        message < WM_USER) return FALSE;
    holdKeyProc = GetProcAddress(library, "HoldKeyboard");
    holdRecordProc = GetProcAddress(library, "HoldRecord");
    if (!holdKeyProc || !holdRecordProc) {
        holdKeyProc = holdRecordProc = NULL;
        return FALSE;
    }
    holdOwner = GetCurrentTask();
    holdTarget = target;
    holdMessage = message;
    holdAllowed = allowed != FALSE;
    holdStopping = FALSE;
    holdGesture = HOLD_NONE;
    holdPending = 0;
    holdFocus = NULL;
    holdFocusTask = NULL;
    holdCanceled = TRUE;
    holdRawCanceled = TRUE;
    holdRawDown = (GetAsyncKeyState(VK_SCROLL) & 0x8000) != 0;
    GetCursorPos(&cursor);
    holdMouseL = (WORD)cursor.x;
    holdMouseH = (WORD)cursor.y;
    ++holdSerial;
    if (!holdSerial) ++holdSerial;
    /* An empty previous chain is not a documented install failure. */
    holdRecordLive = TRUE;
    nextHoldRecord = SetWindowsHook(WH_JOURNALRECORD, holdRecordProc);
    holdKeyLive = TRUE;
    nextHoldKey = SetWindowsHook(WH_KEYBOARD, holdKeyProc);
    return TRUE;
}

BOOL FAR PASCAL HoldPolicy(HWND target, BOOL allowed)
{
    if (!holdKeyLive || !holdRecordLive || holdStopping ||
        GetCurrentTask() != holdOwner || target != holdTarget) return FALSE;
    allowed = allowed != FALSE;
    if (!allowed || allowed != holdAllowed) holdCancel();
    holdAllowed = allowed;
    return TRUE;
}

BOOL FAR PASCAL HoldTake(HWND target, DWORD token)
{
    HWND active;
    if (GetCurrentTask() != holdOwner || target != holdTarget ||
        !token || token != holdPending) return FALSE;
    holdPending = 0;
    if (holdDepth || !holdKeyLive || !holdRecordLive || !holdContext() ||
        (DWORD)(GetTickCount() - holdPosted) > (DWORD)HOLD_MAX_AGE) return FALSE;
    active = GetActiveWindow();
    return active && active == holdFocus && IsWindow(active) &&
           GetWindowTask(active) == holdFocusTask;
}

static BOOL holdUnhook(BOOL finalUnload)
{
    MSG message;
    holdAllowed = FALSE;
    holdStopping = TRUE;
    holdCancel();
    /* A callback can be reentered by a downstream filter. It must not unload
       its code; a swallowed make must also retain its matching break. */
    if (!finalUnload && (holdDepth || holdGesture == HOLD_OWNED)) return FALSE;
    if (holdKeyLive) {
        if (!UnhookWindowsHook(WH_KEYBOARD, holdKeyProc)) return FALSE;
        holdKeyLive = FALSE;
        holdKeyProc = nextHoldKey = NULL;
    }
    if (holdRecordLive) {
        if (!UnhookWindowsHook(WH_JOURNALRECORD, holdRecordProc)) return FALSE;
        holdRecordLive = FALSE;
        holdRecordProc = nextHoldRecord = NULL;
    }
    /* This message number is reserved exclusively for Hold requests. Drain
       only the owning task's queue, outside either hook, before module reset. */
    if (!finalUnload && holdOwner == GetCurrentTask() && holdTargetValid())
        while (PeekMessage(&message, holdTarget, holdMessage, holdMessage, PM_REMOVE))
            ;
    holdOwner = NULL;
    holdTarget = holdFocus = NULL;
    holdFocusTask = NULL;
    holdMessage = holdGesture = 0;
    return TRUE;
}

BOOL FAR PASCAL HoldRemove(void)
{
    BOOL result;
    /* PeekMessage can dispatch sent messages even with a private filter.
       Retain code across the entire removal, including the post-detach drain. */
    if (holdRemoving) return FALSE;
    if (!holdKeyLive && !holdRecordLive) return TRUE;
    if (holdOwner != GetCurrentTask()) return FALSE;
    holdRemoving = TRUE;
    result = holdUnhook(FALSE);
    holdRemoving = FALSE;
    return result;
}

int FAR PASCAL LibMain(HINSTANCE instance, WORD ds, WORD heap, LPSTR cmd)
{
    library = instance;
    return 1;
}

int FAR PASCAL WEP(int systemExit)
{
    /* Best effort for abnormal owner termination; caller must first use
       both applicable removers and must NOT FreeLibrary after either fails.
       WEP cannot veto an unload; it does not wait for an owned key release. */
    holdUnhook(TRUE);
    unhook();
    return 1;
}
