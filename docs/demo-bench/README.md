# ProMentum Demo Bench

These files are generated from fixed seeds so the creative voice can be tuned
without using AI APIs, paid models, accounts, or cloud calls.

Regenerate the full demo bench from the app root:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\ProMentumData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:PROMENTUM_HOME = "D:\ProMentumData"
python scripts\sample_collisions.py --demo --count 28 --output-dir docs\demo-bench
```

Use this folder as the tuning bench before changing the engine voice. Good
changes should make multiple files sharper, not just one lucky seed.

The generated text should use current ProMentum recipe labels.
