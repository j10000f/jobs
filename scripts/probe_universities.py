"""Diagnostic: examine public university vacancy pages, no login/cookies or bot bypass."""
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from html.parser import HTMLParser
import re

PAGES={
 "konstanz":"https://stellen.uni-konstanz.de/site/v2/de/professuren.html",
 "hu-berlin":"https://hu-berlin.stellenticket.de/de/offers/",
 "uzh":"https://www.uzh.ch/en/explore/work/jobs.html",
 "bern":"https://unibe.prospective.ch/?lang=en",
 "basel":"https://jobs.unibas.ch/?lang=en",
 "lausanne":"https://www.unil.ch/travailler",
 "lausanne2":"https://www.unil.ch/emploi",
 "lausanne3":"https://www.unil.ch/carrieres",
}

PAGES.update({
 "konstanz_js":"https://static.b-ite.com/jobs-api/loader-v1/api-loader-v1.min.js",
 "uzh_widget":"https://ohws.prospective.ch/public/v2/careercenter/1002007/?lang=en",
 "bern_js":"https://unibe.prospective.ch/careercenter/1001892/static/index-CtgvSgPP.js",
 "unil_sf":"https://career5.successfactors.eu/career?company=universitdP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH",
 "unil_jobs":"https://joblens.ch/unil",
 "konstanz_main":"https://www.uni-konstanz.de/personalabteilung/stellenangebote-1/stellenangebote-der-universitaet-konstanz/",
})
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.tags=[];self.current=None
 def handle_starttag(self,t,a):
  d=dict(a)
  if t in ("iframe","script","form","base"):self.tags.append((t,dict((k,(v or "")[:220]) for k,v in d.items())))
  if t=="a":self.current=[d.get("href",""),""]
 def handle_data(self,x):
  if self.current:self.current[1]+=x
 def handle_endtag(self,t):
  if t=="a" and self.current:
   a,b=self.current
   if len(b.strip())>=7:self.tags.append(("link",{"href":a,"text":re.sub(r"\s+"," ",b.strip())[:75]}))
   self.current=None
for name,url in PAGES.items():
 print("===== TARGET",name,url,flush=True)
 try:
  with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; JobsMirror/1.0)","Accept":"text/html,*/*","Accept-Language":"de,en;q=0.8"}), timeout=22) as r:
   page=r.read(1300000).decode("utf-8","replace")
   print("STATUS",r.status,"FINAL",r.geturl(),"BYTES",len(page))
   if name=="bern_js" or name=="konstanz_js":
    for m in list(re.finditer(r"https?://[^\"\x27\s)]+|/api/[a-zA-Z0-9_/-]+|/public/v[0-9]+/[a-zA-Z0-9_/-]+",page))[:25]: print("API_HINT",repr(page[max(m.start()-35,0):min(m.end()+55,len(page))]))
  p=Links();p.feed(page)
  print("IFRAMES/FORMS/SCRIPTS",[(t,d) for t,d in p.tags if t in ("iframe","form","script","base")][:15])
  keys=["job","stellen","beruf","professor","vacanc","offre","poste","career","recruit","apply"]
  related=[(t,d) for t,d in p.tags if t=="link" and any(k in (d["href"]+" "+d.get("text","")).lower() for k in keys)]
  print("JOB LINKS",related[:22])
  for pat in ("__NEXT_DATA__","jobListing","JobPosting","iframe","position","JobID","career","jobSearch","sfApply","successfactors","professur"):
   m=re.search(pat,page,re.I)
   if m: print("SIGNAL",pat,repr(re.sub(r"\s+"," ",page[max(m.start()-70,0):m.start()+170])))
 except Exception as e:print("FAIL",type(e).__name__,str(e),flush=True)

print("===== DEEP DIAGNOSTICS")
URLS = [
 ("konstanz_loader","https://static.b-ite.com/jobs-api/loader-v1/api-loader-v1.min.js"),
 ("konstanz_api","https://static.b-ite.com/jobs-api/v5/"),
 ("uzh_bundle","https://ohws.prospective.ch/careercenter/1002007/static/bundle.js"),
 ("bern_bundle","https://unibe.prospective.ch/careercenter/1001892/static/index-CtgvSgPP.js"),
 ("basel_html","https://jobs.unibas.ch/?lang=en"),
 ("hu_html","https://hu-berlin.stellenticket.de/de/offers/"),
 ("unil_sf","https://career5.successfactors.eu/career?company=universitdP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"),
 ("unil_joblens","https://joblens.ch/unil")
]
for name,url in URLS:
 try:
  with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html,*/*"}),timeout=20) as r: page=r.read(1600000).decode("utf-8","replace")
  print("SCAN",name,len(page),flush=True)
  keys = {"konstanz_loader":["jobs-api","listing","fetch(","api"],"konstanz_api":["script","src"],
          "uzh_bundle":["/public/v1","/public/v2","getJobs","getJob","/jobs","/api/","axios","fetch("],
          "bern_bundle":["/public/v1","/public/v2","getJobs","getJob","/jobs","/api/","axios","fetch("],
          "basel_html":["pagination","Next","&page","offset","job-list","online","result"], 
          "hu_html":["/de/offers/20","Humboldt-Universität","W1","Angebote von Hochschulen","page"], 
          "unil_sf":["jobSearch","job_listing_summary","jobReq","jobTitle","Search Results","jobListing","Requisition","emploi"],
          "unil_joblens":["job-open","successfactors","Postdoc","Professor"]
         }.get(name,[])
  for key in keys:
   matches=list(re.finditer(re.escape(key),page,re.I))
   print("PATTERN",name,key,"hits",len(matches))
   for m in matches[-3:]:print("CONTEXT",name,key,repr(re.sub(r"\s+"," ",page[max(0,m.start()-160):min(len(page),m.end()+230)])[:450]))
 except Exception as e: print("DEEP_FAIL",name,type(e).__name__,str(e))
