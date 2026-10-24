"""Opt-in PR155 after current XR1; no accepted payload is replaced.

XR1 aliases FlushRetainRows to FlushRows rather than defining a separate
procedure. Settle held rows before viewport changes, DIB writes, disable,
memory Output, and rejected scanline gates as well as PR155's draw entries.
An abandoned begin remains pending until the next foreground driver call.
Interrupt cursor paths never copy shadow data or execute BatchClose.
"""
from pathlib import Path
import importlib.machinery

HERE = Path(__file__).resolve().parent


def patch(renderer):
    rr = importlib.machinery.SourceFileLoader(
        "xr155", str(HERE.parents[1] / "src/rrect/RRPATCH.PY")).load_module()
    p = renderer / "EGA/TSOFT.ASM"
    t = p.read_bytes().decode("latin1")
    t = rr.batch_after_candidate(t, "FlushRows endp\r\n")
    # A recognized screen marker deliberately cleared dirty. Bypass the
    # fallback test below so BEGIN does not immediately close its own batch.
    t = rr.replace_n(t,
        "TOutput_marker_off:\r\n    mov dirty,0\r\n    jmp TOutput_render\r\n",
        "TOutput_marker_off:\r\n    mov dirty,0\r\n    jmp TOutput_batch_ready\r\n",
        1, "XR recognized marker bypass")
    t = rr.replace_n(t, "BatchClose proc near\r\n",
                     "public BatchClose\r\n"
                     "BatchSettleFar proc far\r\n"
                     "    call BatchClose\r\n    retf\r\nBatchSettleFar endp\r\n"
                     "BatchClose proc near\r\n", 1, "XR batch export")
    # The gate saved all scratch registers/FLAGS. Settle before the renderer
    # for a memory target or any fill that failed conservative validation.
    t = rr.replace_n(t, "TOutput_render:\r\n", """TOutput_render:
    cmp dirty,0
    je TOutput_batch_settle
    cmp style,80
    je TOutput_batch_ready
    cmp style,81
    je TOutput_batch_ready
    cmp style,4
    jne TOutput_batch_settle
    cmp outrows,0
    jne TOutput_batch_ready
TOutput_batch_settle:
    call BatchClose
TOutput_batch_ready:
""".replace("\n", "\r\n"), 1, "XR rejected/memory Output settle")
    for entry, end in (("TControl", "DeviceBitmap"), ("TDisable", "TControl")):
        start = t.index("cProc " + entry + ",")
        stop = t.index("cProc " + end + ",", start)
        old = t[start:stop]
        # These entries live outside _TEXT, unlike the near drawing helpers.
        new = rr.replace_n(old, "cBegin\r\n", "cBegin\r\n    call BatchSettleFar\r\n", 1, entry + " settle")
        t = t[:start] + new + t[stop:]
    p.write_bytes(t.encode("latin1"))
    p = renderer / "SDIB88.ASM"
    t = p.read_bytes().decode("latin1")
    t = rr.replace_n(t, "externNP FlushShadow\r\n",
                     "externNP FlushShadow\r\nexternNP BatchClose\r\n", 1, "DIB batch import")
    t = rr.replace_n(t, "cBegin\r\n    cld\r\n", "cBegin\r\n    call BatchClose\r\n    cld\r\n", 1, "DIB settle")
    p.write_bytes(t.encode("latin1"))
