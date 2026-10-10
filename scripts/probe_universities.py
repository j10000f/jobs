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
  p=Links();p.feed(page)
  print("IFRAMES/FORMS/SCRIPTS",[(t,d) for t,d in p.tags if t in ("iframe","form","script","base")][:15])
  keys=["job","stellen","beruf","professor","vacanc","offre","poste","career","recruit","apply"]
  related=[(t,d) for t,d in p.tags if t=="link" and any(k in (d["href"]+" "+d.get("text","")).lower() for k in keys)]
  print("JOB LINKS",related[:22])
  for pat in ("__NEXT_DATA__","jobListing","JobPosting","iframe","position","JobID","career","jobSearch","sfApply","successfactors","professur"):
   m=re.search(pat,page,re.I)
   if m: print("SIGNAL",pat,repr(re.sub(r"\s+"," ",page[max(m.start()-70,0):m.start()+170])))
 except Exception as e:print("FAIL",type(e).__name__,str(e),flush=True)
