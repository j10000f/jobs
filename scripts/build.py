#!/usr/bin/env python3
"""Public job feed mirrors; Python standard library only; output is static HTML."""
import html
import json
import re
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path("public")
SOURCES = {
 "uni-graz": ("University of Graz — job postings", "https://personal.uni-graz.at/api/erec/public/job-postings", "json"),
 "tu-graz": ("TU Graz — job postings", "https://personal.tugraz.at/api/erec/public/job-postings", "json"),
 "eco-evo": ("EcoEvoJobs — weekly RSS", "https://calebcharpentier.com/EcoEvoJobSearcher/feed-week.xml", "rss"),
 "tu-wien": ("TU Wien — newest Gazette JSON (not a vacancy feed)", "https://tiss.tuwien.ac.at/mbl/main/uebersicht?fuer=mb", "tiss"),
}
HEADERS={"User-Agent":"AcademicJobMirrors/1.0 (+https://github.com/j10000f/jobs)", "Accept":"text/html,application/json,application/xml,text/xml,application/rss+xml,*/*"}
def fetch(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=40) as response:
        data=response.read(16*1024*1024+1)
    if len(data)>16*1024*1024: raise ValueError("Source exceeds 16MB")
    return data

def json_rows(data):
    value=json.loads(data.decode("utf-8-sig"))
    if isinstance(value,list): rows=value
    elif isinstance(value,dict):
        rows=next((value[k] for k in ("data","results","job_postings","jobPostings","items") if isinstance(value.get(k),list)), None)
        if rows is None: raise ValueError("Unknown JSON envelope; not claiming zero vacancies")
    else: raise ValueError("JSON root not a list/object")
    if not all(isinstance(r,dict) for r in rows): raise ValueError("Unexpected JSON rows")
    return rows

def xml_tag(tag):
    if tag.startswith("{"):
        ns,_,local=tag[1:].partition("}")
        mapping={"http://purl.org/dc/elements/1.1/":"dc","http://purl.org/rss/1.0/modules/content/":"content","http://www.w3.org/2005/Atom":"atom"}
        return mapping.get(ns,ns)+":"+local
    return tag

def xml_value(el):
    text="".join(el.itertext()).strip()
    attrs="; ".join(xml_tag(k)+"="+v for k,v in el.attrib.items())
    return (text+" ("+attrs+")") if text and attrs else text or attrs

def xml_row(el):
    result={}
    for child in el:
        name=xml_tag(child.tag)
        val=xml_value(child)
        if name in result:
            prev=result[name]
            result[name] = prev + " | " + val
        else: result[name]=val
    if xml_tag(el.tag)=="atom:entry":
        for ch in el:
            if xml_tag(ch.tag)=="atom:link" and ch.get("href") and ch.get("rel","alternate")=="alternate":
                result.setdefault("link",ch.get("href")); break
    return result

def rss_rows(data):
    root=ET.fromstring(data)
    if xml_tag(root.tag)=="rss":
        channel=root.find("channel")
        if channel is None: raise ValueError("RSS without channel")
        items=channel.findall("item")
    elif xml_tag(root.tag)=="atom:feed":
        items=[x for x in root if xml_tag(x.tag)=="atom:entry"]
    elif root.tag.endswith("}RDF"):
        items=[x for x in root if xml_tag(x.tag).endswith(":item")]
    else: raise ValueError("Not RSS/Atom")
    return [xml_row(el) for el in items]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]; self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=="a": self.current={"href":dict(attrs).get("href",""),"text":""}
    def handle_data(self,data):
        if self.current is not None: self.current["text"]+=data
    def handle_endtag(self,tag):
        if tag=="a" and self.current is not None:
            self.links.append(self.current); self.current=None

def tiss_rows(data,base):
    p=Links();p.feed(data.decode("utf-8","replace"))
    gazettes=[]
    for a in p.links:
        t=" ".join(a["text"].split())
        if ("Gazette" not in t and "Mitteilungsblatt" not in t) or not re.search(r"\d",t):continue
        href=urllib.parse.urljoin(base,a["href"])
        gazettes.append((t,href))
    if not gazettes: raise ValueError("No dated Gazette issues discovered")
    # Typically the PDF page URL includes an issue ID (not guaranteed).
    title,url=gazettes[0]
    html_doc=fetch(url).decode("utf-8","replace")
    matches=re.findall(r"(?:/api/mbl/v\d+/id/|/mbl/.*?(?:id=|/id/))(\d+)",html_doc)
    if not matches:
        # Some overview links may have ID in their own URL.
        matches=re.findall(r"(?:id=|/id/|/anzeigen/)(\d+)",url)
    if not matches:
        return [{"issue":title,"issue_url":url,"json_status":"No public per-issue JSON ID located; Gazette metadata only"}]
    api=f"https://tiss.tuwien.ac.at/api/mbl/v22/id/{matches[0]}"
    payload=json.loads(fetch(api).decode("utf-8-sig"))
    if isinstance(payload,dict):
        return [{"issue":title,"issue_url":url,"json_api":api,**payload}]
    if isinstance(payload,list):
        return [{"issue":title,"issue_url":url,"json_api":api,**(x if isinstance(x,dict) else {"value":x})} for x in payload]
    return [{"issue":title,"issue_url":url,"json_api":api,"value":payload}]

def safe_text(v):
    if v is None:return ""
    if isinstance(v,str):return v
    if isinstance(v,(dict,list)):return json.dumps(v,ensure_ascii=False)
    return str(v)
def render(v):
    v=safe_text(v)
    escaped=html.escape(v,quote=True)
    parsed=urllib.parse.urlsplit(v)
    if parsed.scheme in ("https","http") and parsed.netloc and not re.search(r"\s",v):
        return '<a rel="noopener noreferrer" href="'+html.escape(v,quote=True)+'">'+escaped+'</a>'
    return escaped
STYLE="""body{font:14px/1.5 system-ui,Arial,sans-serif;margin:2rem;max-width:1500px;color:#17222e}a{color:#07529b}nav a{margin-right:15px}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{padding:8px;border:1px solid #ddd;vertical-align:top;text-align:left;white-space:pre-wrap;overflow-wrap:anywhere}th{background:#eef1f5}tr:nth-child(even){background:#fafafa}.meta{color:#526377}.fail{color:#aa3500}"""
def document(title,body):
    nav=' '.join('<a href="'+html.escape(k)+'.html">'+html.escape(v[0].split(" — ")[0])+'</a>' for k,v in SOURCES.items())
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style></head><body><nav><a href="index.html">Index</a> '+nav+'</nav><h1>'+html.escape(title)+'</h1>'+body+'</body></html>'
def table(rows):
    cols=list(dict.fromkeys(k for r in rows for k in r))
    if not rows:return "<p>No records supplied by a successfully parsed feed.</p>"
    return '<div class="wrap"><table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in cols)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+render(r.get(k))+'</td>' for k in cols)+'</tr>' for r in rows)+'</tbody></table></div>'
def main():
    ROOT.mkdir(exist_ok=True)
    time=datetime.now(timezone.utc).isoformat(timespec="seconds")
    states={}
    index=[]
    for slug,(title,url,kind) in SOURCES.items():
        problem=None;rows=None
        try:
            raw=fetch(url)
            if kind=="json":rows=json_rows(raw)
            elif kind=="rss":rows=rss_rows(raw)
            elif kind=="tiss":rows=tiss_rows(raw,url)
            print(slug,len(rows),"rows",flush=True)
        except Exception as e:
            problem=type(e).__name__+": "+str(e)
            print(slug,"FAILED",problem,flush=True)
        states[slug]={"source":url,"retrieved_at_utc":time,"ok":problem is None,"count":len(rows) if rows is not None else None,"error":problem}
        note="<p class='meta'>Source: <a href='"+html.escape(url,quote=True)+"'>"+html.escape(url)+"</a> · Checked "+html.escape(time)+" · "+("Records: "+str(len(rows)) if rows is not None else "Retrieval failed")+"</p>"
        if kind=="tiss":note+="<p>Gazette issue metadata, not a complete vacancy list; read advertised positions in the official linked issue.</p>"
        if problem: note+="<p class='fail'>Source unavailable or could not be parsed: "+html.escape(problem)+". This does NOT mean zero vacancies.</p>"
        (ROOT/(slug+".html")).write_text(document(title,note+(table(rows) if rows is not None else "")),encoding="utf-8")
        index.append('<li><a href="'+slug+'.html">'+html.escape(title)+'</a> — '+(str(len(rows))+" records" if rows is not None else "unavailable")+'</li>')
    (ROOT/"index.html").write_text(document("Academic jobs — source mirrors","<p>Static unfiltered source data, not validated job recommendations. Last checked "+html.escape(time)+" UTC.</p><ul>"+"".join(index)+"</ul><p><a href='status.json'>Machine-readable collection status</a></p>"),encoding="utf-8")
    (ROOT/"status.json").write_text(json.dumps({"generated_utc":time,"sources":states},indent=2,ensure_ascii=False),encoding="utf-8")
    (ROOT/".nojekyll").write_text("",encoding="utf-8")
    # Fail if *all* retrievals are unsuccessful; prevent an all-failure deployment.
    if not any(x["ok"] for x in states.values()): sys.exit("Every source failed: do not deploy all-failure pages")
if __name__=="__main__":main()
