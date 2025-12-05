README.TXT

USING NOTEPAD TO VIEW ON-LINE DOCUMENTS
=======================================

  *  If you enlarge Notepad to its maximum size, the following 
     document will be easier to read. To do so, click the 
     Maximize button in the upper-right corner of the Notepad 
     window. Or open the Control menu in the upper-left corner
     of the Notepad window and choose Maximize.

  *  To move through the document, press PAGE UP and PAGE DOWN 
     or click the arrows at the top and bottom of the scroll bar 
     along the right side of the Notepad window.

  *  To print the document, choose Print from the Notepad File 
     menu.

  *  To read other on-line documents, choose Open from the File
     menu.

  *  For Help using Notepad, press F1.

  *  If you are currently setting up Windows, choose Exit from 
     the Notepad File menu to continue with Setup.


NOTES ON WINDOWS 3.0
====================

This document contains important information that is not 
included in the Windows User's Guide or in on-line Help. These 
topics are covered:

  *  Copying files from the Windows 3.0 disks

  *  Running out of memory and how to increase available memory

  *  Using the Swapfile utility

  *  Using HIMEM.SYS

  *  Giving maximum priority to an application

  *  Using Windows 2.x drivers with Windows 3.0

  *  Running specific non-Windows applications

  *  Running specific Windows applications

  *  General notes about applications

  *  General notes about hardware

  

COPYING FILES FROM THE WINDOWS 3.0 DISKS
========================================

The files on the Windows 3.0 installation disks are compressed. 
The files are not usable until they are expanded. Setup and 
Control Panel expand the compressed files as they are copied 
onto your hard disk.

If you need to copy files directly from a Windows 3.0 disk 
without using Setup or Control Panel, follow these steps:

  1.  Copy EXPAND.EXE from Microsoft Windows Disk #2 onto your 
      hard drive. (This utility expands compressed files to a 
      useable format.)

  2.  Insert the disk with the file you want to expand into 
      drive A: (or any floppy-disk drive).

  3.  Type the following and press ENTER:

        expand x:<filename> y:<filename>

      where x: is the disk drive you are copying from (source)
            y: is the disk drive you are copying to (destination)

      The compressed file is expanded as it is copied onto your 
      hard-disk drive.

System files (.SYS) are named SY$ as compressed files. For 
example, MOUSE.SYS is named MOUSE.SY$; HIMEM.SYS, HIMEM.SY$ and 
so forth. When you use Windows Setup to install these files, 
they are renamed with .SYS extensions automatically.

If you use the expand utility to copy .SY$ files onto your hard 
disk, you must change their filename extensions to .SYS. You can
use the MS-DOS Rename command or you can rename each file as you
copy them from the Windows Disk with the Expand command.

To rename a file when you expand it, type the following command 
and press ENTER:

  expand x:filename.sy$ c:\windirectory\filename.sys

where x: is the source disk
      filename.sy$ is the name of the compressed file you want
        to copy
      \windirectory is the name of your windows directory
      filename.sys is the renamed file that will appear on your
        hard disk


WHAT IF YOU RUN OUT OF MEMORY?
==============================

As you're running applications in Windows or are trying to start
an application, you might receive messages about being out of 
memory. You can find out how much memory is available and of what
type by choosing the About command from the Help menu in either
Program Manager or File Manager. A dialog box containing memory 
information appears.

The following list describes each memory category and suggests 
how to increase available memory:

Amount of memory free   This number is the amount of conventional
			memory currently available for 
			applications.  
  			
			When you run Windows in standard mode, 
			this number includes extended memory.

                        When you run Windows in 386 enhanced 
			mode, this number includes virtual 
			memory and could be much larger than the
			physical amount of memory in your 
			computer. 

			If you need more memory or if the amount
  			of free memory is less than 30K, close 
			some applications.

Amount of EMS free      When you run Windows in real mode with 
			an expanded memory driver installed, 
			this number shows the amount of expanded 
			memory currently available. It is 
			possible to have plenty of expanded 
			memory available, but be out of 
			conventional memory. 

			You can close some applications to free 
			up conventional memory.

SMARTDrive Amount       This number is the amount of expanded 
			memory claimed by SMARTDrive. Windows 
			3.0 can allocate memory from SMARTDrive 
			as needed.

                        For more information on how to use 
			SMARTDrive, see Chapter 13, "Optimizing 
			Windows," in the Windows User's Guide.

System Resources        This number is the percentage of system 
			resources available. This number never 
			reaches 100% because the system itself 
			takes up some system resources.

			If this number is too low (about 15%), 
			you cannot run more applications 
			regardless of how much free memory you 
			have. Close some applications to free 
			system resources. 


USING THE SWAPFILE UTILITY
==========================

Windows 3.0 includes a utility that can dramatically improve 
Windows' performance on some computers when you are running in 
386 enhanced mode. Swapfile turns a portion of hard disk space 
into additional memory. However, Swapfile cannot be used with 
all hard disk drives because of the way some drives interact 
with MS-DOS. 

If you want to run Swapfile with Windows, see Chapter 13, 
"Optimizing Windows," in the Windows User's Guide for important
information.


USING HIMEM.SYS
===============

HIMEM.SYS is a driver required by Windows 3.0 for using extended 
memory. It must be included in your CONFIG.SYS file. The method 
HIMEM uses to access extended memory depends on your hardware.

When you boot your computer, HIMEM is loaded from your
CONFIG.SYS file. After it is loaded, you will see a message like
the following telling you the method HIMEM will use to access 
extended memory on your computer.

  Installed A20 handler number X.

   where X is 1 through 8 which corresponds to one of the 
   following methods:

      Number   Name               Computer type
  --------------------------------------------------------------
        1        at               ; IBM AT or 100% compatible.
        2        ps2              ; IBM PS/2
        3        ptlcascade       ; Phoenix Cascade BIOS
        4        hpvectra         ; HP Vectra (A & A+)
        5        att6300plus      ; AT&T 6300 Plus
        6        acer1100         ; Acer 1100
        7        toshiba          ; Toshiba 1600 & 1200XE
        8        wyse             ; Wyse 12.5 Mhz 286 


If HIMEM does not work properly, you can try a different method.
Specify the switch for your computer type on the 
device=HIMEM.SYS line in your CONFIG.SYS file. Computer type 
corresponds to either the number or the name of your computer 
from the table.

For example the following lines are equivalent:

  device=c:\himem.sys /M:ps2
  device=c:\himem.sys /M:2

This entry forces HIMEM to use the IBM PS/2 A20 method for 
accessing extended memory.


GIVING MAXIMUM PRIORITY TO AN APPLICATION
=========================================
Windows lets you set the specific amount of processing time 
your applications will receive relative to other applications 
that are running. 
 
To ensure that a particular application receives all the 
processing time it needs without interruption, set its Priority 
Foreground option to 10000. With this setting, no background
applications will be allowed to run unless the foreground
application is idle. 

See Chapter 12, "More About Applications," in the 
Windows User's Guide for more information about this setting.


USING WINDOWS 2.X DRIVERS WITH WINDOWS 3.0
==========================================

Windows 3.0 will not start in standard mode or 386 enhanced 
mode if you installed Windows 2.x display, mouse, sound, system,
or communications drivers. You must update these drivers to run 
Windows 3.0.

To start Windows in real mode, type the following at the MS-DOS 
prompt and press ENTER:

  win /r

If you use Windows 2.x printer drivers with Windows 3.0, you 
might see a warning when you print. As with Windows 2.x 
applications, 2.x printer drivers work reliably only if you run 
Windows 3.0 in real mode.

  NOTE  It is recommended that you install only the drivers 
	provided with Windows 3.0. If you want to use a special
	device driver that was not provided with Windows, contact
	the manufacturer for an updated driver that works with 
	Windows 3.0.


RUNNING SPECIFIC NON-WINDOWS APPLICATIONS
=========================================

This section describes some problems you might have running 
non-Windows applications with Windows 3.0.


Microsoft Flight Simulator 
--------------------------
Microsoft Flight Simulator cannot be run as a background 
application. When you are running Windows in standard or real 
modes, do not switch from Flight Simulator (ALT+TAB or ALT+ESC) 
to any other application.


Using MultiSoft PC-Kwik Disk Accelerator
----------------------------------------
If you use PC-Kwik with Windows running in 386 enhanced mode, 
make sure the version is 3.55 or later and that you use 
PC-Kwik in extended memory, not expanded memory.

If you need to upgrade your version of PC-Kwik, call MultiSoft 
at 1-800-888-KWIK in the United States. Outside the U.S., call
1-503-644-5644.


Professional Oracle
-------------------
You can run Oracle only in real mode, and without the 
HIMEM extended memory driver loaded. 


QModem 
------
If you have problems running QModem with Windows, create a 
program information file (PIF) for QModem that specifies a 
limit of 0 for EMS memory. Specifying 0 disables EMS for 
QModem, freeing that memory for use by Windows. 


Borland Reflex
--------------
If you have performance problems running Borland Reflex with 
Windows in 386 enhanced mode, include the following line in the 
[386Enh] section of your SYSTEM.INI file:
  
  VirtualHDIrq=FALSE


Microsoft Word
--------------
You might have problems using ALT+TAB with Microsoft Word 5.0 
and also using ALT+SPACEBAR to transfer data into Microsoft Word
5.0 from the Windows 3.0 Clipboard. If so, contact Microsoft 
Customer Service for an updated version of Microsoft Word 5.0. 
The updated version contains a keyboard driver that lets you use
ALT+TAB and ALT+SPACEBAR.


RUNNING SPECIFIC WINDOWS APPLICATIONS
=====================================

This section describes some problems you might have running 
some Windows applications.


Control Panel 
-------------
If you are running Windows 3.0 in real mode and using expanded 
memory, a new desktop wallpaper selection will not take effect 
immediately. You must quit and then restart Windows to see the 
new selection.


Print Manager and Network Printers
----------------------------------
The availability of several features in Print Manager depends 
on the support provided by your Network software. The 
NETWORKS.TXT on-line document contains important information 
about the networks you can use with Windows and which features 
are available in Print Manager for each network type. See 
NETWORKS.TXT for more information.


Using Terminal from the OS/2 DOS Compatibility Box
--------------------------------------------------
If you want Terminal to communicate through COM ports from the 
OS/2 DOS compatibility box, you must set the port before you 
start Windows. To do so, you can run the SETCOM command from 
the DOS prompt or you can include the initialization in your 
CONFIG.SYS file.

To set the COM port from the DOS prompt, type the following 
before you start Windows:

  SETCOM40 COMx=ON

For example, if you want to use COM1, you would type the 
following command:

  SETCOM40 COM1=ON

To set the COM port automatically, you can add a line in your 
CONFIG.SYS file. See your OS/2 documentation for instructions.


Paintbrush
----------
You can print color images from Paintbrush only if you are 
using a color PostScript printer or an HP PaintJet printer. 
These are the only printers that currently recognize Device 
Independent Bitmaps (DIBs), the color file format Paintbrush 
uses.

In addition, when running Windows in real mode, you might 
receive out-of-memory messages when you try to print. If so, 
try one of the following:

  *  Close all other applications and try printing again.

  *  Save the Paintbrush file and exit Windows. Start Windows 
     again in standard mode or 386 enhanced mode, and then print
     the Paintbrush file.

  *  If you can run only in real mode, you can convert the color
     image and save it to a black and white format, then open 
     the converted file, and print the monochrome bitmap.


GENERAL NOTES ABOUT APPLICATIONS
================================

This section includes important information about other problems
you might encounter running applications with Windows 3.0.


Running non-Windows Applications
--------------------------------
If you have problems with your display when you try to run two 
non-Windows applications and Windows in 386 enhanced mode, add 
the following line to the [386Enh] section of your SYSTEM.INI
file:

  local=EGA$


Increasing Your Display's Update Speed
--------------------------------------
If a non-windows application running in 386 enhanced mode 
Windows seems to be updating the display very slowly, try 
creating or modifying the application's program information 
file (PIF).

Check the application's PIF file to make sure none of the 
Monitor Ports check boxes are selected in the Advanced Settings
dialog box. On some displays, canceling the Monitor Ports 
options might mean that you cannot switch back to the 
application after switching away. In this case, you must exit 
the first application before starting another.

See "Specifying Advanced PIF Options for 386 Enhanced Mode" in 
Chapter 12, "More About Applications" in the Windows User's 
Guide for information on PIFs and the Monitor Ports options.


Using COM Ports for Communications
----------------------------------
If you are running a non-Windows application that uses COM 
ports for communications, you might lose characters or receive 
protection violations. If so, include the following setting in 
your SYSTEM.INI file:

  COMxProtocol=XOFF

    where x is the number for the COM port

For information on this switch and instructions on changing 
SYSTEM.INI settings, see the on-line document, SYSINI2.TXT.


Running Windows 2.x and Windows 3.0
-----------------------------------
  *  If you have both versions of Windows on your hard disk, 
     make sure that the directory containing Windows 3.0 is 
     included in the PATH command in your AUTOEXEC.BAT, not the 
     directory for Windows 2.x.

  *  Because Windows searches the current directory before it 
     searches other directories in the PATH command, when you 
     want to run an application, print, install a printer, or 
     install any other drivers in Windows 3.0, make sure the 
     Windows 2.x directory is not the current directory.

  *  If you want to run Windows versions 2.x and 3.0 on the same
     computer at different times, make sure that your CONFIG.SYS
     file includes the Windows 3.0 HIMEM.SYS driver. 

  *  If you use SMARTDrive or RAMDrive with Windows/386 2.x, 
     make sure the drivers are 2.x drivers. The Windows 3.0 
     drivers for SMARTDrive and RAMDrive will not work with 
     Windows/386 2.x.


Omit the APPEND, JOIN, and SUBST MS-DOS Utilities
-------------------------------------------------
The MS-DOS utilities APPEND, JOIN, and SUBST can cause problems
when you are running Windows 3.0. If you included APPEND, JOIN, 
or SUBST in your AUTOEXEC.BAT file, remove them and refrain from 
running them within Windows.


Running Batch Files and Embedded Macros
---------------------------------------
If you want to run a batch file with a Windows application that 
uses embedded macro language, do so from a PIF. If you will
be running it with Windows in 386 enhanced more, make sure that 
the Background check box in the batch file's PIF is not selected.
That way the batch file will run exclusively, causing the 
Windows application to pause until processing is complete. To 
learn about creating PIFs, see Chapter 12, "More About 
Applications," in the Windows User's Guide.


Using SHARE.EXE with Windows
----------------------------
To prevent two applications from modifying the same file, run 
the MS-DOS utility, SHARE.EXE, before you start Windows. It will 
not work correctly if you run it from within Windows. See your 
MS-DOS documentation for details about what SHARE.EXE does and 
how to install it.


Preventing Stack Overflow 
-------------------------
Stacks are temporary data structures that MS-DOS and applications
use for processing hardware events. If you receive the Internal
Stack Overflow message when you are running Windows in 386 
enhanced mode, you need to change your stacks= setting.

  *  If your system uses MS-DOS 3.2, include the following line 
     in your CONFIG.SYS file:

       stacks=9,192

  *  If your system uses MS-DOS 3.3 or above, include the 
     following line in your CONFIG.SYS file:

       stacks=0,0


Selecting a Port for a Serial Mouse
-----------------------------------
Do not try to run your serial mouse from a COM3 or COM4 port. 
Windows supports serial mice on COM1 and COM2 only.


Running Windows from the OS/2 version 1.2 DOS Compatibility Box
---------------------------------------------------------------
  *  Do not allow Windows Setup to make changes to your 
     AUTOEXEC.BAT file or CONFIG.SYS file. Make the appropriate
     changes yourself.

  *  To print, you must set the printer driver port to one with 
     an .OS2 extension as follows:

     If your printer is physically connected to LPT1 or to LPT2,
     when you configure your printer, make sure you set the 
     printer-driver port to LPT1.OS2 or LPT2.OS2.

     If the printer is physically connected to LPT3 or LPT4, you
     must create a line for LPT3.OS2 or LPT4.OS2 in the [ports] 
     section of your WIN.INI file and then set the printer 
     driver to the appropriate .OS2 port when you configure it.

     For more information about WIN.INI settings, see the 
     on-line document called WININI.TXT.


Running Applications that Require Expanded Memory
-------------------------------------------------
If you have an 80386 system and use applications that require 
expanded memory, you can use EMM386.SYS, the expanded memory 
emulator that comes with Windows 3.0. See Chapter 13, 
"Optimizing Windows," in the Windows User's Guide for 
information on using EMM386.SYS.


Setting the D= Switch for EMM386
--------------------------------
If you install EMM386, before you can start Windows in 386
enhanced mode, you must include the following setting on your 
EMM386 command line:

  d=48


GENERAL NOTES ABOUT HARDWARE
============================

More than 16 megabytes (MB) of RAM
----------------------------------
If your computer has over 16MB of RAM, you must run the 
HIMEM.SYS that you received with Windows 3.0, not other XMS 
drivers.


Adaptec Controller Boards
-------------------------
If you are using an Adaptec controller board, you might need to
turn off double-buffering in SMARTDrive. You can do this by 
adding the /B- switch at the end of the SMARTDrive device line 
in your CONFIG.SYS file.

The following is an example of such an entry:

  device=c:\windows\smartdrv.sys 1024 512 /B-


The All ChargeCard with a 3Com Network
---------------------------------------
If you have problems running the All ChargeCard in standard mode
with a 3Com network, remove ALLEMM4.SYS from your CONFIG.SYS file. 

Alternately, you can keep ALLEMM4.SYS and start Windows in real 
mode. To start in real mode, type WIN /r at the DOS prompt and 
press ENTER.


Apricot Computers
-----------------

  *  If you are running Windows in 386 enhanced mode on Apricot 
     DOS 3.3, you must install a console device driver such as 
     the ANSI.SYS driver you received with MS-DOS.

Adding an entry like the following to your CONFIG.SYS file will 
suffice:

  device=c:\DOS\ANSI.SYS

Failing to do so might cause CTRL+BREAK keystrokes to terminate 
the wrong application.


  *  If you want to run Windows in 386 enhanced mode, you need 
     to install special drivers.  You can obtain these from your
     Apricot distributor.


AST Rampage Boards
------------------
You need to upgrade your AST RAMTYPE.SYS driver if both the 
following conditions are true:

  *  You have an IBM PS/2 or micro-channel architecture computer.
  *  Your board is configured for expanded and extended memory.

RAMTYPE drivers before version 1.20 will not coexist with other
applications that use extended memory. This makes them 
incompatible with the HIMEM.SYS, which is required by Windows 
3.0.

The Windows Setup procedure removes RAMTYPE.SYS from your
CONFIG.SYS file. This might cause error messages to appear when
you start your computer, as other drivers that rely on RAMTYPE
cannot load. This also means that no application can use the 
expanded memory on your system. However, with RAMTYPE.SYS 
removed, Windows 3.0 runs correctly.

If you have a version of RAMTYPE newer than 1.20, or if you 
upgrade to a newer version, you can include the RAMTYPE command 
line in your CONFIG.SYS file. If you are installing an upgrade, 
you can simply copy this entry from CONFIG.OLD made by Setup 
when you installed Windows.


AT&T 386 computers with Phoenix ROM BIOS 
----------------------------------------
If your AT&T 386 computer has a Phoenix ROM BIOS version 
1.10.14 or earlier, you might be unable to run a non-Windows 
application in a window. (To determine whether your computer
uses a Phoenix ROM BIOS and which version, reboot and check 
the top line on your screen.)
    
To correct the problem, complete the following steps:

  1.  Reboot with the AT&T Customer Test disk you received 
      with your computer.

  2.  Choose the Setup Utility.

  3.  Make sure these two settings are disabled:
	Redirect to Com1
        Redirect to Com2

  4.  Follow the instructions to exit and save your changes.


CD-ROM Extensions
-----------------
If you are using CD-ROM Extensions, include the following entry 
in the [386Enh] section of your SYSTEM.INI file:

  device=LANMAN10.386

You also need to activate the drive by sending it a command 
before you start Windows. For example, type the following at 
the DOS prompt and then start Windows:

  dir x:

  where x is the drive letter for the CD ROM drive.


Epson Screen Savers
-------------------
Some Epson computers have screen-saver utilities that clear the 
screen after a specified period of inactivity. With Windows 3.0,
the screen saver might detect that the system is idle when it is
not. Windows will function properly even though the screen is 
blank, but nothing will be displayed until you exit Windows and 
start up again.

See the documentation that you received with your Epson computer 
for instructions about disabling the screen saver.


Everex 386/25 and EMM386.SYS
----------------------------
If you are using an Everex 386/25 with EMM386.SYS, include the 
following parameters in your CONFIG.SYS file:

  device=EMM386.SYS C600-C7FF


Hitachi Amdek Drives 
--------------------
These drives do not work reliably with Windows 3.0. To resolve 
this problem access the drive before you start Windows by typing 
the following at the DOS prompt:

  dir x:

  where x: is the drive letter for the Amdek drive


IBM Expanded Memory 
-------------------
If you want your 286-based PS/2 computer configured to use 
expanded memory, you must add the following line to your 
CONFIG.SYS file:

  device=XMA2EMS.SYS

When you ran Setup to install Windows and chose to let Windows
modify your CONFIG.SYS, this line was removed. Check the backup,
CONFIG.OLD for the exact entry you must add.

See your "IBM DOS Command Reference" for further information on
using XMA2EMS.SYS.


Logitech Bus Mouse
------------------
If you have a Logitech bus mouse on your computer, Setup will 
identify it as a Microsoft or PS/2 mouse. This is correct. 
The Logitech bus mouse is compatible with the Microsoft mouse 
driver.

The Logitech serial mouse uses its own driver.


LCD displays
------------
If you use an LCD display, set it for white text on a black 
background instead of black on white. When you are using Windows,
black on white is hard on LCD displays. See the documentation 
that came with your display for instructions on changing it.


NCR 925 and EMM386.SYS
----------------------
If you are using an NCR 925 with EMM386.SYS, include the 
following parameters in your CONFIG.SYS file:

  device=EMM386.SYS E000-EFFF


Plus Hardcard
-------------
To run Windows 3.0 with a Hardcard you must include the 
following line in your SYSTEM.INI file in the [386Enh] section:

  VirtualHDIRQ=off

See the on-line document SYSINI3.TXT for information about the 
procedure.

It is also a good idea to use SMARTDrive with a Hardcard. See 
Chapter 13, "Optimizing Windows," in the Windows User's Guide 
for more information on using SMARTDrive.


SCSI Hard Disk Drive using DMA
------------------------------
If your computer has an SCSI hard disk that uses DMA, you must 
include the following entry in the [386Enh] section of your 
SYSTEM.INI file:  

  VirtualHDIRQ=FALSE 

In addition, you must have SmartDrive installed and you must NOT
disable double-buffering by using the /B- option.


Columbia Data Products  SCSI
----------------------------
To use the Columbia Data Products SCSI hard disk controller with
Windows 3.0 in 386 enhanced mode, you must update the Columbia 
Data Products SCSI software to version 3.35 or higher.


Tandy 2500 XL with ROM DOS
---------------------------
The Tandy 2500 XL can be configured to use ROM DOS. If you want 
to use this feature, after you run Windows Setup, you must run 
the Tandy setup program (SETUPXL). Modify your configuration
so that your AUTOEXEC.BAT and CONFIG.SYS files are read from 
drive C.


Toshiba Plasma Display
----------------------
Toshiba VGA-compatible plasma displays have built-in protection
against overheating. This protection causes the screen to dim 
whenever more than half of the screen is brightly lit. If this 
makes your display difficult to use with Windows, change your 
display colors by using the VCHAD program provided with your 
Toshiba hardware. 

To change the plasma display colors you'll need to copy special 
files to your Windows directory, modify the Windows desktop 
colors, and create a special batch file for starting Windows. 
The procedures are outlined in the following steps.


--Copying the Files--

  1.  Copy VCHAD.EXE into your Windows directory.
      (The VCHAD program should be on the Toshiba Diagnostics 
      and Supplemental Disk you received with the DOS disks for 
      your Toshiba. If not, request it from Toshiba at 
      1-800-999-4CSD in the United States. Outside the U.S.,
      contact your local Toshiba office.)

  2.  Copy TOSHWIN.VCD from Windows 3.0 Disk #2 into your Windows 
      directory.


--Modifying the Windows Desktop Colors--

  1.  Start Windows and from Control Panel, choose the Color icon.

  2.  Open the Color Scheme drop-down list box and select 
      Fluorescent.

  3.  Choose the Color Palette button.

  4.  Make the following color changes to Screen Elements:

	Screen Element		Color
	---------------------------------------------------
	Window Background	fifth column, fifth color
	Window Text 		bottom right color (white)
	Application Workspace 	last column, second color

     See Chapter 5, "Control Panel," in the Windows User's Guide
     for more information on changing desktop colors.

  5.  Choose the Save Scheme button and choose OK to save your 
      changes.

  6.  Choose OK to close Control Panel.


--Creating the Batch File--

  1.  Using Windows Notepad (or another text editor), create the
      following batch file and save it in your Windows directory
      as WINPLSMA.BAT.

        VCHAD /R:TOSHWIN.VCD
        WIN
        VCHAD /C:1

      For information about using Notepad, see Chapter 10, 
      "Additional Accessories," in the Windows User's Guide.
  
  2.  Exit Windows and start it again using WINPLSMA.BAT.


Wyse Computers
--------------
If you are using a Wyse computer to run Windows, you might need 
to modify the device=HIMEM.SYS line in your CONFIG.SYS file to
read:

  device=[path]HIMEM.SYS  /M:WYSE


Using VGA Display Adapters 
--------------------------
  *  If you use a VGA-compatible display adapter and have 
     difficulties running Windows in 386 enhanced mode, you 
     might need to include the following line in the [386Enh] 
     section of your SYSTEM.INI file:

       EMMEXCLUDE=C400-C7FF

     This is because some VGA compatible cards use additional 
     memory to enhance the performance of their cards. 
     Manufacturers of these cards include Video 7 and Paradise. 
     Display adapter boards with the main chip(s) manufactured 
     by Tseng Labs, Chips and Technologies, Paradise, and 
     Headland Technologies also function this way.
  
     When Windows is running in 386 enhanced mode and is 
     configured for VGA, Windows detects most of these cards
     and automatically excludes the additional memory. However, 
     you must add the line to SYSTEM.INI yourself if:

       - You have both an 8514 and a VGA display adapter and
         configured Windows for the 8514.

       - You have an enhanced VGA adapter that Windows does
         not recognize.

     See the SYSINI2.TXT on-line document for the procedure.

  *  If you have both a VGA display adapter (primary) and an 
     8514 (secondary), you might have problems switching between  
     full-screen non-Windows applications when running Windows 
     in 386 enhanced mode.

     If an application does not display properly, the digital 
     to analog converter (DAC) on your VGA card needs to be 
     updated. Contact the manufacturer for an upgrade. 
 
     In the meantime, if your application has a command to 
     refresh the screen, you might be able to temporarily 
     correct the display so you can use the application. For 
     example, if your display is a color display, you can type 
     the following at the DOS Prompt and press ENTER: 
 
       MODE CO80 
 
     See your application's documentation for information about 
     commands that refresh the screen. 


Using Self-Configuring Display Adapters
---------------------------------------
Some display adapters can change their configurations to match
what an application tries to do. For example, if an application 
tries to use a VGA display, the adapter could switch from an EGA 
configuration to VGA. This type of display adapter makes use of
non-maskable interrupts (NMIs) to reconfigure itself as you work.

To use this type of display adapter with Windows running in 
386 enhanced mode, you must disable the NMI (self-configuring)
option. First configure the display adapter for the type of
monitor you have, then disable the NMI option. See your hardware 
documentation for further instructions.


OTHER ON-LINE DOCUMENTS
=======================

The following are other on-line documents that contain important
information not included in the Windows User's Guide or in 
on-line Help:  

3270.TXT	Information about using specific non-Windows
		3270 emulation applications.

NETWORKS.TXT    Information about running Windows with specific 
                network configurations.

PRINTERS.TXT    Information about particular printers and fonts 
     		that help you configure them to run in the 
    		Windows environment.

SYSINI.TXT      Procedures for modifying SYSTEM.INI settings 
SYSINI2.TXT     (for advanced users only).
SYSINI3.TXT

WININI.TXT      Procedures for modifying WIN.INI settings 
WININI2.TXT  	(for advanced users only).




