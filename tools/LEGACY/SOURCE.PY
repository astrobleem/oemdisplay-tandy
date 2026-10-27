"""Read exact superseded sources for historical acceptance; never changes pins."""
from pathlib import Path
import hashlib,zipfile,io
ARCHIVE_SHA = '0455f35979ecfdd9ffb3ea12a0e9508478303cda38e96d7ef8f741d48cddaf53'
NAMES = ('src/panui/HOSTUI.PY', 'src/panui/PANDLG.C', 'src/panui/VERIFY.PY', 'src/pcp/CPVERIFY.PY', 'src/softpan/BLDTEST.BAT', 'src/softpan/BUILDAPP.PY', 'src/softpan/PANCFG.C', 'src/softpan/PANCFG.DEF', 'src/softpan/PANCFG.RSP', 'src/xtpan/XTPAN.C', 'src/xtpan/XTPAN.DEF', 'src/xtpan/XTPAN.RSP', 'tools/CURRENT/BUNDLE.PY', 'tools/SPPACK/PACKAGE.PY')

def source(name,data,pin,normalize=False):
    def identity(b):
        if normalize:b=b.replace(b'\r\n',b'\n')
        return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    if identity(data)==pin:return data
    if name not in NAMES:return data
    raw=(Path(__file__).parent/'SOURCES.ZIP').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ARCHIVE_SHA:raise ValueError('Changed historical source snapshot')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=len(NAMES) or set(z.namelist())!=set(NAMES):raise ValueError('Historical source inventory differs')
        old=z.read(name)
    if identity(old)!=pin:raise ValueError('Historical source pin differs: '+name)
    return old
