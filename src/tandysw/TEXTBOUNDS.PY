"""Synchronous fixed-profile text columns over each exact Output bounds stage."""
from pathlib import Path
import hashlib


EXPECTED = {
    '160x200x16': '71a51923b59b271e6dc578310da479b45bdaad84ba093801443e52ed902075e5',
    '320x200x16': 'b2b2f9e97c05e798da0d817f6b71dca9d13d4d9b15577f0d0ab4d6f817f63bb0',
    '640x200x4': '9fc359b921a669b5e7a79c516c80d8d6eea9e516999bb02f6d5f9d64d22eeb52',
    '320x200x4': '336f6576239239327afee5d48812e76a712820295f7bd739fbd3113f1da5d238',
    '640x200x2': '11bb2d84ea9b51b8691dc256726ae4f065a374fea77355c930a4fce4976d985e',
}
# Keep the original single-profile API constant for existing callers.
SOURCE_SHA256 = EXPECTED["640x200x4"]


def _dos(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


OLD_HEADER = _dos("""; Snapshot only final row endpoints before the unchanged renderer call.
; dirty=0 means no flush, 1 full flush, and 2 proven full-width row interval.
; The last three macro arguments are explicit even for ordinary StrBlt.
""")

NEW_HEADER = _dos("""; Snapshot final row endpoints and the original clip's byte columns.
; dirty=0 means no flush, 1 full flush, and 2 proven bounded presentation.
; All original text gates and renderer calls remain unchanged.
; The last three macro arguments are explicit even for ordinary StrBlt.
""")

OLD_CLIP = _dos("""    text_rectangle clip,restore
    ; Prove signed y+h cannot overflow and is wholly on screen.
""")

NEW_CLIP = _dos("""    text_rectangle clip,restore
    ; TEXTCOL: get_clip confines glyphs and any opaque fill to this RECT.
    ; Capture X now, before an optional opaque RECT replaces ES:DI.
    ; Round outward to complete logical bytes; empty clips remain safe.
    mov ax,es:[di].left
    shr ax,1
    shr ax,1
    shr ax,1
    mov colfirst,ax
    mov ax,es:[di].right
    add ax,7
    shr ax,1
    shr ax,1
    shr ax,1
    mov collast,ax
    ; Prove signed y+h cannot overflow and is wholly on screen.
""")

OLD_LOCALS = _dos("""    localW rowfirst
    localW rowlast
cBegin
""")

NEW_LOCALS = _dos("""    localW rowfirst
    localW rowlast
    localW colfirst
    localW collast
cBegin
""")

OLD_FLUSH = _dos("""text_flush macro
local full,done
    push ax
    push bx
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    call FlushRows
    jmp short done
 full:
    call FlushShadow
 done:
    pop bx
    pop ax
endm
""")

NEW_FLUSH = _dos("""text_flush macro
local full,done
    push ax
    push bx
    push cx
    push dx
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    mov cx,colfirst
    mov dx,collast
    call FlushRetainColumns
    jmp short done
 full:
    call FlushShadow
 done:
    pop dx
    pop cx
    pop bx
    pop ax
endm
""")

REPLACEMENTS = (
    (OLD_HEADER, NEW_HEADER, 1),
    (OLD_CLIP, NEW_CLIP, 1),
    (OLD_LOCALS, NEW_LOCALS, 2),
    (OLD_FLUSH, NEW_FLUSH, 1),
)


def _require_crlf(source):
    if b"\n" in source.replace(b"\r\n", b"") or b"\r" in source.replace(b"\r\n", b""):
        raise ValueError("DOS source must retain exact CRLF line endings")


def transform(source, mode="640x200x4"):
    """Return staged bytes; reject every source except the accepted column stage."""
    _require_crlf(source)
    if mode not in EXPECTED or hashlib.sha256(source).hexdigest() != EXPECTED[mode]:
        raise ValueError("Text bounds require the exact Output column stage for " + mode)
    text = source.decode("latin1")
    for old, new, count in REPLACEMENTS:
        if text.count(old) != count or new in text:
            raise ValueError("Text bounds anchor mismatch: " + old.splitlines()[0])
        text = text.replace(old, new)
    result = text.encode("latin1")
    _require_crlf(result)
    return result


def port(renderer, mode):
    """Opt in only exact fixed profiles. Native/runtime qualification is separate."""
    if mode not in EXPECTED:
        return {"changed": False, "mode": mode}
    path = Path(renderer) / "EGA" / "TSOFT.ASM"
    source = path.read_bytes()
    result = transform(source, mode)
    path.write_bytes(result)
    return {
        "changed": True,
        "mode": mode,
        "added_data_bytes": 0,
        "extra_local_stack_bytes": 4,
        "extra_flush_save_bytes": 4,
    }


def selftest(source, mode="640x200x4"):
    """Read-only host checks. These do not replace native or framebuffer tests."""
    candidate = transform(source, mode)
    width = int(mode.split("x")[0])
    text = candidate.decode("latin1")
    # An exact inverse verifies that helpers, renderer calls, every validation
    # gate, and the entire non-text driver body remain byte-for-byte unchanged.
    for old, new, count in reversed(REPLACEMENTS):
        assert text.count(new) == count
        text = text.replace(new, old)
    assert text.encode("latin1") == source
    assert candidate.count(b"    localW colfirst\r\n") == 2
    assert candidate.count(b"    localW collast\r\n") == 2
    before = candidate.index(b"    text_rectangle clip,restore\r\n")
    snapshot = candidate.index(b"    mov colfirst,ax\r\n")
    after = candidate.index(b"    text_rectangle optr,restore\r\n")
    assert before < snapshot < after

    # All ordered in-screen clip intervals, including empty intervals and both
    # screen edges. Ceiling-right cannot overflow a 16-bit word (max 647).
    intervals = 0
    for left in range(width + 1):
        for right in range(left, width + 1):
            first = left >> 3
            last = (right + 7) >> 3
            assert 0 <= first <= last <= width // 8
            assert first * 8 <= left <= right <= last * 8
            if left < right:
                assert first <= (left >> 3) <= ((right - 1) >> 3) < last
            intervals += 1
    assert intervals == (width + 1) * (width + 2) // 2

    # The full source pin prevents partial, duplicate, and wrong-profile ports.
    for bad in (candidate, source + b"; changed\r\n", source.replace(b"\r\n", b"\n")):
        try:
            transform(bad, mode)
        except ValueError:
            pass
        else:
            raise AssertionError("An invalid source was accepted")
    assert port(Path("__must_not_be_opened__"), "unsupported") == {
        "changed": False, "mode": "unsupported"
    }
    return {
        "source_bytes": len(source),
        "candidate_bytes": len(candidate),
        "clip_intervals_checked": intervals,
        "exact_inverse": True,
        "bad_sources_rejected": 3,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Exact staged Output-bounded TSOFT.ASM")
    parser.add_argument("--mode", default="640x200x4", choices=tuple(EXPECTED))
    args = parser.parse_args()
    print("TEXTBOUNDS_HOST_CHECKS", selftest(args.source.read_bytes(), args.mode))
