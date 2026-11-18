Three ideas made it through, and none is clearly ahead of the others (20, 19 and 17 points). All three need no API keys or accounts.

## Fraud Loss Cliff  ·  `fraud-loss-cliff`
Check whether federal fraud sentences really jump at each step of the sentencing guidelines' loss table (USSG §2B1.1, where a bigger dollar loss means a longer recommended sentence), using public US Sentencing Commission data.

**For / when:** You, reading about white-collar sentencing reform, maybe for a law-school essay, and wondering whether the dollar-loss table actually drives prison time or judges ignore it.
**Day-one version does:**
- Downloads one to three years of the Sentencing Commission's individual offender data. Its Economic Crime file is limited to fraud-guideline cases.
- Plots each defendant's loss amount (log scale) against months in prison, with the loss-table step boundaries drawn on the chart.
- Measures the size of the sentence jump right at each step. Economists call this a regression-discontinuity estimate.
- Flags the loss brackets where judges most often sentence below the guidelines.
- Uses the right version of the loss table for each case, because the table changed in 2001 and 2015.

**Sharp edge:** It doesn't just describe the data. It tests whether the table's arbitrary dollar cutoffs show up as real jumps in prison time. It's also timely, because the Commission has reportedly just voted to collapse the table to 8 steps.
**Prior art** (ADJACENT, medium confidence · 9 queries across 7 sources plus the web):
- [USSC Sourcebook Table E-6](https://www.ussc.gov/sites/default/files/pdf/research-and-publications/annual-reports-and-sourcebooks/2024/TableE6.pdf): sentence length by loss bracket. It only shows averages per bracket and does no test at the cutoffs.
- [Yale Law Journal note, "Fifty Shades of Gray"](https://yalelawjournal.org/note/fifty-shades-of-gray-sentencing-trends-in-major-white-collar-cases): compares actual sentences to guideline ranges, but only in big white-collar cases, with no cutoff-by-cutoff test.
- [USSC Commission Datafiles](https://www.ussc.gov/research/datafiles/commission-datafiles): the raw data this would use, with no analysis included.

**Riskiest assumption:** The data has a dollar loss amount for each case, not just the bracket. The scout found signs it does, rounded and with an "unspecified" code, but couldn't open the codebook to confirm.
**Access:** open: no keys needed
**Scores:** novelty 4 · would-use 4 · demo 4 · feasibility 3 · skill fit 5 = 20/25 · key penalty −0 = **20**

## US News Law Rebuild  ·  `usnews-law-rebuild`
For the law schools on your list, recompute the US News score from public American Bar Association (ABA) data and show how much of each rank comes from the reputation surveys.

**For / when:** You, this application cycle, deciding whether a school's rank reflects outcomes or reputation.
**Day-one version does:**
- Loads the ABA's required disclosures for each school (admissions, employment, bar passage). A cleaned CSV of the admissions and bar data exists on GitHub.
- Applies US News's published weights for the current methodology to the public parts only.
- Takes the peer reputation scores from the 2026–27 list on TaxProf Blog.
- Prints a table and chart for your 10–20 schools: how much of each rank the public data explains and how much reputation adds.

**Sharp edge:** It reverse-engineers the scoring rule applicants use to choose schools, then separates out the part that is only reputation.
**Prior art** (ADJACENT, medium confidence · 8 queries across 7 sources plus the web):
- [Derek Muller's projected rankings](https://derektmuller.substack.com/p/updated-projected-2026-2027-usnwr): predicts the overall rank from ABA data (mostly paywalled). It doesn't split out reputation per school.
- [Spivey Consulting explainer](https://www.spiveyconsulting.com/blog-post/how-does-us-news-actually-rank-law-schools): explains the method but doesn't calculate anything per school.
- [LSD.law rankings page](https://lsd.law/law-school-rankings/usnwr): shows published ranks and reputation scores without recomputing them.

**Riskiest assumption:** Enough of US News's adjustments are public that the public-only score is close. Some of the scaling isn't disclosed, so the result will be approximate.
**Access:** open: no keys needed
**Scores:** novelty 3 · would-use 5 · demo 4 · feasibility 3 · skill fit 4 = 19/25 · key penalty −0 = **19**

## BSA Penalty Curve  ·  `bsa-penalty-curve`
Match FinCEN's anti-money-laundering (Bank Secrecy Act) penalties against bank size, so you can tell whether a new fine is big or small for that bank.

**For / when:** You, the day a new FinCEN fine on a bank makes the news, wondering whether it's actually harsh for a bank that size.
**Day-one version does:**
- Builds a CSV of the roughly 30–50 FinCEN bank penalties, with amounts typed in by hand from the orders.
- Looks up each bank's total assets in the quarter before the penalty, using the FDIC's free bank-data API.
- Fits a curve of penalty against bank size.
- Has one command, `bsa-curve place "<bank>" <amount> <date>`, that prints where a new fine falls relative to past ones.

**Sharp edge:** It judges penalties against bank size instead of raw dollars. The scout found no tool or study that does this match.
**Prior art** (ADJACENT, medium confidence · 8 queries across 7 sources plus the web):
- [Violation Tracker (FinCEN page)](https://violationtracker.goodjobsfirst.org/agency/FINCEN): lists penalties in dollars, with no adjustment for bank size.
- [BankersOnline anti-money-laundering penalties](https://bankersonline.com/penalty/penalty-type/bsa-aml-civil-money-penalties?page=1): a plain list, with no bank-size match or curve.
- [CRS R45076](https://www.everycrsreport.com/reports/R45076.html): cites a single 2018 figure that a third of these penalties were over 10% of the bank's capital.

**Riskiest assumption:** About 30–50 data points are enough for a meaningful curve. Willfulness may drive penalties more than size, and other regulators often fine the same bank for the same conduct.
**Access:** open: no keys needed
**Scores:** novelty 4 · would-use 3 · demo 3 · feasibility 3 · skill fit 4 = 17/25 · key penalty −0 = **17**

Runners-up: none came close. The red-team review cut `imsa-bop-reverse` (too much PDF and timing-file parsing for one day) and `nascar-rating-rebuild` (the Driver Rating formula is already public).

I saved all 21 ideas from this run, including the 18 that were cut, so future runs will skip them.

What next?
- `/kiln:brief <slug>` to write the build prompt
- Reject one with a quick reason. I'll run `kiln ledger reject <slug> --reason "…"`, and the reason goes into your taste log.
- Reroll (`/kiln:idea` again, optionally with a theme)