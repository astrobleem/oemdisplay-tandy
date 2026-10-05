WINDOWS XT SPLASH-ONLY UPDATE 0.2
================================
For recognized Windows 3.0 WIN.COM files, including the retained Trial4
installations. Run from plain DOS after completely exiting Windows.

DO NOT rerun
Windows Setup to install this update: doing so from an older OEM disk could
replace a newer Trial4 display driver. This tool changes only the appended
startup picture in WIN.COM. It never opens drivers, fonts or INI files for
writing, and it does not reinstall a display profile.

BEFORE APPLYING
Keep a separate backup of your working installation/card. A small guarded
file transaction cannot guarantee FAT integrity during arbitrary power loss,
media failure or torn writes. This package has been tested privately; your
actual card has not been read or written as part of that testing.

1. Extract this package into a NEW directory, for example C:\WINXT\SPLASH.
   Keep WXTSPL.EXE and WXTSPL01.RLE together.
2. Exit Windows completely. Do not use its MS-DOS Prompt or a task switcher.
3. At DOS, change to the extracted directory:
       CD C:\WINXT\SPLASH
4. Run the read-only check, using your real Windows directory:
       WXTSPL CHECK C:\WINDOWS
5. Proceed only if CHECK reports PASS for the intended directory:
       WXTSPL APPLY C:\WINDOWS
6. Start Windows with your EXISTING normal launcher. Its RESERVE handling,
   display driver, fonts, shell and sound settings are not changed.

A different Windows directory can be supplied explicitly. Do not guess the
card's drive letter. A refusal means stop and keep the existing files; the
utility deliberately does not accept an unrecognized WIN.COM or artwork.
No Python is needed on the DOS computer.

BACKUP AND RESTORE
APPLY creates/validates WIN.WXN, then renames the verified original WIN.COM
to WIN.WXB without overwriting an existing backup. It verifies that backup
before moving the verified replacement into the now-empty WIN.COM name.
The original 4,336-byte configuration/loader prefix stays byte-identical.

To undo, from plain DOS and this package directory:
       WXTSPL RESTORE C:\WINDOWS
RESTORE puts the exact original back into WIN.COM. The backup is consumed
by that rename; the approved replacement is retained as WIN.WXN. Repeated
APPLY or RESTORE is safe for recognized states. APPLY can reuse a verified
WIN.WXN on a later run. Existing files are never deleted or overwritten.

INTERRUPTION RECOVERY
Run CHECK after an interruption. If WIN.COM is temporarily absent but the
original WIN.WXB is recognized, RESTORE can recover it. Alternatively APPLY
can finish a recognized staged update. A partial/unknown WIN.WXN is preserved
and blocks APPLY; RESTORE can still put a verified original backup back.
If CHECK refuses unknown/conflicting files, preserve all files and request
review. Do not delete or overwrite WIN.WXB. Do not start Windows while
WIN.COM is absent. A successful logical write/rename is not a guarantee
against physical FAT/controller/cache failure.

An already-approved WIN.COM without WIN.WXB is reported as already applied;
it does not create a fake original backup, and RESTORE is unavailable there.

RECOGNIZED FILES
Stock retained WIN.COM: 11,118 bytes, SHA-256
5551ebcd3f32df26f759c5423f806733e006c3cae640a8336e5c618f8d899659
Old Tandy splash WIN.COM: 10,266 bytes, SHA-256
6f07b5a9fc764c74f9b3c5a0e0c521f87cdd1b3507863f1772dee4da814b1907
Approved Windows XT result: 8,398 bytes, SHA-256
8c8901b4c8482a2aefcf8a0a1beaba2ee07f90af94bf23993a8cf49eb6a30ebc
Artwork WXTSPL01.RLE: 4,062 bytes, SHA-256
eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c

VERIFICATION AND LIMITS
Built with Microsoft C 6 /G0 for the 8088, no floating point. Native DOS
apply/restore/idempotence/refusal/recovery checks passed with 640 KB and the
8086_prefetch core. Independent host sanitizer/state/fault tests verify that
recognized originals stay recoverable and unrelated files stay untouched.
A copied optimized Trial4 TR43216.DRV installation cold-booted the exact
approved image, reached its desktop and exited cleanly to DOS. Its installed
Windows files changed only at WIN.COM and the new original-backup WIN.WXB.
The Windows-active guard refused the tool from an actual Windows 3.0 DOS app.
The retained five Trial4 fixtures share the recognized startup file; their
individual driver/font layouts are not modified by this tool.

Native screenshot BOOT.PNG is an unedited 640x400 framebuffer capture:
640x200 logical rows doubled. It matches every approved artwork pixel.
Physical Tandy/card testing and cycle-exact hardware timing remain unverified.
See QA/README.MD for test scope and SOURCE for the updater source.

This package includes no Windows/DOS loader, configuration, driver or font
binaries. Those bytes come only from your recognized existing WIN.COM.
The artwork/project name makes no claim of Microsoft endorsement.
