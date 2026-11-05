"""Build either qualified fixed-profile COPY driver completely from source.

Uses explicit external native DDK/C6 tools, canonical 8086 backend staging,
and the integrated generic-ellipse/profile sources. The reference closure is
read only for qualification checks, never a source of project object inputs.
Writes fresh developer outputs; accepted driver and product pins are unchanged.
"""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]


def main():
    producer = ROOT/'experiments/DGSCOPY/FULL.PY'
    runpy.run_path(str(producer))['main']()


if __name__ == '__main__':
    main()
