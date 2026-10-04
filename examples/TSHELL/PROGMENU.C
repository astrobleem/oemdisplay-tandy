/* Read-only Program Manager bridge for Windows 3.0 / real-mode 8086. */
#define WINVER 0x0300
#include <windows.h>
#include <direct.h>
#include "GRPREAD.H"
#include "PROGMENU.H"
#include "TNOTICE.H"

#define PM_GROUPS 40
#define PM_PATH 144
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
} PmIndex;

/* Only labels and registration numbers survive between group reads. */
static PmIndex pmIndex[PM_GROUPS];
static PmGroup pmGroup;
static HINSTANCE pmInstance;
static char pmIni[PM_PATH], pmWindows[PM_PATH];
static int pmGroups, pmLevel, pmPage, pmGroupPage, pmRows, pmSelected;
static int pmBusy, pmMoreGroups;
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

static int pmopen(int number)
{
    char path[PM_PATH];
    LONG length;
    int status;
    pmclose();
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

static int pmrefresh(void)
{
    int n, status;
    char path[PM_PATH];
    pmGroups = 0; pmMoreGroups = 0;
    n = GetWindowsDirectory(pmWindows, sizeof(pmWindows));
    if (!n || n >= sizeof(pmWindows) - 14) return 0;
    lstrcpy(pmIni, pmWindows);
    lstrcat(pmIni, "\\PROGMAN.INI");
    for (n = 1; n <= PM_GROUPS; ++n) {
        status = pmgroupfile(n, path);
        /* Windows 3.0 stops at the first missing GroupN registration. */
        if (!status) break;
        pmIndex[pmGroups].number = (unsigned char)n;
        status = status < 0 ? PM_IO : pmopen(n);
        pmIndex[pmGroups].status = (unsigned char)status;
        if (status) wsprintf(pmIndex[pmGroups].title, "Group%d [bad]", n);
        else lstrcpy(pmIndex[pmGroups].title, pmGroup.title);
        pmclose();
        ++pmGroups;
    }
    if (pmGroups == PM_GROUPS && pmgroupfile(PM_GROUPS + 1, path))
        pmMoreGroups = 1;
    return 1;
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

static void pmstatus(HWND w, char *text)
{
    SetDlgItemText(w, PM_STATUS, text);
}

static void pmpage(HWND w)
{
    char name[PM_NAME_MAX + 1], status[24];
    int count, i, from, end, pages, result;
    count = pmLevel ? (int)pmGroup.count : pmGroups;
    from = pmPage * pmRows;
    end = from + pmRows;
    if (end > count) end = count;
    SendDlgItemMessage(w, PM_LIST, LB_RESETCONTENT, 0, 0L);
    for (i = from; i < end; ++i) {
        if (pmLevel) {
            result = PmReadName(pmread, &pmFile, &pmGroup,
                                (unsigned)i, name, sizeof(name));
            if (result) lstrcpy(name, "[Read failed]");
        } else lstrcpy(name, pmIndex[i].title);
        SendDlgItemMessage(w, PM_LIST, LB_ADDSTRING, 0, (LPARAM)(LPSTR)name);
    }
    pages = (count + pmRows - 1) / pmRows;
    if (!pages) pages = 1;
    wsprintf(status, "%s %d/%d", (LPSTR)(pmLevel ? "Apps" : "Groups"),
             pmPage + 1, pages);
    pmstatus(w, status);
    SetWindowText(w, pmLevel ? pmGroup.title : "Programs");
    SetDlgItemText(w, IDOK, pmLevel ? "&Run" : "&Open");
    EnableWindow(GetDlgItem(w, PM_BACK), pmPage > 0 || pmLevel);
    EnableWindow(GetDlgItem(w, PM_NEXT), end < count);
    EnableWindow(GetDlgItem(w, IDOK), count > 0);
    if (end > from) SendDlgItemMessage(w, PM_LIST, LB_SETCURSEL, 0, 0L);
    SetFocus(GetDlgItem(w, PM_LIST));
    if (!count) pmstatus(w, pmLevel ? "Empty group" : "No groups found");
    else if (!pmLevel && pmMoreGroups) pmstatus(w, "First 40 groups");
}

static void pmchoose(HWND w)
{
    char command[128];
    int selected, status;
    selected = (int)SendDlgItemMessage(w, PM_LIST, LB_GETCURSEL, 0, 0L);
    if (selected == LB_ERR) return;
    selected += pmPage * pmRows;
    if (!pmLevel) {
        if (selected >= pmGroups) return;
        /* Revalidate on entry even when the index was obtained moments ago. */
        status = pmopen(pmIndex[selected].number);
        if (status) { pmstatus(w, pmreason(status)); return; }
        pmSelected = selected;
        pmGroupPage = pmPage;
        pmPage = 0; pmLevel = 1;
        pmpage(w);
    } else {
        if (selected >= (int)pmGroup.count) return;
        status = PmReadCommand(pmread, &pmFile, &pmGroup,
                              (unsigned)selected, command, sizeof(command));
        if (status) { pmstatus(w, pmreason(status)); return; }
        /* Close the group handle before WinExec, preserving the parsed command. */
        pmclose();
        if (PmLaunch(w, command)) { EndDialog(w, IDOK); return; }
        status = pmopen(pmIndex[pmSelected].number);
        if (status) {
            pmLevel = 0; pmPage = pmGroupPage;
        }
        pmpage(w);
    }
}

BOOL FAR PASCAL PmDialogProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    RECT r, c;
    HWND child;
    HDC dc;
    HFONT oldfont;
    TEXTMETRIC tm;
    int ww, hh, i, ids[6];
    if (m == WM_INITDIALOG) {
        GetWindowRect(w, &r); GetClientRect(w, &c);
        ww = PM_CLIENT_W + r.right - r.left - c.right;
        hh = PM_CLIENT_H + r.bottom - r.top - c.bottom;
        SetWindowPos(w, NULL, (GetSystemMetrics(SM_CXSCREEN) - ww) / 2,
                     (GetSystemMetrics(SM_CYSCREEN) - hh) / 2,
                     ww, hh, SWP_NOZORDER);
        CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | SS_LEFT,
                     4, 2, 120, 14, w, (HMENU)PM_STATUS, pmInstance, NULL);
        CreateWindow("LISTBOX", "", WS_CHILD | WS_VISIBLE | WS_TABSTOP |
                     WS_BORDER | WS_HSCROLL | LBS_NOTIFY | LBS_NOINTEGRALHEIGHT,
                     4, 18, 120, PM_LIST_H, w, (HMENU)PM_LIST, pmInstance, NULL);
        CreateWindow("BUTTON", "&Back", WS_CHILD | WS_VISIBLE | WS_TABSTOP,
                     4, 104, 58, 20, w, (HMENU)PM_BACK, pmInstance, NULL);
        CreateWindow("BUTTON", "&Next", WS_CHILD | WS_VISIBLE | WS_TABSTOP,
                     66, 104, 58, 20, w, (HMENU)PM_NEXT, pmInstance, NULL);
        CreateWindow("BUTTON", "&Open", WS_CHILD | WS_VISIBLE | WS_TABSTOP |
                     BS_DEFPUSHBUTTON, 4, 128, 58, 20,
                     w, (HMENU)IDOK, pmInstance, NULL);
        CreateWindow("BUTTON", "&Cancel", WS_CHILD | WS_VISIBLE | WS_TABSTOP,
                     66, 128, 58, 20, w, (HMENU)IDCANCEL, pmInstance, NULL);
        ids[0] = PM_STATUS; ids[1] = PM_LIST; ids[2] = PM_BACK;
        ids[3] = PM_NEXT; ids[4] = IDOK; ids[5] = IDCANCEL;
        for (i = 0; i < 6; ++i) {
            child = GetDlgItem(w, ids[i]);
            if (!child) { EndDialog(w, IDCANCEL); return TRUE; }
            SendMessage(child, WM_SETFONT, (WPARAM)GetStockObject(SYSTEM_FIXED_FONT), 0L);
        }
        dc = GetDC(w);
        oldfont = SelectObject(dc, GetStockObject(SYSTEM_FIXED_FONT));
        GetTextMetrics(dc, &tm);
        SelectObject(dc, oldfont); ReleaseDC(w, dc);
        pmRows = (PM_LIST_H - 2 * GetSystemMetrics(SM_CYBORDER) -
                  GetSystemMetrics(SM_CYHSCROLL)) / tm.tmHeight;
        if (pmRows < 1) pmRows = 1;
        if (pmRows > 8) pmRows = 8;
        SendDlgItemMessage(w, PM_LIST, LB_SETHORIZONTALEXTENT,
                           (PM_NAME_MAX + 1) * tm.tmAveCharWidth, 0L);
        pmLevel = 0; pmPage = 0;
        pmpage(w); return FALSE;
    }
    if (m == WM_COMMAND) {
        if (wp == IDOK || (wp == PM_LIST && HIWORD(lp) == LBN_DBLCLK)) {
            pmchoose(w); return TRUE;
        }
        if (wp == PM_NEXT) {
            if ((pmPage + 1) * pmRows < (pmLevel ? (int)pmGroup.count : pmGroups)) {
                ++pmPage; pmpage(w);
            }
            return TRUE;
        }
        if (wp == PM_BACK) {
            if (pmPage) --pmPage;
            else if (pmLevel) {
                pmclose(); pmLevel = 0; pmPage = pmGroupPage;
            }
            pmpage(w); return TRUE;
        }
        if (wp == IDCANCEL) { EndDialog(w, IDCANCEL); return TRUE; }
    }
    if (m == WM_CLOSE) { EndDialog(w, IDCANCEL); return TRUE; }
    return FALSE;
}

static void pmword(BYTE FAR **p, unsigned value)
{
    *(*p)++ = (BYTE)value; *(*p)++ = (BYTE)(value >> 8);
}

void PmPrograms(HWND owner, HINSTANCE instance)
{
    HGLOBAL memory;
    BYTE FAR *p;
    FARPROC proc;
    DWORD style, units;
    char *title;
    if (pmBusy) return;
    pmBusy = 1;
    pmInstance = instance;
    if (!pmrefresh()) {
        pmerror(owner, "Windows path\nerror."); pmBusy = 0; return;
    }
    memory = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, 64);
    if (!memory) { pmBusy = 0; return; }
    p = (BYTE FAR *)GlobalLock(memory);
    if (!p) { GlobalFree(memory); pmBusy = 0; return; }
    style = WS_POPUP | WS_CAPTION | WS_SYSMENU | DS_MODALFRAME;
    pmword(&p, LOWORD(style)); pmword(&p, HIWORD(style)); *p++ = 0;
    units = GetDialogBaseUnits();
    pmword(&p, 0); pmword(&p, 0);
    pmword(&p, PM_CLIENT_W * 4 / LOWORD(units));
    pmword(&p, PM_CLIENT_H * 8 / HIWORD(units));
    *p++ = 0; *p++ = 0;
    title = "Programs";
    while (*title) *p++ = *title++;
    *p = 0;
    GlobalUnlock(memory);
    proc = MakeProcInstance((FARPROC)PmDialogProc, instance);
    if (proc) {
        DialogBoxIndirect(instance, memory, owner, (DLGPROC)proc);
        FreeProcInstance(proc);
    }
    GlobalFree(memory);
    pmclose(); pmBusy = 0;
}
