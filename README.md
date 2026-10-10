# Academic job source mirrors

Daily GitHub Actions collector rendering public job feeds as static HTML (no JavaScript): https://j10000f.github.io/jobs/

| Page | Data |
| --- | --- |
| uni-graz.html | Uni Graz public JSON API, original fields |
| tu-graz.html | TU Graz public JSON API, original fields |
| eco-evo.html | EcoEvoJobSearcher weekly RSS (not faculty-only) |
| tu-wien.html | Latest TISS Gazette JSON where available (not a full vacancy API) |
| status.json | Last run source counts, timestamps, errors |

**Directly monitored, without mirrors:** [IIASA onlyfy](https://iiasa.onlyfy.jobs/en) and [CSH Personio](https://csh.jobs.personio.com/?language=de). Both are readable through the ChatGPT web reader.

**Enable GitHub Pages:** Repository Settings → Pages → Build and deployment → Source: **GitHub Actions**.

The workflow [publish.yml](.github/workflows/publish.yml) runs daily at approximately 05:17 UTC, on source changes, or manually under Actions. No credentials or Python dependencies required. To test locally run `python3 scripts/build.py`. Results are written to `public/`.

Collectors preserve source fields and rows when recognized; do not filter by career stage or relevance. If a feed fails, its page clearly states the extraction failure, never reporting zero vacancies. Verify deadlines and official job conditions with the recruiting institution. TISS data is gazette issue metadata, not a conventional job list.

## Directly readable job portals (not mirrored)

- [Complexity Science Hub Personio](https://csh.jobs.personio.com/?language=de) — readable directly by ChatGPT's web reader.
- [IIASA onlyfy](https://iiasa.onlyfy.jobs/en) — readable directly by ChatGPT's web reader.

These two sites are deliberately excluded from the GitHub Pages collector and HTML index. Old `csh.html` or `iiasa.html` pages, if cached from earlier deployments, are not maintained.
