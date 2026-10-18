from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path


EVIDENCE = Path(__file__).with_name("evidence")
RAW_FILES = {"W16API.LOG", "WINRET.TXT"}
SMOKE_PATTERNS = (
    r"(?m)^VM GetVersion import=PASS calls=1 steps=3 stack=8\r?$",
    r"(?m)^GetVersion DWORD=0x06160003\r?$",
    r"(?m)^VM wrong-cookie result=0 stack=1 steps=10\r?$",
    r"(?m)^RESULT=PASS\r?$",
)
FAR_PATTERNS = (
    r"(?m)^VM far GetVersion CALL=PASS calls=1 steps=3 far_calls=1 retf=1 retf_bytes=0 return=1000:0005 stack=1\r?$",
    r"(?m)^GetVersion DWORD=0x06160003\r?$",
    r"(?m)^VM far wrong-cookie result=0 stack=1 retf=1 bytes=6 return=1000:0005\r?$",
    r"(?m)^VM unknown far import fail-closed=PASS\r?$",
    r"(?m)^EnumWindows all-pass result=1 callbacks=3 cookie_ok=1 probe_seen=1\r?$",
    r"(?m)^EnumWindows stop result=0 callbacks=1\r?$",
    r"(?m)^VM callbacks=4 failures=0 getversion_calls=1 far_getversion_calls=1\r?$",
    r"(?m)^RESULT=PASS\r?$",
)


def validate_record(
    directory: Path,
    patterns: tuple[str, ...],
    *,
    tested_source: Path | None = None,
) -> tuple[str, ...]:
    errors: list[str] = []
    manifest_path = directory / "MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return (f"manifest unavailable or invalid: {exc}",)

    for key in ("source_commit", "private_exe_sha256"):
        value = manifest.get(key)
        length = 40 if key == "source_commit" else 64
        if not isinstance(value, str) or re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
            errors.append(f"invalid {key}")

    for key in (
        "log_absent_before_run",
        "fresh_guest_log",
        "shared_lease_acquired_and_released",
        "owned_emulator_stopped",
        "private_clone_only",
    ):
        if manifest.get(key) is not True:
            errors.append(f"manifest does not confirm {key}")
    for key in (
        "private_media_or_executable_included",
        "physical_hardware_tested",
        "display_driver_qualified",
        "generic_ne_import_bridge_claimed",
    ):
        if manifest.get(key) is not False:
            errors.append(f"manifest must explicitly set {key}=false")

    normalized_source_hash = manifest.get("source_file_sha256_lf_normalized")
    if normalized_source_hash is not None and tested_source is not None:
        source = tested_source.read_bytes()
        source = source.replace(b"\r\n", b"\n")
        if normalized_source_hash != hashlib.sha256(source).hexdigest():
            errors.append("source file no longer matches the tested run record")

    file_records = manifest.get("files")
    if not isinstance(file_records, dict) or set(file_records) != RAW_FILES:
        errors.append("manifest must hash exactly W16API.LOG and WINRET.TXT")
        file_records = file_records if isinstance(file_records, dict) else {}

    decoded: dict[str, str] = {}
    for name in RAW_FILES:
        path = directory / name
        try:
            data = path.read_bytes()
        except OSError:
            errors.append(f"missing raw evidence file {name}")
            continue
        record = file_records.get(name)
        if not isinstance(record, dict):
            errors.append(f"missing hash record for {name}")
        else:
            if record.get("bytes") != len(data):
                errors.append(f"byte count mismatch for {name}")
            digest = hashlib.sha256(data).hexdigest()
            if record.get("sha256") != digest:
                errors.append(f"SHA-256 mismatch for {name}")
        if b"\n" not in data or not data.endswith(b"\r\n"):
            errors.append(f"{name} is not a CRLF text record")
        try:
            decoded[name] = data.decode("ascii")
        except UnicodeDecodeError:
            errors.append(f"{name} is not sanitized ASCII text")

    log = decoded.get("W16API.LOG", "")
    if log and ("C:\\" in log or "\\Users\\" in log):
        errors.append("raw log contains a local host path")
    if log.count("RESULT=PASS") != 1 or "RESULT=FAIL" in log:
        errors.append("raw log has a missing/duplicate PASS or a FAIL record")
    for pattern in patterns:
        if re.search(pattern, log) is None:
            errors.append(f"raw log missing expected record: {pattern}")

    if directory.name.startswith("farcall-"):
        callback_rows = re.findall(
            r"(?m)^VM guest callback result=([01]) stack=([01]) steps=[0-9]+ far_calls=([0-9]+) retf=([0-9]+) retf_bytes=([0-9]+) return=([0-9A-F]{4}):([0-9A-F]{4})\r?$",
            log,
        )
        if len(callback_rows) != 4:
            errors.append(f"expected four far callback rows, found {len(callback_rows)}")
        if [row[0] for row in callback_rows] != ["1", "1", "1", "0"]:
            errors.append("far callback results do not match all-pass and stop runs")
        if any(row[1:] != ("1", "1", "1", "6", "1000", "0005") for row in callback_rows):
            errors.append("far callback did not restore stack and return with RETF 6")
    else:
        callback_rows = re.findall(r"(?m)^VM callback result=([01]) stack=([01]) steps=[0-9]+\r?$", log)
        if len(callback_rows) != 4 or [row[0] for row in callback_rows] != ["1", "1", "1", "0"]:
            errors.append("baseline callback records are incomplete or inconsistent")

    winret = decoded.get("WINRET.TXT", "")
    if re.search(r"(?m)^WINRET=0[ \t]*\r?$", winret) is None:
        errors.append("DOS return record is missing WINRET=0")
    return tuple(errors)


class NativeFixtureEvidenceTests(unittest.TestCase):
    def test_historical_smoke_evidence_is_hashed_and_complete(self) -> None:
        self.assertEqual(
            validate_record(EVIDENCE / "smoke-20261018", SMOKE_PATTERNS), ()
        )

    def test_farcall_retf_evidence_is_hashed_and_complete(self) -> None:
        self.assertEqual(
            validate_record(EVIDENCE / "farcall-retf6-20261018", FAR_PATTERNS), ()
        )

    def test_farcall_record_keeps_its_historical_source_identity(self) -> None:
        manifest = json.loads(
            (EVIDENCE / "farcall-retf6-20261018" / "MANIFEST.json").read_text(
                encoding="ascii"
            )
        )
        self.assertEqual(
            manifest["source_commit"], "2e4753f812211686a9e219527236a7782e13ca0e"
        )
        self.assertEqual(
            manifest["source_file_sha256_lf_normalized"],
            "d2745b2567b80c6beb0f5e8248b2d53d18449e43b211847d606da38b3f54dccd",
        )

    def test_missing_raw_log_cannot_pass(self) -> None:
        source = EVIDENCE / "farcall-retf6-20261018"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            shutil.copy2(source / "MANIFEST.json", target / "MANIFEST.json")
            shutil.copy2(source / "WINRET.TXT", target / "WINRET.TXT")
            errors = validate_record(target, FAR_PATTERNS)
        self.assertTrue(any("missing raw evidence file W16API.LOG" in error for error in errors))

    def test_stale_raw_log_cannot_pass_its_recorded_hash(self) -> None:
        source = EVIDENCE / "farcall-retf6-20261018"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for name in RAW_FILES | {"MANIFEST.json"}:
                shutil.copy2(source / name, target / name)
            with (target / "W16API.LOG").open("ab") as stream:
                stream.write(b"STALE\r\n")
            errors = validate_record(target, FAR_PATTERNS)
        self.assertTrue(any("SHA-256 mismatch for W16API.LOG" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
