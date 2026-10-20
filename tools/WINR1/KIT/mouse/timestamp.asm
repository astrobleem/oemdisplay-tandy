; SPDX-License-Identifier: MIT
; Newly authored parallel BIOS-tick ring for the first-party wheel candidate.
.8086
.model small
DGROUP GROUP _BSS
_BSS SEGMENT WORD PUBLIC 'BSS'
PUBLIC timestamp_table, timestamp_oldhead
timestamp_table   db 128 dup (?) ; 32 little-endian DWORD BIOS tick stamps
timestamp_oldhead db ?          ; single IRQ4 producer scratch byte
_BSS ENDS
END
