#!/usr/bin/env python3
"""Check showcase text line endings required by AGENTS.md."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
FILES = ('README.md', 'docs/PROMO/SHOWCASE.MD', 'docs/PROMO/PBRUSH16.JSON')

def verify():
    for name in FILES:
        data = (ROOT / name).read_bytes()
        if b'\n' in data.replace(b'\r\n', b'') or b'\r' in data.replace(b'\r\n', b''):
            raise SystemExit('Non-CRLF line ending: ' + name)
        data.decode('utf-8')
    json.loads((ROOT / 'docs/PROMO/PBRUSH16.JSON').read_bytes())
    print('PASS showcase text: UTF-8, CRLF, valid capture metadata')

if __name__ == '__main__':
    verify()
