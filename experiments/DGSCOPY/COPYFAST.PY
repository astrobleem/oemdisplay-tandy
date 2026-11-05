"""Opt-in COPY span stage after the fixed-profile colored-COPY producer."""
from pathlib import Path
import argparse

HERE = Path(__file__).resolve().parent
PROFILES = {'colorplus32016': ('N32016', 160, 40),
            'yamaha160-b800': ('N16016', 80, 20)}
ANCHOR = b' first=(unsigned)l>>3;last=(unsigned)(r-1)>>3;\r\n'


def transform(raw, profile):
    name, stride, step = PROFILES[profile]
    block = ''' /* COPY outlines usually touch one byte per side. Compute its mask and
  * row offset once; retain the existing XOR and multi-byte paths below.
  * Reuse existing locals so this fast path adds no local stack storage. */
 if(!invert&&first==last){
  mask=(255U>>((unsigned)l&7U))&((255U<<(7U-((unsigned)(r-1)&7U)))&255U);
  offset=(unsigned)y*STRIDEU+first;
  for(plane=0;plane<4;plane++){
   value=c->shadow[offset];
   if(color&1)value=(unsigned char)(value|mask);
   else value=(unsigned char)(value&~mask);
   c->shadow[offset]=value;
   color>>=1;offset+=STEPU;
  }
  return;
 }
'''.replace('STRIDEU', str(stride)+'U').replace('STEPU', str(step)+'U')
    block = block.replace('\n', '\r\n').encode('ascii')
    expected = (HERE/name/'GENDRAW.C').read_bytes()
    if expected.count(block) != 1 or raw != expected.replace(block, b''):
        raise ValueError('Exact fixed-profile colored-COPY input required')
    if raw.count(ANCHOR) != 1:
        raise ValueError('Unique span anchor required')
    result = raw.replace(ANCHOR, ANCHOR+block)
    if result != expected:
        raise ValueError('Generated source differs from the tested candidate')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', choices=PROFILES, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = transform(a.source.read_bytes(), a.profile)
    with a.output.open('xb') as f:
        f.write(result)
    print('Generated exact tested source:', a.output)
