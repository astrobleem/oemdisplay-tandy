#!/usr/bin/env python3
"""Pure checkers shared by the PCjr install tests (no emulator, no I/O).

JRSESS.PY, JRCONV.PY and JRGRTEST.PY call these on what the guest wrote;
TESTPACK.PY feeds them good and deliberately bad inputs. Each returns
(ok, detail) so a failure says why.
"""
import struct

GUARD_OK_OWNED = b"JRGUARD: OK, video page is held by a DOS system block.\r\n"
GUARD_REFUSED = (b"JRGUARD: video page 18000h-1FFFFh is not reserved by DOS.\r\n"
                 b"         Load a PCjr memory driver that reserves it, see PCJR.MD.\r\n")
JRWIN_REFUSED = b"JRWIN: guard refused/failed. Windows not started.\r\n"


def rc_lines(text):
    """{label: rc} from C:\\JRLOG.TXT lines 'LABEL RC=n' (n 0-4, or '5+')."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if " RC=" in line:
            label, rc = line.split(" RC=", 1)
            if label in out:
                out[label] = "duplicate"
            else:
                out[label] = rc
    return out


def guard_passed(output, rc):
    """JRGUARD's own OK text for a DOS-owned page, and exit code 0."""
    ok = output == GUARD_OK_OWNED and rc == "0"
    return ok, {"output": output.decode("latin-1"), "rc": rc}


def guard_refused_launch(output, rc):
    """The refused-launch case passes only when JRWIN's whole output is
    JRGUARD's 'not reserved' refusal followed by JRWIN's 'guard refused'
    line, and the exit code is exactly 1 (JRGUARD's refusal code, passed
    on by JRWIN). A missing WIN.COM, an EXEC error, a different refusal
    reason, silence or any other code is not this case."""
    ok = output == GUARD_REFUSED + JRWIN_REFUSED and rc == "1"
    return ok, {"output": output.decode("latin-1"), "rc": rc}


def inf_display_entries(text):
    """Every entry in OEMSETUP.INF's [display] section, whatever its key."""
    entries, sec = [], None
    for raw in text.split("\r\n"):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1].strip().lower()
            continue
        if sec == "display":
            entries.append(line)
    return entries


def szdd_expand(data):
    """Microsoft COMPRESS 'SZDD' (LZSS, 4 KB window) expansion."""
    if data[:8] != b"SZDD\x88\xf0\x27\x33" or data[8:9] != b"A":
        raise ValueError("not an SZDD file")
    size = struct.unpack_from("<I", data, 10)[0]
    window = bytearray(b" " * 4096)
    pos, i, out = 4096 - 16, 14, bytearray()
    while i < len(data) and len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(8):
            if i >= len(data) or len(out) >= size:
                break
            if flags & (1 << bit):
                b = data[i]
                i += 1
                out.append(b)
                window[pos] = b
                pos = (pos + 1) & 4095
            else:
                if i + 1 >= len(data):
                    break
                lo, hi = data[i], data[i + 1]
                i += 2
                src, n = lo | ((hi & 0xF0) << 4), (hi & 0x0F) + 3
                for k in range(n):
                    b = window[(src + k) & 4095]
                    out.append(b)
                    window[pos] = b
                    pos = (pos + 1) & 4095
    if len(out) != size:
        raise ValueError("SZDD data ends early")
    return bytes(out)


def win_com_static_logo(win_com, win_cnf_installed, win_cnf_media, lgo, rle):
    """WIN.COM must be exactly the media's WIN.CNF (expanded) followed by
    the packet's XTSTATIC.LGO and WXTSPL01.RLE, and the installed
    SYSTEM\\WIN.CNF must be that same expanded file."""
    try:
        cnf = szdd_expand(win_cnf_media) if win_cnf_media[:4] == b"SZDD" else win_cnf_media
    except ValueError as e:
        return False, {"error": str(e)}
    detail = {"win_com_bytes": len(win_com), "cnf_bytes": len(cnf), "lgo_bytes": len(lgo),
              "rle_bytes": len(rle), "installed_cnf_equals_media": win_cnf_installed == cnf,
              "win_com_equals_cnf_lgo_rle": win_com == cnf + lgo + rle}
    return detail["installed_cnf_equals_media"] and detail["win_com_equals_cnf_lgo_rle"], detail
