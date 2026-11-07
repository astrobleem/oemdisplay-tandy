"""Add optional fixed display choices without changing the installed default."""
import re
ROWS = (
 ('fixed6404','TNDY6404.DRV','Tandy EX/HX 640x200 4 colors (red/green/white)'),
 ('fixed3204','TNDY3204.DRV','Tandy EX/HX 320x200 4 colors (cyan/magenta/white)'),
 ('fixed160','TNDY160.DRV','Tandy EX/HX 160x200 16 colors (no panning)'),
 ('fixed6402','TNDY6402.DRV','Tandy EX/HX 640x200 monochrome (no panning)'),
)
def transform(data):
    if b'\n' in data.replace(b'\r\n',b''):
        raise ValueError('Expected CRLF Setup metadata')
    text=data.decode('latin1')
    matches=list(re.finditer(r'(?im)^\[display\]\r\n(.*?)(?=^\[|\Z)',text,re.S))
    if len(matches)!=1:raise ValueError('Expected one display section')
    section=matches[0].group(1)
    if len(re.findall(r'(?im)^fixed\s*=\s*a:TANDY88\.DRV,',section))!=1:
        raise ValueError('Expected retained fixed320 choice')
    hp=list(re.finditer(r'(?im)^hpxy\s*=\s*a:HPXY\.DRV,[^\r]*\r\n',section))
    if len(hp)!=1:raise ValueError('Expected retained HPXY choice')
    for name in ('XTCSYS.FON','XTCFIX.FON','XTCOEM.FON','TANDYGR.GR2','XTSTATIC.LGO','WXTSPL01.RLE'):
        if name.lower() not in text.lower():raise ValueError('Missing existing support: '+name)
    if any(driver.lower() in text.lower() for _,driver,_ in ROWS):
        raise ValueError('Optional display already present')
    added=''.join('%s = a:%s, "%s", "200,96,48", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\r\n'%row for row in ROWS)
    offset=matches[0].start(1)+hp[0].start()
    result=text[:offset]+added+text[offset:]
    assert result.replace(added,'',1)==text
    return result.encode('latin1')
