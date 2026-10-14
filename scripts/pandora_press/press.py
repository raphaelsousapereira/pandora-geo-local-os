#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PANDORA PRESSROOM Ω v1.3.0 — registro cronológico e citável (stdlib only).

Uso: python pandora_pressroom_omega_v1_2_0.py --help
Não valida automaticamente a veracidade de declarações; evidências são metadados.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import html
import io
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.request import Request
from urllib.parse import urljoin, urlsplit
from urllib.error import URLError
import json
import re
import sqlite3
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

VERSION = '1.3.0'
KINDS = {'book':'Book','chapter':'Chapter','paper':'ScholarlyArticle','preprint':'ScholarlyArticle','article':'Article','interview':'Article','press':'NewsArticle','talk':'Event','podcast':'CreativeWork','event':'Event','software':'SoftwareSourceCode','framework':'CreativeWork','award':'CreativeWork','institutional':'CreativeWork','partnership':'CreativeWork','collaboration':'CreativeWork','course':'Course','workshop':'Event','other':'CreativeWork'}
EVIDENCE_TYPES = {'author_statement','website','interview','publisher','repository','archive','document','other'}
STATUSES = {'declared','pending','verified','conflicted','corrected','retracted'}
SCHEMA = '''PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS authors (id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT, description TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS records (
 id TEXT PRIMARY KEY, author_id TEXT NOT NULL REFERENCES authors(id), kind TEXT NOT NULL,
 title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '', quote TEXT NOT NULL DEFAULT '',
 event_date TEXT, publication_date TEXT, date_precision TEXT NOT NULL DEFAULT 'unknown',
 venue TEXT, publisher TEXT, url TEXT, identifier TEXT, status TEXT NOT NULL DEFAULT 'declared',
 topics_json TEXT NOT NULL DEFAULT '[]', related_json TEXT NOT NULL DEFAULT '[]',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS ix_records_timeline ON records(author_id,event_date,publication_date,id);
CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, record_id TEXT NOT NULL REFERENCES records(id), source_url TEXT, source_note TEXT, source_type TEXT NOT NULL DEFAULT 'author_statement', added_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_evidence_record ON evidence(record_id);
CREATE TABLE IF NOT EXISTS evidence_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, evidence_id TEXT NOT NULL, record_id TEXT NOT NULL, payload_json TEXT NOT NULL, previous_hash TEXT, entry_hash TEXT NOT NULL, added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidates (id TEXT PRIMARY KEY, author_id TEXT NOT NULL REFERENCES authors(id), source_url TEXT NOT NULL, source_hash TEXT NOT NULL, title TEXT NOT NULL, candidate_date TEXT, kind TEXT NOT NULL, excerpt TEXT NOT NULL, discovered_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', record_id TEXT, UNIQUE(author_id,source_url,source_hash));
CREATE TABLE IF NOT EXISTS candidate_signals (candidate_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidate_reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id TEXT NOT NULL, action TEXT NOT NULL, reason TEXT, reviewed_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_candidates_author ON candidates(author_id,status);
CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, record_id TEXT NOT NULL REFERENCES records(id), revision INTEGER NOT NULL, changed_at TEXT NOT NULL, reason TEXT NOT NULL, before_json TEXT, after_json TEXT NOT NULL, previous_hash TEXT, entry_hash TEXT NOT NULL);
'''
FIELDS = {'kind','title','summary','quote','event_date','publication_date','date_precision','venue','publisher','url','identifier','status','topics','related'}

def same_site(host, root_host):
    strip=lambda h:(h or '').lower().removeprefix('www.')
    return strip(host)==strip(root_host)

def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
def dumps(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',',':'))
def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db

def validate_date(value):
    if value in (None,''): return None,'unknown'
    if not isinstance(value,str): raise ValueError('data deve ser string ISO')
    if re.fullmatch(r'\d{4}',value):
        if not 1 <= int(value) <= 9999: raise ValueError('ano inválido')
        return value,'year'
    if re.fullmatch(r'\d{4}-\d{2}',value):
        dt.date.fromisoformat(value+'-01'); return value,'month'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        dt.date.fromisoformat(value); return value,'day'
    raise ValueError('data deve ser AAAA, AAAA-MM ou AAAA-MM-DD')

def validate_url(value):
    if not value: return None
    p=urlparse(value)
    if p.scheme not in ('http','https') or not p.netloc or p.username or p.password: raise ValueError('URL inválida: use http(s) sem credenciais')
    return value

def validate_record(payload, old=None):
    if not isinstance(payload,dict): raise ValueError('registro deve ser objeto JSON')
    unknown=set(payload)-FIELDS
    if unknown: raise ValueError('campos desconhecidos: '+', '.join(sorted(unknown)))
    d={k:old[k] for k in FIELDS if old and k in old}
    d.update(payload)
    if not isinstance(d.get('title'),str) or not d['title'].strip(): raise ValueError('title obrigatório')
    d['title']=d['title'].strip()
    if d.get('kind','other') not in KINDS: raise ValueError('kind inválido')
    d.setdefault('kind','other')
    if d.get('status','declared') not in STATUSES: raise ValueError('status inválido')
    d.setdefault('status','declared')
    for key in ('event_date','publication_date'):
        d[key],precision=validate_date(d.get(key))
        if key=='event_date': event_precision=precision
        else: publication_precision=precision
    d['date_precision']=event_precision if d['event_date'] else publication_precision
    for key in ('url',): d[key]=validate_url(d.get(key))
    for key in ('summary','quote','venue','publisher','identifier'):
        if d.get(key) is not None and not isinstance(d[key],str): raise ValueError(key+' deve ser texto')
        d[key]=d.get(key) or ''
    for key in ('topics','related'):
        if not isinstance(d.get(key,[]),list) or not all(isinstance(x,str) for x in d.get(key,[])): raise ValueError(key+' deve ser lista de textos')
        d[key]=list(dict.fromkeys(d.get(key,[])))
    return d

def record_dict(row):
    d=dict(row)
    d['topics']=json.loads(d.pop('topics_json'))
    d['related']=json.loads(d.pop('related_json'))
    return d

def save(db, author_id, payload, record_id=None, reason='registro inicial'):
    if not db.execute('SELECT 1 FROM authors WHERE id=?',(author_id,)).fetchone(): raise ValueError('autor não encontrado')
    previous=None
    if record_id:
        row=db.execute('SELECT * FROM records WHERE id=? AND author_id=?',(record_id,author_id)).fetchone()
        if not row: raise ValueError('registro não encontrado')
        previous=record_dict(row)
    d=validate_record(payload,previous)
    stamp=now()
    rid=record_id or str(uuid.uuid4())
    revision=(previous['revision']+1) if previous else 1
    if previous:
        db.execute('''UPDATE records SET kind=?,title=?,summary=?,quote=?,event_date=?,publication_date=?,date_precision=?,venue=?,publisher=?,url=?,identifier=?,status=?,topics_json=?,related_json=?,updated_at=?,revision=? WHERE id=?''',
            (d['kind'],d['title'],d['summary'],d['quote'],d['event_date'],d['publication_date'],d['date_precision'],d['venue'],d['publisher'],d['url'],d['identifier'],d['status'],dumps(d['topics']),dumps(d['related']),stamp,revision,rid))
    else:
        db.execute('''INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (rid,author_id,d['kind'],d['title'],d['summary'],d['quote'],d['event_date'],d['publication_date'],d['date_precision'],d['venue'],d['publisher'],d['url'],d['identifier'],d['status'],dumps(d['topics']),dumps(d['related']),stamp,stamp,revision))
    after=record_dict(db.execute('SELECT * FROM records WHERE id=?',(rid,)).fetchone())
    last=db.execute('SELECT entry_hash FROM history WHERE record_id=? ORDER BY id DESC LIMIT 1',(rid,)).fetchone()
    prior=last['entry_hash'] if last else None
    canonical=dumps({'record_id':rid,'revision':revision,'changed_at':stamp,'reason':reason,'before':previous,'after':after,'previous_hash':prior})
    db.execute('INSERT INTO history(record_id,revision,changed_at,reason,before_json,after_json,previous_hash,entry_hash) VALUES(?,?,?,?,?,?,?,?)',
               (rid,revision,stamp,reason,dumps(previous) if previous else None,dumps(after),prior,digest(canonical)))
    return after

def list_records(db,author_id):
    rows=db.execute('''SELECT * FROM records WHERE author_id=? ORDER BY CASE WHEN COALESCE(event_date,publication_date) IS NULL THEN 1 ELSE 0 END, COALESCE(event_date,publication_date), id''',(author_id,)).fetchall()
    return [record_dict(x) for x in rows]

PUBLIC_STATUSES=('declared','pending','verified','corrected')

def public_records(db,author_id,statuses=PUBLIC_STATUSES):
    """Registros exportáveis: por padrão exclui 'conflicted' e 'retracted'."""
    return [r for r in list_records(db,author_id) if r['status'] in statuses]

def jsonld(db,author_id,statuses=PUBLIC_STATUSES):
    a=db.execute('SELECT * FROM authors WHERE id=?',(author_id,)).fetchone()
    if not a: raise ValueError('autor não encontrado')
    person={'@type':'Person','@id':a['url']+'#person' if a['url'] else 'urn:uuid:'+a['id'],'name':a['name']}
    if a['url']: person['url']=a['url']
    if a['description']: person['description']=a['description']
    graph=[person]
    records=public_records(db,author_id,statuses)
    url_count={}
    for r in records:
        if r['url']: url_count[r['url']]=url_count.get(r['url'],0)+1
    for r in records:
        rid=r['url'] if r['url'] and url_count[r['url']]==1 else (r['url']+'#'+r['id'] if r['url'] else 'urn:uuid:'+r['id'])
        role='performer' if KINDS[r['kind']]=='Event' else 'creator'
        item={'@type':KINDS[r['kind']],'@id':rid,'name':r['title'],role:{'@id':person['@id']}}
        if r['summary']: item['description']=r['summary']
        if r['publication_date']: item['datePublished']=r['publication_date']
        if r['event_date'] and r['kind'] in ('talk','event'): item['startDate']=r['event_date']
        if r['url']: item['url']=r['url']
        if r['identifier']: item['identifier']=r['identifier']
        if r['publisher']: item['publisher']={'@type':'Organization','name':r['publisher']}
        if r['topics']: item['keywords']=r['topics']
        graph.append(item)
    return {'@context':'https://schema.org','@graph':graph}

def export_html(db,author_id,statuses=PUBLIC_STATUSES):
    a=db.execute('SELECT * FROM authors WHERE id=?',(author_id,)).fetchone()
    if not a: raise ValueError('autor não encontrado')
    e=html.escape
    sections=[]
    for r in public_records(db,author_id,statuses):
        date=r['event_date'] or r['publication_date'] or 'Data desconhecida'
        link=('<p><a href="'+e(r['url'],quote=True)+'" rel="noopener noreferrer">Fonte / publicação</a></p>') if r['url'] else ''
        quote=('<blockquote>'+e(r['quote'])+'</blockquote>') if r['quote'] else ''
        details=''.join('<p><strong>'+e(k)+':</strong> '+e(str(r[k]))+'</p>' for k in ('venue','publisher','identifier') if r[k])
        details+=''.join('<p><strong>'+e(k)+':</strong> '+e(', '.join(r[k]))+'</p>' for k in ('topics','related') if r[k])
        sections.append('<article><time>'+e(date)+'</time><h2>'+e(r['title'])+'</h2><p>'+e(r['kind'])+' · '+e(r['status'])+'</p><p>'+e(r['summary'])+'</p>'+details+quote+link+'</article>')
    ld=dumps(jsonld(db,author_id,statuses)).replace('<','\\u003c')
    description=e('Cronologia de publicações e participações de '+a['name'],quote=True)
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="'+description+'"><title>Sala de Imprensa — '+e(a['name'])+'</title><script type="application/ld+json">'+ld+'</script><style>body{font:16px/1.6 system-ui,sans-serif;max-width:850px;margin:auto;padding:2rem;color:#eee;background:#151515}article{border-top:1px solid #555;padding:1.5rem 0}time{color:#9f9}a{color:#aef}blockquote{border-left:3px solid #9f9;padding-left:1rem}@media(prefers-color-scheme:light){body{background:#fff;color:#222}article{border-color:#aaa}time{color:#285}a{color:#1766a3}}</style></head><body><main><h1>Sala de Imprensa — '+e(a['name'])+'</h1><p>Registros cronológicos; a classificação de verificação acompanha cada item.</p>'+''.join(sections)+'</main></body></html>'

def evidence_add(db,record_id,source_url=None,source_note=None,source_type='author_statement'):
    source_url=validate_url(source_url)
    if source_type not in EVIDENCE_TYPES: raise ValueError('source_type inválido')
    if not source_url and not source_note: raise ValueError('informe source_url ou source_note')
    if not db.execute('SELECT 1 FROM records WHERE id=?',(record_id,)).fetchone(): raise ValueError('registro não encontrado')
    eid=str(uuid.uuid4()); stamp=now()
    db.execute('INSERT INTO evidence VALUES (?,?,?,?,?,?)',(eid,record_id,source_url,source_note,source_type,stamp))
    payload={'id':eid,'record_id':record_id,'source_url':source_url,'source_note':source_note,'source_type':source_type,'added_at':stamp}
    last=db.execute('SELECT entry_hash FROM evidence_audit ORDER BY id DESC LIMIT 1').fetchone()
    previous=last['entry_hash'] if last else None
    entry_hash=digest(dumps({'payload':payload,'previous_hash':previous}))
    db.execute('INSERT INTO evidence_audit(evidence_id,record_id,payload_json,previous_hash,entry_hash,added_at) VALUES(?,?,?,?,?,?)',(eid,record_id,dumps(payload),previous,entry_hash,stamp))
    return eid

def verify_history(db,record_id):
    prev=None
    rows=db.execute('SELECT * FROM history WHERE record_id=? ORDER BY id',(record_id,)).fetchall()
    for row in rows:
        obj={'record_id':row['record_id'],'revision':row['revision'],'changed_at':row['changed_at'],'reason':row['reason'],'before':json.loads(row['before_json']) if row['before_json'] else None,'after':json.loads(row['after_json']),'previous_hash':row['previous_hash']}
        if row['previous_hash']!=prev or digest(dumps(obj))!=row['entry_hash']: return False
        prev=row['entry_hash']
    return bool(rows)

def verify_evidence(db):
    previous=None
    for x in db.execute('SELECT * FROM evidence_audit ORDER BY id'):
        payload=json.loads(x['payload_json'])
        if x['previous_hash']!=previous or x['entry_hash']!=digest(dumps({'payload':payload,'previous_hash':previous})): return False
        current=db.execute('SELECT * FROM evidence WHERE id=?',(x['evidence_id'],)).fetchone()
        if current is None or dict(current)!=payload: return False
        previous=x['entry_hash']
    return db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0]==db.execute('SELECT COUNT(*) FROM evidence_audit').fetchone()[0]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__();self.title='';self.text=[];self.links=[];self.meta={};self.ld=[];self._title=False;self._skip=0;self._ld=False;self._ldbuf=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('script','style','noscript'):
            self._skip+=1
            if tag=='script' and a.get('type','').lower()=='application/ld+json':self._ld=True;self._ldbuf=[]
        if tag=='title':self._title=True
        if not self._skip and tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='meta' and a.get('content'):
            k=a.get('property') or a.get('name')
            if k:self.meta[k.lower()]=a['content']
    def handle_endtag(self,tag):
        if tag=='title':self._title=False
        if tag in ('script','style','noscript'):
            if tag=='script' and self._ld:self.ld.append(''.join(self._ldbuf));self._ld=False
            self._skip=max(0,self._skip-1)
    def handle_data(self,data):
        if self._ld:self._ldbuf.append(data)
        elif self._title:self.title+=data
        elif not self._skip and data.strip():self.text.append(data.strip())

def safe_public_url(url):
    """Checks DNS at validation time, but does NOT pin connection IP.

    DNS rebinding / TOCTOU remains possible. Do not use against hostile domains
    in privileged networks; run crawler in network-isolated sandbox.
    """
    p=urlsplit(validate_url(url) or '')
    if not p.hostname or p.port not in (None,80,443):raise ValueError('host ou porta inválidos')
    if p.hostname.lower() in ('localhost',) or p.hostname.lower().endswith(('.local','.internal')):raise ValueError('host privado')
    for result in socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM):
        ip=ipaddress.ip_address(result[4][0])
        if not ip.is_global:raise ValueError('endereço IP não público')
    return url

def fetch_page(url):
    # Redirects blocked: a redirect target must be validated separately by operator.
    from urllib.request import build_opener, HTTPRedirectHandler
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise ValueError('redirecionamento bloqueado')
    safe_public_url(url)
    opener=build_opener(NoRedirect())
    req=Request(url,headers={'User-Agent':'PANDORA-Pressroom/'+VERSION+' (+manual-review)','Accept':'text/html'})
    with opener.open(req,timeout=8) as resp:
        if 'text/html' not in resp.headers.get('Content-Type','').lower():raise ValueError('conteúdo não HTML')
        raw=resp.read(1_000_001)
        if len(raw)>1_000_000:raise ValueError('página maior que 1 MB')
        return raw.decode(resp.headers.get_content_charset() or 'utf-8',errors='replace')

def extract_candidate(url,body):
    parser=PageParser();parser.feed(body)
    text=' '.join(parser.text)
    title=(parser.meta.get('og:title') or parser.title or '').strip()[:250]
    description=(parser.meta.get('description') or parser.meta.get('og:description') or text[:450]).strip()[:600]
    date=parser.meta.get('article:published_time','')[:10]
    kind='other';kind_source='none'
    corpus=(title+' '+url).lower()
    for needle,k in [('livro','book'),('book','book'),('paper','paper'),('pesquisa','paper'),('entrevista','interview'),('podcast','podcast'),('palestra','talk'),('artigo','article'),('noticia','press'),('notícia','press')]:
        if needle in corpus:kind=k;kind_source='keyword';break
    for ld in parser.ld:
        try:
            data=json.loads(ld)
            nodes=data if isinstance(data,list) else data.get('@graph',[data]) if isinstance(data,dict) else []
            for node in nodes:
                if not isinstance(node,dict):continue
                t=node.get('@type',[]);t=[t] if isinstance(t,str) else t
                if 'Book' in t:kind='book';kind_source='jsonld'
                if 'ScholarlyArticle' in t:kind='paper';kind_source='jsonld'
                if 'NewsArticle' in t:kind='press';kind_source='jsonld'
                if 'Article' in t and kind=='other':kind='article';kind_source='jsonld'
                date=date or str(node.get('datePublished',''))[:10]
        except (ValueError,TypeError):pass
    if date:
        try:date=validate_date(date)[0]
        except ValueError:date=None
    return {'url':url,'title':title,'date':date,'kind':kind,'kind_source':kind_source,'excerpt':description,'links':parser.links}

def collect_site(db,author_id,root,max_pages=12,fetcher=fetch_page):
    if not 1<=max_pages<=50:raise ValueError('max-pages deve ser 1..50')
    if not db.execute('SELECT 1 FROM authors WHERE id=?',(author_id,)).fetchone():raise ValueError('autor não encontrado')
    safe_public_url(root)
    host=urlsplit(root).hostname
    queue=[root];seen=set();added=0;errors=[]
    while queue and len(seen)<max_pages:
        url=queue.pop(0).split('#')[0]
        if url in seen:continue
        seen.add(url)
        try:
            safe_public_url(url)
            data=extract_candidate(url,fetcher(url))
            if data['title']:
                sha=digest(dumps({k:data[k] for k in ('title','date','kind','excerpt')}))
                with db:
                    cur=db.execute('INSERT OR IGNORE INTO candidates(id,author_id,source_url,source_hash,title,candidate_date,kind,excerpt,discovered_at) VALUES(?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),author_id,url,sha,data['title'],data['date'],data['kind'],data['excerpt'],now()))
                    added+=cur.rowcount
            for link in data['links']:
                target=urljoin(url,link).split('#')[0]
                parts=urlsplit(target)
                if parts.scheme in ('http','https') and same_site(parts.hostname,host) and target not in seen and target not in queue and len(queue)<100:queue.append(target)
        except (ValueError,URLError,OSError,UnicodeError) as ex:errors.append({'url':url,'error':str(ex)[:150]})
    return {'visited':len(seen),'new_candidates':added,'errors':errors,'note':'Candidatos não são fatos confirmados. Aprovação humana obrigatória.'}

def approve_candidate(db,author_id,candidate_id,kind=None,date=None):
    c=db.execute('SELECT * FROM candidates WHERE id=? AND author_id=?',(candidate_id,author_id)).fetchone()
    if not c or c['status']!='pending':raise ValueError('candidato inexistente ou já revisado')
    # Approval is explicit; never auto-verified.
    summary=c['excerpt'].split('\n[DISCOVERY] ')[0].strip()
    payload={'title':c['title'],'kind':kind or c['kind'],'publication_date':date or c['candidate_date'],'summary':summary,'url':c['source_url'],'status':'pending'}
    with db:
        rec=save(db,author_id,payload,reason='candidato aprovado manualmente')
        evidence_add(db,rec['id'],source_url=c['source_url'],source_note='Página de origem; verificação factual pendente',source_type='website')
        db.execute("UPDATE candidates SET status='approved',record_id=? WHERE id=?",(rec['id'],candidate_id))
        db.execute('INSERT INTO candidate_reviews(candidate_id,action,reason,reviewed_at) VALUES(?,?,?,?)',(candidate_id,'approved','',now()))
    return {'record_id':rec['id'],'status':'pending','candidate_id':candidate_id}


def report_pdf(db, author_id, output, title='Relatório de Sala de Imprensa'):
    """Relatório editorial PDF com fontes, estados e cronologia. Requer reportlab."""
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
    except ImportError as exc:
        raise ValueError('Para gerar PDF, instale reportlab: pip install reportlab') from exc
    a=db.execute('SELECT * FROM authors WHERE id=?',(author_id,)).fetchone()
    if a is None: raise ValueError('autor não encontrado')
    records=list_records(db,author_id)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='PressTitle',parent=styles['Title'],fontSize=18,leading=23,textColor=colors.HexColor('#182b25'),spaceAfter=12))
    styles.add(ParagraphStyle(name='PressMeta',parent=styles['Normal'],fontSize=9,leading=13,textColor=colors.HexColor('#505b58'),spaceAfter=6))
    styles.add(ParagraphStyle(name='PressItem',parent=styles['Heading2'],fontSize=12,leading=16,spaceBefore=14,spaceAfter=6))
    esc=html.escape
    story=[Paragraph(esc(title),styles['PressTitle']),Paragraph('Autor: '+esc(a['name']),styles['Normal']),
           Paragraph('Emitido em '+dt.datetime.now(dt.timezone.utc).strftime('%d/%m/%Y %H:%M UTC')+' | Registros: '+str(len(records)),styles['PressMeta']),
           Paragraph('Estados de verificação não equivalem a comprovação independente. Fontes e registros exigem análise crítica.',styles['PressMeta']),Spacer(1,10)]
    if a['url']: story.append(Paragraph('Site do autor: '+esc(a['url']),styles['PressMeta']))
    for r in records:
        block=[Paragraph(esc((r['event_date'] or r['publication_date'] or 'Sem data')+' — '+r['title']),styles['PressItem']),
               Paragraph('Categoria: '+esc(r['kind'])+' | Estado: '+esc(r['status'])+' | Precisão: '+esc(r['date_precision']),styles['PressMeta'])]
        for label,key in [('Síntese','summary'),('Citação','quote'),('Local / veículo','venue'),('Editora / organização','publisher'),('Identificador','identifier'),('Site / fonte principal','url')]:
            if r[key]: block.append(Paragraph('<b>'+label+':</b> '+esc(str(r[key])),styles['Normal']))
        if r['topics']: block.append(Paragraph('<b>Temas:</b> '+esc(', '.join(r['topics'])),styles['Normal']))
        if r['related']: block.append(Paragraph('<b>Relações:</b> '+esc(', '.join(r['related'])),styles['Normal']))
        sources=db.execute('SELECT source_url,source_note,source_type FROM evidence WHERE record_id=? ORDER BY added_at',(r['id'],)).fetchall()
        for ev in sources:
            text=' | '.join(str(x) for x in (ev['source_type'],ev['source_url'],ev['source_note']) if x)
            block.append(Paragraph('<b>Evidência:</b> '+esc(text),styles['PressMeta']))
        story.extend(block)
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=2*cm,leftMargin=2*cm,topMargin=2*cm,bottomMargin=2*cm,title=title,author=a['name'])
    doc.build(story)

def main(argv=None):
    p=argparse.ArgumentParser(description='PANDORA PRESSROOM Ω v'+VERSION)
    p.add_argument('--db',default='pressroom.sqlite3')
    p.add_argument('--version',action='version',version=VERSION)
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('author-list')
    a=sub.add_parser('author-edit');a.add_argument('--id',required=True);a.add_argument('--name');a.add_argument('--url');a.add_argument('--description')
    a=sub.add_parser('author-add');a.add_argument('--name',required=True);a.add_argument('--url');a.add_argument('--description',default='')
    a=sub.add_parser('add');a.add_argument('--author',required=True);a.add_argument('--file',required=True);a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('update');a.add_argument('--author',required=True);a.add_argument('--id',required=True);a.add_argument('--file',required=True);a.add_argument('--reason',required=True);a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('import');a.add_argument('--author',required=True);a.add_argument('--file',required=True)
    a=sub.add_parser('list');a.add_argument('--author',required=True)
    a=sub.add_parser('evidence-add');a.add_argument('--id',required=True);a.add_argument('--url');a.add_argument('--note');a.add_argument('--type',default='author_statement')
    a=sub.add_parser('history');a.add_argument('--id',required=True)
    a=sub.add_parser('history-verify');a.add_argument('--id');a.add_argument('--all',action='store_true');a.add_argument('--author')
    a=sub.add_parser('evidence-list');a.add_argument('--id',required=True)
    sub.add_parser('evidence-verify')
    a=sub.add_parser('collect');a.add_argument('--author',required=True);a.add_argument('--url',required=True);a.add_argument('--max-pages',type=int,default=12)
    a=sub.add_parser('candidates');a.add_argument('--author',required=True)
    a=sub.add_parser('candidate-approve');a.add_argument('--author',required=True);a.add_argument('--id',required=True);a.add_argument('--kind');a.add_argument('--date')
    a=sub.add_parser('candidate-reject');a.add_argument('--author',required=True);a.add_argument('--id',required=True);a.add_argument('--reason',default='')
    a=sub.add_parser('selftest')
    a=sub.add_parser('report-pdf');a.add_argument('--author',required=True);a.add_argument('--out',required=True);a.add_argument('--title',default='Relatório de Sala de Imprensa')
    a=sub.add_parser('export');a.add_argument('--author',required=True);a.add_argument('--format',choices=['json','jsonld','html','csv'],required=True);a.add_argument('--out',required=True);a.add_argument('--only-verified',action='store_true',help='HTML/JSON-LD só com verified/corrected')
    args=p.parse_args(argv)
    db=None
    try:
        if args.cmd=='selftest':
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                testdb=connect(str(Path(td)/'test.db'))
                with testdb: testdb.execute('INSERT INTO authors VALUES (?,?,?,?,?)',('a','Test',None,'',now()))
                old=save(testdb,'a',{'title':'Old','event_date':'2022'})
                save(testdb,'a',{'title':'New','event_date':'2026'})
                assert [x['title'] for x in list_records(testdb,'a')]==['Old','New']
                assert verify_history(testdb,old['id'])
                with testdb: evidence_add(testdb,old['id'],source_note='manual')
                assert verify_evidence(testdb)
                def mock_fetch(url):
                    return '<html><head><title>Entrevista em 2024</title><meta name="description" content="Entrevista sobre pesquisa"></head><body><article>Entrevista publicada</article></body></html>'
                # DNS validation is mocked only for this isolated test.
                from unittest.mock import patch
                with patch(__name__+'.safe_public_url',lambda url:url):
                    result=collect_site(testdb,'a','https://example.com',max_pages=1,fetcher=mock_fetch)
                assert result['new_candidates']==1
                candidate=testdb.execute('SELECT id FROM candidates').fetchone()['id']
                approved=approve_candidate(testdb,'a',candidate)
                assert approved['status']=='pending'
                assert verify_history(testdb,approved['record_id'])
                assert verify_evidence(testdb)
                assert testdb.execute('SELECT status FROM candidates WHERE id=?',(candidate,)).fetchone()['status']=='approved'
                testdb.close()
            print(dumps({'selftest':'passed'}));return 0
        db=connect(args.db)
        if args.cmd=='author-add':
            args.url=validate_url(args.url);aid=str(uuid.uuid4())
            with db: db.execute('INSERT INTO authors VALUES (?,?,?,?,?)',(aid,args.name,args.url,args.description,now()))
            print(dumps({'author_id':aid}))
        elif args.cmd=='author-list': print(json.dumps([dict(x) for x in db.execute('SELECT * FROM authors ORDER BY name')],ensure_ascii=False,indent=2))
        elif args.cmd=='author-edit':
            old=db.execute('SELECT * FROM authors WHERE id=?',(args.id,)).fetchone()
            if not old: raise ValueError('autor não encontrado')
            with db: db.execute('UPDATE authors SET name=?,url=?,description=? WHERE id=?',(args.name if args.name is not None else old['name'],validate_url(args.url) if args.url is not None else old['url'],args.description if args.description is not None else old['description'],args.id))
            print(dumps({'updated':args.id}))
        elif args.cmd in ('add','update'):
            payload=json.loads(Path(args.file).read_text(encoding='utf-8'))
            if getattr(args,'dry_run',False):
                old=None
                if args.cmd=='update':
                    row=db.execute('SELECT * FROM records WHERE id=? AND author_id=?',(args.id,args.author)).fetchone()
                    if row is None: raise ValueError('registro não encontrado')
                    old=record_dict(row)
                print(dumps({'valid':True,'record':validate_record(payload,old)}))
            else:
                with db: result=save(db,args.author,payload,getattr(args,'id',None),getattr(args,'reason','registro inicial'))
                print(dumps(result))
        elif args.cmd=='import':
            path=Path(args.file)
            if path.suffix.lower()=='.csv':
                with path.open(encoding='utf-8-sig',newline='') as f: data=list(csv.DictReader(f))
                for r in data:
                    for key in ('topics','related'):
                        if key in r: r[key]=[x.strip() for x in (r[key] or '').split('|') if x.strip()]
            else:
                data=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data,list): raise ValueError('importação exige lista de registros')
            ids=[]
            with db:
                for item in data: ids.append(save(db,args.author,item)['id'])
            print(dumps({'imported':len(ids),'ids':ids}))
        elif args.cmd=='list': print(json.dumps(list_records(db,args.author),ensure_ascii=False,indent=2))
        elif args.cmd=='evidence-add':
            with db: eid=evidence_add(db,args.id,args.url,args.note,args.type)
            print(dumps({'evidence_id':eid}))
        elif args.cmd=='history':
            print(json.dumps([dict(x) for x in db.execute('SELECT * FROM history WHERE record_id=? ORDER BY id',(args.id,))],ensure_ascii=False,indent=2))
        elif args.cmd=='history-verify':
            if args.all and args.id: raise ValueError('use --id ou --all, não ambos')
            ids=[x['id'] for x in db.execute('SELECT id FROM records WHERE author_id=?',(args.author,))] if args.all and args.author else ([x['id'] for x in db.execute('SELECT id FROM records')] if args.all else [args.id])
            if not args.all and not args.id: raise ValueError('informe --id ou --all')
            result={i: ('valid' if verify_history(db,i) else 'no_history' if not db.execute('SELECT 1 FROM history WHERE record_id=?',(i,)).fetchone() else 'invalid') for i in ids}
            print(dumps(result));return 0 if all(x=='valid' for x in result.values()) else 2
        elif args.cmd=='evidence-list': print(json.dumps([dict(x) for x in db.execute('SELECT * FROM evidence WHERE record_id=? ORDER BY added_at',(args.id,))],ensure_ascii=False,indent=2))
        elif args.cmd=='evidence-verify':
            ok=verify_evidence(db);print(dumps({'valid':ok}));return 0 if ok else 2
        elif args.cmd=='collect': print(dumps(collect_site(db,args.author,args.url,args.max_pages)))
        elif args.cmd=='candidates': print(json.dumps([dict(x) for x in db.execute('SELECT * FROM candidates WHERE author_id=? ORDER BY candidate_date,discovered_at',(args.author,))],ensure_ascii=False,indent=2))
        elif args.cmd=='candidate-approve': print(dumps(approve_candidate(db,args.author,args.id,args.kind,args.date)))
        elif args.cmd=='candidate-reject':
            with db:
                cur=db.execute("UPDATE candidates SET status='rejected' WHERE id=? AND author_id=? AND status='pending'",(args.id,args.author))
                if not cur.rowcount: raise ValueError('candidato não encontrado ou já revisado')
                db.execute('INSERT INTO candidate_reviews(candidate_id,action,reason,reviewed_at) VALUES(?,?,?,?)',(args.id,'rejected',args.reason,now()))
            print(dumps({'rejected':args.id}))
        elif args.cmd=='report-pdf':
            report_pdf(db,args.author,args.out,args.title)
            print(dumps({'output':args.out,'format':'pdf'}))
        elif args.cmd=='export':
            path=Path(args.out)
            st=('verified','corrected') if args.only_verified else PUBLIC_STATUSES
            if args.format=='json': content=json.dumps(list_records(db,args.author),ensure_ascii=False,indent=2)
            elif args.format=='jsonld': content=json.dumps(jsonld(db,args.author,st),ensure_ascii=False,indent=2)
            elif args.format=='html': content=export_html(db,args.author,st)
            else:
                f=io.StringIO();rows=list_records(db,args.author)
                if rows:
                    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
                    for r in rows: w.writerow({k:dumps(v) if isinstance(v,list) else v for k,v in r.items()})
                content=f.getvalue()
            path.write_text(content,encoding='utf-8');print(dumps({'output':str(path)}))
        return 0
    except (ValueError,sqlite3.Error,OSError,json.JSONDecodeError) as ex:
        print('ERRO: '+str(ex),file=sys.stderr);return 1
    finally:
        if db is not None: db.close()
if __name__=='__main__': sys.exit(main())
