# ProMentum

ProMentum is a local-first first-move generator. It takes your own ideas,
phrases, people, places, questions, rules, and obsessions, then turns stuck
thoughts into repeatable sparks, hooks, scene seeds, and next moves.

It has no API keys, no cloud calls, no accounts, no npm, and no build step.

## Start On Windows

1. Open this folder.
2. Double-click `START_ProMentum_WINDOWS.bat`.
3. Your browser opens.
4. Follow the red, amber, and green readiness lights.
5. Press `Generate First Move`.

If Windows says Python is missing, install Python 3.10 or newer from:

```text
https://www.python.org/downloads/windows/
```

Tick `Add python.exe to PATH` during install, then double-click the launcher
again.

By default on Windows, ProMentum saves local data to `D:\ProMentumData` when
D: exists. If D: is missing, it uses the portable `promentum_data` folder beside
the app. You can set `PROMENTUM_HOME` to choose another folder.

## D-Drive Development

For this project, keep runtime data and temporary files on D:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"
python -m idea_collider_app.app
```

`IDEA_COLLIDER_HOME` still works as an older compatibility fallback, but new
test and release commands should use `PROMENTUM_HOME`.

## App Pages

- `Start` shows readiness, quick-adds one raw ingredient, and can switch between a blank bank and the starter bank.
- `Spark Bank` edits raw ingredients, adds quick lines, and cleans duplicates.
- `Generate` chooses mode, seed, weirdness, and ingredient count.
- `Result` shows hooks, what the idea could become, next moves, and why it happened.
- `Library` keeps favourites.
- `Settings` shows the local data folder and reset controls.
- On Generate, press **Enter** in the Seed field to run immediately.

## Result Controls

- `Regenerate Variant` keeps the mode but moves the seed forward.
- `Keep Same Ingredients` changes the drift while preserving the exact selected ingredients.
- `Lock Best Ingredient` keeps the strongest ingredient visible and lets the rest change.
- `Copy Seed Recipe` copies the repeatable seed, mode, weirdness, and ingredient count.

## Manual Start

```powershell
python -m idea_collider_app.app
```

The app opens at a local address such as:

```text
http://127.0.0.1:53842
```

Close the terminal window, or press `Ctrl+C`, to stop it.

## Development Checks

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"
python -m unittest discover -s tests
python -m compileall idea_collider_app tests scripts
python scripts\sample_collisions.py --count 5
python -m idea_collider_app.app --doctor
```

## Close Down After A Dev Stage

Before handing the machine back to other agents, stop any local ProMentum server
you started:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1
```

To preview what it would close without stopping anything:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1 -DryRun
```

The script only targets Python processes running `idea_collider_app.app`.

## Demo Bench

The fixed tuning bench lives in `docs\demo-bench`.

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"
python scripts\sample_collisions.py --demo --count 28 --output-dir docs\demo-bench
```

Use those files to judge engine changes before trusting one lucky seed.

## Manual QA

- Run `docs\UX_SMOKE_CHECKLIST.md` on each UI change before release.

## Licence

ProMentum is source-available for personal and non-commercial use under the
PolyForm Noncommercial License 1.0.0. Commercial use requires a separate
written licence from the licensor. See `LICENSE`.

## Release ZIP

Maintainers can build and verify a clean local ZIP with:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData, D:\ProMentumVerifyWork | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"
powershell -ExecutionPolicy Bypass -File scripts\make_release_zip.ps1
$zip = (Get-ChildItem dist\ProMentum-v*.zip | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
powershell -ExecutionPolicy Bypass -File scripts\verify_release_zip.ps1 -ZipPath $zip -WorkRoot D:\ProMentumVerifyWork
```

The ZIP includes the app, tests, scripts, and demo text files. It excludes
runtime data, screenshots, caches, and temporary build folders.

## Design Promise

ProMentum should teach by movement. Each page has one job, and the traffic
lights should make the next step obvious without turning the app into a manual.

## Visual Identity

The app uses generated local-first WebP artwork under
`idea_collider_app\static\assets`: a workshop backdrop, a console panel, an
idea-bank workbench, and a saved-sparks shelf. They are UI assets only, contain
no readable text, brand logos, or external service dependency, and are kept
small enough for the release ZIP.
