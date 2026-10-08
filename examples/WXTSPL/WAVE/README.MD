# Default Windows XT startup: slow flag wave

The accepted default uses the original Windows XT flag geometry with steady
pane colors and lettering. Sixteen restrained phases take about 3.2 seconds;
a pending key skips to the rest frame. The flashing color-swap prototype is
retired. This is a pre-load animation, not concurrent loading.

The original raw module and wrapper are exact native-qualified 8086 bytes.
The wrapper restores text mode after loader failure, including the owned
loader's nonzero-kernel-status hide bypass. It cannot recover that swallowed
kernel status. No DOS/IRQ/timer hooks run inside the logo; 48 bytes remain for
relocated hide. Supported start: known Tandy signatures,624 KB, text mode 3/page 0 and
the exact existing RESERVE reservation. Other layouts refuse safely.

Prepare the independent default on a modern host using your own Windows 3.0:

```text
python MKSTART.PY --windows /path/to/owned/WINDOWS --out /new/private-addon
```

This reads the exact owned SYSTEM/WIN.CNF and creates a fresh PRIVATE add-on:
WINDOWS/XTTEST.COM,WINDOWS/XTCLEAN.COM,RESERVE.COM and START.BAT. It does not
change the source installation or WIN.COM. Use the add-on in an authorized
disposable/user-owned C:\WINDOWS clone. Do not redistribute the completed
private add-on, which contains owned loader bytes. On the DOS target use
START.BAT from that clone root. No Python is needed on the Tandy.

The 720 KB DOS installer now prepares this default from your exact owned
loader during the guarded installation. The normal `C:\WINXT\WINXT` launcher
uses the wave for qualified Color mode and static startup for other profiles.
See [installation and rollback](../../../tools/FLASHDISK/README.MD) and
[installer qualification](../../../docs/QUAL/WAVEINS.JSON). The independent
host builder remains available for separate private clones.

Native tests verified all 16 geometries and fixed RGB colors in 210 complete frames,
key skip, rest settling, relocated/repeated hide, reservation, missing kernel,
low memory, failed EXEC and nonzero-kernel-return cleanup. Actual 320x200 Windows
GUI execution and normal DOS return were verified independently. EXJOY/test
still fails two timing/polling assertions identically in the unchanged
baseline; those app diagnostics and physical hardware are not claimed PASS.

Sources are original implementation and first-party vector-derived raster
data. No Microsoft loader/kernel/font/compiler bytes are embedded in public
files. Reproduction uses an existing OpenWatcom host 8086 assembler/linker:
wasm -0 -zcm=masm XTLOGO.ASM; wlink format raw bin file XTLOGO.obj name XTLOGO.LGO.
Verify DEFAULT.JSON pins; changed executable bytes require requalification.
