# Build: Fraud Loss Cliff

> Boundary-by-boundary regression-discontinuity estimates of how much real federal fraud sentences jump at each USSG §2B1.1 loss-table step, built from the U.S. Sentencing Commission's public individual datafiles. Built for a white-collar defense lawyer, law student or policy researcher at the moment they ask: "If the loss is $560k instead of $540k, does the sentence actually change, or only the guideline range?"

## 1. The demo (acceptance test)

This 60-second walkthrough is how we know it works. Do not call the build done
until every step below works on real data.

1. `python -m losscliff fetch --years 2016-2025`  →  downloads each fiscal year's
   individual-offender CSV zip from ussc.gov (cached in `data/raw/`), pulls only the
   needed columns, and prints one line per year, e.g.
   `FY2024: 61,678 rows → 5,015 §2B1.1 → 3,950 with usable dollar loss`.
   The FY2024 figures are real and were checked against the file. Writes `data/cases.parquet`.
2. `python -m losscliff estimate`  →  prints a 15-row table, one row per loss threshold
   ($6,500 … $550,000,000): n left / n right, **designed jump** (change in guideline-minimum
   months at the cutoff), **actual jump** (local-linear RD estimate of the change in imposed prison
   months, 95% CI), **pass-through %** (actual ÷ designed), a **bunching** flag (more cases just
   below the cutoff than just above), and a **variance** flag (sentence dispersion within the
   bracket is unusually wide). Also writes `out/estimates.csv`.
3. `python -m losscliff report`  →  writes `out/report.html`, a single file you can open offline:
   a "cliff chart" (designed vs actual jump for every boundary, side by side), then one panel per
   boundary with binned-mean sentence vs log(loss/threshold), the fitted lines on each side, and
   a histogram underneath for the density/bunching check.
4. The "huh, neat" moment: on the $550,000 panel you can see the gap. The guideline minimum
   jumps by design, and the panel shows whether imposed sentences follow it, how much of the
   jump passes through, and whether loss amounts pile up just under the line, which is a sign
   of plea-negotiated loss figures. Every panel footer links the codebook and the manual
   page the threshold comes from.

## 2. Scope

**In (day one):**
- Fetch + column-extract FY2016–FY2025 individual datafiles (CSV), cached and idempotent.
- Clean sample: `GDLINEHI == "2B1.1"`, usable dollar `LOSSHI`, `LOSSPROB == 0`, `AMENDYR` 2015–2024 (one loss table, listed below).
- Sharp RD at each of the 15 thresholds: local-linear fit with a triangular kernel in x = ln(loss / threshold), using a bandwidth that never crosses the midpoint (in log space) to the neighbouring threshold. Outcomes: imposed prison months (`SENSPLT0`) and guideline minimum (`XMINSOR`).
- Bunching check: count ratio in a narrow band just below vs just above each cutoff, plus a binned histogram.
- Per-bracket variance flag: within-bracket SD (or IQR) of `SENSPLT0 − XMINSOR`, flagged when it is > 1.5× the median across brackets.
- CLI (`fetch`, `estimate`, `report`) + one static HTML report + `estimates.csv`.

**Out — do NOT build these:**
- Web app, server, dashboard hosting, user accounts, settings UI.
- Pre-2015 data and the 2001–2015 loss table (needs a second threshold set; maybe later).
- The newer inflation-adjusted table in the current manual ($9,000 … $750M). No sentenced cases under it exist in FY2016–FY2025 data.
- Covariate-adjusted RD, fuzzy RD, IV, donut-hole sensitivity grids, bandwidth optimizers beyond one simple rule. (A single `rdrobust` cross-check at one boundary is OK if it installs cleanly; skip it if it doesn't.)
- Splitting by district, judge, race/sex, economic-crime offense type, or circuit.
- The SAS/SPSS files, the Economic Crime Offense Type files (they hold only an offense-type code, no dollars), or any other USSC special-coding datafile.
- Any LLM summary or "explain this chart" text.
- PDF export, a Shiny or Streamlit version, a notebook as the deliverable.
- Automatic re-download when USSC posts a new year.

## 3. Stack (and why)

| Piece | Choice | Why |
|-------|--------|-----|
| Language | Python 3.12 | The user is fluent; the whole pipeline (fetch, stats, HTML) fits in one language. |
| CSV extraction | `pyarrow.csv` with `ConvertOptions(include_columns=[...])`, all columns read as strings | The files are about 1.7 GB with 27,265 columns. pyarrow parses only the columns you ask for, and fast. Fall back to stdlib `csv` streaming if memory spikes. |
| Storage | One Parquet file (`data/cases.parquet`) | Small (roughly 40k rows × 12 cols), typed, and quick to reload. Easy to inspect with DuckDB/SQL if wanted. |
| Data wrangling | pandas | Familiar, and the dataset is small after extraction. |
| RD estimation | statsmodels WLS (triangular weights, HC1 SEs), hand-rolled | Transparent: each estimate is about 20 lines a reviewer can read. No black-box package. |
| Charts + report | Plotly (offline, `include_plotlyjs="inline"` or CDN) inside one f-string HTML template | One self-contained file with hover and zoom for the panels. No template engine needed. |
| CLI | `argparse` in `losscliff/__main__.py` | Three subcommands. A CLI framework would be overkill. |
| Tests | pytest | Core math on synthetic fixtures. |
| HTTP | `requests` with a descriptive User-Agent | Plain static zip downloads. |

Keep it boring. No framework unless the form requires one.

## 4. Verified data sources

### USSC Individual Offender Datafiles (CSV), FY2016–FY2025
- **Endpoint:** `https://www.ussc.gov/sites/default/files/zip/opafy{YY}nid_csv.zip`
  (e.g. `opafy24nid_csv.zip`). Index page with every link: `https://www.ussc.gov/research/datafiles/commission-datafiles`.
  The index lists `opafy13nid_csv.zip` … `opafy25nid_csv.zip`, including `opafy20nid_csv.zip` and `opafy21nid_csv.zip`.
  **Scrape the hrefs from the index page rather than hard-coding names**, because the SAS zips have irregular names such as `opafy16-nid.zip`.
- **Auth:** none.
- **Rate limit:** none documented. The server sets F5 cookies but did not challenge a plain `curl`. Be polite: sequential downloads, cache in `data/raw/`, never re-download a zip that's already there.
- **Verified on 2026-11-18:**
  - Index page `HTTP/1.1 200 OK` (Drupal, `Cache-Control: max-age=10800`).
  - `opafy24nid_csv.zip`: `200`, 21,246,992 bytes zipped → one file `opafy24nid.csv`, 1,720,273,516 bytes, 61,679 lines (header + 61,678 cases), **27,265 columns**, quoted header names.
  - Column positions in FY2024 (they **differ by year**, so always select by name): `SENTTOT` 684, `SENSPLT0` 685, `USSCIDN` 691, `LOSSPROB` 794, `NOCOMP` 814, `XCRHISSR` 875, `XFOLSOR` 877, `AMENDYR` 879, `XMAXSOR` 1390, `XMINSOR` 1391, `LOSS1` 25777, `GDLINEHI` 26497, `LOSSHI` 26498.
  - FY2024 §2B1.1 rows (`GDLINEHI == "2B1.1"`): **5,015**. `LOSSHI`: 3,954 dollar amounts, 908 = `9999999997` (some loss, amount unspecified), 152 = 0, 1 blank. `LOSSPROB`: 5,011 = 0, 4 = 1. Usable (dollar & LOSSPROB = 0): **3,950**. `AMENDYR`: 2016 (6), 2018 (844), 2023 (4,165). `SENSPLT0`: 1,067 zeros (probation / no prison), 0 blanks.
  - Trimmed sample (columns extracted from FY2024):
    ```
    USSCIDN,GDLINEHI,LOSSHI,LOSSPROB,SENSPLT0,XFOLSOR,XCRHISSR,AMENDYR,XMINSOR,XMAXSOR,NOCOMP
    2828330,"2B1.1",99,0,0,4,1,2018,0,6,1
    2828347,"2B1.1",2000000,0,24,22,1,2018,41,51,1
    2828351,"2B1.1",9999999997,0,72,30,1,2018,97,121,1
    2828353,"2B1.1",677965,0,0,19,1,2018,30,37,1
    2828376,"2B1.1",4259376,0,64,27,1,2018,70,87,1
    2828541,"2B1.1",1003,0,21.52,4,3,2018,0,6,1
    ```
  - Raw binned means around the $550k cutoff, FY2024 only (dollar loss, LOSSPROB = 0, no controls). This is a sanity check, not a result:
    ```
    $500k–550k  n=69  mean prison=24.7 mo
    $550k–600k  n=53  mean prison=30.7 mo
    ```
- **Codebook (verified 200):** `https://www.ussc.gov/sites/default/files/pdf/research-and-publications/datafiles/USSC_Public_Release_Codebook_FY99_FY25.pdf` (revised April 7, 2026). Key definitions:
  - `LOSS1-LOSSX / LOSSHI`: "The dollar amount of loss for which the sentenced individual is held responsible … rounded off to the nearest whole dollar." Codes are 0 = no loss and 9,999,999,997 = some loss, amount not specified. "All guideline variables available FY2012-present."
  - `LOSSPROB`: 1 = "unresolved problem between the loss held accountable amount and SOC range … Analyses using loss may be advised to screen on this variable."
  - `SENSPLT0`: total prison sentence in months, with probation = 0, and life capped at 470.
- **Gotchas:**
  - A 1.7 GB CSV per year. Unzip to a temp file, extract the columns, delete the CSV, and keep the zip.
  - In FY2024, a plain comma split gave a consistent 27,265 fields on every §2B1.1 row, but use a real CSV parser anyway.
  - Read every column as a string, then cast. `SENSPLT0` has decimals (e.g. `21.52`, `0.03` = time served, a few days).
  - Exact threshold amounts belong to the **lower** bracket (the table says "More than $X"). FY2024 already has 11 cases at exactly $40k/$95k/$150k/$250k/$550k/$1.5M. Treat heaping at round numbers as a finding to show, not noise to hide.

### USSG §2B1.1(b)(1) loss table (Guidelines Manual, Nov 1, 2024)
- **Endpoint:** `https://www.ussc.gov/sites/default/files/pdf/guidelines-manual/2024/GLMFull.pdf` (verified 200, 4,582,032 bytes, page 86).
- **Auth:** none.
- **Verified on 2026-11-18**, text as extracted:
  ```
  (A) $6,500 or less            no increase
  (B) More than $6,500          add 2
  (C) More than $15,000         add 4
  (D) More than $40,000         add 6
  (E) More than $95,000         add 8
  (F) More than $150,000        add 10
  (G) More than $250,000        add 12
  (H) More than $550,000        add 14
  (I) More than $1,500,000      add 16
  (J) More than $3,500,000      add 18
  (K) More than $9,500,000      add 20
  (L) More than $25,000,000     add 22
  (M) More than $65,000,000     add 24
  (N) More than $150,000,000    add 26
  (O) More than $250,000,000    add 28
  (P) More than $550,000,000    add 30.
  ```
  This table took effect Nov 1, 2015 and still applied in the Nov 2024 manual. Hard-code it in `losscliff/table.py`, keyed by manual year, and restrict to `AMENDYR` 2015–2024.
- **Gotcha:** the **current** online manual (`/guidelines/2026-guidelines-manual/annotated-2026-chapter-2-c`, checked 2026-11-18) has a newer, inflation-adjusted table: "More than $9,000", "$20,000", "$55,000", "$150,000", "$200,000", "$350,000", "$750,000", "$2,000,000" … "$750,000,000". Do **not** use it for this data. Assert that no row with `AMENDYR ≥ 2025` makes it into the sample.

## 5. Build order

Each milestone ends with something you can run. Run it before moving on.

- **M0 — Spike (15 min):** download `opafy24nid_csv.zip`, extract the 12 columns above by name with pyarrow, filter to §2B1.1, and print the counts. They must match: 5,015 §2B1.1 / 3,950 usable. Print peak memory and wall time. If pyarrow struggles with 27k columns, switch to stdlib `csv` streaming now.
- **M1 — Core loop, ugly (≈2.5 h):** for FY2024 alone: assign the bracket from `LOSSHI` with the table, compute x = ln(loss/threshold) for each cutoff, and run local-linear RD on `SENSPLT0` and on `XMINSOR` with a triangular kernel and neighbour-midpoint bandwidth. Print the 15-row table to stdout.
- **M2 — Real data path (≈1.5 h):** scrape the index for `opafy{16..25}nid_csv.zip`, then download, extract and cache all years into `data/cases.parquet` with an `FY` column, applying the `AMENDYR` 2015–2024 filter. Re-run `estimate` on the pooled data, add the bunching ratio and the variance flag, and write `out/estimates.csv`.
- **M3 — Edge cases & errors (≈1.5 h):** boundaries with too few cases (e.g. n < 30 per side at $250M/$550M), which should print "insufficient data" rather than an estimate. Handle a failed or partial download (resume or clean retry, with a clear message), a missing column in some year (name it and the year), and the sentinel values 0 / 9999999997 / blank. Add pytest tests (see below).
- **M4 — Polish (≈1.5 h):** build `report.html`: the cliff chart, per-boundary panels, a methods box (sample filters, bandwidth rule, kernel, "this is descriptive, not causal advice"), source links on every panel, and the run date. Write a README with install steps, the three commands, a screenshot of the $550k panel, and a limitations section.

## 6. Quality bar

- Tests for the core logic:
  - `bracket_for(loss)` at exact thresholds (550,000 → +12; 550,001 → +14), at 0, and at the sentinel.
  - `running_var(loss, cutoff)` sign and scale.
  - `bandwidth_for(cutoff)` never reaches past the log-midpoint to a neighbouring threshold.
  - `rd_estimate()` recovers a known jump (e.g. 6.0 ± 0.5) on synthetic data with a planted discontinuity, and gives ~0 on data with none.
  - `bunching_ratio()` on a synthetic heap.
  - The sample filter drops `LOSSPROB == 1`, `LOSSHI ∈ {0, 9999999997, blank}`, and out-of-range `AMENDYR`.
- No placeholder or mock data in the final demo. Fixtures are for tests only.
- Graceful failures:
  - If ussc.gov is down or a zip 404s, name the year and URL, then continue with the cached years.
  - With no cached data, say "run `fetch` first."
  - A boundary with thin data shows "insufficient data (n_left=…, n_right=…)", never a number.
- Legal-data correctness rule: every estimate shows its n and CI. The report states the sample filters and the manual year of the loss table, and links the codebook PDF and the Guidelines Manual page so a reader can verify each threshold. Label results as descriptive associations at the cutoff, not legal advice and not a prediction for any individual case.

## 7. How to work

- Start by writing a short plan. Then build milestone by milestone.
- After each milestone, run it and show the output.
- Only stop to ask me if something in "Out" starts to look required.
- Commit after each milestone if this is a git repo.

## 8. Prior art (stay different from these)

| Existing tool | What it does | How this build differs |
|---------------|--------------|------------------------|
| [USSC Sourcebook Table E-6 / Interactive Data Analyzer](https://www.ussc.gov/sites/default/files/pdf/research-and-publications/annual-reports-and-sourcebooks/2024/TableE6.pdf) | Descriptive tables of loss-amount categories vs sentence length for §2B1.1 offenders. | Uses continuous dollar loss instead of bins, estimates a jump at each boundary, and adds bunching and per-bracket variance flags. |
| [Yale Law Journal note, "Fifty Shades of Gray"](https://yalelawjournal.org/note/fifty-shades-of-gray-sentencing-trends-in-major-white-collar-cases) | Compares post-Booker sentences with loss-driven guideline ranges in major white-collar cases. | Covers all loss levels, not just high-loss cases, and tests explicitly for discontinuities at each table step. |
| [USSC Commission Datafiles (incl. Economic Crime Offense Types)](https://www.ussc.gov/research/datafiles/commission-datafiles) | Official raw data and codebooks. | Raw data only. This build is the reproducible analysis on top of it. |
| [Federal Defender testimony on the loss table (Dena, 2024)](https://src.fd.org/sites/src/files/blog/2024-03/20240227%20Daniel%20Dena%20Witness%20Statement%20-%20Loss.pdf) | Argues the loss table lacks an empirical basis. | Advocacy. This build produces the estimate that argument is about. |

The wedge, in one sentence: an open, reproducible, boundary-by-boundary RD and bunching estimate of how much each §2B1.1 loss step actually moves imposed sentences, compared with what the guidelines designed, with a variance flag per bracket.
