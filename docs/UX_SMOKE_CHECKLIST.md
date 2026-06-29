# ProMentum UX Smoke Checklist

Use this for a quick first-run pass on Windows after UI or release changes.

## Environment

- Run from D: where possible.
- Set these before launching:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"
python -m idea_collider_app.app --doctor
```

## Smoke Checklist

1. Opened app quickly from one command or `START_ProMentum_WINDOWS.bat`.
2. Today page explains one next action, or clearly says to generate/save a project first.
3. Open Capture, press **Add Ingredient**, and confirm the ingredient lands in the bank.
4. Open Spark Bank and confirm:
   - `New ingredient` field has focus.
   - One line add works with **Enter**.
   - Active tab panel updates.
5. From Spark Bank, add at least one realistic ingredient in three categories.
6. Open Generate and confirm:
   - `Seed` field has focus by default.
   - `Use First-Run Defaults` resets mode, ingredient count, weirdness, and seed to a simple first run.
   - Seed normalizes to a whole-number only experience: typing non-integers shows guidance, blank means random.
   - A seed can be pasted and then cleared to `auto` for random behavior.
   - Weirdness slider updates the value badge instantly and clearly.
   - Ingredient input clamps to 3-7 with clear on-screen feedback if adjusted.
   - **Generate First Move** works once the engine says ready.
7. Open Result and run:
   - `Copy Output` works.
   - `Copy Hook` and `Copy Seed Recipe` work.
   - `Keep Same Ingredients`, `Lock Best Ingredient`, `Regenerate Variant` return fresh output.
   - `Save Favourite` adds an item to Library.
   - `Save as Project` opens Momentum with a real project.
   - `Export TXT` and `Export HTML` write files.
   - `Copy Share Summary` and `Export Share Card` create a short shareable version without leaving the machine.
   - `Open Exports Folder` opens after export.
8. Open Momentum and confirm:
   - Project title, v0.3.0 stage, traffic light, notes, blockers, wins, history, and action list are visible.
   - Add Action works and appears in the project list.
   - Checking an action updates the traffic-light summary after save.
   - Add Win works and appears in the project journal.
   - Add Blocker moves the project toward a red/parked state after save.
   - `Copy Project Brief` works.
   - `Export Project Brief`, `Export Today Plan`, and `Export Progress Log` write local TXT files.
   - `Export Project Card` writes a local HTML file and enables exports-folder opening.
   - Closing and reopening the app restores the project.
9. Return to Today and confirm:
   - A single recommended project action is visible.
   - `Start 10 Minutes` changes the session state.
   - `Mark Action Done` saves a history entry and advances the project.
   - `Save Win` and `Save Blocker` write to the same local project.
10. Open Library and load one favourite to Result.
11. Open Settings and confirm data path shows local folder on D:\ and projects path is visible.
12. Quick check on mobile-like width (500px or lower):
    - Side-nav compresses cleanly without clipping labels.
    - Form controls and call-to-action buttons stack full width.
    - No horizontal overflow in long output blocks.
13. Quick check on tablet width (768px-900px):
    - Page and side-nav spacing feels breathable.
    - Top bar, traffic meter, and main cards remain readable.
14. Close browser, restart app, and confirm the bank data, projects, project history, and favourites still restore from local storage.
15. On at least one OS/browser refresh, verify no stale errors remain in the console during first smoke run.
16. Close the local app server before ending the dev stage:
    `powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1`

## Smoke Runbook

Use this exact order for a fast, consistent first run.

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"

# Health check (fast)
python -m idea_collider_app.app --doctor

# Optional headless smoke in a separate terminal
# leaves server running on an ephemeral port until you press Ctrl+C
python -m idea_collider_app.app --no-open --port 0

# Optional CLI checks
python -m unittest discover -s tests
python scripts\sample_collisions.py --count 1

# Final cleanup
powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1
```

Recommended run notes:
- During the browser flow, keep notes for each section that fails:
  - Today / Capture / Bank / Generate / Result / Library / Settings
  - Momentum / project save / 10-minute loop / project export
- Log pass/fail per check above in plain text for testers.
- For any visual issue, capture one screenshot at the failing viewport.

## Done Conditions

- No visible layout overflow on mobile-width viewport.
- No obvious dead-end state where the next step button is locked without explanation.
- Input validation and seed/weirdness controls behave predictably.
- No console-blocking errors in a 60-second smoke run.

## Cross-surface Checklist

- [ ] Desktop (1200x800): happy path is complete in under 60 seconds.
- [ ] Tablet (768x1024): no overlap/overflow and full-width action groups on smaller controls.
- [ ] Mobile (390x844): single-column controls, readable labels, and stable flow status text.
