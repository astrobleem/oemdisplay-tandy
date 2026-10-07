#!/usr/bin/env python3
"""Host-only private WINXT staging. No Python is needed on the DOS target.
SZDD expansion follows the existing distribution STAGE.PY. Fixed-cell font
resource transplant follows experiments/TEXTMODE/FIXFONT.PY; no font bytes
are embedded or redistributed here.
"""
from pathlib import Path
import argparse,csv,hashlib,re,struct
class DiskError(Exception):pass
SUPPORT_HASHES = {'CGA.GR2': '1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067', 'CGALOGO.LGO': 'd9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807', 'CGAFIX.FON': 'b0c043a65e2b551bce3c77d25921394dfd2533f50633bc129abd240c7aeb5f89', 'CGAOEM.FON': '1a86d9e42c73ccefcbc82c822abe8dbcd61cf0116454f213c3a95f4d7436cd0d', 'CGASYS.FON': 'baf8fa607806d949dfb6992113ce93494678abdef07783b22222b62e5de28ef4', 'EGAFIX.FON': '6df45a74e5756dd0746bcee593be9ac4df4a35458c26bf4570b748def2d394cb', 'EGAOEM.FON': '05bd6ef11802bbca20473b0e409116fd8919c5bbcbbbc26b7ee2ea1f33ad23be', 'EGASYS.FON': '8bd307d7886d0f2fdfc1de3da8253e294233d1c757fd9131a66405fca5825b09'}

SPLASH_NAME = 'WXTSPL01.RLE'
SPLASH_SHA = 'eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c'
SPLASH_BYTES = 4062
DERIVED_HASH='b7353ceca94cce0c7cad568ebafa26f8fa5fa855be551a24e3502161415a0807'
def expanded_file(data, name):
    """Decode bounded SZDD mode-A files from Windows 3.0 media, when needed."""
    signature = b"SZDD\x88\xf0\x27\x33"
    if not data.startswith(signature):
        if not data or len(data) > 1024 * 1024:
            raise DiskError(name + ": empty or oversized Windows support file")
        return data
    if len(data) < 14 or data[8] != ord("A"):
        raise DiskError(name + ": unsupported or truncated SZDD header")
    expected = struct.unpack_from("<I", data, 10)[0]
    if not 1 <= expected <= 1024 * 1024:
        raise DiskError(name + ": invalid expanded size (limit 1 MiB)")
    ring = bytearray(b" " * 4096)
    cursor, pos = 4096 - 16, 14
    result = bytearray()
    while len(result) < expected:
        if pos >= len(data):
            raise DiskError(name + ": truncated SZDD flags")
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(result) == expected:
                break
            if flags & (1 << bit):
                if pos >= len(data):
                    raise DiskError(name + ": truncated SZDD literal")
                chunk = bytes((data[pos],))
                pos += 1
                result.extend(chunk)
                ring[cursor] = chunk[0]
                cursor = (cursor + 1) & 4095
            else:
                if pos + 2 > len(data):
                    raise DiskError(name + ": truncated SZDD reference")
                offset = data[pos] | ((data[pos + 1] & 0xf0) << 4)
                length = (data[pos + 1] & 0x0f) + 3
                pos += 2
                if len(result) + length > expected:
                    raise DiskError(name + ": SZDD reference exceeds declared size")
                for index in range(length):
                    value = ring[(offset + index) & 4095]
                    result.append(value)
                    ring[cursor] = value
                    cursor = (cursor + 1) & 4095
    if pos != len(data):
        raise DiskError(name + ": unexpected data after SZDD stream")
    return bytes(result)



def resources(data):
 ne=struct.unpack_from('<I',data,60)[0];p=ne+struct.unpack_from('<H',data,ne+36)[0];shift=struct.unpack_from('<H',data,p)[0];p+=2;out={}
 while True:
  typ,n=struct.unpack_from('<HH',data,p);p+=8
  if typ==0:break
  for i in range(n):
   off,length,flags,rid=struct.unpack_from('<HHHH',data,p);out[(typ,rid)]=(p,off<<shift,length<<shift,shift);p+=12
 return out

def digest(b):return hashlib.sha256(b).hexdigest()
def textfont(data):
 a=bytearray(data['CGASYS.FON']);b=data['CGAFIX.FON'];ar,br=resources(a),resources(b)
 for key in [(0x8007,0x8001),(0x8008,0x801b)]:
  ent,off,size,shift=ar[key];_,boff,bsize,_=br[key]
  if bsize>size:raise DiskError('Fixed-cell font resource does not fit')
  a[off:off+size]=b[boff:boff+bsize]+bytes(size-bsize)
 if digest(a)!=DERIVED_HASH:raise DiskError('Unexpected derived fixed-cell font')
 return bytes(a)

def verify_default_splash(payload):
    """Current installs have one approved XT image, never a splash menu."""
    art = payload.get(SPLASH_NAME, b'')
    if len(art) != SPLASH_BYTES or hashlib.sha256(art).hexdigest() != SPLASH_SHA:
        raise DiskError('Current default requires the approved Windows XT splash')
    section = ''; profiles = set()
    try:
        for line in payload['OEMSETUP.INF'].decode('ascii').splitlines():
            line = line.strip()
            if not line or line.startswith(';'): continue
            if line.startswith('['): section = line.lower(); continue
            if section != '[display]': continue
            name, separator, value = line.partition('=')
            name = name.strip().upper()
            row = next(csv.reader([value], skipinitialspace=True, strict=True))
            if not separator or name in profiles or len(row) != 9 or row[8].strip().upper() != 'A:' + SPLASH_NAME:
                raise DiskError('Every current Setup profile must select Windows XT')
            profiles.add(name)
    except (KeyError, UnicodeError, csv.Error, StopIteration) as error:
        raise DiskError('Invalid Windows XT splash selection: ' + str(error))
    if profiles != {'TR53216', 'TR56404', 'TR51616', 'TR53204', 'TR56402', 'TXTMODE'}:
        raise DiskError('Expected all six current Windows XT display profiles')

def stage(support,out):
 root=Path(__file__).resolve().parent
 if out.exists():raise DiskError('Output exists; choose a fresh directory')
 manifest={}
 for line in (root/'MANIFEST.SHA').read_text('ascii').splitlines():
  h,n=line.split()
  if not re.fullmatch(r'[0-9a-f]{64}',h) or not re.fullmatch(r'[A-Z0-9_]{1,8}\.[A-Z0-9_]{1,3}',n) or n in manifest:raise DiskError('Bad manifest')
  manifest[n]=h
 required=set(SUPPORT_HASHES)|{'TXTSYS.FON','TR53216.DRV','TR56404.DRV','TR51616.DRV','TR53204.DRV','TR56402.DRV','TXTMODE.DRV','INSTALL.BAT','TINST.EXE','OEMSETUP.INF','RESERVE.COM','TSSETUP.BAT','TSTART.BAT','SHELLSEL.EXE','TSCHECK.EXE','TSHELL.EXE','TSHELL.INI','TSINPUT.DLL',SPLASH_NAME}
 if not required<=set(manifest):raise DiskError('Incomplete runtime manifest')
 data={}
 for n,h in SUPPORT_HASHES.items():
  matches=[p for p in support.iterdir() if p.name.upper() in (n,n[:-1]+'_')]
  if len(matches)!=1:raise DiskError('Missing or ambiguous support file: '+n)
  p=matches[0]
  if p.is_symlink() or not p.is_file() or p.stat().st_size>1024*1024:raise DiskError('Invalid support file: '+n)
  b=expanded_file(p.read_bytes(),n)
  if digest(b)!=h:raise DiskError('Unverified Windows support: '+n)
  data[n]=b
 data['TXTSYS.FON']=textfont(data)
 for n,h in manifest.items():
  if n not in data:
   p=root/n
   if p.is_symlink() or not p.is_file() or p.stat().st_size>1024*1024:raise DiskError('Invalid runtime file: '+n)
   data[n]=p.read_bytes()
  if digest(data[n])!=h:raise DiskError('Payload hash mismatch: '+n)
 verify_default_splash(data)
 data['MANIFEST.SHA']=(root/'MANIFEST.SHA').read_bytes()
 out.mkdir(parents=False)
 for n,b in data.items():
  with (out/n).open('xb') as f:f.write(b)
 print('Complete own-media DOS source:',out)
 print('Copy this single folder to C:\\WINXT, then run INSTALL at DOS.')
 print('Experimental text remains opt-in and has known character corruption.')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--windows-files',type=Path,required=True,help='Folder with eight original Windows 3.0 support files, expanded or SZDD');a.add_argument('--out',type=Path,required=True,help='Fresh output folder, usually WINXT');v=a.parse_args()
 try:stage(v.windows_files,v.out)
 except (DiskError,OSError,ValueError,KeyError,struct.error) as e:a.exit(1,'Refused: '+str(e)+'\n')
