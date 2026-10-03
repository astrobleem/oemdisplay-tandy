# Tandy Start: optional Windows 3.0 shell

TSHELL.EXE is a small native 8086 / Windows 3.0 real-mode launcher with a
bottom Start button, a native popup menu, and a 24-hour HH:MM clock.
It is optional. It never overwrites PROGMAN.EXE or edits SYSTEM.INI itself.

## Try it safely first

Copy TSHELL.EXE to your existing Windows directory. Start your accepted Tandy
Windows installation using its existing TANDY88 launcher, then choose File /
Run in Program Manager and enter TSHELL.EXE. This regular-app mode includes
Close bar, which closes only TSHELL. Keep your original setup unchanged
until this works. Test in a separate copy of your own Windows installation
first; no Windows media or stock applications are included in this package.

Click Start, press F10 while the bar is active, or use Space when its button
has focus. Arrow keys and each menu item's underlined letter use Windows'
native menu handling; Escape cancels. The clock reads DOS time without
changing it. It samples every ten seconds and repaints only when the minute
changes. Its displayed time can lag a boundary by up to ten seconds, or
longer while a non-cooperative application owns Windows execution.

Available entries: Run, Program Manager, Notepad, Paintbrush, Cookie, About
Tandy, Slosh and Mouth. Missing executables are grayed out. Optional demos must be
in the Windows directory or Windows executable search path; they are not
bundled here. WinExec errors are displayed rather than claiming a launch.
The bar is not permanently topmost: another window may cover it. Use the
normal Windows task switching keys to return to Tandy Start.

## Run and Browse

Start / Run opens a compact 128-pixel client dialog with a command line,
Run, Cancel and Browse. Type an executable and optional arguments, then
choose Run or press Enter. Escape, Cancel and closing the dialog cancel it.
Commands are limited to 126 characters. Empty, overlong and failed launches
leave the dialog open with a short error; successful WinExec calls close it.
The command edit scrolls horizontally. This uses Windows 3.0's existing
WinExec rules; it does not interpret shell operators or expand variables.

Browse uses a private Windows 3.0 dialog, not COMMDLG. Choose EXE, COM or BAT
with the filter, then select a file and Open, or double-click it. Directories,
[..] and drive entries navigate. The current directory shows a shortened
trailing path when needed. Choosing a file replaces the executable while
preserving existing command arguments. Cancel leaves the command unchanged.
The original directory on every visited drive is restored after browsing;
a restoration failure is shown and does not launch anything. Long commands
remain rejected rather than silently truncated. DOS filenames use 8.3 names.

## Optional shell selection and rollback

This is an application-shell choice only, not a display-driver install.
Do not change the accepted Tandy launcher, reservation helper, or drivers.
First exit Windows and back up C:\WINDOWS\SYSTEM.INI to a named safe copy,
for example C:\WINDOWS\SYSSTART.BAK. Verify that the backup exists and keep
bootable DOS access. In SYSTEM.INI's existing [boot] section, change only:

    shell=progman.exe

to:

    shell=tshell.exe

Keep PROGMAN.EXE in place. TSHELL recognizes that exact shell setting and
activates shell mode, which omits Close bar and
routes the bar's Close action through the Windows exit request. Start with
your existing TANDY88 launcher. Do not run WIN directly on real Tandy hardware
if that bypasses the accepted video-memory reservation helper.

To roll back, exit Windows to DOS and restore the saved SYSTEM.INI, or change
that one [boot] line back to shell=progman.exe. Restart through your existing
launcher. If TSHELL will not start, perform the same restoration from DOS.
Do not delete TSHELL before restoring Program Manager as the shell.

Program Mgr launches stock Program Manager alongside the bar and restores
an existing minimized Program Manager window. It does not
change the configured shell. Exit Windows uses the normal ExitWindows API:
applications receive the session-end query and may cancel for unsaved work.
The shell does not force termination or discard application documents.

## Deliberate limits

This is a small launcher and clock, not Explorer or a Windows 95 taskbar.
It has no task buttons, minimized-window management, tray, file manager,
desktop icons, shell hooks, drag/drop, OLE, startup-item handling,
or work-area reservation. Maximized applications may cover the bar.
Windows 3.0 stock app dialogs can clip at 160x200; TSHELL cannot fix those.
The clock is the guest's DOS local time; it is not synchronized by TSHELL.

## Build

Use the existing repository Microsoft C / Win16 libraries and DOSBox-X:

    python3 examples/TSHELL/BUILD.PY --dosbox /path/to/dosbox-x --out /new/path

/G0 /Gw /AS targets 8086 and Windows. No new compiler or library is included.
The optional shell lives entirely in examples/TSHELL. No accepted driver,
launcher, reservation helper, splash or other demo is altered.

See TESTS.MD for measured emulator coverage and remaining limitations.
Physical Tandy behavior and performance are not claimed.
