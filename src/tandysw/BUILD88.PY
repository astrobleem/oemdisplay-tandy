#!/usr/bin/env python3
"""Build the 8088 correction; a successful build is not runtime validation."""
from pathlib import Path
import argparse, hashlib, importlib.util, importlib.machinery, json, os, re, subprocess, sys
import build as baseline

HERE = Path(__file__).resolve().parent

def bounded_run(command, env, path, timeout=180):
    """Bound every emulator's runtime and host log size (16 MiB)."""
    limits = None
    if os.name == "posix":
        import resource
        def limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (16*1024*1024, 16*1024*1024))
    with path.open("wb") as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                       timeout=timeout, check=True, preexec_fn=limits if os.name == "posix" else None)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[1])
    parser.add_argument("--dosbox", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, dosbox, out = args.repo.resolve(), args.dosbox.resolve(), args.out.resolve()
    if out.exists():
        raise SystemExit("Choose a fresh --out directory")
    out.mkdir(parents=True)
    renderer, resources = baseline.prepare(repo, out)
    loader = importlib.machinery.SourceFileLoader("port8086", str(HERE / "PORT8086.PY"))
    spec = importlib.util.spec_from_loader("port8086", loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = module.port(renderer, repo)
    dib_loader = importlib.machinery.SourceFileLoader("portdib", str(HERE / "PORTDIB.PY"))
    dib_spec = importlib.util.spec_from_loader("portdib", dib_loader)
    dib_module = importlib.util.module_from_spec(dib_spec)
    dib_spec.loader.exec_module(dib_module)
    dib_audit = dib_module.port(renderer, repo)
    for filename in ("BLDCOR.BAT", "BLDCUR.BAT"):
        path = renderer / filename
        text = baseline.normalized(path).replace("SET INCLUDE=", "SET INCLUDE=R:\\INC;")
        text = text.replace("MASM -I", "MASM -LA -I")
        # A full listing is evidence for every linked assembly input.
        if filename == "BLDCOR.BAT":
            text = re.sub(r",([a-z0-9]+)\.obj;", r",\1.obj,\1.lst;", text)
        baseline.write_dos(path, text)
    cfg = out / "BUILD.CNF"
    cfg.write_text("[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=16\n"
                   "working directory option=force\nworking directory default=" + str(out) +
                   "\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[mixer]\nnosound=true\n"
                   "[midi]\nmididevice=none\n[autoexec]\n@echo off\n"
                   'mount C "' + str(repo) + '"\nmount R "' + str(renderer) +
                   '"\nmount D "' + str(resources) + '"\nR:\n')
    # Use the accepted 8086 ISA core with the four-byte 8088 prefetch queue.
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", TANDY_REPO=str(repo))
    for label, batch, drive in (("core", "BLDCOR.BAT", "R:"),
                                ("cursor", "BLDCUR.BAT", "R:"),
                                ("resources", "BUILD.BAT", "D:")):
        command = [str(dosbox), "-nopromptfolder", "-conf", str(cfg), "-c", drive, "-c", batch]
        bounded_run(command, env, out / (label + "-host.log"))
    for path in (renderer / "EGA/BUILD0.LOG", renderer / "EGA/CURSOR.LOG", renderer / "EGA/LINK.LOG",
                 resources / "BUILD.LOG"):
        text = path.read_text(errors="replace")
        errors = [int(n) for n in re.findall(r"(\d+)\s+Severe\s+Errors", text)]
        if any(errors) or re.search(r"error L\d+|fatal error", text, re.I):
            raise SystemExit("Build failed; inspect " + str(path))
    audit_loader = importlib.machinery.SourceFileLoader("audit88", str(HERE / "AUDIT88.PY"))
    audit_spec = importlib.util.spec_from_loader("audit88", audit_loader)
    audit_module = importlib.util.module_from_spec(audit_spec)
    audit_spec.loader.exec_module(audit_module)
    listings = sorted((renderer / "EGA").glob("*.LST"))
    if len(listings) != 27:
        raise SystemExit("Expected 27 linked-module listings, got " + str(len(listings)))
    instruction_audit = audit_module.audit(listings)
    link_audit = module.audit_link(renderer, dib_audit["new_objects"])
    subprocess.run([sys.executable, str(resources / "PACKRES.PY"), "build"], env=env, check=True)
    resource_file = resources / "TANDY.RES"
    assert hashlib.sha256(resource_file.read_bytes()).hexdigest() == baseline.RESOURCE_SHA
    binary = out / "TANDY88.DRV"
    subprocess.run([sys.executable, str(resources / "PACKRES.PY"), "attach", str(resource_file),
                    str(renderer / "EGA/TSOFT.DRV"), str(binary)], env=env, check=True)
    report = {"build": "PASS", "runtime": "NOT_TESTED", "target": "8086/8088 real mode", "candidate": "05 DIB save/readback correction",
              "driver_bytes": binary.stat().st_size,
              "driver_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "port": audit, "dib": dib_audit,
              "instruction_audit": instruction_audit, "link_audit": link_audit}
    (out / "RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
