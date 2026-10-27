/* PANKEY.DLL: retains the CGAPAN viewport commands (Ctrl+Alt+arrows, Home,
 * End, S) while the machine is busy.
 *
 * A Windows 3.0 keyboard hook sees every key when the application that has
 * the focus finally reads it from the system queue, in order and with the
 * modifier state of that key. The hook only records the command in a small
 * ring and posts one wake-up message to PANCTL; it never pans, draws or
 * calls the driver. PANCTL drains the ring from its own message loop and
 * does the work from its timer. Keys are observed, never swallowed.
 *
 * Fixed-code, single-data DLL for the 8086, no CRT and no local heap.
 */
#define WINVER 0x0300
#include <windows.h>

#define RING 32

#define CMD_HOME 1
#define CMD_END 2
#define CMD_LEFT 3
#define CMD_RIGHT 4
#define CMD_UP 5
#define CMD_DOWN 6
#define CMD_SETTINGS 7

static HINSTANCE module;
static FARPROC hookProc, nextHook;
static HWND owner;
static WORD wakeMessage;
static BYTE ring[RING];
static int head, tail, posted, live, depth;

static int Command(WORD key)
{
    switch (key) {
    case VK_HOME: case VK_NUMPAD7: return CMD_HOME;
    case VK_END: case VK_NUMPAD1: return CMD_END;
    case VK_LEFT: case VK_NUMPAD4: return CMD_LEFT;
    case VK_RIGHT: case VK_NUMPAD6: return CMD_RIGHT;
    case VK_UP: case VK_NUMPAD8: return CMD_UP;
    case VK_DOWN: case VK_NUMPAD2: return CMD_DOWN;
    case 'S': return CMD_SETTINGS;
    }
    return 0;
}

/* Bit 31 clear: key down. Bit 29 set: Alt is down. GetKeyState reads the
 * state belonging to this key, not the live keyboard, so a key that was
 * released while the machine was busy still counts. */
int FAR PASCAL PanKeyHook(int code, WORD key, DWORD bits)
{
    int cmd, next, result;
    ++depth;
    if (code == HC_ACTION && live && owner && !(bits & 0x80000000L) &&
        (bits & 0x20000000L) && (GetKeyState(VK_CONTROL) & 0x8000)) {
        cmd = Command(key);
        if (cmd) {
            next = (head + 1) % RING;
            if (next != tail) {
                ring[head] = (BYTE)cmd;
                head = next;
            }
            if (!posted && PostMessage(owner, wakeMessage, 0, 0L))
                posted = 1;
        }
    }
    result = (int)DefHookProc(code, key, bits, (FARPROC FAR *)&nextHook);
    --depth;
    return result;
}

/* The next retained command, or 0. Emptying the ring lets the next key post
 * a new wake-up. */
int FAR PASCAL PanKeyNext(void)
{
    int cmd = 0;
    if (tail != head) {
        cmd = ring[tail];
        tail = (tail + 1) % RING;
    }
    if (tail == head)
        posted = 0;
    return cmd;
}

BOOL FAR PASCAL PanKeyInstall(HWND who, WORD message)
{
    if (live)
        return FALSE;
    hookProc = GetProcAddress(module, "PanKeyHook");
    if (!hookProc)
        return FALSE;
    owner = who;
    wakeMessage = message;
    head = tail = posted = 0;
    live = 1;
    nextHook = SetWindowsHook(WH_KEYBOARD, hookProc);
    return TRUE;
}

/* FALSE means the hook is still installed: the caller must not FreeLibrary. */
BOOL FAR PASCAL PanKeyRemove(void)
{
    if (!live)
        return TRUE;
    /* A downstream hook may close the owner reentrantly. Keep our code
     * resident until the active callback has returned. */
    owner = NULL;
    if (depth)
        return FALSE;
    live = 0;
    if (!UnhookWindowsHook(WH_KEYBOARD, hookProc)) {
        /* Keep the DLL resident, but never post to a destroyed owner. */
        owner = NULL;
        live = 1;
        return FALSE;
    }
    hookProc = nextHook = NULL;
    return TRUE;
}

int FAR PASCAL LibMain(HINSTANCE instance, WORD ds, WORD heap, LPSTR cmd)
{
    module = instance;
    return 1;
}

int FAR PASCAL WEP(int systemExit)
{
    /* Best effort when the owner ended without removing the hook. */
    if (live) {
        live = 0;
        UnhookWindowsHook(WH_KEYBOARD, hookProc);
    }
    return 1;
}
