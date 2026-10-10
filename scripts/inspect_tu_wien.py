#!/usr/bin/env python3
"""Read-only inspection of TU Wien's public job listing frontend. Prints no cookies or secrets."""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
import re
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.forms = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "script":
            self.scripts.append((d.get("src",""),d.get("type","")))
        elif tag == "form":
            self.forms.append({"action":d.get("action"),"method":d.get("method")})
        elif tag == "link" and d.get("rel") in ("preload","modulepreload"):
            self.links.append(d.get("href"))
URL = "https://jobs.tuwien.ac.at/Jobs?culture=de"
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; public job listings inspection)", "Accept":"text/html,application/javascript,*/*", "Accept-Language":"de,en;q=0.8"}
def request(url,limit=5_000_000):
    with urlopen(Request(url,headers=HEADERS),timeout=35) as r:
        result=r.read(limit)
        print("FETCH",r.status,r.headers.get("Content-Type"),len(result),r.geturl())
        return result.decode("utf-8","replace")
def excerpts(text, label,patterns,max_occurrences=18):
    seen=set();count=0
    for pat in patterns:
        for m in re.finditer(pat,text,re.I):
            st=max(m.start()-110,0)
            en=min(m.end()+170,len(text))
            value=re.sub(r"\s+"," ",text[st:en])
            if value in seen:continue
            seen.add(value); count+=1
            print("MATCH",label,pat,repr(value[:300]))
            if count>=max_occurrences:return
def main():
    html=request(URL)
    parser=Inspector();parser.feed(html)
    excerpts(html,"HTML-INIT",[r"new JobList",r"PopulateList",r"jobList",r"JobList",r"JobListing",r"ajax",r"Jobs.*Json",r"jobs.*Url"],25)
    print("HAS TABLE TR",html.count("<tr"),"HAS JOB LINKS",len(re.findall(r'/Job/\d+',html,re.I)))
    print("FORMS",parser.forms)
    print("SCRIPTS",parser.scripts[:45])
    excerpts(html,"HTML",[r"/api/",r"fetch\(",r"ajax",r"jobProfiles",r"joblist",r"Job/\d+",r"<tbody",r"jobsTable"],18)
    for src,typ in parser.scripts[:25]:
        if not src:continue
        url=urljoin(URL,src)
        if urlparse(url).netloc not in ("jobs.tuwien.ac.at",):continue
        try:
            script=request(url,2_500_000)
            if "/bundles/jobs/index?" in url:print("COMPLETE_JOB_SCRIPT",repr(script))
            excerpts(script,url,[r"/api/[A-Za-z_/\-]+",r"/Jobs?/[A-Za-z_/\-]+",r"GetJobs",r"GetJob",r"JobList",r"SearchJob",r"\.ajax\(",r"fetch\(",r"/api/",r"GetVacanc",r"JobsFilter"],14)
        except Exception as e: print("SCRIPT_ERROR",url,type(e).__name__,str(e)[:180])
if __name__ == "__main__":main()
