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
2. Start page explains next step and traffic-light state is readable without clicks.
3. Press **Add Ingredient** from Start and confirm the ingredient lands in the bank.
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
   - `Export TXT` and `Export HTML` write files.
   - `Copy Share Summary` and `Export Share Card` create a short shareable version without leaving the machine.
   - `Open Exports Folder` opens after export.
8. Open Library and load one favourite to Result.
9. Open Settings and confirm data path shows local folder on D:\.
10. Quick check on mobile-like width (500px or lower):
    - Side-nav compresses cleanly without clipping labels.
    - Form controls and call-to-action buttons stack full width.
    - No horizontal overflow in long output blocks.
11. Quick check on tablet width (768px-900px):
    - Page and side-nav spacing feels breathable.
    - Top bar, traffic meter, and main cards remain readable.
12. Close browser, restart app, and confirm the bank data and favourites still restore from local storage.
13. On at least one OS/browser refresh, verify no stale errors remain in the console during first smoke run.
14. Close the local app server before ending the dev stage:
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
  - Start / Bank / Generate / Result / Library / Settings
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
