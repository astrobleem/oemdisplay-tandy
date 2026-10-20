# Windows XT first-party serial wheel driver R1

The replaced dependency is the private TPDRV03 build03 WHEEL.DRV, 4,641 bytes,
SHA256 `3ae7c27a08d25bd54178df60443c0bac905641c29080e2ed554d6969ab789a5d`.
Its retained TPDRV03 README describes a source-built extension of the user's
Microsoft Windows mouse DDK and explicitly asserts no redistribution license.
The staged derivative source retains Microsoft 1987-1989 copyrights. No terms
establishing public binary redistribution were found in that supplied kit.

This replacement has newly authored `driver.asm`, `decoder.asm` and `timestamp.asm`. It links
only those three newly assembled objects, with no DDK implementation, macro file,
Microsoft runtime object, SDK import library or copied driver binary. The
driver has no imports. Its source is offered under the accompanying MIT license.
The driver's scope is Windows 3.0 real mode, COM1 at 03F8h, IRQ4, 1200 baud,
7 data bits, no parity and one stop bit on original 8086/8088-class machines.
Other ports, protected mode and Windows 3.1 are not implemented.

This is not a clean-room claim. The integrating author inspected the supplied
Microsoft-DDK mouse interface declarations/comments and MOUSEINFO field layout,
callback register contract, export ordinals and the standard Win16 export
prologue listing to establish ABI facts. The author also read the first-party
TPDRV03 README's packet/API contract and existing first-party WXTWHL client
interfaces. Those reference implementations and proprietary headers are not
included in this driver source directory. Luna authored the decoder from the
stated interface/protocol facts without inspecting a DDK implementation.

The standard mouse exports are Inquire, Enable, Disable and MouseGetIntVect
(ordinals 1-4), plus WEP. MOUSEINFO is 14 bytes; callbacks receive status in AX,
relative signed X/Y in BX/CX and two buttons in DX. The private wheel API names
are WheelApiVersion (0100h), WheelReadDelta (destructive signed event queue)
and WheelLostPackets (saturating WORD), ordinals 10-12. The queue capacity is
31 events; newest events are dropped when full. Read APIs preserve caller
DS/BX/BP and lasting IF/DF; ordinary arithmetic flags are not promised.

The accepted serial contract is immediate three-byte Microsoft pointer/button
delivery and one optional fourth byte whose high three bits are clear. Its
signed low nibble represents -8..7 wheel units; bit 4 is ignored. This retains
ordinary three-byte mouse operation without waiting for a fourth byte. It is
the previously tested Genius/IntelliMouse-style contract, not a universal
serial/PS2/USB mouse claim. UART error samples abandon the partial packet.

Reference interface source available publicly:
https://github.com/stsp/win31-mouse-driver/blob/master/src/MOUSE.ASM
The reference is used for ABI facts, not incorporated code or licensing.
Existing emulator serial packet implementation reference:
https://github.com/joncampbell123/dosbox-x/blob/b13702c/src/hardware/serialport/serialmouse.cpp
Native qualification uses the already installed unchanged 86Box original 8088
core and UART loopback; no emulator patch or newly downloaded tool is required.

The combined own-media installer remains private. Its Windows media and CGA
grabber are Microsoft inputs; this driver license grants no rights to them or
to other separately derived display/keyboard components. A public mouse-only
source/runtime packet can exclude all such dependencies. Public combined
installer readiness requires its own explicit dependency/notices audit and
an owned-media preparation route.

## Timestamp extension

New first-party code adds parallel per-slot IRQ BIOS timestamps and ordinal 13 without changing the decoder. Its implementation and linked operands were independently reviewed. The earlier candidate DOS pass had a DOS/NE segment-resolution blind spot; TIMED-API1 failed and is retained. Explicit DS repair passed DOS2 and API2. Native driver API proof and the private bridge recovery proof are distinct. No additional proprietary implementation, header or library is linked into this driver.
