# Demo checklist (ICBSN 2026 / BIO-INSPIRE, 17–18 Dec)

The live demo: start the app, run one validation isolate, open the ERR4796343 (XDR-TB) report, show the Validation tab. Everything runs on the laptop. No internet is needed.

## What was tested (28 Nov 2026)

| Check | Result |
|---|---|
| App starts from a fresh terminal (`conda activate bioinfo`, `streamlit run app.py`) | OK, no warnings, bound to localhost:8501 |
| All three tabs load, ERR4796343 report opens | OK |
| Pipeline with no network, ERR4796343 from scratch | OK, 67 s, same calls as the validation run (XDR-TB, 7 variants) |
| Pipeline with no network, ERR4796343 cached (what the app does) | OK, 7 s |
| Windows browser, Wi-Fi on: ERR4796343 run from the app | OK, XDR-TB report, QC PASS |
| Windows browser, Wi-Fi on: Browse tab | OK, 120 isolates, 113 PASS, 7 WARN, 88 pre-XDR/XDR |
| Windows browser, Wi-Fi on: Validation tab | OK, 116 isolates, 1,216 calls, 97.0%, both charts |
| Windows browser, Wi-Fi on: change a widget mid-run (ERR4830657), then run again | OK, run stopped, rerun finished with no lock error |
| Windows browser with Wi-Fi off | To do on rehearsal day (see "Day before", step 3) |

The pipeline-only tests ran in a Linux namespace with no network (`unshare -rn`). The browser tests were done by hand on the laptop with Wi-Fi on. The full Wi-Fi-off run in the browser is still to be done.

## Day before

1. Plug in the charger. Set Windows power mode to "Best performance". Pause Windows Update for a week so it can't restart the laptop.
2. Fresh terminal:
   ```bash
   cd ~/projects/tb-wgs
   conda activate bioinfo
   bash scripts/demo_preflight.sh
   ```
   Every line must say PASS.
3. Full rehearsal with Wi-Fi switched off in Windows:
   - `streamlit run app.py`, then open http://localhost:8501 in the Windows browser.
   - Run tab: pick the demo isolate, press Run pipeline. A cached run finishes in under 15 s; a fresh one takes about 1–2 min.
   - Browse tab: open ERR4796343. Check the red XDR-TB banner and drug table are visible.
   - Validation tab: charts and tables load.
   - Set the browser zoom that looks right on the projector (or on a 1280×720 window) and note it here: ____
4. Make fallbacks, in case the app fails on the day:
   - Copy `pipeline_out/reports/ERR4796343.report.html` and one PASS report to a USB stick and to the Windows desktop (`cp pipeline_out/reports/ERR4796343.report.html /mnt/c/Users/<you>/Desktop/`). They open offline in any browser.
   - Record a short screen video of the rehearsal (Win+Alt+R with Xbox Game Bar) and put it on the USB stick too.
5. After the rehearsal, avoid other pipeline runs. If you must run one, always add `-resume` when using the main `work/` folder. A run without `-resume` and without `-w` starts a new cache session, and the next demo run would be a full 1–2 min run.

## Day of

1. Charger in, Wi-Fi off, Windows notifications off (Focus / Do not disturb), close other apps.
2. Fresh terminal:
   ```bash
   cd ~/projects/tb-wgs
   conda activate bioinfo
   bash scripts/demo_preflight.sh
   streamlit run app.py
   ```
3. Open http://localhost:8501 in the browser, set the zoom from step 3 above.
4. Warm-up before the talk: run the demo isolate once, so the real run on stage comes from cache.
5. On stage: while a run is going, don't click anything else in the app. Touching another widget restarts the page and stops the run (the app now stops Nextflow cleanly, so you can just press Run again).

## If something fails

| Problem | What to do |
|---|---|
| Preflight FAIL "bioinfo env is active" or "streamlit on PATH" | `conda activate bioinfo` |
| Preflight FAIL "nextflow on PATH" or "Java 17" | Close the terminal and open a new one so `~/.bashrc` runs |
| Preflight FAIL "no Streamlit already running" / "port 8501 free" | Stop the old app: `pkill -f "streamlit run"` |
| Preflight FAIL "no other Nextflow run active" | Wait for it, or stop it with Ctrl+C in its terminal |
| Browser can't reach localhost:8501 | Check the terminal shows the app running; try http://127.0.0.1:8501; restart WSL with `wsl --shutdown` in PowerShell, then start again |
| Run fails or hangs | Go to the Browse tab and open the existing report instead |
| App won't start at all | Open the report file from the desktop or USB stick, or play the recording |

## Known limits (say so if asked)

- The "All samples" link inside an embedded report doesn't work inside the app. Use the Browse tab.
- The public site (GitHub Pages) needs internet. Don't rely on it for the demo.
- Research use only. Predictions need clinician review alongside phenotypic testing.
