BUILDING FLY SWAT
=================

Use your existing licensed Microsoft C 6 / Windows 3.0 SDK toolkit.
No compiler, import libraries, Windows files, or emulated guest is included.

From a host with Python 3 and your existing DOSBox-X installation:

python3 BUILD.PY --dosbox <dosbox-x> --repo <toolkit-root> --out <new-output>

The toolkit root must contain BIN/CL.EXE, BIN/LINK4.EXE, DDK/286/INC,
INCLUDE, LIB/SLIBCEW.LIB and LIB/LIBW.LIB. The build targets /G0 /Gw /AS.
It does not build or alter a display driver.

Native regression in a COPY of your already installed Windows guest:

python3 RUNLAB.PY --template <owned-guest-root> --exe <SWAT.EXE>
  --dosbox <dosbox-x> --out <new-run-output> --mode T

Keep this command on one line. For the slow approximate XT diagnostic use
--preset approx-xt --mode R --timeout 900. This preset is not calibrated
to physical 4.77 MHz hardware. It needs an existing TANDY88 installation.

Shared logic test, using a host GCC C compiler:
gcc -x c -std=c89 -Wall -Wextra -fsanitize=address,undefined TESTHOST.C -o swattest
ASAN_OPTIONS=detect_leaks=0 ./swattest

Scoped NE instruction audit requires GNU objdump and the matching MAP file:
python3 AUDIT.PY <output/SWAT.EXE>

All supplied DOS-facing text uses CRLF. Preserve 8.3 filenames.
