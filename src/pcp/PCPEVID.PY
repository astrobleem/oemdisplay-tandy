#!/usr/bin/env python3
"""Validate recorded capture provenance and current palette-attempt records.

  python3 src/pcp/PCPEVID.PY --evidence docs/pc1512 --width 640

No guest, disk reader or native tool is used. Raw captures can be checked
only where the index retains a raw_copy; a filename alone is not raw proof.
"""
import argparse
import importlib.machinery
import json
import re
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FRAME_ID = re.compile(r"[A-Za-z0-9_]+\Z")
ATTEMPT = re.compile(r"(arrow_\d{2})_t([1-9]\d*)\Z")


def validate_index(index, evidence, width):
    """Return unique records after checking capture/alias/file associations."""
    root = Path(evidence).resolve()
    records, sources = {}, set()
    rows = index.get("frames") if isinstance(index, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("capture index must contain a nonempty frames list")
    for row in rows:
        name = row.get("frame") if isinstance(row, dict) else None
        if not isinstance(name, str) or not FRAME_ID.fullmatch(name):
            raise ValueError("invalid capture frame identifier")
        if name in records:
            raise ValueError("duplicate frame identifier: " + name)
        records[name] = row
        if "accepted_from" in row:
            if "source" in row or "decoded" in row:
                raise ValueError("accepted alias must not claim a raw capture: " + name)
        else:
            source = row.get("source")
            if not isinstance(source, str) or not source or source in sources:
                raise ValueError("missing or duplicate raw capture source: " + name)
            if type(row.get("decoded")) is not bool:
                raise ValueError("capture must state whether it was decoded: " + name)
            sources.add(source)

    if any(ATTEMPT.fullmatch(n) for n in records):
        aliases = {n for n, r in records.items() if "accepted_from" in r}
        if aliases != {f"arrow_{c:02d}" for c in range(16)}:
            raise ValueError("attempt index must contain all 16 accepted palette aliases")

    pixels = {}
    def frame(row):
        rel = row.get("repo_file")
        if not isinstance(rel, str):
            raise ValueError("decoded frame/alias has no repo_file: " + row["frame"])
        path = (root / rel).resolve()
        if root not in path.parents:
            raise ValueError("repo_file is outside evidence directory")
        if path not in pixels:
            with Image.open(path) as im:
                data = im.tobytes()
                if im.mode != "P" or im.size != (width, 200) or max(data) > 15:
                    raise ValueError("not an exact IRGB frame: " + rel)
                pixels[path] = data
        return pixels[path]

    decoder = None
    for name, row in records.items():
        if row.get("decoded") or "accepted_from" in row:
            data = frame(row)
        if "accepted_from" in row:
            origin = row["accepted_from"]
            match = ATTEMPT.fullmatch(origin) if isinstance(origin, str) else None
            if not match or match[1] != name or origin not in records or int(match[2]) > 8:
                raise ValueError("invalid accepted_from: " + name)
            capture = records[origin]
            if not capture.get("decoded") or not capture.get("source"):
                raise ValueError("accepted_from is not a decoded raw capture: " + name)
            if data != frame(capture):
                raise ValueError("accepted alias differs from its attempt: " + name)
            attempts = sorted(int(m[2]) for n in records
                              if (m := ATTEMPT.fullmatch(n)) and m[1] == name)
            if attempts != list(range(1, int(match[2]) + 1)):
                raise ValueError("attempts are not contiguous through acceptance: " + name)
        elif ATTEMPT.fullmatch(name):
            alias = records.get(ATTEMPT.fullmatch(name)[1], {})
            if not alias.get("accepted_from"):
                raise ValueError("attempt has no accepted alias: " + name)
        if row.get("raw_copy") and row.get("decoded"):
            raw = (root / row["raw_copy"]).resolve()
            if root not in raw.parents:
                raise ValueError("raw_copy is outside evidence directory")
            if decoder is None:
                decoder = importlib.machinery.SourceFileLoader(
                    "evidence_shotdec", str(HERE / "SHOTDEC.PY")).load_module()
            decoded, worst, bad, size, geometry = decoder.decode(str(raw), width)
            if bad or bytes(decoded) != data:
                raise ValueError("raw_copy differs from decoded frame: " + name)
    return records


def landing_report(rows, read_frame, hotspots, accepts):
    """Validate every accepted attempt, including earlier rejected attempts.

    Old curated LANDING records omit accepted_from; infer its name from the
    recorded attempt number, then verify the retained attempt pixels. New
    runs record accepted_from explicitly. Missing/exhausted cases fail.
    """
    report = dict(cases=0, first_try=0, recovered_by_retry=[], errors=[])
    if not isinstance(rows, list):
        report["errors"].append("LANDING must be a list")
        report["valid"] = False
        return report
    report["cases"] = len(rows)
    seen = set()
    for row in rows:
        name = row.get("frame") if isinstance(row, dict) else None
        if not isinstance(name, str) or name not in hotspots or name in seen:
            report["errors"].append("unknown or duplicate palette case: " + str(name))
            continue
        seen.add(name)
        count = row.get("attempts")
        if type(count) is not int or not 1 <= count <= 8:
            report["errors"].append("no successful accepted attempt: " + name)
            continue
        accepted = f"{name}_t{count}"
        if row.get("accepted_from", accepted) != accepted:
            report["errors"].append("accepted_from disagrees with attempts: " + name)
            continue
        hx, hy = hotspots[name]
        if row.get("hotspot") != [hx, hy]:
            report["errors"].append("incorrect requested hotspot: " + name)
            continue
        try:
            if read_frame(name) != read_frame(accepted):
                raise ValueError("accepted alias differs from current attempt")
            if not accepts(accepted, hx, hy):
                raise ValueError("accepted attempt does not show the exact arrow")
            for n in range(1, count):
                previous = f"{name}_t{n}"
                read_frame(previous)
                if accepts(previous, hx, hy):
                    raise ValueError("an earlier attempt already passed")
        except (OSError, KeyError, ValueError) as exc:
            report["errors"].append(name + ": " + str(exc))
            continue
        report["first_try"] += count == 1
        if count > 1:
            report["recovered_by_retry"].append(dict(
                frame=name, attempts=count, accepted_from=accepted,
                misses=row.get("misses", [])))
    missing = sorted(set(hotspots) - seen)
    if missing:
        report["errors"].append("missing palette cases: " + ", ".join(missing))
    report["valid"] = not report["errors"]
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--width", type=int, default=320, choices=[320, 640])
    args = ap.parse_args()
    root = Path(args.evidence)
    try:
        rows = validate_index(json.loads((root / "P86RAW.JSN").read_bytes()), root, args.width)
    except (OSError, ValueError, SystemExit) as exc:
        ap.exit(1, "PCPEVID: FAIL: " + str(exc) + "\n")
    print(json.dumps(dict(verdict="PASS", unique_frame_ids=len(rows),
                         raw_sources=sum("source" in r for r in rows.values()),
                         decoded_captures=sum(bool(r.get("decoded")) for r in rows.values()),
                         accepted_aliases=sum("accepted_from" in r for r in rows.values()),
                         retained_raw_redecodes=sum(bool(r.get("raw_copy")) and bool(r.get("decoded"))
                                                   for r in rows.values()),
                         raw_scope="Only retained raw_copy files were independently decoded."), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
