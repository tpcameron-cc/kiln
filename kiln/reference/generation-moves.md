# Generation moves

Use several different moves per run; never generate the whole pool with one
move. Combine at least one seed ingredient with at least one profile fact in
every idea. The examples assume a sample profile (works in consumer law, follows
motorsport and sim racing, likes audio gear, writes Python/SQL). Swap in the
real profile's facts when you use a move.

### 1. Collide a seed data source with an interest
Take a `data_sources` draw and force it into a profile interest.
> NHTSA recalls API × car shopping → paste a Facebook Marketplace listing URL,
> get open recalls + complaint clusters for that exact VIN year/trim before you drive out.

### 2. Make an invisible thing visible
Something that happens, matters, and can't be seen.
> NASCAR live feed → a terminal strip that shows the *pit-cycle* undercut in real
> time: who gained positions purely in the pits this run.

### 3. Invert the workflow
Start from the output people want and work backward.
> Instead of searching CourtListener for cases, write the motion first; the tool
> lists every case citation in your draft that has since been reversed or questioned.

### 4. Port a professional tool to a hobby (or the reverse)
> Code-review "diff" for iRacing `.sto` setups: show what changed between two
> setups and which handling direction each change pushes.
> Reverse: sim-racing "delta bar" for a settlement negotiation — live gap between
> current offer and the creditor's historical settle percentage.

### 5. The most annoying 5 minutes
Find a weekly chore in the profile and kill exactly those 5 minutes.
> Every Monday, checking which creditors changed collection-agency assignment →
> a watch on state debt-buyer license lists that emails only the diffs.

### 6. Turn a boring public dataset into a delightful artifact
> FRED + BLS → a printable one-page "what $100 meant" poster for the year you were born.

### 7. Build the missing CLI for a GUI-only site
> `imsa results <race>` that pulls the Al Kamel timing PDFs/CSVs and prints stint
> tables and class gaps in the terminal.

### 8. The expert's secret spreadsheet
What does a pro in the user's field quietly track in Excel?
> Debt-relief negotiators track "creditor X settles at Y% after Z months". A local
> SQLite + CLI that logs offers and predicts the next counter from your own history.

### 9. Cross the format of one domain with the content of another
> Law-school case briefs as Anki cards; motorsport stint charts drawn as
> Gantt charts in an `.ics` calendar; SEC Form 4 filings as a "box score".

### 10. Join two public datasets nobody joins
> OFAC SDN list × FAA aircraft registry: aircraft whose registered owner name
> fuzzy-matches a sanctioned entity.

### 11. Show the change, not the state
> Federal Register: a daily diff of *proposed → final* rule text for CFPB debt-collection rules.

### 12. The "second opinion" tool
Check someone else's work against a primary source.
> Paste a collection letter → flags FDCPA/Reg F timing and validation-notice
> elements that are missing, each with the exact CFR cite.

### 13. A countdown for something real
> The statute-of-limitations clock for each consumer debt by state + last-payment
> date, exported as calendar events.

### 14. Measure what people only guess at
> Headphone frequency-response CSVs (AutoEq) → "which of my headphones is
> closest to my car's audio system" given an REW measurement of the car.

### 15. Capture something that disappears
> Archive daily NASCAR penalty reports and DOJ press-release edits via the Wayback CDX API
> so you can see what was quietly changed.

## Pool hygiene

- No two ideas in the pool may share both the same data source *and* the same form.
- At least a third of the pool should use something other than a CLI or web dashboard.
- At least a third should come from a domain *not* in the profile (the seeds supply these).
- Write each pool idea as a single line: `name — who/when — what it does — the sharp edge`.
