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
