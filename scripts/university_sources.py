"""University source collectors for public vacancy indices (no sign-in or anti-bot bypass).

All parsers preserve returned source data. Secondary pages are explicitly identified.
"""
import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlencode, urlparse
from urllib.request import Request, urlopen


class AnchorReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.cur = None
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.cur = [dict(attrs).get("href", ""), []]
    def handle_data(self, data):
        if self.cur is not None:
            self.cur[1].append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.cur is not None:
            self.links.append((self.cur[0], " ".join("".join(self.cur[1]).split())))
            self.cur = None


def get_bytes(url, data=None, timeout=35):
    req = Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AcademicJobsMirror/1.0; https://github.com/j10000f/jobs)",
        "Accept": "application/json,text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en,de;q=0.9,fr;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urlopen(req, timeout=timeout) as r:
        blob = r.read(16_000_001)
    if len(blob) > 16_000_000:
        raise ValueError("Response size exceeds safety limit")
    return blob


def prospective_rows(medium_id):
    """Observed official Prospective /public/v1/medium/{id}/jobs endpoint.
    Paginate by offset, never conflate a first page with complete coverage.
    """
    base = f"https://ohws.prospective.ch/public/v1/medium/{medium_id}/jobs"
    offset = 0
    page_size = 96
    rows = []
    total = None
    seen = set()
    for _ in range(40):
        query = urlencode({"lang": "en", "offset": offset, "limit": page_size})
        data = json.loads(get_bytes(base + "?" + query).decode("utf-8-sig"))
        chunk = data.get("jobs")
        if not isinstance(chunk, list) or not isinstance(data.get("total"), int):
            raise ValueError("Prospective API returned an unexpected data structure")
        total = data["total"]
        for entry in chunk:
            if not isinstance(entry, dict):
                raise ValueError("Unexpected Prospective job object")
            identifier = str(entry.get("id") or entry.get("viewkey") or "")
            if not identifier or identifier in seen:
                continue
            seen.add(identifier)
            # Avoid fabricating per-job URLs; index and job ID are retained for verification.
            rows.append(entry)
        if len(rows) >= total:
            break
        if not chunk:
            raise ValueError(f"Prospective incomplete: got {len(rows)} of {total}")
        offset += len(chunk)
    if total is None or len(rows) != total:
        raise ValueError(f"Prospective incomplete: got {len(rows)} of {total}")
    return rows


def basel_rows(base="https://jobs.unibas.ch/?lang=en"):
    """Reproduce Basel's public POST form pagination offset=0,10,...
    The HTML has <a href=.../offene-stellen/...> official job adverts.
    """
    results = []
    seen = set()
    for page in range(60):
        payload = urlencode({"offset": page * 10, "limit": 10, "lang": "en"}).encode("utf-8")
        source = get_bytes(base, data=payload).decode("utf-8", "replace")
        parser = AnchorReader()
        parser.feed(source)
        entries = []
        for href, title in parser.links:
            link = urljoin(base, html.unescape(href))
            if "/offene-stellen/" not in urlparse(link).path or not title:
                continue
            if link in seen:
                continue
            seen.add(link)
            entries.append({"Title": title, "OriginalJobUrl": link})
        if not entries:
            if page == 0:
                raise ValueError("No Basel listings found: not claiming zero jobs")
            break
        results.extend(entries)
        if len(entries) < 10:
            break
    else:
        raise ValueError("Basel listings have more than the permitted 60 pages")
    return results


def hu_berlin_rows():
    """Humboldt's public Stellenticket page, including all university postings.
    Stellenticket also hosts outside employers; these are separate leads and the
    employer must be checked by following each original advert.
    """
    base = "https://hu-berlin.stellenticket.de/de/offers/"
    results = []
    seen = set()
    for offset in range(0, 1000, 100):
        query = urlencode({"jobs_science[per_page]": 100, "jobs_science[offset]": offset})
        source = get_bytes(base + "?" + query).decode("utf-8", "replace")
        anchors = AnchorReader()
        anchors.feed(source)
        count = 0
        for href, label in anchors.links:
            link = urljoin(base, html.unescape(href))
            match = re.search(r"/(?:de|en)/offers/(\d+)/", link)
            if not match or len(label) < 10 or not re.search(r"[A-Za-zÄÖÜäöüß]", label):
                continue
            job_id = match.group(1)
            if job_id in seen:
                continue
            seen.add(job_id)
            results.append({
                "Id": job_id, "Title": label,
                "OriginalJobUrl": link,
                "EmployerNote": "Unfiltered Stellenticket list includes other employers. Verify employer in original ad.",
            })
            count += 1
        if count < 100:
            break
    else:
        raise ValueError("Humboldt Stellenticket pagination exceeded scan limit")
    if not results:
        raise ValueError("No Stellenticket job entries parsed")
    return results


def lausanne_rows():
    """Secondary index; each extracted link targets original UNIL SuccessFactors ad.
    Explicitly a secondary lead source, not an exhaustive university index.
    """
    base = "https://joblens.ch/unil"
    rows, seen = [], set()
    for page in range(1, 15):
        url = base if page == 1 else base + "?" + urlencode({"page": page})
        source = get_bytes(url).decode("utf-8", "replace")
        matched = 0
        for m in re.finditer(
            r'<a\s+class="job-title"[^>]*>(.*?)</a>\s*<a\s+class="job-open"\s+href="([^"]+)"',
            source, re.I | re.S):
            title = " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split())
            href = html.unescape(m.group(2))
            ident = re.search(r"career_job_req_id=(\d+)", href)
            if not title or not ident or "company=universitdP" not in href:
                continue
            if ident.group(1) in seen:
                continue
            seen.add(ident.group(1))
            rows.append({
                "Id": ident.group(1), "Title": title,
                "OriginalJobUrl": href,
                "Coverage": "Secondary index (joblens); original UNIL SuccessFactors ad must be checked",
            })
            matched += 1
        if not matched:
            break
    if not rows:
        raise ValueError("No usable UNIL original advertisement links in secondary index")
    return rows


def konstanz_rows():
    """Render University's official B-ITE widget, which has no jobs in raw HTML."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("The B-ITE public widget needs Playwright; install chromium in workflow") from e
    url = "https://stellen.uni-konstanz.de/site/v2/de/professuren.html"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = browser.new_page(locale="de-DE", user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector(".bite-jobs-list-table, .bite-jobs-list--empty", timeout=40000)
            page.wait_for_timeout(1300)
            anchors = page.locator(".bite-jobs-list--titel-link")
            rows=[]
            for i in range(anchors.count()):
                a = anchors.nth(i)
                title = a.locator("strong").inner_text() if a.locator("strong").count() else a.inner_text()
                href = a.get_attribute("href")
                if title.strip() and href:
                    rows.append({
                        "Title": title.strip(),
                        "OriginalJobUrl": urljoin(url, href),
                        "ListingRow": a.locator("xpath=ancestor::tr").inner_text()[:650],
                    })
            if not rows:
                # The B-ITE listing was loaded; if it genuinely has no ads, return zero.
                if page.locator(".bite-jobs-list--empty").count():
                    return []
                raise ValueError("B-ITE widget loaded but did not expose any vacancy links")
            return rows
        finally:
            browser.close()
