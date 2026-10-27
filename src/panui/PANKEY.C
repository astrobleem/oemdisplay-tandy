/* PANKEY.DLL: retains the configured panning commands while the machine is busy.
 *
 * A Windows 3.0 keyboard hook sees every key when the application that has
 * the focus finally reads it from the system queue, in order and with the
 * modifier state of that key. The hook only records the command in a small
 * ring and posts one wake-up message to the owner; it never pans, draws or
 * calls the driver. The owner drains the ring from its own message loop and
 * does the work from its timer. Keys are observed, never swallowed.
 *
 * Fixed-code, single-data DLL for the 8086, no CRT and no local heap.
 */
#define WINVER 0x0300
#include <windows.h>

#include "PANKEY.H"
#define RING 32

static HINSTANCE module;
static FARPROC hookProc, nextHook;
static HWND owner;
static WORD wakeMessage;
static BYTE ring[RING];
static int head, tail, posted, live, depth, count;
static PANBIND bindings[PK_BIND_MAX];

static int Command(WORD key,DWORD bits)
{
    int i,mods=0;
    if(GetKeyState(VK_CONTROL)&0x8000)mods|=PK_CTRL;
    if(bits&0x20000000L)mods|=PK_ALT;
    if(GetKeyState(VK_SHIFT)&0x8000)mods|=PK_SHIFT;
    for(i=0;i<count;i++)
        if(bindings[i].key==key && (mods&bindings[i].mods)==bindings[i].mods &&
           (!(bindings[i].flags&PK_ONCE) || !(bits&0x40000000L)))
            return bindings[i].command;
    return 0;
}

/* Bit 31 clear: key down. Bit 29 set: Alt is down. GetKeyState reads the
 * state belonging to this key, not the live keyboard, so a key that was
 * released while the machine was busy still counts. */
int FAR PASCAL PanKeyHook(int code, WORD key, DWORD bits)
{
    int cmd, next, result;
    ++depth;
    if (code == HC_ACTION && live && owner && !(bits & 0x80000000L)) {
        cmd = Command(key,bits);
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

BOOL FAR PASCAL PanKeyInstallEx(HWND who,WORD message,const PANBIND FAR *map,int n)
{
    int i;
    if(live || !who || !message || !map || n<1 || n>PK_BIND_MAX)return FALSE;
    for(i=0;i<n;i++)if(!map[i].key || !map[i].command || map[i].command>255 ||
        (map[i].mods&~7) || (map[i].flags&~PK_ONCE))return FALSE;
    hookProc=GetProcAddress(module,"PanKeyHook");
    if(!hookProc)return FALSE;
    for(i=0;i<n;i++)bindings[i]=map[i];
    count=n;owner=who;wakeMessage=message;head=tail=posted=0;live=1;
    /* NULL is also a valid empty prior hook chain in Windows 3.0. */
    nextHook=SetWindowsHook(WH_KEYBOARD,hookProc);
    return TRUE;
}

BOOL FAR PASCAL PanKeyInstall(HWND who,WORD message)
{
    static int keys[13]={VK_HOME,VK_END,VK_LEFT,VK_RIGHT,VK_UP,VK_DOWN,
        VK_NUMPAD7,VK_NUMPAD1,VK_NUMPAD4,VK_NUMPAD6,VK_NUMPAD8,VK_NUMPAD2,'S'};
    PANBIND map[13];int i;
    for(i=0;i<13;i++){
        map[i].key=keys[i];map[i].command=i==12?PK_SETTINGS:i%6+1;
        map[i].mods=PK_CTRL|PK_ALT;map[i].flags=0;
    }
    return PanKeyInstallEx(who,message,(const PANBIND FAR *)map,13);
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
