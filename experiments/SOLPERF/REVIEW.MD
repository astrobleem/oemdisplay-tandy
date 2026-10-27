# Source and evidence review

The emitted MASM listing uses only 8086/8088 instructions. All four unsigned
predicates accept exactly 00h/FFh. The checks touch AL/flags only; the original
mixed converter resets AL, and the outer save frame restores flags/registers.
The uniform path reuses the original nibble macro, writes exactly four repeated
bytes, and rejoins the original wrap/row/stage logic. It adds no far calls,
segment assumptions, cursor handler, pending-flush state or allocation.

The independent native pixel oracle validates the bank mapping, shadow bands,
real cursor AND/XOR composition and saved-under recovery. Both 41-frame suites,
144 extra pixel assertions and all canonical-shadow equality checks pass. Source
review found no correctness defect within this tested scope.

The performance finding prevents a release recommendation: 3.0% faster Solitaire
in one matched pair, but 12.0% slower late mixed-plane checkerboard batch. The
candidate stays opt-in and does not change frozen runtime/package pins. A
separate reviewer has not signed off. No physical-machine qualification is
claimed. Initial oracle calibration errors and live FAT warnings are preserved
and explained in README.MD and the private native receipts.

## DIB-only follow-on review

DIB.PY pins both input modules and changes only copy_e4i/copy_ie4 full-group
routines. The repeated bodies match the originals exactly. The import helper
still reads four source bytes and produces one byte in each DDB plane per
group; export still reads one byte per plane and writes four packed bytes.
No AH value is consumed by the export body. Its original AH=0 return value is
restored explicitly. Import restores temp_bit_count=0. The final outer DEC
retains the original zero/condition state, while MOV does not change flags.
The near JMP after the inverted short JZ is valid on 8086 and avoids branch
range expansion. Emitted MASM listings confirm both encodings. Neither helper
changes its stack frame, linkage, color table, pointer progression, partial
handler, segment dispatch or callback behavior. Presentation source hash is
identical to the release; the earlier SOLID predicate is absent.

The independent pixel oracle passed both 41-frame suites. The native DIB
checks passed partial/full groups, palette permutations, RLE4, source and
destination 64KB crossing, and 32 guard bytes. The huge alias points exactly
65520 bytes into a 66048-byte allocation and normalizes the far pointer;
payload plus guard is bounded by the allocation tail. DDB selection is
restored before GetDIBits. Both suites returned normally with 0 failures.
All three brush batches matched between drivers, including both checkerboards.

This source/listing review and independent oracle support the tested 4bpp
scope; a separate reviewer has not signed off. Other DIB formats retain their
source but were not newly exercised here. Native packaging/installer and
physical-machine qualification remain open. DIBRES.JSN records the separate
matched startup result and exact evidence. No accepted driver was replaced.
