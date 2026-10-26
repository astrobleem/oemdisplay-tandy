"""Busy emulator refusal must precede every owned-image mutation."""
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch
import importlib.machinery,runpy,sys,tempfile,os

HERE=Path(__file__).resolve().parent
class Busy(Exception):pass
class Runner:
    def __init__(self,record):pass
    @contextmanager
    def lease(self):raise Busy('conflicting emulator');yield

with tempfile.TemporaryDirectory() as d:
    out=Path(d);(out/'CROOT').mkdir()
    image=out/'DISK.IMG';image.write_bytes(b'owned-image-must-not-change')
    stop=out/'STOP.NOW';stop.write_bytes(b'preserve')
    command=out/'CROOT/UITASK.TXT';command.write_bytes(b'preserve-input')
    original=importlib.machinery.SourceFileLoader.load_module
    def loader(self,*args):
        if self.name=='lease':return SimpleNamespace(Runner=Runner)
        return original(self,*args)
    for args in (['BUSY'],['--prepare']):
        with patch.object(importlib.machinery.SourceFileLoader,'load_module',loader),patch.object(sys,'argv',['RUNUI86.PY',*args,'--out',str(out)]):
            try:runpy.run_path(str(HERE/'RUNUI86.PY'),run_name='__main__')
            except Busy:pass
            else:raise AssertionError('busy runner did not refuse')
        assert image.read_bytes()==b'owned-image-must-not-change'
        assert stop.read_bytes()==b'preserve'
        assert command.read_bytes()==b'preserve-input'
        assert not (out/'DISK-PRE-COPY.IMG').exists()
print('PASS busy run and prepare leave the owned image and controls unchanged')

lease=importlib.machinery.SourceFileLoader('lease_config',str(HERE/'WINRUN.PY')).load_module()
with patch.dict(os.environ,{},clear=True):
    try:lease.Runner('unused-record.json')
    except RuntimeError as e:assert 'TANDY_EMULATOR_LOCK' in str(e)
    else:raise AssertionError('missing shared lease was accepted')
with tempfile.TemporaryDirectory() as d:
    lock=Path(d)/'existing-shared.lock';record=Path(d)/'record.json'
    with patch.dict(os.environ,{'TANDY_EMULATOR_LOCK':str(lock)}):
        assert lease.Runner(record).lock==lock
    assert not lock.exists() and not record.exists()
print('PASS explicit shared lease configuration never creates a replacement lock')
