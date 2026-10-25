"""Complete native consumer packet, expansion, pin and archive checks."""
import importlib.machinery
import io
import json
import ntpath
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
publish = importlib.machinery.SourceFileLoader('xs_publish_tests', str(HERE / 'PUBLISH.PY')).load_module()

class PackageTests(unittest.TestCase):
    def test_exact_native_runtime_and_grabber(self):
        entries = publish.collect()
        self.assertEqual(len([n for n in entries if n.startswith('PAYLOAD/')]), 14)
        grabber = entries['PAYLOAD/CGA.GR2']
        self.assertEqual(publish.pub.identity(grabber), {'bytes': 2104, 'sha256': '1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067'})
        self.assertEqual(publish.pub.identity(entries['PAYLOAD/XRSYNC.DRV']), publish.DRIVER)
        self.assertFalse(any(n.endswith('.PY') for n in entries))

    def test_supplied_szdd_and_corruption(self):
        data = (publish.REPO / 'distributions/WINXT/CGA.GR2').read_bytes()
        body = b''.join(bytes([(1 << len(data[i:i+8])) - 1]) + data[i:i+8] for i in range(0,len(data),8))
        raw = b'SZDD\x88\xf0\x27\x33A\x00' + len(data).to_bytes(4,'little') + body
        self.assertEqual(len(data), 2104)
        self.assertEqual(raw[:8], b'SZDD\x88\xf0\x27\x33')
        self.assertEqual(publish.media.expanded_file(raw, 'CGA.GR2'), publish.collect()['PAYLOAD/CGA.GR2'])
        for bad in (raw[:13], raw[:-1], raw + b'extra'):
            with self.assertRaises(ValueError):
                publish.media.expanded_file(bad, 'CGA.GR2')

    def test_public_zip_closed_deterministic(self):
        entries = publish.collect()
        first = publish.pub.zip_bytes(entries)
        self.assertEqual(first, publish.pub.zip_bytes(entries))
        publish.pub.check_zip(first, entries, 'test')
        with zipfile.ZipFile(io.BytesIO(first)) as z:
            self.assertEqual(set(z.namelist()), set(entries))
            self.assertIn('PAYLOAD/CGA.GR2', z.namelist())
            self.assertNotIn('PAYLOAD/RUNSYNC.BAT', z.namelist())

    def test_mz_overlay_and_native_crc_contract(self):
        import zlib
        entries = publish.collect()
        helper = entries['XSETUP.EXE']
        size = publish.mz_size(helper)
        data = helper + publish.pub.zip_bytes(entries)
        self.assertEqual(data[size:size+4], b'PK\x03\x04')
        header = (HERE.parent / 'DOSINST/XSPINS.H').read_text()
        rows = re.findall(r'{"([^"\n]+)","([0-9a-f]{64})",(\d+)UL,0,0x([0-9a-f]+)UL}', header)
        self.assertEqual(len(rows), 10)
        for name, sha, length, crc in rows:
            body = entries['PAYLOAD/' + name]
            self.assertEqual(len(body), int(length))
            self.assertEqual(publish.pub.digest(body), sha)
            self.assertEqual(zlib.crc32(body), int(crc, 16))

    def test_oem_paths_and_bundled_selections(self):
        text = (HERE / 'PAYLOAD/OEMSETUP.INF').read_text()
        disk = next(line for line in text.splitlines() if line.startswith('a = '))
        location = disk.split('=', 1)[1].split(',', 1)[0].strip()
        for windows in ('C:\\WINDOWS', 'D:\\WIN30', 'C:\\OS\\WIN30'):
            self.assertEqual(ntpath.normpath(ntpath.join(windows, location)), 'C:\\XR155')
        entries = publish.collect()
        for name in ('CGA.GR2', 'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON', 'XTSTATIC.LGO', 'WXTSPL01.RLE'):
            self.assertIn(name, text)
            self.assertIn('PAYLOAD/' + name, entries)

    def test_native_evidence_hashes(self):
        directory = publish.REPO / 'docs/QUAL/DOSINST'
        for report in ('XSPACE.JSN', 'XRSYNC.JSN'):
            receipt = json.loads((directory / report).read_bytes())
            for name, pin in receipt['evidence'].items():
                self.assertEqual(publish.pub.identity((directory / name).read_bytes()), pin, name)

    def test_release_qualification_and_readback(self):
        # Requires the actual tested final packet receipt; no synthetic approval.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'release'
            commit = '092700f59067824e7c8b30e70979ff735816d841'
            publish.build(target, commit)
            publish.build(target, commit)
            with (target / 'XRSYNC.ZIP').open('ab') as f:
                f.write(b'tamper')
            with self.assertRaises(ValueError):
                publish.build(target, commit)

if __name__ == '__main__':
    unittest.main()
