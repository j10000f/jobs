# Academic job source mirrors

Daily GitHub Actions collector rendering public job feeds as static HTML (no JavaScript): https://j10000f.github.io/jobs/

| Page | Data |
| --- | --- |
| uni-graz.html | Uni Graz public JSON API, original fields |
| tu-graz.html | TU Graz public JSON API, original fields |
| eco-evo.html | EcoEvoJobSearcher weekly RSS (not faculty-only) |
| csh.html | CSH Personio XML (only if employer enabled feed) |
| iiasa.html | IIASA onlyfy public HTML job links (not JSON) |
| tu-wien.html | Latest TISS Gazette JSON where available (not a full vacancy API) |
| status.json | Last run source counts, timestamps, errors |

**Enable GitHub Pages:** Repository Settings → Pages → Build and deployment → Source: **GitHub Actions**.

The workflow [publish.yml](.github/workflows/publish.yml) runs daily at approximately 05:17 UTC, on source changes, or manually under Actions. No credentials or Python dependencies required. To test locally run `python3 scripts/build.py`. Results are written to `public/`.

Collectors preserve source fields and rows when recognized; do not filter by career stage or relevance. If a feed fails, its page clearly states the extraction failure, never reporting zero vacancies. Verify deadlines and official job conditions with the recruiting institution. TISS data is gazette issue metadata, not a conventional job list.
