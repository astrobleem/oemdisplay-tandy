#!/usr/bin/env python3
"""Audit the assembled RLE helper ABI in the MASM listing."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


_OPCODE_LINE = re.compile(r"^\s*([0-9A-F]{4})\s+([0-9A-F]{2})\b(.*)$", re.I)
def _label_re(label: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*[0-9A-F]{{4}}\s+{re.escape(label)}:\s*$", re.I)


def _instructions_after(lines: list[str], label: str, count: int) -> list[tuple[int, str]]:
    starts = [i for i, line in enumerate(lines) if _label_re(label).match(line)]
    if len(starts) != 1:
        raise AssertionError(f"expected one emitted {label} label, found {len(starts)}")
    found: list[tuple[int, str]] = []
    for line in lines[starts[0] + 1:]:
        match = _OPCODE_LINE.match(line)
        if match:
            found.append((int(match.group(2), 16), match.group(3).strip()))
            if len(found) == count:
                return found
    raise AssertionError(f"{label} has fewer than {count} emitted instructions")


def audit_source(source: str) -> dict[str, object]:
    """Check the intended near-return and byte-sized delta-state source."""
    normalized = source.lower()
    helper = re.search(
        r"rlesp_ok\s*:\s*clc\s*retn\s*rlesp_bad\s*:\s*stc\s*retn\b",
        normalized,
    )
    if not helper:
        raise AssertionError("both rle_store_pixel outcomes must explicitly use RETN")
    if not re.search(r"^\s*rsskip\s+equ\s+27\s*$", normalized, re.M):
        raise AssertionError("rsSkip must remain the byte at RLESTATE offset 27")
    if not re.search(r"^\s*rsdeltax\s+equ\s+28\s*$", normalized, re.M):
        raise AssertionError("rsDeltaX must remain the word at RLESTATE offset 28")
    pending = re.search(r"rlen_pending\s*:(.*?)rlen_apply_delta_x\s*:",
                        normalized, re.S)
    if not pending or not re.search(
            r"cmp\s+byte ptr\s+es:\[di\+rsskip\]\s*,\s*0\b", pending.group(1)):
        raise AssertionError("rlen_pending must test only the byte-sized rsSkip")
    if re.search(r"\bmov\s+ax\s*,\s*es:\[di\+rsskip\]", pending.group(1)):
        raise AssertionError("word read of rsSkip overlaps rsDeltaX")
    return {"near_helper_returns": 2, "delta_skip_width": 1}


def audit_listing(listing: str) -> dict[str, object]:
    """Require near CALL/RETN balance on both helper paths and far API returns."""
    lines = listing.splitlines()
    calls = []
    call_re = re.compile(
        r"^\s*([0-9A-F]{4})\s+E8\s+[0-9A-F]{4}(?:\s+R)?\s+.*"
        r"\bcall\s+rle_store_pixel\s*$", re.I)
    for line in lines:
        match = call_re.match(line)
        if match:
            calls.append(int(match.group(1), 16))
    if len(calls) != 4:
        raise AssertionError(f"expected four emitted near CALL rle_store_pixel sites, got {len(calls)}")

    success = _instructions_after(lines, "rlesp_ok", 2)
    failure = _instructions_after(lines, "rlesp_bad", 2)
    for name, emitted, flag_opcode in (("success", success, 0xF8),
                                        ("failure", failure, 0xF9)):
        if emitted[0][0] != flag_opcode or emitted[1][0] != 0xC3:
            raise AssertionError(
                f"{name} helper path must set its carry result and emit near RETN C3; "
                f"got {[f'{op:02X}' for op, _ in emitted]}"
            )
        # E8 near CALL pushes a two-byte IP; C3 near RETN pops that same word.
        call_push_bytes, return_pop_bytes = 2, 2
        if call_push_bytes != return_pop_bytes:
            raise AssertionError(f"{name} helper path is not stack-balanced")

    far_returns = {
        "RLEInit": re.compile(r"^\s*[0-9A-F]{4}\s+CA\s+0018\s+.*\bret\s+24\s*$", re.I),
        "RLENextRow": re.compile(r"^\s*[0-9A-F]{4}\s+CA\s+0008\s+.*\bret\s+8\s*$", re.I),
    }
    for name, pattern in far_returns.items():
        if sum(bool(pattern.match(line)) for line in lines) != 1:
            raise AssertionError(f"{name} must retain its far return and Pascal argument cleanup")

    delta_lines = [line for line in lines if re.search(
        r"\bcmp\s+byte ptr\s+es:\[di\+rsSkip\]\s*,\s*0\b", line, re.I)]
    if len(delta_lines) != 1 or not re.search(
            r"26:\s*80\s+7D\s+1B\s+00\b", delta_lines[0], re.I):
        raise AssertionError("listing must emit an ES-prefixed byte compare at RLESTATE offset 27")
    if any(re.search(r"\bmov\s+ax\s*,\s*es:\[di\+rsSkip\]", line, re.I)
           for line in lines):
        raise AssertionError("listing still contains the overlapping word read of rsSkip")
    return {
        "near_call_sites": [f"{site:04X}" for site in calls],
        "helper_success_opcode": "C3",
        "helper_failure_opcode": "C3",
        "helper_stack_delta_bytes": {"success": 0, "failure": 0},
        "far_cleanup": {"RLEInit": 24, "RLENextRow": 8},
        "delta_skip_compare": "byte [ES:DI+27]",
    }


def audit_files(listing_path: Path, source_path: Path) -> dict[str, object]:
    source = source_path.read_text(encoding="latin-1")
    listing = listing_path.read_text(encoding="latin-1", errors="replace")
    return {"source": audit_source(source), "listing": audit_listing(listing)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("listing", type=Path, help="fresh RLE88.LST from the native build")
    parser.add_argument("--source", type=Path, default=Path(__file__).with_name("RLE88.ASM"))
    args = parser.parse_args()
    print(json.dumps(audit_files(args.listing, args.source), indent=2))


if __name__ == "__main__":
    main()
