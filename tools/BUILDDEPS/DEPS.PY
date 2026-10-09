#!/usr/bin/env python3
"""Explicit, commit-pinned legacy build inputs; never runs guest programs."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

REMOTE = "https://github.com/astrobleem/oemdisplay-tandy.git"
ROOTS = ("BIN", "DDK", "INCLUDE", "LIB")
PROFILES = {
    "display": ("src/tandysw/", "docs/"),
    "keyboard": ("src/tandyk3/",),
    "shell": ("examples/TSHELL/", "docs/"),
    "examples": ("examples/", "docs/"),
    "textmode": ("experiments/TEXTMODE/", "src/tandysw/", "docs/"),
    "experiments": ("experiments/", "src/tandysw/", "docs/"),
    "tools": ("tools/", "distributions/WINXT/", "examples/WXTSPL/",
              "src/splash/assets/", "src/tandysw/TINST.C", "docs/"),
    "release": ("tools/FLASHDISK/", "tools/CPSET/", "docs/QUAL/CPSET.JSON",
                "distributions/WINXT/",
                "examples/TSHELL/", "examples/WXTSPL/",
                "src/splash/assets/", "src/tandysw/TINST.C", "docs/QUAL/WAVEINS.JSON"),
}


class Refusal(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def exact_commit(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise Refusal("Require a full lowercase commit SHA; floating refs are refused")
    return value


def git(repo, *args):
    return subprocess.run(["git", "--no-replace-objects", "-c", "protocol.allow=never",
                           "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def checked_commit(repo, commit):
    exact_commit(commit)
    if git(repo, "rev-parse", commit + "^{commit}").decode().strip() != commit:
        raise Refusal("Commit identity differs from lock")


def tree(repo, commit):
    checked_commit(repo, commit)
    rows = {}
    for record in git(repo, "ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        mode, kind, blob = meta.decode("ascii").split()
        rows[name.decode("utf-8")] = (mode, kind, blob)
    return rows


def valid_path(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or p.as_posix() != name or
            any(x in (".", "..") for x in name.split("/")) or
            "\\" in name or ":" in name or "\0" in name):
        raise Refusal("Unsafe or noncanonical path: " + repr(name))


def check_paths(names, case_sensitive):
    seen = {}
    for name in names:
        valid_path(name)
        parts = name.split("/")
        for i in range(1, len(parts) + 1):
            prefix = "/".join(parts[:i])
            key = prefix if case_sensitive else prefix.casefold()
            if key in seen and seen[key] != prefix:
                raise Refusal("Case-sensitive checkout required: " + seen[key] +
                              " conflicts with " + prefix)
            seen[key] = prefix


def blobs(repo, rows):
    """Read exact Git bytes, avoiding autocrlf and checkout case collisions."""
    payload = {}
    proc = subprocess.Popen(["git", "--no-replace-objects", "-c", "protocol.allow=never",
                             "-C", str(repo), "cat-file", "--batch"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        for name, (mode, kind, blob) in sorted(rows.items()):
            if mode != "100644" and mode != "100755":
                raise Refusal("Links/submodules are not build inputs: " + name)
            proc.stdin.write((blob + "\n").encode("ascii"))
            proc.stdin.flush()
            fields = proc.stdout.readline().decode("ascii").split()
            if len(fields) != 3 or fields[:2] != [blob, "blob"] or kind != "blob":
                raise Refusal("Unexpected Git object for " + name)
            size = int(fields[2])
            data = proc.stdout.read(size)
            if len(data) != size or proc.stdout.read(1) != b"\n":
                raise Refusal("Truncated Git object for " + name)
            payload[name] = data
        proc.stdin.close()
        if proc.wait(timeout=30):
            raise Refusal("Git object reader failed")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        proc.stdout.close()
        proc.stderr.close()
    return payload


def load_lock(path, allow_provisional=False):
    lock = json.loads(Path(path).read_bytes())
    if lock.get("schema") != 1 or lock.get("repository") != REMOTE:
        raise Refusal("Unsupported lock schema or repository")
    exact_commit(lock["commit"])
    if lock.get("status") not in ("provisional", "settled-dev"):
        raise Refusal("Unknown preservation status")
    if lock["status"] == "provisional" and not allow_provisional:
        raise Refusal("DEV snapshot is not settled; local review requires --allow-provisional")
    files = lock["files"]
    if not files:
        raise Refusal("Empty dependency lock")
    check_paths(files, False)
    for name, entry in files.items():
        if name.split("/")[0] not in ROOTS:
            raise Refusal("Unexpected dependency root: " + name)
        if (set(entry) != {"blob", "bytes", "sha256"} or
                not re.fullmatch(r"[0-9a-f]{40}", entry["blob"]) or
                not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) or
                type(entry["bytes"]) is not int or entry["bytes"] < 0):
            raise Refusal("Invalid dependency record: " + name)
    return lock


def fresh_out(path, protected=()):
    path = Path(os.path.abspath(str(path)))
    if path.exists() or path.is_symlink():
        raise Refusal("Output exists; choose a new path: " + str(path))
    if not path.parent.is_dir() or path.parent.resolve() != path.parent:
        raise Refusal("Output parent must exist without linked ancestors")
    for root in protected:
        root = Path(root).resolve()
        if path == root or root in path.parents:
            raise Refusal("Output must stay outside the source/dependency repository")
    return path


def write_payload(out, payload):
    out.mkdir()
    for name, data in sorted(payload.items()):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)


def dependency_payload(repo, lock):
    rows = {n: r for n, r in tree(repo, lock["commit"]).items()
            if n.split("/")[0] in ROOTS}
    if set(rows) != set(lock["files"]):
        raise Refusal("Dependency tree differs from locked membership")
    for name, row in rows.items():
        if row[2] != lock["files"][name]["blob"]:
            raise Refusal("Locked Git blob differs: " + name)
    data = blobs(repo, rows)
    for name, content in data.items():
        entry = lock["files"][name]
        if len(content) != entry["bytes"] or sha(content) != entry["sha256"]:
            raise Refusal("Dependency SHA256/size differs: " + name)
    return data


def verified_directory(root, lock):
    root = Path(os.path.abspath(str(root)))
    if not root.is_dir() or root.resolve() != root:
        raise Refusal("Dependency directory must exist without linked ancestors")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink() or path.resolve() != path.absolute():
            raise Refusal("Linked dependency path refused: " + str(path))
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != set(lock["files"]):
        raise Refusal("Dependency directory has missing or extra files")
    data = {}
    for name, entry in lock["files"].items():
        content = (root / name).read_bytes()
        if len(content) != entry["bytes"] or sha(content) != entry["sha256"]:
            raise Refusal("Dependency SHA256/size differs: " + name)
        data[name] = content
    return data


def make_lock(repo, commit, status="provisional", archive_ref="refs/remotes/origin/DEV"):
    checked_commit(repo, commit)
    if status == "settled-dev":
        if git(repo, "rev-parse", archive_ref + "^{commit}").decode().strip() != commit:
            raise Refusal("DEV ref must equal the exact pre-cleanup snapshot commit")
    rows = {n: r for n, r in tree(repo, commit).items() if n.split("/")[0] in ROOTS}
    check_paths(rows, False)
    data = blobs(repo, rows)
    return {"schema": 1, "repository": REMOTE, "commit": commit,
            "status": status, "archive_ref": archive_ref,
            "files": {n: {"blob": rows[n][2], "bytes": len(b), "sha256": sha(b)}
                      for n, b in sorted(data.items())}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("lock", help="Record exact local Git dependency bytes")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--status", choices=("provisional", "settled-dev"), default="provisional")
    p.add_argument("--archive-ref", default="refs/remotes/origin/DEV")
    for command in ("fetch", "materialize", "verify", "view"):
        p = sub.add_parser(command)
        p.add_argument("--lock", type=Path, required=True)
        p.add_argument("--allow-provisional", action="store_true")
        if command in ("fetch", "materialize", "view"):
            p.add_argument("--out", type=Path, required=True)
        if command == "materialize":
            p.add_argument("--repo", type=Path, required=True)
        if command in ("verify", "view"):
            p.add_argument("--deps", type=Path, required=True)
        if command == "view":
            p.add_argument("--source-repo", type=Path, required=True)
            p.add_argument("--source-commit", required=True)
            p.add_argument("--profile", choices=PROFILES, required=True)
    args = parser.parse_args(argv)
    if args.command == "lock":
        out = fresh_out(args.out)
        lock = make_lock(args.repo, args.commit, args.status, args.archive_ref)
        out.write_bytes((json.dumps(lock, indent=2, sort_keys=True) + "\r\n").replace("\n", "\r\n").replace("\r\r\n", "\r\n").encode("ascii"))
        print("Locked", len(lock["files"]), "files at", lock["commit"], lock["status"])
        return
    lock = load_lock(args.lock, args.allow_provisional)
    if args.command == "fetch":
        # Only this explicitly named command accesses the network.
        out = fresh_out(args.out)
        subprocess.run(["git", "init", "--bare", str(out)], check=True)
        subprocess.run(["git", "-C", str(out), "fetch", "--no-tags", "--depth=1",
                        REMOTE, lock["commit"]], check=True)
        checked_commit(out, lock["commit"])
        print("Fetched exact commit; materialize separately to verify file hashes")
    elif args.command == "materialize":
        out = fresh_out(args.out, (args.repo,))
        data = dependency_payload(args.repo, lock)
        write_payload(out, data)
        verified_directory(out, lock)
        print("Materialized verified dependencies:", out)
    elif args.command == "verify":
        verified_directory(args.deps, lock)
        print("PASS: exact dependency membership, SHA256 and sizes")
    else:
        out = fresh_out(args.out, (args.source_repo, args.deps))
        source = {n: r for n, r in tree(args.source_repo, args.source_commit).items()
                  if any(n.startswith(prefix) for prefix in PROFILES[args.profile])}
        if not source:
            raise Refusal("Selected source profile is empty")
        check_paths(source, os.name != "nt")
        data = verified_directory(args.deps, lock)
        data.update(blobs(args.source_repo, source))
        check_paths(data, os.name != "nt")
        write_payload(out, data)
        verified_directory_subset = {n: (out / n).read_bytes() for n in lock["files"]}
        if any(sha(b) != lock["files"][n]["sha256"] for n, b in verified_directory_subset.items()):
            raise Refusal("Staged dependency bytes changed")
        print("Build view:", out, "profile:", args.profile,
              "source:", args.source_commit, "dependencies:", lock["commit"])


if __name__ == "__main__":
    try:
        main()
    except (Refusal, OSError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit("REFUSED: " + str(error))
