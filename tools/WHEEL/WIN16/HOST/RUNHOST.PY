from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
compiler = os.environ.get("CC", "gcc")
resolved_compiler = shutil.which(compiler)
if not resolved_compiler:
    raise SystemExit(f"C compiler not found on PATH: {compiler}")
env = dict(os.environ)
env["PATH"] = str(Path(resolved_compiler).resolve().parent) + os.pathsep + env.get("PATH", "")

flags = [
    "-x", "c", "-std=c89", "-Wall", "-Wextra", "-Werror",
    "-Wno-cast-function-type", "-Wno-pointer-to-int-cast",
    "-Wno-int-to-pointer-cast",
]
with tempfile.TemporaryDirectory(prefix="winwheel-host-") as temp:
    exe = Path(temp) / "HOSTTEST.EXE"
    built = subprocess.run(
        [compiler, *flags, str(ROOT / "HOST" / "HOSTTEST.C"), "-o", str(exe)],
        capture_output=True, text=True, timeout=30, env=env,
    )
    if built.returncode:
        raise SystemExit(built.stdout + built.stderr)
    result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15, env=env)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    passed = result.stdout.count("PASS ")
    if result.returncode or passed != 27 or "FAILURES=0" not in result.stdout:
        raise SystemExit(f"host suite failed: exit={result.returncode}, checks={passed}")
    print(f"HOST_PASS checks={passed}")
