/* Read-only Program Manager bridge for Windows 3.0 / real-mode 8086. */
#define WINVER 0x0300
#include <windows.h>
#include <direct.h>
#include "GRPREAD.H"
#include "PROGMENU.H"
#include "TNOTICE.H"
#include "TSMENU.H"

#define PM_GROUPS 40
#define PM_PATH 144
#define PM_BUNDLED 12
#define PM_LIST 210
#define PM_BACK 211
#define PM_NEXT 212
#define PM_STATUS 213
#define PM_CLIENT_W 128
#define PM_CLIENT_H 154
#define PM_LIST_H 82

typedef struct {
    char title[PM_NAME_MAX + 1];
    unsigned char number, status;
    HMENU menu;
    unsigned size, checksum;
} PmIndex;

/* Only labels and registration numbers survive between group reads. */
static PmIndex pmIndex[PM_GROUPS + 1];
typedef struct {
    char name[PM_NAME_MAX + 1], command[PM_CMD_MAX + 1];
} PmBundled;
static PmBundled pmBundled[PM_BUNDLED];
static int pmBundleCount, pmBundleActive;
static PmGroup pmGroup;
static HINSTANCE pmInstance;
static char pmIni[PM_PATH], pmWindows[PM_PATH];
static int pmGroups, pmRows, pmReady, pmOpenGroup;
static HMENU pmRoot;
#define PM_FIRST 1000
static int pmBusy;
static HFILE pmFile = HFILE_ERROR;

static void pmerror(HWND w, char *text)
{
    TinyNotice(w, (HINSTANCE)GetWindowWord(w, GWW_HINSTANCE),
               "Programs", text);
}

static char *pmreason(int code)
{
    switch (code) {
    case PM_IO: return "Read failed";
    case PM_CHECKSUM: return "Bad checksum";
    case PM_VERSION: return "Needs Win3.0 GRP";
    case PM_LIMIT: return "Too many items";
    case PM_STRING: return "Bad GRP string";
    case PM_LONG: return "Max 126 chars";
    default: return "Bad group file";
    }
}

static int pmread(void *context, unsigned long offset,
                   unsigned char *buffer, unsigned count)
{
    HFILE file;
    file = *(HFILE *)context;
    return _llseek(file, (LONG)offset, 0) == (LONG)offset &&
           _lread(file, buffer, count) == count;
}

static void pmclose(void)
{
    if (pmFile != HFILE_ERROR) _lclose(pmFile);
    pmFile = HFILE_ERROR;
}

/* Relative GRP filenames are resolved under the Windows directory. */
static int pmgroupfile(int number, char *path)
{
    char key[12], value[PM_PATH];
    int n;
    wsprintf(key, "Group%d", number);
    n = GetPrivateProfileString("Groups", key, "", value,
                                 sizeof(value), pmIni);
    if (!n) return 0;
    if (n >= sizeof(value) - 1) return -1;
    if (value[1] == ':' && value[2] == '\\') lstrcpy(path, value);
    else {
        if (value[0] == '\\' || value[1] == ':' ||
            lstrlen(pmWindows) + n + 2 > PM_PATH) return -1;
        lstrcpy(path, pmWindows);
        lstrcat(path, "\\");
        lstrcat(path, value);
    }
    return 1;
}

static void pmbundles(void)
{
    char profile[PM_PATH], key[16], name[PM_NAME_MAX + 2];
    char command[PM_CMD_MAX + 2], token[128];
    int count, i, n;
    OFSTRUCT of;
    pmBundleCount = 0;
    lstrcpy(profile, pmWindows); lstrcat(profile, "\\TSHELL.INI");
    count = GetPrivateProfileInt("Programs", "Count", 0, profile);
    if (count < 0 || count > PM_BUNDLED) return;
    for (i = 1; i <= count; ++i) {
        wsprintf(key, "Name%d", i);
        n = GetPrivateProfileString("Programs", key, "", name,
                                   sizeof(name), profile);
        if (!n || n > PM_NAME_MAX) continue;
        wsprintf(key, "Command%d", i);
        n = GetPrivateProfileString("Programs", key, "", command,
                                   sizeof(command), profile);
        if (!n || n > PM_CMD_MAX ||
            !PmCommandToken(command, token, sizeof(token)) ||
            PmTokenKind(token) != 2 ||
            OpenFile(token, &of, OF_EXIST) == HFILE_ERROR) continue;
        lstrcpy(pmBundled[pmBundleCount].name, name);
        lstrcpy(pmBundled[pmBundleCount].command, command);
        ++pmBundleCount;
    }
}

static int pmopen(int number)
{
    char path[PM_PATH];
    LONG length;
    int status;
    pmclose(); pmBundleActive = number == 0;
    if (pmBundleActive) {
        pmbundles();
        lstrcpy(pmGroup.title, "Windows XT");
        pmGroup.count = (unsigned)pmBundleCount;
        return PM_OK;
    }
    if (pmgroupfile(number, path) != 1) return PM_IO;
    pmFile = _lopen(path, OF_READ | OF_SHARE_DENY_WRITE);
    if (pmFile == HFILE_ERROR) return PM_IO;
    length = _llseek(pmFile, 0L, 2);
    if (length < 0) status = PM_IO;
    else status = PmReadGroup(pmread, &pmFile, (unsigned long)length,
                              &pmGroup);
    if (status) pmclose();
    return status;
}

/* Preserve exact command bytes, including switch case and whitespace. */
UINT PmLaunchShow(HWND w, char *command, int show)
{
    char token[128], directory[PM_PATH], old[PM_PATH], targetOld[PM_PATH];
    char error[48];
    OFSTRUCT of;
    int i, last, oldDrive, targetDrive, changed, restored, n;
    UINT result;
    if (!command || lstrlen(command) > PM_CMD_MAX) {
        pmerror(w, "Command too\nlong. Maximum\n126 chars."); return 0;
    }
    if (!PmCommandToken(command, token, sizeof(token)) ||
        !PmTokenKind(token)) {
        pmerror(w, "Unsupported\npath. Use full\nDOS path or\nbare filename.");
        return 0;
    }
    /* Resolve only for the launch directory; never replace the saved tail. */
    if (OpenFile(token, &of, OF_EXIST) == HFILE_ERROR) {
        n = lstrlen(token);
        last = 0;
        for (i = 0; token[i]; ++i) if (token[i] == '\\') last = i + 1;
        for (i = last; token[i]; ++i) if (token[i] == '.') break;
        if (token[i] || n + 5 > sizeof(token)) {
            pmerror(w, "App not found."); return 0;
        }
        lstrcat(token, ".EXE");
        if (OpenFile(token, &of, OF_EXIST) == HFILE_ERROR) {
            pmerror(w, "App not found."); return 0;
        }
    }
    lstrcpy(directory, of.szPathName);
    last = -1;
    for (i = 0; directory[i]; ++i) if (directory[i] == '\\') last = i;
    if (last < 2 || directory[1] != ':') {
        pmerror(w, "Cannot find\napp path."); return 0;
    }
    if (last == 2) directory[3] = 0;
    else directory[last] = 0;
    targetDrive = directory[0];
    if (targetDrive >= 'a' && targetDrive <= 'z') targetDrive -= 32;
    targetDrive -= 'A' - 1;
    oldDrive = _getdrive();
    if (targetDrive < 1 || targetDrive > 26 || oldDrive < 1 ||
        !getcwd(old, sizeof(old)) ||
        !_getdcwd(targetDrive, targetOld, sizeof(targetOld))) {
        pmerror(w, "Cannot save\ncurrent path."); return 0;
    }
    changed = 0;
    result = 0;
    if (!_chdrive(targetDrive)) {
        changed = 1;
        if (!chdir(directory)) result = WinExec(command, show);
    }
    /* WinExec can yield; restore even on failure. No per-drive CWD leaks. */
    restored = 1;
    if (changed && chdir(targetOld)) restored = 0;
    if (_chdrive(oldDrive)) restored = 0;
    if (chdir(old)) restored = 0;
    if (!restored) {
        pmerror(w, "Path restore\nfailed. Please\nrestart bar."); return 0;
    }
    if (result < 32) {
        if (!result) pmerror(w, "Launch failed\nor app path\nunavailable.");
        else {
            wsprintf(error, "Launch failed.\nError %u.", result);
            pmerror(w, error);
        }
        return 0;
    }
    return (UINT)result;
}

int PmLaunch(HWND w, const char *command)
{
    return PmLaunchShow(w, (char *)command, SW_SHOWNORMAL) >= 32;
}


/* A session owns one root, at most 40 group placeholders, and bounded pages.
   Only the entered group is parsed; command tails are never cached/truncated. */
static void pmclear(HMENU menu)
{
    HMENU child;
    while (GetMenuItemCount(menu) > 0) {
        child = GetSubMenu(menu, 0);
        if (!RemoveMenu(menu, 0, MF_BYPOSITION)) break;
        if (child) DestroyMenu(child);
    }
}

/* Ampersands in saved names are literal, not accidental menu accelerators.
   Complete labels retain the exact group/item mapping. */
static void pmlabel(char *out, char *name)
{
    int i, n;
    /* Display fitting belongs to the selected-font popup renderer. Keep the
       complete label here; IDs and saved launch bytes remain unchanged. */
    for (i = 0, n = 0; name[i]; ++i) {
        out[n++] = name[i];
        if (name[i] == '&') out[n++] = '&';
    }
    out[n] = 0;
}

static int pmrows(void)
{
    HDC dc; HFONT old; TEXTMETRIC tm; int row, count, height;
    /* Use a conservative fallback if a low-memory GDI query fails. The
       physical viewport of every current EX/HX profile is 200 rows, even
       when the optional panning desktop reports a taller logical screen. */
    row=GetSystemMetrics(SM_CYMENU);if(row<1)row=17;
    dc=GetDC(NULL);
    if(dc){
        old=(HFONT)SelectObject(dc,GetStockObject(SYSTEM_FONT));
        if(GetTextMetrics(dc,&tm) && tm.tmHeight>0)
            row=tm.tmHeight+GetSystemMetrics(SM_CYBORDER);
        SelectObject(dc,old);ReleaseDC(NULL,dc);
    }
    height=GetSystemMetrics(SM_CYSCREEN);if(height>200)height=200;
    count=(height-8)/row-1;
    if(count<1)count=1;if(count>24)count=24;
    return count;
}

static int pmpeek(int number, char *title)
{
    char path[PM_PATH]; LONG length; int result;
    if (pmgroupfile(number, path) != 1) return PM_IO;
    pmFile = _lopen(path, OF_READ | OF_SHARE_DENY_WRITE);
    if (pmFile == HFILE_ERROR) return PM_IO;
    length = _llseek(pmFile, 0L, 2);
    result = length < 0 ? PM_IO : PmReadTitle(pmread, &pmFile,
                              (unsigned long)length, title, PM_NAME_MAX+1);
    pmclose(); return result;
}

static int pmstamp(unsigned *checksum)
{
    unsigned char b[2];
    if (!pmread(&pmFile, 4UL, b, 2)) return 0;
    *checksum = (unsigned)b[0] | ((unsigned)b[1] << 8); return 1;
}

static int pmnext(HMENU *page, char *label)
{
    HMENU next;
    next = CreatePopupMenu();
    if (!next) return 0;
    if (!AppendMenu(*page, MF_POPUP, (UINT)next, label)) {
        DestroyMenu(next); return 0;
    }
    *page = next; return 1;
}

static int pmfillroot(void)
{
    int n, found, status; char path[PM_PATH], label[2*PM_NAME_MAX+1];
    HMENU page, child;
    pmGroups = 0; pmRows = pmrows();
    n = GetWindowsDirectory(pmWindows, sizeof(pmWindows));
    if (!n || n >= sizeof(pmWindows)-14) return 0;
    lstrcpy(pmIni, pmWindows); lstrcat(pmIni, "\\PROGMAN.INI");
    page = pmRoot; pmclear(page);
    for (n=1; n<=PM_GROUPS; ++n) {
        found = pmgroupfile(n, path);
        if (!found) break; /* Match Win3.0 GroupN registration semantics. */
        if (pmGroups && !(pmGroups % pmRows) && !pmnext(&page, "&More")) return 0;
        pmIndex[pmGroups].number = (unsigned char)n;
        status = found < 0 ? PM_IO : pmpeek(n, pmIndex[pmGroups].title);
        pmIndex[pmGroups].status = (unsigned char)status;
        pmIndex[pmGroups].menu = NULL;
        if (status) {
            wsprintf(pmIndex[pmGroups].title, "Group%d [bad]", n);
            pmlabel(label, pmIndex[pmGroups].title);
            if (!AppendMenu(page, MF_STRING|MF_GRAYED, 0, label)) return 0;
        } else {
            child = CreatePopupMenu(); if (!child) return 0;
            if (!AppendMenu(child, MF_STRING|MF_GRAYED, 0, "...") ||
                !AppendMenu(page, MF_POPUP, (UINT)child,
                   (pmlabel(label, pmIndex[pmGroups].title), label))) {
                DestroyMenu(child); return 0;
            }
            pmIndex[pmGroups].menu = child;
        }
        ++pmGroups;
    }
    pmbundles();
    if (pmBundleCount) {
        if (pmGroups && !(pmGroups % pmRows) && !pmnext(&page,"&More")) return 0;
        pmIndex[pmGroups].number=0;pmIndex[pmGroups].status=0;
        lstrcpy(pmIndex[pmGroups].title,"Windows XT");
        child=CreatePopupMenu();if(!child)return 0;
        pmlabel(label,pmIndex[pmGroups].title);
        if (!AppendMenu(child,MF_STRING|MF_GRAYED,0,"...") ||
            !AppendMenu(page,MF_POPUP,(UINT)child,label)) { DestroyMenu(child);return 0; }
        pmIndex[pmGroups++].menu=child;
    }
    if (!pmGroups && !AppendMenu(page, MF_STRING|MF_GRAYED, 0, "No groups")) return 0;
    if (pmGroups==PM_GROUPS && pmgroupfile(PM_GROUPS+1,path) &&
        !AppendMenu(page, MF_STRING|MF_GRAYED, 0, "First 40 groups")) return 0;
    return 1;
}

static int pmfillgroup(int group)
{
    int status, i; unsigned checksum; HMENU page;
    char name[PM_NAME_MAX+1], label[2*PM_NAME_MAX+1];
    page = pmIndex[group].menu; pmclear(page);
    status = pmopen(pmIndex[group].number);
    if (status) { AppendMenu(page, MF_STRING|MF_GRAYED, 0, pmreason(status)); return 1; }
    checksum=0;
    if (!pmBundleActive && !pmstamp(&checksum)) { pmclose(); return 0; }
    pmIndex[group].size = pmGroup.size; pmIndex[group].checksum = checksum;
    if (!pmGroup.count) AppendMenu(page, MF_STRING|MF_GRAYED, 0, "Empty group");
    for (i=0; i<(int)pmGroup.count; ++i) {
        if (i && !(i % pmRows) && !pmnext(&page, "&More")) { pmclose(); return 0; }
        if (pmBundleActive) { lstrcpy(name,pmBundled[i].name);status=0; }
        else status = PmReadName(pmread, &pmFile, &pmGroup, (unsigned)i, name, sizeof(name));
        if (status) { pmclose(); return 0; }
        pmlabel(label, name);
        if (!AppendMenu(page, MF_STRING | (!pmBundleActive && pmGroup.item[i].commandLength>PM_CMD_MAX?MF_GRAYED:0),
                         PM_FIRST+group*PM_MAX_ITEMS+i, label)) { pmclose(); return 0; }
    }
    pmclose(); return 1;
}

HMENU PmMenuCreate(HINSTANCE inst)
{
    if (pmBusy) return NULL;
    pmRoot = CreatePopupMenu(); if (!pmRoot) return NULL;
    if (!AppendMenu(pmRoot, MF_STRING|MF_GRAYED, 0, "...")) {
        DestroyMenu(pmRoot); pmRoot=NULL; return NULL;
    }
    pmInstance=inst; pmBusy=1; pmReady=0; pmGroups=0;pmOpenGroup=-1;
    /* The tracker initializes Programs before measuring its popup.
       Leave all group-label reads deferred until Programs is entered. */
    return pmRoot;
}

void PmMenuDone(void)
{
    /* Win3.0 posts WM_COMMAND after TrackPopupMenu returns. Keep only the
       small ID/registration snapshot until that command or the next session.
       All native menu objects have already been recursively destroyed. */
    pmclose(); pmRoot=NULL; pmBusy=0;
}

void PmMenuInit(HMENU menu)
{
    int i;
    if (!pmBusy) return;
    if (menu==pmRoot && !pmReady) {
        pmReady=1;
        if (!pmfillroot()) {
            pmclear(pmRoot);pmGroups=0;
            AppendMenu(pmRoot, MF_STRING|MF_GRAYED, 0, "Menu unavailable");
        }
        return;
    }
    for (i=0; i<pmGroups; ++i) if (menu==pmIndex[i].menu) {
        if (!pmIndex[i].status) {
            /* Keep only one populated group, rather than up to 2,000 strings.
               The tracker has closed the previous child before initializing this one;
               its group placeholder stays attached to the Programs root. */
            if(pmOpenGroup>=0 && pmOpenGroup!=i){
                pmclear(pmIndex[pmOpenGroup].menu);
                AppendMenu(pmIndex[pmOpenGroup].menu,MF_STRING|MF_GRAYED,0,"...");
                pmIndex[pmOpenGroup].status=0;
            }
            pmOpenGroup=i;
            pmIndex[i].status=1; /* No repeated I/O within the open group. */
            if (!pmfillgroup(i)) {
                pmclear(menu);AppendMenu(menu, MF_STRING|MF_GRAYED, 0, "Menu unavailable");
            }
        }
        return;
    }
}

int PmMenuCommand(unsigned command)
{
    return command>=PM_FIRST && command<PM_FIRST+(PM_GROUPS+1)*PM_MAX_ITEMS;
}

int PmMenuChoose(HWND owner, unsigned command)
{
    int group, item, status; unsigned checksum; char saved[PM_CMD_MAX+2];
    if (!PmMenuCommand(command)) return 0;
    if (!pmReady) return 1;
    group=(command-PM_FIRST)/PM_MAX_ITEMS; item=(command-PM_FIRST)%PM_MAX_ITEMS;
    if (group>=pmGroups || !pmIndex[group].menu || !pmIndex[group].status) return 1;
    pmReady=0; /* Consume a posted selection once. */
    if (!pmIndex[group].number) {
        if (item>=pmBundleCount) return 1;
        lstrcpy(saved,pmBundled[item].command);
        pmbundles();
        if (item>=pmBundleCount || lstrcmp(saved,pmBundled[item].command))
            pmerror(owner,"Group changed.\nReopen Start.");
        else PmLaunch(owner,saved);
        return 1;
    }
    status=pmopen(pmIndex[group].number);
    if (!status && (!pmstamp(&checksum) || pmGroup.size!=pmIndex[group].size ||
                    checksum!=pmIndex[group].checksum)) {
        pmclose();pmerror(owner,"Group changed.\nReopen Start.");return 1;
    }
    if (!status) status=PmReadCommand(pmread,&pmFile,&pmGroup,(unsigned)item,saved,sizeof(saved));
    pmclose(); /* No group handle survives WinExec or its modal error dialog. */
    if (status) pmerror(owner,pmreason(status));
    else PmLaunch(owner,saved);
    return 1;
}

void PmPrograms(HWND owner, HINSTANCE inst)
{
    HMENU menu;
    menu=PmMenuCreate(inst);if(!menu)return;
    PmMenuInit(menu);SetActiveWindow(owner);SetFocus(owner);
    TSMenuTrack(menu, 0, 0, owner);
    DestroyMenu(menu);PmMenuDone();
}

/* Retained export for old optional callers; Programs tracks the same HMENU tree. */
BOOL FAR PASCAL PmDialogProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    return FALSE;
}
