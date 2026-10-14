#!/usr/bin/env python3
"""PANDORA COMPETITOR Ω v3.1 — universal public-site weekly change intelligence (stdlib)."""
import argparse, collections, datetime as dt, hashlib, html.parser, json, math, re, sqlite3, time, difflib, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

class Page(html.parser.HTMLParser):
 def __init__(self,base):
  super().__init__();self.base=base;self.tag=None;self.title='';self.h1='';self.text=[];self.links=set();self.meta={};self.canonical='';self.jsonld=[];self.script=False;self.script_text='';self.skip=0
 def handle_starttag(self,t,attrs):
  a={k:(v or '') for k,v in attrs}
  if t in ('style','script','noscript'):self.skip+=1
  if t=='script' and a.get('type')=='application/ld+json':self.script=True;self.script_text=''
  if t in ('title','h1'):self.tag=t
  if t=='link' and 'canonical' in a.get('rel','').lower():self.canonical=urljoin(self.base,a.get('href',''))
  if t=='meta':self.meta[a.get('name',a.get('property','')).lower()]=a.get('content','')
  if t=='a' and a.get('href'):
   u=urldefrag(urljoin(self.base,a['href']))[0]
   if urlsplit(u).scheme in ('http','https'):self.links.add(u)
 def handle_endtag(self,t):
  if t==self.tag:self.tag=None
  if t=='script' and self.script:
   try:self.jsonld.append(json.loads(self.script_text))
   except ValueError:pass
   self.script=False
  if t in ('style','script','noscript'):self.skip=max(0,self.skip-1)
 def handle_data(self,s):
  if self.script:self.script_text+=s
  if not self.skip:
   self.text.append(s)
   if self.tag=='title':self.title+=s
   if self.tag=='h1':self.h1+=s

CONTENT_FIELDS=('title','description','canonical','h1','author','published','modified','schema_types','text','links')
def content_hash(item):
 """Hash do conteúdo extraído: ignora nonces, timestamps e markup que mudam a cada requisição."""
 return hashlib.sha256(json.dumps({k:item.get(k) for k in CONTENT_FIELDS},ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def nodes(o):
 if isinstance(o,list):
  for x in o:yield from nodes(x)
 if isinstance(o,dict):
  yield o
  for k in ('@graph','author'):yield from nodes(o.get(k,[]))

def extract(raw,url):
 p=Page(url);p.feed(raw);ns=[n for obj in p.jsonld for n in nodes(obj)]
 authors=[str(n.get('name')) for n in ns if n.get('@type')=='Person' and n.get('name')]
 return {'title':p.title.strip(),'description':p.meta.get('description',''),'canonical':p.canonical,'h1':p.h1.strip(),'author':'; '.join(sorted(set(authors+[p.meta.get('author','')]))).strip('; '),'modified':next((n['dateModified'] for n in ns if 'dateModified' in n),p.meta.get('article:modified_time','')),'published':next((n['datePublished'] for n in ns if 'datePublished' in n),''),'text':' '.join(' '.join(p.text).split())[:80000],'links':sorted(p.links),'schema_types':sorted({str(n.get('@type','')) for n in ns if n.get('@type')}),'author_evidence':{'meta_author':p.meta.get('author',''),'jsonld_persons':authors}}

def same_site(host,domain):
 strip=lambda h:(h or '').lower().removeprefix('www.')
 return strip(host)==strip(domain)

def crawl(root,limit,delay):
 root=root.rstrip('/')+'/';domain=urlsplit(root).hostname
 rp=RobotFileParser();rp.set_url(urljoin(root,'/robots.txt'))
 try:rp.read()
 except Exception:rp=None
 queue=[root];seen=set();out={}
 while queue and len(out)<limit:
  u=queue.pop(0)
  if u in seen:continue
  seen.add(u)
  if rp and not rp.can_fetch('PandoraCompetitorOmega',u):out[u]={'error':'robots_disallow'};continue
  try:
   with urlopen(Request(u,headers={'User-Agent':'PandoraCompetitorOmega/'+VERSION}),timeout=15) as r:
    final=r.geturl()
    if not same_site(urlsplit(final).hostname,domain):raise ValueError('cross-domain redirect')
    if 'html' not in r.headers.get('Content-Type',''):raise ValueError('non-html')
    data=r.read(2000001)
    if len(data)>2000000:raise ValueError('too large')
    raw=data.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
   item=extract(raw,final);item['html_sha256']=hashlib.sha256(raw.encode()).hexdigest()
   item['hash']=content_hash(item);out[u]=item
   for link in item['links']:
    if same_site(urlsplit(link).hostname,domain) and link not in seen and link not in queue and len(queue)<limit*6 and not re.search(r'\.(pdf|jpg|png|svg|webp|zip|css|js)$',urlsplit(link).path,re.I):queue.append(link)
  except Exception as e:out[u]={'error':str(e)[:200]}
  time.sleep(delay)
 return out

def terms(s):return set(re.findall(r'[a-zà-ÿ0-9]{3,}',s.lower()))-set('para com que dos das uma por como seu sua the and for with'.split())
def score(a,b):
 a=[v for v in a.values() if 'text' in v];b=[v for v in b.values() if 'text' in v]
 if not a or not b:return None,[]
 ats=[terms(x['title']+' '+x['h1']+' '+x['text'][:3500]) for x in a];matches=[]
 for item in b:
  bt=terms(item['title']+' '+item['h1']+' '+item['text'][:3500]);v=max((len(bt&t)/len(bt|t) if bt|t else 0,i) for i,t in enumerate(ats))
  matches.append({'competitor_title':item['title'],'primary_title':a[v[1]]['title'],'similarity':round(v[0],3),'authorship_claim':item['author'] or 'not_identified','fit':'review_existing' if v[0]>=.2 else 'potential_gap'})
 return min(1000,round(sum(m['similarity'] for m in matches)/len(matches)*2500)),matches


VERSION='3.1.1'
STOP=set('para como pelo pela onde quando quem quais sobre entre dos das uma umas uns com que seu sua seus suas the and for with from this that have been'.split())
def weighted_terms(page):
    """Frequency-weighted, transparent lexical features; no LLM inference."""
    result=collections.Counter()
    for field,weight in [('title',5),('h1',4),('description',3),('text',1)]:
        for term in re.findall(r'[a-zà-ÿ0-9]{3,}',str(page.get(field,'')).lower()[:12000]):
            if term not in STOP:result[term]+=weight
    return result

def cosine(a,b):
    if not a or not b:return 0.0
    numerator=sum(v*b.get(k,0) for k,v in a.items())
    denom=math.sqrt(sum(v*v for v in a.values())*sum(v*v for v in b.values()))
    return numerator/denom if denom else 0.0

def similarity(a,b):
    ca,cb=weighted_terms(a),weighted_terms(b)
    return round(cosine(ca,cb),4)

def semantic_map(primary,other):
    pa=[(u,p) for u,p in primary.items() if 'text' in p]
    co=[(u,p) for u,p in other.items() if 'text' in p]
    result=[]
    for u,p in co:
        options=sorted(((similarity(p,q),v,q) for v,q in pa),key=lambda x:-x[0])
        top=options[0] if options else None
        value=top[0] if top else 0
        result.append({'competitor_url':u,'competitor_title':p.get('title',''),
           'primary_url':top[1] if top else None,'primary_title':top[2].get('title','') if top else None,
           'similarity':value,'editorial_fit':'strong_overlap_review' if value>=.65 else 'related_review' if value>=.35 else 'possible_gap_manual_review',
           'authorship':{'declared':p.get('author') or None,'evidence':p.get('author_evidence',{}),'verification':'not_independently_verified'}})
    return sorted(result,key=lambda x:-x['similarity'])

def compare_snapshots(old,now):
    changes=[]
    for url in sorted(set(old)|set(now)):
        a=old.get(url);b=now.get(url)
        if a is None:kind='newly_discovered'
        elif b is None:kind='not_recrawled_unconfirmed'
        elif a.get('error')!=b.get('error'):kind='fetch_status_changed'
        elif a.get('hash')==b.get('hash'):continue
        elif a.get('text')==b.get('text'):kind='html_metadata_or_markup_changed'
        else:kind='visible_text_changed'
        fields=[k for k in ('title','description','canonical','h1','author','author_evidence','published','modified','schema_types','text','links','error') if a and b and a.get(k)!=b.get(k)]
        author_changed=bool(set(fields)&{'author','author_evidence'})
        severity='high' if author_changed or 'canonical' in fields else 'medium' if 'text' in fields or 'title' in fields else 'low'
        changes.append({'url':url,'change':kind,'fields':fields,'author_change':author_changed,
                        'severity':severity,'before_author':a.get('author') if a else None,
                        'after_author':b.get('author') if b else None})
    return changes

def classify(primary,other):
    matches=semantic_map(primary,other)
    if not matches or not any('text' in p for p in primary.values()):return {'score':None,'level':'insufficient_data','matches':matches,'confidence':'none'}
    values=[x['similarity'] for x in matches]
    mean=sum(values)/len(values)
    # 0-1000 lexical topic overlap, not verified market competition
    s=round(1000*mean)
    return {'score':s,'level':'high_overlap' if s>=650 else 'moderate_overlap' if s>=350 else 'low_overlap',
      'confidence':'limited_lexical_proxy','method':'weighted token cosine, title x5, h1 x4, description x3, body x1',
      'matches':matches,'mean_similarity':round(mean,4)}

def advice(item):
    if item['editorial_fit']=='strong_overlap_review':return 'Compare accuracy, freshness and evidence on the existing page; do not duplicate automatically.'
    if item['editorial_fit']=='related_review':return 'Review intent and audience before updating an existing page or adding internal links.'
    return 'Possible topic gap: validate business relevance, search intent and demand before commissioning content.'


# v2.1: optional multilingual embeddings, intent classification and provenance checks.
INTENT_PATTERNS={
 'transactional':r'\b(comprar|contratar|orçamento|orcamento|preço|preco|agendar|hire|buy|pricing|quote)\b',
 'commercial':r'\b(melhor|comparar|comparativo|avaliação|avaliacao|review|versus|vs|best|compare)\b',
 'navigational':r'\b(login|entrar|contato|telefone|endereço|endereco|contact|address)\b',
 'informational':r'\b(como|o que|porque|por que|guia|tutorial|what|how|why|guide)\b'}
def classify_intent(page):
    """Weak, explainable pattern classification, not observed search intent."""
    text=' '.join(str(page.get(k,'')) for k in ('title','h1','description')).lower()
    matches=[k for k,v in INTENT_PATTERNS.items() if re.search(v,text)]
    return {'labels':matches or ['undetermined'],'evidence':'title/h1/description keyword rules','confidence':'low'}

def entity_claims(page):
    """Surface declared names/types; do not pretend to resolve real-world identities."""
    return {'author_claim':page.get('author') or None,
      'author_sources':page.get('author_evidence',{}),
      'schema_types':page.get('schema_types',[]),
      'canonical_claim':page.get('canonical') or None,
      'verified_identity':False,
      'limitations':'Metadata and structured data are publisher claims, not independent verification'}

class SemanticMatcher:
    def __init__(self,model_name=None):
        self.model=None;self.error=None;self.model_name=model_name
        if model_name:
            try:
                from sentence_transformers import SentenceTransformer
                self.model=SentenceTransformer(model_name)
            except (ImportError,OSError,RuntimeError,ValueError) as exc:
                self.error=str(exc)[:300]
    def compare(self,a,b):
        if self.model is None:
            cache=self.__dict__.setdefault('_terms',{})
            va=cache.get(id(a)) or cache.setdefault(id(a),weighted_terms(a))
            vb=cache.get(id(b)) or cache.setdefault(id(b),weighted_terms(b))
            return round(cosine(va,vb),4),'weighted_lexical_cosine'
        import numpy as np
        texts=[' '.join(str(p.get(k,'')) for k in ('title','h1','description','text'))[:6000] for p in (a,b)]
        vectors=self.model.encode(texts,normalize_embeddings=True)
        return round(max(0.0,float(np.dot(vectors[0],vectors[1]))),4),'multilingual_embedding_cosine'

def semantic_map_v21(primary,other,matcher):
    pa=[(u,p) for u,p in primary.items() if 'text' in p]
    co=[(u,p) for u,p in other.items() if 'text' in p]
    result=[]
    for u,p in co:
        options=[]
        for v,q in pa:
            sim,method=matcher.compare(p,q)
            options.append((sim,v,q,method))
        options.sort(key=lambda x:-x[0])
        best=options[0] if options else None
        sim=best[0] if best else 0
        result.append({'competitor_url':u,'competitor_title':p.get('title',''),
          'primary_url':best[1] if best else None,'primary_title':best[2].get('title','') if best else None,
          'similarity':sim,'similarity_method':best[3] if best else 'not_available',
          'editorial_fit':'strong_overlap_review' if sim>=.65 else 'related_review' if sim>=.35 else 'possible_gap_manual_review',
          'competitor_intent':classify_intent(p),'primary_intent':classify_intent(best[2]) if best else None,
          'entities':entity_claims(p),
          'authorship':{'declared':p.get('author') or None,'evidence':p.get('author_evidence',{}),'verification':'not_independently_verified'}})
    return sorted(result,key=lambda x:-x['similarity'])

def classify_v21(primary,other,matcher):
    matches=semantic_map_v21(primary,other,matcher)
    if not matches or not any('text' in p for p in primary.values()):
        return {'score':None,'level':'insufficient_data','matches':matches}
    mean=sum(m['similarity'] for m in matches)/len(matches)
    value=round(mean*1000)
    return {'score':value,'level':'high_overlap' if value>=650 else 'moderate_overlap' if value>=350 else 'low_overlap',
      'matches':matches,'method':matches[0]['similarity_method'],
      'warning':'Topic overlap only, not verified SERP competition, traffic or competitive threat'}

def pdf_report(report,path):
    """Optional premium-style PDF; pip install reportlab. Never hides incomplete evidence."""
    try:
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import mm
        from xml.sax.saxutils import escape
    except ImportError as exc:raise RuntimeError('PDF requires pip install reportlab') from exc
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='PandoraTitle',parent=styles['Title'],fontSize=22,leading=28,textColor=colors.HexColor('#14241B'),spaceAfter=14))
    styles.add(ParagraphStyle(name='PandoraHead',parent=styles['Heading2'],textColor=colors.HexColor('#166534'),spaceBefore=14,spaceAfter=8))
    styles.add(ParagraphStyle(name='PandoraBody',parent=styles['BodyText'],fontSize=9.5,leading=14,spaceAfter=7))
    doc=SimpleDocTemplate(str(path),pagesize=(210*mm,297*mm),rightMargin=19*mm,leftMargin=19*mm,topMargin=18*mm,bottomMargin=18*mm)
    story=[Paragraph('PANDORA COMPETITOR Ω',styles['PandoraTitle']),Paragraph('Inteligência competitiva | Versão '+escape(str(report.get('version','')))+' | Relatório de evidências',styles['PandoraBody']),
      Paragraph('Execução UTC: '+escape(report['timestamp']),styles['PandoraBody']),Paragraph('Domínio principal: '+escape(report['primary']),styles['PandoraBody']),
      Paragraph('ESCOPO E LIMITAÇÕES',styles['PandoraHead'])]
    for limitation in report['limitations']:story.append(Paragraph('• '+escape(limitation),styles['PandoraBody']))
    for r in report['results']:
        story.extend([Paragraph(escape(r['name'])+' — '+escape(r['domain']),styles['PandoraHead']),
          Paragraph('Score de sobreposição: '+str(r['score_0_1000'] if r['score_0_1000'] is not None else 'N/A')+'/1000 | '+escape(r['level']),styles['PandoraBody']),
          Paragraph('Páginas processadas: '+str(r['coverage']['parsed'])+' | Falhas: '+str(r['coverage']['errors'])+' | Alterações observadas: '+str(len(r['changes'])),styles['PandoraBody'])])
        for change in r['changes'][:20]:
            story.append(Paragraph(escape(change['change']+' | '+change['url'])[:250],styles['PandoraBody']))
        story.append(Paragraph('Correspondências editoriais (amostra)',styles['PandoraHead']))
        for m in r['matches'][:12]:
            story.append(Paragraph(escape(m['competitor_title'][:100] or m['competitor_url'][:100])+' | '+str(m['similarity'])+' | '+escape(m['editorial_fit']),styles['PandoraBody']))
            story.append(Paragraph('Autor declarado: '+escape(str(m['authorship']['declared'] or 'não identificado')),styles['PandoraBody']))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(19*mm,12*mm,'PANDORA Ω | evidência pública | não representa ranking Google')
        canvas.drawRightString(191*mm,12*mm,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

def report_md(report):
    lines=['# PANDORA COMPETITOR Ω v3.0.0', '',f"Run UTC: {report['timestamp']}",f"Primary: {report['primary']}",
           '', '**Method:** lexical proxy, not a ranking or traffic measurement. Authorship is declared, not verified.',
           '**Coverage:** bounded crawl; missing pages do not prove deletion.','']
    for r in report['results']:
        lines += [f"## {r['name']} — {r['domain']}",f"Overlap score: {r['score_0_1000'] if r['score_0_1000'] is not None else 'N/A'}/1000 ({r['level']})",
          f"Baseline created: {r['baseline_created']}; pages: {r['coverage']['pages']}; fetch errors: {r['coverage']['errors']}",
          f"Changes since prior scan: {len(r['changes'])}",'']
        for ch in r['changes']:
            lines.append(f"- [{ch['severity']}] {ch['change']} {ch['url']} — fields: {', '.join(ch['fields']) or 'N/A'}" )
        lines+=['','### Editorial opportunity assessment']
        for m in r['matches'][:30]:
            lines += [f"- **{m['competitor_title'] or m['competitor_url']}** ({m['similarity']:.3f})",
              f"  - Competitor: {m['competitor_url']}",f"  - Closest own page: {m['primary_url'] or 'none'}",
              f"  - Declared author: {m['authorship']['declared'] or 'not identified'} (not independently verified)",
              f"  - Recommendation: {advice(m)}"]
        lines.append('')
    return chr(10).join(lines)

def validate_config(cfg):
    sites=[cfg['primary']]+cfg['competitors']
    if not cfg.get('competitors'):raise ValueError('At least one competitor is required')
    domains=[]
    for site in sites:
        url=site['url'];p=urlsplit(url)
        if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:raise ValueError('Invalid site URL')
        domains.append(p.hostname.lower())
    if len(domains)!=len(set(domains)):raise ValueError('Duplicate domains')
    limit=int(cfg.get('max_pages',30));delay=float(cfg.get('delay_seconds',1))
    if not 1<=limit<=1000 or not .2<=delay<=120:raise ValueError('max_pages 1..1000 and delay_seconds 0.2..120')
    return sites,domains,limit,delay

def scan(cfg,db,out,model_name=None,make_pdf=False):
    sites,domains,limit,delay=validate_config(cfg)
    conn=sqlite3.connect(db)
    conn.execute('CREATE TABLE IF NOT EXISTS snapshots(domain TEXT,stamp TEXT,payload TEXT,PRIMARY KEY(domain,stamp))')
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshots={};deltas={};baselines={}
    for site,domain in zip(sites,domains):
        oldrow=conn.execute('SELECT payload FROM snapshots WHERE domain=? ORDER BY stamp DESC LIMIT 1',(domain,)).fetchone()
        old=json.loads(oldrow[0]) if oldrow else {}
        now=crawl(site['url'],limit,delay)
        snapshots[domain]=now;deltas[domain]=compare_snapshots(old,now) if oldrow else []
        baselines[domain]=oldrow is None
        conn.execute('INSERT INTO snapshots VALUES(?,?,?)',(domain,stamp,json.dumps(now,ensure_ascii=False)))
        conn.commit()
        print(f'{domain}: {len(now)} attempted; {sum("text" in x for x in now.values())} parsed; {len(deltas[domain])} changes',file=sys.stderr)
    matcher=SemanticMatcher(model_name)
    report={'engine':'PANDORA COMPETITOR Ω','version':VERSION,'timestamp':stamp,'primary':domains[0],
       'limitations':['Public HTML only; JS rendering not supported','Lexical score is a topic-overlap proxy, not actual SERP competition',
         'Metadata author is not independently verified','Incomplete crawl does not establish deletion','Content recommendations require editorial review', 'Author metadata is not proof of actual authorship', 'Intent detection is heuristic and not based on search query logs'],
       'results':[]}
    for site,domain in zip(sites[1:],domains[1:]):
        comp=classify_v21(snapshots[domains[0]],snapshots[domain],matcher);pages=snapshots[domain]
        report['results'].append({'name':site['name'],'domain':domain,'score_0_1000':comp['score'],'level':comp['level'],
           'score_method':comp.get('method'),'baseline_created':baselines[domain],
           'coverage':{'pages':len(pages),'parsed':sum('text' in p for p in pages.values()),'errors':sum('error' in p for p in pages.values())},
           'changes':deltas[domain],'matches':comp['matches'],
           'alerts':[{'type':'author_changed','url':x['url'],'priority':'high'} for x in deltas[domain] if x['author_change']]})
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    j=out/f'competitor_v21_{stamp}.json';m=out/f'competitor_v21_{stamp}.md'
    j.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    m.write_text(report_md(report),encoding='utf-8')
    paths={'json':str(j),'markdown':str(m),'competitors':len(report['results'])}
    if make_pdf:
        pdf=out/f'competitor_v21_{stamp}.pdf'
        pdf_report(report,pdf);paths['pdf']=str(pdf)
    print(json.dumps(paths,ensure_ascii=False))
    conn.close()

def selftest():
    raw='<html><head><title>SEO Técnico</title><meta name="author" content="Ana"><link rel="canonical" href="/seo"></head><body><h1>Auditoria</h1><p>Conteúdo relevante</p></body></html>'
    p=extract(raw,'https://example.org/')
    assert p['author']=='Ana' and p['canonical']=='https://example.org/seo'
    assert p['title']=='SEO Técnico' and p['h1']=='Auditoria'
    a={'https://a.test/':dict(p,hash='old')};b={'https://a.test/':dict(p,hash='new',author='Bruno')}
    c=compare_snapshots(a,b);assert c[0]['author_change'] and c[0]['severity']=='high'
    assert compare_snapshots(a,a)==[]
    assert classify(a,b)['score'] is not None
    assert classify({},b)['score'] is None
    assert classify(a,b)['matches'][0]['authorship']['verification']=='not_independently_verified'
    assert classify_intent({'title':'Como fazer SEO'})['labels']==['informational']
    assert entity_claims(p)['verified_identity'] is False
    matcher=SemanticMatcher()
    assert classify_v21(a,b,matcher)['score'] is not None
    assert classify_v21({},b,matcher)['score'] is None
    print('SELFTEST PASS: HTML, canonical, author, diff, no-change, score, missing evidence, provenance')


# v3.0 strategic intelligence: transparent evidence, author drift and actionable fit.
def author_profile(page):
    """Claims only: does not verify real-world author identity."""
    evidence=page.get('author_evidence') or {}
    name=page.get('author') or None
    sources=[k for k,v in evidence.items() if v]
    return {'declared_name':name,'sources':sources,'schema_types':page.get('schema_types',[]),
            'published_claim':page.get('published') or None,'modified_claim':page.get('modified') or None,
            'verification':'publisher_claim_only' if name else 'unidentified'}

def authorship_drift(previous,current):
    changes=[]
    for url in sorted(set(previous)&set(current)):
        before,after=previous[url],current[url]
        if 'error' in before or 'error' in after:continue
        old,new=author_profile(before),author_profile(after)
        changed=[k for k in ('declared_name','sources','published_claim','modified_claim','schema_types') if old[k]!=new[k]]
        if changed:
            changes.append({'url':url,'changed_fields':changed,'before':old,'after':new,
                            'priority':'high' if 'declared_name' in changed else 'medium',
                            'interpretation':'Metadata change, not evidence of who actually edited the page'})
    return changes

def business_fit(primary_page, competitor_page, similarity_value):
    """Conservative recommendation. No copying, publishing or deletion."""
    if primary_page is None:
        return {'belongs_to_site':'undetermined','action':'investigate_topic',
                'reason':'No primary page could be compared','confidence':'insufficient'}
    a=set(classify_intent(primary_page)['labels'])-{'undetermined'}
    b=set(classify_intent(competitor_page)['labels'])-{'undetermined'}
    intent_agrees=bool(a&b)
    if similarity_value>=.70 and intent_agrees:
        decision,action='likely_related','review_existing_page'
    elif similarity_value>=.40:
        decision,action='needs_editorial_review','compare_audience_and_intent'
    else:
        decision,action='unproven_fit','validate_business_relevance'
    return {'belongs_to_site':decision,'action':action,'confidence':'heuristic_low',
            'intent_alignment':intent_agrees,'reason':'Content similarity and weak keyword-based intent signals; editorial validation required'}

def competitive_context(primary,competitor,matches):
    """Classify content overlap, not verified geographic or SERP competition."""
    usable_p={u:p for u,p in primary.items() if 'text' in p}
    usable_c={u:p for u,p in competitor.items() if 'text' in p}
    if not usable_p or not usable_c:return {'level':'insufficient_evidence','score':None,'confidence':'none','decisions':[]}
    decisions=[]
    for match in matches:
        cu=match.get('competitor_url');pu=match.get('primary_url')
        if cu not in usable_c:continue
        sim=float(match.get('similarity') or 0)
        fit=business_fit(usable_p.get(pu),usable_c[cu],sim)
        decisions.append({'competitor_url':cu,'primary_url':pu,'similarity':round(sim,4),**fit,
                          'author':author_profile(usable_c[cu])})
    avg=sum(x['similarity'] for x in decisions)/len(decisions) if decisions else 0
    return {'level':'high_topic_overlap' if avg>=.65 else 'moderate_topic_overlap' if avg>=.35 else 'low_topic_overlap',
            'score':round(avg*1000),'confidence':'limited_proxy',
            'not_measured':['SERP rankings','traffic','backlinks','geographic market','real-world authorship'],
            'decisions':decisions}

def enrich_v3_report(report,snapshots,previous):
    report['version']='3.0.0'
    report['score_interpretation']='0–1000 measures observed content similarity, NOT real market competition or ranking potential'
    report['strategic_method']='content similarity + weak intent matching + publisher-declared authorship; human approval required'
    primary=snapshots[report['primary']]
    for result in report['results']:
        domain=result['domain']
        result['authorship_intelligence']={'changes':authorship_drift(previous.get(domain,{}),snapshots[domain]),
            'profiles':{url:author_profile(page) for url,page in snapshots[domain].items() if 'text' in page}}
        result['strategic_intelligence']=competitive_context(primary,snapshots[domain],result['matches'])
        result['priority_queue']=[{'url':d['competitor_url'],'action':d['action'],'reason':d['reason'],
                                    'confidence':d['confidence']} for d in result['strategic_intelligence']['decisions']
                                   if d['action']=='review_existing_page']
    return report

# Keep v2.1 crawler and outputs; enrich report after scan without changing database schema.
scan_v21=scan
def scan(cfg,db,out,model_name=None,make_pdf=False):
    import contextlib,io
    conn=sqlite3.connect(db)
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS snapshots(domain TEXT,stamp TEXT,payload TEXT,PRIMARY KEY(domain,stamp))')
        previous={}
        for site in [cfg['primary']]+cfg['competitors']:
            domain=urlsplit(site['url']).hostname.lower()
            row=conn.execute('SELECT payload FROM snapshots WHERE domain=? ORDER BY stamp DESC LIMIT 1',(domain,)).fetchone()
            previous[domain]=json.loads(row[0]) if row else {}
    finally:conn.close()
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):scan_v21(cfg,db,out,model_name,make_pdf)
    paths=json.loads(buf.getvalue().strip().splitlines()[-1])
    j=Path(paths['json']);report=json.loads(j.read_text(encoding='utf-8'))
    conn=sqlite3.connect(db)
    try:
        snapshots={}
        for site in [cfg['primary']]+cfg['competitors']:
            domain=urlsplit(site['url']).hostname.lower()
            row=conn.execute('SELECT payload FROM snapshots WHERE domain=? ORDER BY stamp DESC LIMIT 1',(domain,)).fetchone()
            snapshots[domain]=json.loads(row[0]) if row else {}
    finally:conn.close()
    report=enrich_v3_report(report,snapshots,previous)
    j3=j.with_name(j.name.replace('v21','v30'));j3.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    md=j3.with_suffix('.md')
    lines=[report_md(report),'\n## PANDORA v3 — Strategic intelligence\n']
    for r in report['results']:
        s=r['strategic_intelligence'];lines.extend([f"### {r['name']}",f"Topic-overlap score: {s['score']}/1000 ({s['level']})",
            f"Authorship metadata changes: {len(r['authorship_intelligence']['changes'])}",f"Editorial reviews suggested: {len(r['priority_queue'])}",''])
        for item in s['decisions'][:30]:lines.append(f"- {item['competitor_url']} — {item['action']} — {item['belongs_to_site']} (similarity {item['similarity']})")
    md.write_text('\n'.join(lines),encoding='utf-8')
    paths['json']=str(j3);paths['markdown']=str(md)
    if make_pdf:
        pdf=j3.with_suffix('.pdf');pdf_report(report,pdf);paths['pdf']=str(pdf)
    print(json.dumps(paths,ensure_ascii=False))

selftest_v21=selftest
def selftest():
    selftest_v21()
    p={'title':'Como fazer SEO local','h1':'SEO local','description':'Guia','text':'SEO local para empresas',
       'author':'Ana','author_evidence':{'meta_author':'Ana'},'schema_types':['Article']}
    q=dict(p,author='Bruno',author_evidence={'meta_author':'Bruno'})
    assert authorship_drift({'u':p},{'u':q})[0]['priority']=='high'
    assert business_fit(p,p,.9)['action']=='review_existing_page'
    assert competitive_context({}, {'u':p},[])['score'] is None
    assert author_profile(p)['verification']=='publisher_claim_only'
    print('V3 SELFTEST PASS: authorship drift, business fit, evidence guardrails')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=['init','scan','selftest'])
    ap.add_argument('--config',default='pandora_competitor.json')
    ap.add_argument('--db',default='pandora_competitor.sqlite3')
    ap.add_argument('--out',default='reports')
    ap.add_argument('--embedding-model',default=None,help='Optional sentence-transformers model path/name; if unavailable falls back to lexical')
    ap.add_argument('--pdf',action='store_true',help='Generate PDF; requires reportlab')
    args=ap.parse_args()
    if args.command=='selftest':selftest();return
    if args.command=='init':
        path=Path(args.config)
        if path.exists():raise SystemExit('Config exists; refusing to overwrite')
        cfg={'primary':{'name':'Meu site','url':'https://example.org/'},'competitors':[{'name':'Concorrente A','url':'https://example.com/'}],
             'max_pages':50,'delay_seconds':1.0}
        path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8');print(path);return
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
    scan(cfg,args.db,args.out,args.embedding_model,args.pdf)

# v3.1: historical forensic intelligence (non-destructive extension).
scan_v30=scan
import io as _io, contextlib as _contextlib

def forensic_history(db, domain, now_stamp, days=(30,60,90)):
    """Observed snapshots only; no interpolation or fabricated week-by-week activity."""
    conn=sqlite3.connect(db)
    try:
        rows=conn.execute('SELECT stamp,payload FROM snapshots WHERE domain=? AND stamp<=? ORDER BY stamp',(domain,now_stamp)).fetchall()
    finally:conn.close()
    current=dt.datetime.strptime(now_stamp,'%Y%m%dT%H%M%S%fZ').replace(tzinfo=dt.timezone.utc)
    windows={}
    for days_back in days:
        eligible=[]
        for stamp,payload in rows:
            when=dt.datetime.strptime(stamp,'%Y%m%dT%H%M%S%fZ').replace(tzinfo=dt.timezone.utc)
            if current-dt.timedelta(days=days_back)<=when<=current:eligible.append((stamp,json.loads(payload)))
        transitions=[]
        for (prev_stamp,prev),(next_stamp,nxt) in zip(eligible,eligible[1:]):
            events=compare_snapshots(prev,nxt)
            transitions.append({'from':prev_stamp,'to':next_stamp,'events':events,'total':len(events),
                'authorship_events':sum(bool(e['author_change']) for e in events)})
        windows[str(days_back)]={'snapshots':len(eligible),'transitions':transitions,
            'total_observed_changes':sum(t['total'] for t in transitions),
            'author_change_events':sum(t['authorship_events'] for t in transitions),
            'coverage':'insufficient_history' if len(eligible)<2 else 'observed_transitions_only'}
    return windows

def forensic_provenance(snapshots):
    evidence=[]
    for url,page in sorted(snapshots.items()):
        body=page.get('text','')
        evidence.append({'url':url,'html_sha256':page.get('html_sha256',page.get('hash')),'content_sha256':page.get('hash'),
            'extracted_text_sha256':hashlib.sha256(body.encode('utf-8')).hexdigest() if body else None,
            'author_claim':page.get('author') or None,
            'date_modified_claim':page.get('modified') or None,
            'collection_status':'failed' if 'error' in page else 'parsed',
            'verification':'publisher_metadata_only'})
    return evidence

def scan(cfg,db,out,model_name=None,make_pdf=False):
    """Run v3 pipeline then enrich with 30/60/90-day evidence and coverage."""
    buf=_io.StringIO()
    with _contextlib.redirect_stdout(buf):scan_v30(cfg,db,out,model_name,make_pdf=False)
    lines=buf.getvalue().strip().splitlines()
    paths=json.loads(lines[-1]); oldpath=Path(paths['json'])
    report=json.loads(oldpath.read_text(encoding='utf-8'))
    stamp=report['timestamp'];conn=sqlite3.connect(db)
    try:
        snaps={}
        for d in [report['primary']]+[r['domain'] for r in report['results']]:
            row=conn.execute('SELECT payload FROM snapshots WHERE domain=? AND stamp=?',(d,stamp)).fetchone()
            snaps[d]=json.loads(row[0]) if row else {}
    finally:conn.close()
    report['version']=VERSION
    report['forensic_protocol']={'evidence':'SHA256 hashes of retrieved HTML and extracted text',
      'temporal_windows_days':[30,60,90],'deletion_policy':'absence in limited crawl is NOT deletion',
      'authorship_policy':'publisher declarations only; identity and credentials not independently verified',
      'competition_policy':'content overlap proxy, not SERP/market share competition'}
    report['primary_forensic']={'history':forensic_history(db,report['primary'],stamp),
        'evidence':forensic_provenance(snaps[report['primary']])}
    for r in report['results']:
        d=r['domain'];r['forensic_history']=forensic_history(db,d,stamp)
        r['evidence_manifest']=forensic_provenance(snaps[d])
        r['risk_flags']=[]
        for event in r['authorship_intelligence']['changes']:
            r['risk_flags'].append({'type':'authorship_metadata_drift','url':event['url'],
                'priority':event['priority'],'evidence_grade':'publisher_claim',
                'review':'Confirm biography, byline and supporting references manually'})
        r['coverage']['crawl_completeness']='unknown_bounded_crawl'
        r['competition_classification']={'direct':'not_verified','indirect':'not_verified',
            'editorial_overlap':r['strategic_intelligence']['level'],
            'geographic':'not_verified','reason':'No independent SERP, customer or market data provided'}
    newpath=oldpath.with_name(oldpath.name.replace('v30','v31'))
    newpath.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    md=newpath.with_suffix('.md')
    content=[f'# PANDORA COMPETITOR Ω v{VERSION} — {stamp}',
        '',f'Primary: {report["primary"]}',
        'WARNING: competitive score is a topical-overlap proxy, not proven ranking or market competition.','']
    for r in report['results']:
        content.extend([f'## {r["name"]} ({r["domain"]})',
            f'Overlap score: {r["strategic_intelligence"]["score"]}/1000',
            f'Author changes: {len(r["authorship_intelligence"]["changes"])}',
            f'Coverage: {r["coverage"]["parsed"]} parsed of {r["coverage"]["pages"]} attempted', ''])
        for days_back,window in r['forensic_history'].items():
            content.append(f'- {days_back}d: {window["snapshots"]} snapshots; {window["total_observed_changes"]} observed changes; {window["coverage"]}')
        for e in r['risk_flags'][:25]:content.append(f'- AUTHOR ALERT: {e["url"]}')
        for d in r['strategic_intelligence']['decisions'][:25]:
            content.append(f'- {d["competitor_url"]} => {d["action"]} ({d["belongs_to_site"]})')
        content.append('')
    md.write_text('\n'.join(content),encoding='utf-8')
    for name in (oldpath.name.replace('v30','v21'),oldpath.name,oldpath.name.replace('v30','v21').replace('.json','.md'),oldpath.with_suffix('.md').name):
        (oldpath.parent/name).unlink(missing_ok=True)
    paths.update(json=str(newpath),markdown=str(md))
    if make_pdf:
        pdf=newpath.with_suffix('.pdf')
        pdf_report(report,pdf)
        paths['pdf']=str(pdf)
    print(json.dumps(paths,ensure_ascii=False))

def selftest_v31():
    selftest()
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        db=Path(tmp)/'x.db';conn=sqlite3.connect(db)
        conn.execute('CREATE TABLE snapshots(domain TEXT,stamp TEXT,payload TEXT,PRIMARY KEY(domain,stamp))')
        t1='20261001T100000000000Z';t2='20261008T100000000000Z'
        a={'https://example.org/':{'author':'Ana','text':'alpha','hash':'1'}}
        b={'https://example.org/':{'author':'Bruno','text':'beta','hash':'2'}}
        for t,x in ((t1,a),(t2,b)):
            conn.execute('INSERT INTO snapshots VALUES(?,?,?)',('example.org',t,json.dumps(x)))
        conn.commit();conn.close()
        h=forensic_history(str(db),'example.org',t2)
        assert h['30']['snapshots']==2 and h['30']['author_change_events']==1
        assert h['60']['total_observed_changes']==1
        assert forensic_provenance(b)[0]['author_claim']=='Bruno'
    print('V3.1 SELFTEST PASS: temporal windows, authorship drift, evidence manifest')
    x=extract('<html><head><link rel><meta property><title>T</title></head><body><h1>H</h1></body></html>','https://e.org/')
    assert x['title']=='T' and x['h1']=='H'
    a=extract('<html><head><title>T</title><script>var n="1"</script></head><body><p>x</p></body></html>','https://e.org/')
    b=extract('<html><head><title>T</title><script>var n="2"</script></head><body><p>x</p></body></html>','https://e.org/')
    assert content_hash(a)==content_hash(b)
    assert compare_snapshots({'u':dict(a,hash=content_hash(a))},{'u':dict(b,hash=content_hash(b))})==[]
    assert same_site('www.e.org','e.org') and same_site('E.org','www.e.org') and not same_site('x.org','e.org')
    print('V3.1.1 SELFTEST PASS: valueless attributes, content hash, www variants')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=['init','scan','selftest'])
    ap.add_argument('--config',default='pandora_competitor.json')
    ap.add_argument('--db',default='pandora_competitor.sqlite3')
    ap.add_argument('--out',default='reports')
    ap.add_argument('--embedding-model',default=None)
    ap.add_argument('--pdf',action='store_true')
    args=ap.parse_args()
    if args.command=='selftest':selftest_v31();return
    if args.command=='init':
        p=Path(args.config)
        if p.exists():raise SystemExit('Config exists; refusing to overwrite')
        p.write_text(json.dumps({'primary':{'name':'My site','url':'https://example.org/'},
          'competitors':[{'name':'Competitor','url':'https://example.com/'}],
          'max_pages':50,'delay_seconds':1.0},indent=2),encoding='utf-8')
        print(p);return
    try:
        cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
        scan(cfg,args.db,args.out,args.embedding_model,args.pdf)
    except (OSError,ValueError,KeyError) as exc:
        raise SystemExit(f'ERRO: {exc}')
if __name__=='__main__':main()
