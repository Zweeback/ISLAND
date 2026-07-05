# ISLAND Scanner Dashboard

Safe prototype imported from the Antigravity scratch handoff in `Consolidating ISLAND Workspace Projects.md`.

## Purpose

This dashboard gives ISLAND a small local control surface for bounded scans and template generation while the larger Jules/OpenClaw autonomy layer is being designed.

It can:

- scan bounded local folders: Desktop, Downloads, Documents/Codex
- scan local Google Drive mount candidates if present
- list public GitHub repositories for `Zweeback`
- generate simple document/report/sheet/slide starter files into `ingest/`

## Safety Notes

- It does not delete, archive, or modify source repositories.
- It does not use credentials, cookies, or private APIs.
- It does not run as a daemon unless you start it manually.
- Google Drive scanning only checks local mounted folders; it does not fabricate cloud results.
- Full private GitHub import still belongs to a separate authenticated consolidation step.

## Run

From this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_dashboard.ps1
```

Or manually:

```powershell
python scanner_backend.py
```

Then open `http://127.0.0.1:8000/`.
