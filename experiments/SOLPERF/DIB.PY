"""Unroll fixed four-byte 4bpp DIB groups after the current HPXY overlay.

No pixel predicate, table, allocation, new stack local, or presentation edit.
Partial-byte and segment-boundary handlers retain their exact source.
"""
from pathlib import Path
import hashlib

EXPECTED = {
    "BMC_ETI.ASM": "ce959e6585ea09caabd75c1abd2c361de77d8c9bc59a0e7fa8645a0ee6e41dda",
    "BMC_ITE.ASM": "aa6a926e6757ae5fe44d9e85374fb2d3d2ba1a80907b89dcfc93b1e08178be96",
}


def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("DIB unroll anchor count: " + repr(old))
    return text.replace(old, new)


def import4(text):
    a = text.index("copy_e4i\tproc near\n")
    b = text.index("copy_e4i\tendp", a)
    part = text[a:b]
    part = once(part, "\tmov\ttemp_bit_count,4\t; Four source bytes per dest byte\n", "")
    part = once(part, "ce4i_next_byte:\n", "\t; Exactly four packed source bytes per planar byte.\n\trept 4\n")
    part = once(part, "\tdec\ttemp_bit_count\n\tjnz\tce4i_next_byte\n", "\tendm\n")
    part = once(part, "\tjnz\tce4i_next_dest_byte\n\tret\n",
                "\tjz\tce4i_finished\n\tjmp\tce4i_next_dest_byte\n"
                "ce4i_finished:\n\t; Preserve the original private-local postcondition.\n"
                "\tmov\ttemp_bit_count,0\n\tret\n")
    return text[:a] + part + text[b:]


def export4(text):
    a = text.index("copy_ie4\tproc near\n")
    b = text.index("copy_ie4\tendp", a)
    part = text[a:b]
    part = once(part, "\tmov\tah,4\t\t\t;Set # bytes to write\n", "")
    part = once(part, "cie4_next_dest_byte:\n", "\t; Exactly four packed destination bytes per planar byte.\n\trept 4\n")
    part = once(part, "\tdec\tah\n\tjnz\tcie4_next_dest_byte\n", "\tendm\n")
    part = once(part, "\tjnz\tcie4_next_byte\n\tpop\tbp\n\tret\n",
                "\tjz\tcie4_finished\n\tjmp\tcie4_next_byte\n"
                "cie4_finished:\n\t; AH was the old four-byte counter and returned zero.\n"
                "\tmov\tah,0\n\tpop\tbp\n\tret\n")
    return text[:a] + part + text[b:]


def patch(renderer):
    changed = {}
    for name, transform in (("BMC_ETI.ASM", import4), ("BMC_ITE.ASM", export4)):
        p = Path(renderer) / name
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != EXPECTED[name]:
            raise RuntimeError("Unreviewed DIB input: " + name)
        text = raw.decode("latin1").replace("\r\n", "\n")
        changed[p] = transform(text).replace("\n", "\r\n").encode("latin1")
    for p, raw in changed.items():
        p.write_bytes(raw)
