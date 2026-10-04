#!/usr/bin/env python3
"""Audit multiline display-copy literals in BRIGHT.C, using Python stdlib only.

ENGINE.C copy and labels are audited against actual compiled strings by the C89
oracle. This supplementary check avoids needing Windows headers to read the UI.
"""
import json
from pathlib import Path
import re
import sys

source = Path(__file__).resolve().parents[1] / "BRIGHT.C"
text = source.read_text()
tokens = re.compile(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
issues = 0
bodies = 0
for token in tokens.finditer(text):
    raw = token.group()
    if not raw.startswith('"'):
        continue
    value = json.loads(raw)
    if "\n" not in value:
        continue
    bodies += 1
    source_line = text.count("\n", 0, token.start()) + 1
    lines = value.split("\n")
    if len(lines) > 4:
        print(f"OVERFLOW BRIGHT.C:{source_line}: {len(lines)} lines (limit 4)")
        issues += 1
    for index, line in enumerate(lines, 1):
        if len(line) > 18:
            print(f"OVERFLOW BRIGHT.C:{source_line} body line {index}: "
                  f"{len(line)} columns: {line}")
            issues += 1
print(f"{'FAIL' if issues else 'PASS'} UI copy audit: {bodies} multiline bodies, "
      f"{issues} violation(s) of 18-column/four-line bound")
sys.exit(1 if issues else 0)
