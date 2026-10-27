# One panning application

Consumers use PAN and its one configuration entry, PAN /SETTINGS. A standalone
expanded PAN.ZIP installs all backend files automatically; updated normal driver
packets include that same application. One detected backend runs at a time.
PAN.EXE is the transient dispatcher/configuration entry; internal backend files
stay separate to avoid making every adapter load every presentation engine.

The PCjr and ColorPlus panning drivers now expose 640x400 through a 320x200 view.
Two 64,000-byte bands retain the existing four-plane GDI representation across
the 64KB segment boundary. The presenter copies the selected rectangle to the
adapter's existing 32KB video page; it never programs hardware pan registers.
The existing HPXY hardware/software and CGA/fixed-display paths remain distinct
presentation backends, with their accepted display/grabber bytes preserved.

PREPARE.PY stages private native transactions and packets for acceptance. It
reuses the existing checked file/INI transaction, verifies exact prior vertical
panning driver bytes before replacement, migrates startup tokens once, preserves
an explicit OFF choice and installs PAN without manual helper copies.
CGA.PY builds/finalizes its exact staged CGA transaction with the supported C6
route and shared lease. All emulator use requires an actual acquired lease.

PUBLISH.PY refuses output until all distinct backend families, native setup,
actual installed bytes, raster comparisons and independent final review pass.
BASE retains exact preceding public packets and superseded source bindings;
original acceptance records and pins are unchanged. HISTORY.PY is only for
replaying the preceding UPAN qualification, never for new PAN source validation.
Current catalog integration uses tools/CURRENT; publication needs separate
explicit approval. No driver, compiler, OS image or emulator is fetched here.
