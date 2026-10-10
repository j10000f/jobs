"""Test observed public feed routes; use for development only."""
from urllib.request import Request,urlopen
from urllib.parse import urlencode
import json,re
cases = [
 ("uzh_jobs","https://ohws.prospective.ch/public/v1/medium/1002007/jobs?lang=en&offset=0&limit=96","GET",None),
 ("bern_jobs","https://ohws.prospective.ch/public/v1/medium/1001892/jobs?lang=en&offset=0&limit=96","GET",None),
 ("basel_post","https://jobs.unibas.ch/?lang=en","POST",urlencode({"offset":10,"limit":10,"lang":"en"}).encode()),
 ("konstanz_js1","https://cs-assets.b-ite.com/uni-konstanz/jobs-api/main-listing-v5.js","GET",None),
 ("konstanz_js2","https://cs-assets.b-ite.com/uni-konstanz/jobs-api/main-listing-v5","GET",None),
 ("konstanz_js3","https://cs-assets.b-ite.com/uni-konstanz/jobs-api/main-listing-v5.json","GET",None),
 ("hu_large","https://hu-berlin.stellenticket.de/de/offers/?jobs_science%5Bper_page%5D=100&jobs_science%5Boffset%5D=0","GET",None),
 ("unil_page2","https://joblens.ch/unil?page=2","GET",None),
]
for name,url,method,body in cases:
 try:
  req=Request(url,data=body,method=method,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json,text/html,*/*","Content-Type":"application/x-www-form-urlencoded"})
  with urlopen(req,timeout=18) as r:
   data=r.read(450000)
   print("OK",name,r.status,len(data),r.geturl(),"CT",r.headers.get("content-type"),flush=True)
  txt=data.decode("utf-8","replace")
  if name in ("uzh_jobs","bern_jobs"):
   try:
    a=json.loads(txt)
    print("JSON",name,"keys",list(a) if isinstance(a,dict) else "list", "total",a.get("total") if isinstance(a,dict) else None,"jobs",len(a.get("jobs",[])) if isinstance(a,dict) else None,"sample",repr(a.get("jobs",[{}])[0])[:500] if isinstance(a,dict) else "",flush=True)
   except Exception as e:print("JSON_FAIL",name,repr(txt[:300]))
  elif name.startswith("konstanz"): print("TEXT",name,repr(txt[:1100]),flush=True)
  else: print("LINK_COUNTS",name,"jobs",len(re.findall(r"/offers/\\d+|class=.job-open.|/offene-stellen/|class=.job-title.",txt,re.I)),"snippet",repr(txt[txt.find("job"):txt.find("job")+100]),flush=True)
 except Exception as e:print("FAIL",name,type(e).__name__,str(e),flush=True)

# Public endpoint smoke test.
