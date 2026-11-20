"""Replay the exact recorded compact verifier; new UI candidates stay separate."""
from pathlib import Path as _Path
from importlib.machinery import SourceFileLoader as _Loader
_Loader('compact_immutable_replay',str(_Path(__file__).with_name('REPLAY.PY'))).load_module().bootstrap(globals())
