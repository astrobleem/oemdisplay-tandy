"""Opt-in 320x400 software desktop composition; fixed drivers stay unchanged."""
from pathlib import Path
import importlib.machinery

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    return importlib.machinery.SourceFileLoader(name, str(ROOT / path)).load_module()


def patch_staged(ega, adapter="pcjr"):
    """Compose adapter addressing before the existing XTPAN viewport clipping.

    All transformations are calculated before any file is written. No CRTC
    start-address programming is introduced: pan_set repaints the viewport.
    """
    if adapter not in ("pcjr", "colorplus"):
        raise ValueError("unsupported adapter: " + adapter)
    pan = load("sp_pan", "src/xtpan/PANPATCH.PY")
    jr = load("sp_jr", "src/pcjr/JRPATCH.PY")
    pcp = load("sp_pcp", "src/pcp/PCPPATCH.PY")
    pan.set_rows(400)
    ega = Path(ega)
    def tsoft(t):
        if adapter == "pcjr":
            return pan.patch_tsoft(jr.patch_v1(t, 4))
        t = pcp.patch_tsoft(t)
        # PANPATCH's row-retain anchor predates the ColorPlus presenter.
        # Normalize only this anchor, then restore the physical plane width.
        t = pan.replace_n(t, "    mov dx,80                 ; PCPPATCH: plane row bytes\n",
                          "    mov dx,160\n", 1, "ColorPlus retain anchor")
        t = pan.patch_tsoft(t)
        return pan.replace_n(t, "    mov dx,160\n", "    mov dx,80                 ; ColorPlus plane row\n",
                             1, "ColorPlus retain width")

    label = "JRPAN PCjr" if adapter == "pcjr" else "CPPAN ColorPlus"
    jobs = {
        ega / "TSOFT.ASM": tsoft,
        ega / "TCURSOR.ASM": lambda t: pan.patch_tcursor(jr.patch_tc(t) if adapter == "pcjr" else pcp.patch_tcursor(t)),
        ega.parent / "SDIB88.ASM": pan.patch_sdib,
        ega / "TSOFT.DEF": lambda t: pan.patch_def(t).replace(
            "XTPAN Tandy 320x400 panned 16-color (experimental)",
            label + " 320x400 software viewport (experimental)"),
    }
    done = {p: fn(p.read_bytes().decode("latin1")) for p, fn in jobs.items()}
    p = ega / "TSOFT.ASM"
    # The reusable XTPAN patch initializes static pan_top only once. Reset on
    # each actual enable and disable, including return from a DOS task.
    for old in ("    mov enabled_flag,1\r\n", "    mov enabled_flag,0\r\n"):
        done[p] = pan.replace_n(done[p], old,
                               "    mov pan_top,0              ; SPPATCH: lifecycle reset\r\n" + old,
                               1, "lifecycle " + old.strip())
    for p, t in done.items():
        jr.check_text(t)
    for p, t in done.items():
        p.write_bytes(t.encode("latin1"))
    return {p.name: t for p, t in done.items()}
