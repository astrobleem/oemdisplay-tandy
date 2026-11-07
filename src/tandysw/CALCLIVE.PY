#!/usr/bin/env python3
"""Preserve pinned live Output/text bounds; add only unsupported Output copy skip."""
from pathlib import Path
import importlib.machinery

HERE = Path(__file__).resolve().parent


def load(name):
    return importlib.machinery.SourceFileLoader('calclive_' + name, str(HERE / (name + '.PY'))).load_module()


def transform(source, mode):
    output, text, fast = load('OUTPUTBOUNDS'), load('TEXTBOUNDS'), load('CALCFAST')
    # Both stages require the full accepted profile source, not loose anchors.
    live = text.transform(output.transform(source, mode), mode)
    old, new, count = fast.CHANGES[0]
    old, new = (value.replace('\n', '\r\n').encode('latin1') for value in (old, new))
    if live.count(old) != count or new in live:
        raise ValueError('CALCLIVE: unsupported Output guard anchor differs')
    result = live.replace(old, new)
    if result.replace(new, old) != live:
        raise ValueError('CALCLIVE: change exceeds unsupported Output guard')
    return result


def port(renderer, mode, repo):
    renderer, repo = Path(renderer), Path(repo)
    load('CALCFAST').validate_dispatch(renderer, repo)
    path = renderer / 'EGA/TSOFT.ASM'
    result = transform(path.read_bytes(), mode)
    path.write_bytes(result)
