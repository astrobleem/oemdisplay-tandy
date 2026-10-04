TSHELL07 DATE/TIME CORE HOST TESTS

Run: python3 examples/TSHELL/TESTS/DATE/RUN.PY from the repository root.
Requires GCC. Uses strict C89, -Wall -Wextra -Werror -pedantic, address and
undefined-behavior sanitizers. Leak inspection is disabled because this
workspace traces child processes; these tests perform no allocations.

Only DTCORE.C and the fake-clock test source are linked. TSDATE.C, DOS clock
setters, host clock setters and physical hardware are never called here.

Coverage: all day values 0..32 for every month in 1980..2099; all 86,400
valid 24-hour times; exact formatting; short, extra, separator, nondigit and
range failures; no-op Apply; validation before any I/O; date-only and time-
only writes after elapsed clock time; both fields; midnight/leap/year
rollover with a two-second readback allowance; failed first/second setter;
no silent rollback; failed and mismatching readback; invalid initial read.

Native UI/DOS behavior is a separate QA stage. Dialog control IDs:
110 date edit, 111 time edit, 112 Reload current, 113 Apply, 2 Cancel.
Caption: Date/time. Client size: 128x164. Success remains in the dialog.
Cancel is the initial/default focus; Enter in an edit cannot apply a change.
Partial or unverifiable changes require Reload before another Apply.
