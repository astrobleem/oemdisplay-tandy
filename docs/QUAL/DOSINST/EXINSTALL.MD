# Expanded Windows XT installation

The consumer ZIP contains SETUP.EXE, README.TXT and the WINXT folder.
SETUP.EXE is an 83,142-byte DOS MZ with no appended archive. It reads real
files from the adjacent folder and never seeks the original ZIP. Existing
runtime, sound/client and full Setup transactions are retained.

The ordinary OEM descriptor uses the stock relative disk convention. The
full install metadata remains HPXY.INF; the portable OEMSETUP.INF is also
staged at the full install destination, so source files remain a usable OEM
disk when extracted elsewhere. Expanded-only output counts are 370 fresh
and 83 update. The qualified core remains 49 runtime inputs and 369/82
outputs; this delta adds one portable metadata file and an input alias.

Native update passed in 222.3 seconds, with preparation complete at 82.1.
All 83 outputs and installed runtime identities matched; boot/INI and the
unrelated KEEP.ME sentinel stayed unchanged. The guest had no ZIP or SFX.
The final capture shows a visible Windows GDI application window.

The negative replay passed in 49.1 seconds. A missing adjacent folder was
refused even with WINXT.ZIP beside the executable. Toggling byte100 of
TP.EXE preserved its length and was refused by CRC before output. Windows
stayed unchanged, SETUPXT was withheld and no incomplete output survived.
The first private attempt had invalid harness paths; its failed receipt is
preserved privately and is excluded from acceptance.

Ordinary stock Windows Setup passed in 130.0 seconds on DOS3.20, using the
same archive under C:\ALT\WINXT with canonical C:\WINXT absent. The custom
SETUP.EXE was never run and the descriptor was never rewritten. The normal
Windows driver-disk prompt was answered with that same source folder.
Exact HPXY, grabber and all three fonts were installed; generated WIN.COM
contained both logo components. Guarded Windows reached real-mode640x256,
ran15seconds and returned toDOS. Stock PROGMAN/sound and every expanded
source file stayed unchanged.

EXPAND.JSN binds raw receipts, logs, captures and all extracted identities.
The affected expanded FRESH replay passed in1,080.5seconds, with preparation
complete at950.6seconds. It ran from C:\EXTRACT, validated all284 Windows
streams and compared all370outputs, including the portable descriptor at
C:\WINXT. All60 extracted source members stayed unchanged. It reused the
qualified installed OS/cache and normal finisher/desktop handoff; unchanged
Windows Setup was not repeated. No new renderer qualification or physical
hardware claim is made. EXRUN1/2 and EXGOLD preserve actual controllers and
expected output identities; raw receipts name their exact controller hashes.
