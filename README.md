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

