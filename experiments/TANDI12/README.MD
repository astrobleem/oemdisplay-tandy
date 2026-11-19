# Tandinator 0.3.9 source and expanded knowledge data

This is a separate development snapshot of the existing Win16 character-guessing
app. The preceding TANDI11 packet and installed defaults remain unchanged.

The roster grows from 256 to 384 characters and from 130 to 166 questions.
All 33,280 original answer cells are preserved. The new biographies combine
CC0 Wikidata structured facts with reviewed broad fame/geographic classifications.
Missing facts remain unknown; 41.16% of the final matrix is unknown.
Five profile pairs remain identical and require confirmation or rejection.
These cells are derived answers, not an equal number of independent facts.

The question budget no longer supplies confidence: too few or contradictory
clues end the round without a named guess. Supported cap offers with tied or
weak separation say TENTATIVE GUESS. Existing Ask Two, notebook, artwork and
sound behavior are retained. This remains roster-based character guessing.

## Rebuild the data offline

From `SOURCE` with Python 3:

```sh
python3 tools/EXPAND.PY
python3 tools/DBBUILD.PY data/STARTER.JSON ../RUN/TANDY.DAT
```

`BASE256.JSON` preserves the original roster. `BIOGRAPHIES.JSON` contains the
biographical input and separately reviewed fame/geography tags. No network is
needed. Do not use strict uniqueness: genuine profile ties are retained.

## Build the native app

Use your licensed complete Microsoft C6 / Win16 SDK toolchain as DOS drive C:
and `SOURCE/src` as drive D:. Run `BUILD.BAT`, which retains `/G0 /Gw /AS`
and LINK4. Place the resulting TANDI.EXE beside `RUN/TANDY.DAT` and ROSTER.TXT
in a separate folder. Start Windows through the existing guarded WindowsXT
launcher, then run the app normally. Keep older installations and notebooks;
notebooks for a different DAT are refused.

Only source, the roster and knowledge data are committed here. No executable,
private Windows guest, emulator, compiler, generated qualification evidence or
inherited checksum manifest is included. This snapshot does not modify a
release, download catalog, installer, workflow or launcher.

The inherited source notice is retained in `SOURCE/NOTICE.TXT`; its references
to original artwork and historical documentation refer to the preserved
[TANDI11 packet](../TANDI11/README.MD). It does not assign a new artwork license.
Wikidata structured data is [CC0](https://www.wikidata.org/wiki/Wikidata:Licensing).
The stored matrix and subjective fame classifications are not an independent
factual audit. No comparable Tiny-2.1 or physical-hardware result is claimed.
