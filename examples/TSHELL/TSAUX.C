/* Optional Start tools; no configuration or Program Manager writes. */
#define WINVER 0x0300
#include <windows.h>
#include "PROGMENU.H"
#include "TNOTICE.H"
#include "TSAUX.H"

static int locate(char *name, char *out)
{
    OFSTRUCT of;
    GetWindowsDirectory(out, 144);
    if (lstrlen(out) + lstrlen(name) + 2 >= 144) return 0;
    lstrcat(out, "\\"); lstrcat(out, name);
    if (OpenFile(out, &of, OF_EXIST) != HFILE_ERROR) {
        lstrcpy(out, of.szPathName); return 1;
    }
    if (OpenFile(name, &of, OF_EXIST) != HFILE_ERROR) {
        lstrcpy(out, of.szPathName); return 1;
    }
    return 0;
}

void TandySystem(HWND w, HINSTANCE instance)
{
    char ini[144], command[128];
    int n;
    GetWindowsDirectory(ini, sizeof(ini)); lstrcat(ini, "\\TSHELL.INI");
    n = GetPrivateProfileString("Apps", "System",
           "C:\\TANDYLAB\\ABOUT\\TABOUT.EXE", command, sizeof(command), ini);
    if (!n || n >= sizeof(command) - 1) {
        TinyNotice(w, instance, "System", "Bad About path.\nSee TSHELL.INI.");
        return;
    }
    PmLaunch(w, command);
}

void TandyClock(HWND w, HINSTANCE instance)
{
    char command[144];
    if (!locate("CLOCK.EXE", command) && !locate("CALENDAR.EXE", command)) {
        TinyNotice(w, instance, "Clock", "Clock/Calendar\nnot found."); return;
    }
    PmLaunch(w, command);
}

void TandyFileManager(HWND w, HINSTANCE instance)
{
    char command[144];
    HWND frame, active;
    /* Win3.0 WINFILE refuses a second instance with a system-modal warning. */
    frame = FindWindow("WFS_Frame", NULL);
    if (frame) {
        if (IsIconic(frame)) ShowWindow(frame, SW_RESTORE);
        else if (!IsWindowVisible(frame)) ShowWindow(frame, SW_SHOW);
        active = GetLastActivePopup(frame);
        if (!active || !IsWindowVisible(active)) active = frame;
        BringWindowToTop(active);
        SetActiveWindow(active);
        return;
    }
    if (!locate("WINFILE.EXE", command)) {
        TinyNotice(w, instance, "My Computer", "File Manager\nnot found."); return;
    }
    PmLaunch(w, command);
}
