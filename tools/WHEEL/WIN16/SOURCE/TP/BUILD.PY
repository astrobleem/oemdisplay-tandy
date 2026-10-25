"""Guarded native build; supply installed DOSBox-X, toolchain and shared lease."""
from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader

HERE = Path(__file__).resolve().parent
shared = (HERE / '../../../../SOUNDOWN/BUILDAPP.PY').resolve()
spec = importlib.util.spec_from_file_location('consumer_build', shared,
    loader=SourceFileLoader('consumer_build', str(shared)))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.build(HERE, 'TP', ('BUILD.BAT', 'PSGOWN.H', 'ROLL.H', 'TP.C', 'TP.DEF', 'TP.RSP', 'TPSOUND.C', 'TPSOUND.H', 'WHEEL.H'), (HERE / 'PSGOWN.H').resolve())
