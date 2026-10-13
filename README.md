# Academic job source mirrors

Daily GitHub Actions collector rendering public job feeds as static HTML (no JavaScript): https://j10000f.github.io/jobs/

| Page | Data |
| --- | --- |
| uni-graz.html | Uni Graz public JSON API, original fields |
| tu-graz.html | TU Graz public JSON API, original fields |
| eco-evo.html | EcoEvoJobSearcher weekly RSS (not faculty-only) |
| tu-wien.html | Current TU Wien vacancies parsed from the embedded `JobList` JSON | 
| tu-wien-gazette.html | Latest TISS Gazette metadata (fallback) |
| konstanz.html | Konstanz B-ITE professorship widget rendered via Chromium |
| hu-berlin.html | Stellenticket university/research listings; may include non-HU employers |
| uzh.html | UZH official Prospective API, paginated |
| unibe.html | University of Bern official Prospective API, paginated |
| unibas.html | University of Basel official ATS listings, paginated |
| unil.html | UNIL SuccessFactors original postings discovered via secondary joblens index; **partial coverage** |
| status.json | Per-source counts, timestamp, errors and coverage limitations |

**Directly monitored, without mirrors:** [IIASA onlyfy](https://iiasa.onlyfy.jobs/en) and [CSH Personio](https://csh.jobs.personio.com/?language=de). Both are readable through the ChatGPT web reader.

**Enable GitHub Pages:** Repository Settings → Pages → Build and deployment → Source: **GitHub Actions**.

The workflow [publish.yml](.github/workflows/publish.yml) runs daily at approximately 05:17 UTC, on source changes, or manually under Actions. No credentials or Python dependencies required. To test locally run `python3 scripts/build.py`. Results are written to `public/`.

Collectors preserve source fields and rows when recognized; do not filter by career stage or relevance. If a feed fails, its page clearly states the extraction failure, never reporting zero vacancies. Verify deadlines and official job conditions with the recruiting institution. `tu-wien.html` extracts the `Jobs` array embedded in TU Wien's `/Jobs` page (not the unrelated Matomo analytics request). It checks `TotalJobsCount` before treating results as complete. `tu-wien-gazette.html` is Gazette issue metadata, not a conventional job list.

## Directly readable job portals (not mirrored)

- [Complexity Science Hub Personio](https://csh.jobs.personio.com/?language=de) — readable directly by ChatGPT's web reader.
- [IIASA onlyfy](https://iiasa.onlyfy.jobs/en) — readable directly by ChatGPT's web reader.

These two sites are deliberately excluded from the GitHub Pages collector and HTML index. Old `csh.html` or `iiasa.html` pages, if cached from earlier deployments, are not maintained.

## GitHub repository snapshots (web-reader-independent)

The same daily workflow also commits the generated plain HTML pages and `status.json` to an independently maintained **[`data` branch](https://github.com/j10000f/jobs/tree/data)**. This is a machine-readable mirror for ChatGPT's connected GitHub integration even if the `github.io` website cannot be opened by its web reader.

Direct GitHub content links (no GitHub Pages or JavaScript required):

- [University of Graz](https://github.com/j10000f/jobs/blob/data/uni-graz.html)
- [TU Graz](https://github.com/j10000f/jobs/blob/data/tu-graz.html)
- [EcoEvoJobs weekly feed](https://github.com/j10000f/jobs/blob/data/eco-evo.html)
- [TU Wien current vacancies](https://github.com/j10000f/jobs/blob/data/tu-wien.html)
- [TU Wien Gazette backup](https://github.com/j10000f/jobs/blob/data/tu-wien-gazette.html)
- [Source collection status](https://github.com/j10000f/jobs/blob/data/status.json)

For the GitHub connector, use repository `j10000f/jobs`, ref `data`, and the root filename (e.g. `tu-wien.html` or `status.json`). Check `status.json` before interpreting missing or zero rows: an inaccessible upstream source is explicitly an error, not zero vacancies. The `data` branch is **generated automatically** and will overwrite manual edits there. The scraper/workflow source remains on `main`.

### Additional Swiss/German sites

The extra collectors address pages the web reader could not reliably extract. UZH and Bern use publicly served Prospective JSON endpoints (with all pages fetched). Basel uses the public application-form POST pagination. Humboldt Stellenticket exposes server-rendered university listings but also lists outside employers, so verify institutional attribution. Konstanz requires a Chromium-rendered B-ITE widget. Lausanne's original SAP SuccessFactors search is JavaScript-driven; the `unil.html` mirror uses a **third-party index solely for discovery**, retaining links to the original official UNIL advertisements. It is NOT guaranteed exhaustive or current: always verify with UNIL and cross-search official ads.

## Archived ecology digests and email delivery

Commit the **complete HTML email body** to `main` at `digests/YYYY-MM-DD.html` (for example,
`digests/2026-10-19.html`). The file becomes a public webpage at:

`https://j10000f.github.io/jobs/digests/YYYY-MM-DD.html`

The [Pages publishing workflow](.github/workflows/publish.yml) now copies the saved
`digests/*.html` files into the published `public/digests/` directory. It runs
on changes to those files as well as on the existing daily schedule.

The separate [digest-email workflow](.github/workflows/email-digests.yml) runs
only on pushes to `main` that include changed `digests/*.html` paths. It
compares the Git commits before and after the push and emails **only newly
added** files with valid `YYYY-MM-DD.html` filenames, not edits to existing
files. The HTML file is sent as the email's HTML content, with a plain-text
link to its public archive; the subject is
`Academic ecology opportunities — week of YYYY-MM-DD`. If multiple new dated
digests are added in a single push, each receives a separate email.

Configure the repository's **Actions variable** `MAIL_USERNAME` with your Gmail
address (used as both the sender and recipient) and the **Actions secret**
`MAIL_PASSWORD` with a Gmail app password. The email workflow uses Gmail SMTP
over TLS on `smtp.gmail.com:465`; credentials are not committed to GitHub.
A Google account with two-step verification and app-password support is needed.
Failures appear in the Actions job logs.

**Important:** These HTML digests are public. Do not include sensitive or
private information in them. Editing a previously added file updates the Pages
copy but does not send it again. Re-running a successful email workflow run
manually may send duplicate messages. Publication and SMTP sending run in
independent workflows, so the email can arrive before the corresponding Pages
deployment finishes.

