TANDINATOR ORIGINAL STARTER DATABASE
===================================
128 characters, 128 broad questions, 16,384 explicit answer values.
22 real people and 106 fictional/legendary characters. Thirty entries are
female; generic Pikachu has unspecified sex. This is a deliberately small
starter roster, not an encyclopedic service and not a historical-1990 roster.
Modern characters are included even though the program targets old hardware.

FILES
-----
STARTER.JSON  Canonical, human-editable source. Edit this for normal changes.
MAKESEED.PY   Reproduces the original curation; NOT run by the normal compiler.
CURATION.JSON  Per-question counts and closest-profile quality diagnostics.
FORMAT.TXT   Exact disk format, limits, packing and validation contract.
SOURCES.TXT  Provenance, reference links, caveats and curation conventions.
../tools/DBBUILD.PY  Python 3, standard-library compiler and validator.
../tests/DBTEST.PY   Python 3, deterministic automated tests.
../build/TANDY.DAT   The playable compiled starter database.
../build/SCALE.DAT   Synthetic 2,000 x 256 structural test fixture only.

The JSON, Python and report files are host development files, not files the
8088 loads. DOS-facing TANDY.DAT and these .TXT documents have 8.3 names;
text documents use ASCII and CRLF. The binary has no line-ending convention.

BUILD ON THE HOST
-----------------
From the project root:
  python3 tools/DBBUILD.PY --strict-unique
  python3 tests/DBTEST.PY
  python3 tools/DBBUILD.PY --check build/TANDY.DAT

Optional explicit paths:
  python3 tools/DBBUILD.PY data/STARTER.JSON build/TANDY.DAT

The compiler writes build/DBREPORT.JSON. Tests write build/DBTEST.JSON and
reproduce build/SCALE.DAT plus build/SCALE.JSON. Do not ship SCALE.DAT as the
playable roster: its names and traits are deterministic random test values.
No third-party Python packages, proprietary data service, scraping account,
or runtime network access are required.

EDITING
-------
A question has a stable lowercase id and printable ASCII text <=79 bytes.
The compiler also enforces the compact UI: words <=26 characters and
questions fitting three 26-column lines.
A character has a stable lowercase id, printable ASCII name <=39 bytes,
notes, source-reference ids, and an answers object with EVERY question id.
Add a question by adding its answer to every character. Use 2 when unknown.
Add a character by supplying every existing answer target. Do not copy an
unrelated character's answers merely to make the input pass validation.

Answer values:
  0 NO; 1 PROBABLY NO; 2 UNKNOWN; 3 PROBABLY YES; 4 YES.

The compiler rejects duplicate ids, JSON keys, display names or question
texts, missing or unknown answer targets, values outside integer 0..4,
booleans used as answers, control characters, non-ASCII text and overlong
strings. Identical answer profiles are reported; --strict-unique rejects
them. No identical profiles or constant questions exist in this starter.

Profiles have a minimum distance of three answer positions. The closest
pairs include Sylvester/Tom, Tom/Jerry and Snoopy/Garfield. Some pairs have
only two strong NO-versus-YES distinctions. One or two wrong answers can
therefore legitimately favor a nearby character; rejection/continuation is
important. Profile uniqueness is not a guarantee of a correct first guess.

Question and character order define disk indices. Keep existing order stable
when updating an in-use source. Rebuild the whole database after edits.
Compiler validation does not prove factual truth: review modified traits and
rerun the engine's simulations as well as these binary tests.

READING POLICY
--------------
Questions concern broad appearance, role, medium of origin, abilities,
setting and relationships. There are no identity questions, name initials,
alphabetical partitions, hidden numeric labels or scraped Akinator records.
Answer for the familiar portrayal described in that character's notes.
Use UNKNOWN when a different adaptation, age, costume or interpretation
would change the answer. The source is intentionally open to correction.
