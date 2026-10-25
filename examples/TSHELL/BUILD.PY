"""Guarded native build; supply installed DOSBox-X, toolchain and shared lease."""
from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader

HERE = Path(__file__).resolve().parent
shared = (HERE / '../../tools/SOUNDOWN/BUILDAPP.PY').resolve()
spec = importlib.util.spec_from_file_location('consumer_build', shared,
    loader=SourceFileLoader('consumer_build', str(shared)))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.build(HERE, 'TSHELL', ('VFAT.C', 'VFAT.H', 'RAWREAD.C', 'RAWREAD.H', 'TSNAMES.C', 'TSNAMES.H', 'TSHELL.C', 'TSCP.C', 'TSCP.H', 'TSHOLD.C', 'TSHOLD.H', 'TSBOOT.C', 'TSBOOT.H', 'PSGOWN.H', 'TNOTICE.C', 'TNOTICE.H', 'PROGMENU.C', 'PROGMENU.H', 'GRPREAD.C', 'GRPREAD.H', 'TSAUX.C', 'TSAUX.H', 'TSSAVER.C', 'TSSAVER.H', 'TSSAVCFG.C', 'TSSAVCFG.H', 'TSSVOPT.C', 'TSSVOPT.H', 'SCFGCORE.C', 'SCFGCORE.H', 'SVCORE.C', 'SVCORE.H', 'TSDATE.C', 'TSDATE.H', 'DTCORE.C', 'DTCORE.H', 'TSHELL.DEF', 'TSHELL.RSP', 'BUILD.BAT'), (HERE / 'PSGOWN.H').resolve())
