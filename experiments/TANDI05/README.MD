# Tandinator bounded question/trait audit (experimental)

Based on main c6ee4b0f20d9a3c5da4b4d2b22bdc65a762c853b, including UI04.
This is a standalone optional app trial. It does not modify the OEM disk,
accepted driver payloads, existing experiments, defaults, or BASE128 recovery.

## Scope

- Review all 130 question wordings; clarify 14.
- Make 32 source-backed/conservative answer changes across 14 profiles.
- Clarify eight version labels; no new characters or questions.
- Preserve all 13,115 pre-existing UNKNOWN cells.
- Preserve UI04 rendering, input, narrower buttons and moving eyes.

The principal correction separates a named film adaptation from the earlier
literary identity. Ahsoka and Catwoman debut-date mistakes are also corrected.
Every changed answer records its previous value, new value, reason and official
source. Named-version interpretations are distinguished from direct date facts.

## Honest outcome

Self-replay first guesses fall 235 to 233/256; eventual recovery stays 256/256.
Mixed-noise recovery falls 2881 to 2862/3072. Uncertain-soft and single-flip
recovery improve slightly. With the same corrected responses supplied to both
databases, recovery improves 251 to 256/256 and first guesses 224 to 233.
Most other answer values remain unverified, so this is not a factual accuracy
measurement. The unchanged 19-case independent sparse sample remains 15 eventual
and 4 first guesses. Pairs with no opposing known answers rise 200 to 215.

Source-backed corrections were not reversed or fabricated to optimize scores.
This pass does not qualify added-roster factual accuracy. No physical 8088 test
or human user study has been performed. Read AUDIT05.TXT and REVIEW05.JSON.

## Reproduce

Run `python3 TESTPUB.PY` to verify exact archived bytes and evidence pins.
Extract TANDI05.ZIP. For a fresh project-only captured-evidence workspace run:

    python3 TANDI05/SOURCE/tools/PREP05.PY --out /new/qa/path

Then run from that output:

    python3 tests/QTEST05.PY
    python3 tests/DBTEST.PY
    python3 tests/CURTEST.PY
    python3 tests/ARTTEST.PY --require-runtime --runtime-tag=-ui05
    python3 tests/UITEST.PY --runtime-tag=-ui05

Fresh emulator runs require the user's own Windows/compiler environment and
the shared emulator lock, as described in BUILDING.TXT. Captured evidence is
not a fresh emulator run. The ZIP excludes Windows, compiler, BIOS and emulator
binaries. Source and current/previous DAT files are included for replay.
