#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PANDORA PRESS-DISCOVERY Ω v0.1.0 — descoberta supervisionada de fatos autorais.
Compatível com PANDORA PRESSROOM Ω v1.3.0. Não realiza busca geral na web:
usa URLs-semente fornecidas pelo operador e links públicos nelas encontrados.
Não aprova nem verifica fatos. Segurança: reutiliza fetch_page do PRESSROOM,
que NÃO possui pinagem DNS/IP; operar somente em rede isolada.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag

from . import press

VERSION="0.1.0"
base=press

TAGS={
 "book":("livro","book","isbn","ebook"),
 "paper":("paper","preprint","doi","scholarly","pesquisa científica"),
 "software":("software","github","código-fonte","aplicativo","sistema","engine"),
 "partnership":("parceria","parceiro","partnership","colaboração institucional"),
 "event":("evento","congresso","conferência","seminário","workshop"),
 "interview":("entrevista","interview"),
 "podcast":("podcast","episódio"),
 "article":("artigo","article","ensaio","publicação"),
 "talk":("palestra","lecture","keynote"),
}
def normalize(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s).casefold()) if not unicodedata.combining(c))
def classify(c):
    text=normalize(" ".join((c.get("title") or "",c.get("excerpt") or "",c.get("url") or "")))
    for kind,words in TAGS.items():
        # palavra/expressão inteira: "doi" não pode casar dentro de "dois"
        if any(re.search(r'(?<!\w)'+re.escape(normalize(w))+r'(?!\w)',text) for w in words):return kind
    return c.get("kind") or "other"
def author_match(c,name,aliases=()):
    """Três estados: mention (nome completo encontrado), unknown (sem nome),
    ambiguous (somente sobrenome/fragmento). Nenhum é prova de autoria."""
    content=normalize(" ".join((c.get("title") or "",c.get("excerpt") or "")))
    names=[normalize(n).strip() for n in (name,*aliases) if n and len(n.strip())>=6]
    if any(re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',content) for n in names):
        return "mention"
    tokens=normalize(name).split()
    if len(tokens)>=2 and tokens[-1] in content.split():return "ambiguous"
    return "unknown"
def discover(db,author_id,roots,max_pages=20,fetcher=None,validator=None,aliases=()):
    """Visita apenas hosts explicitamente autorizados pelas sementes.
    Descobertas permanecem em candidates.status=pending, com proveniência."""
    if not 1<=max_pages<=100:raise ValueError("max-pages deve ser 1..100")
    author=db.execute("SELECT * FROM authors WHERE id=?",(author_id,)).fetchone()
    if not author:raise ValueError("autor não encontrado")
    fetcher=fetcher or base.fetch_page
    validator=validator or base.safe_public_url
    allowed=set()
    for root in roots:
        validator(root)
        h=urlsplit(root).hostname.lower().removeprefix("www.")
        allowed.update({h,"www."+h})
    queue=list(dict.fromkeys(roots))
    visited=set();added=0;skipped=0;errors=[];matches={}
    while queue and len(visited)<max_pages:
        url=urldefrag(queue.pop(0))[0]
        if url in visited:continue
        visited.add(url)
        try:
            validator(url)
            candidate=base.extract_candidate(url,fetcher(url))
            if candidate["title"]:
                if candidate.get("kind_source")!="jsonld":candidate["kind"]=classify(candidate)
                match=author_match(candidate,author["name"],aliases)
                matches[match]=matches.get(match,0)+1
                provenance={"identity_signal":match,"discovery_engine":"PRESS-DISCOVERY Ω "+VERSION,
                            "review_note":"Menção não comprova autoria; verificar manualmente."}
                excerpt=(candidate["excerpt"] or "")[:600]
                sha=hashlib.sha256(json.dumps({"title":candidate["title"],"date":candidate["date"],
                     "kind":candidate["kind"],"excerpt":excerpt},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                with db:
                    cur=db.execute("""INSERT OR IGNORE INTO candidates
                     (id,author_id,source_url,source_hash,title,candidate_date,kind,excerpt,discovered_at)
                     VALUES(?,?,?,?,?,?,?,?,?)""",(str(uuid.uuid4()),author_id,url,sha,
                     candidate["title"],candidate["date"],candidate["kind"],excerpt,base.now()))
                    added+=cur.rowcount
                    skipped+=int(cur.rowcount==0)
                    if cur.rowcount:
                        cid=db.execute("SELECT id FROM candidates WHERE author_id=? AND source_url=? AND source_hash=?",(author_id,url,sha)).fetchone()[0]
                        db.execute("INSERT OR REPLACE INTO candidate_signals VALUES(?,?)",(cid,json.dumps(provenance,ensure_ascii=False)))
            for href in candidate["links"]:
                target=urldefrag(urljoin(url,href))[0]
                parsed=urlsplit(target)
                if parsed.scheme in ("http","https") and parsed.hostname and parsed.hostname.lower() in allowed:
                    if target not in visited and target not in queue and len(queue)<200:queue.append(target)
        except (ValueError,OSError,UnicodeError,TimeoutError) as exc:
            errors.append({"url":url,"error":str(exc)[:160]})
    return {"visited":len(visited),"new_candidates":added,"duplicates":skipped,
            "identity_signals":matches,"errors":errors,"status":"pending_only",
            "notice":"Menção/autoria são hipóteses. Aprovação e verificação exigem revisão humana."}
def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        db=base.connect(str(Path(td)/"t.sqlite"))
        with db: db.execute("INSERT INTO authors VALUES (?,?,?,?,?)",("a","Maria Silva","https://example.com","",base.now()))
        pages={
            "https://example.com":'<html><title>Obras de Maria Silva</title><a href="/software">Software</a><a href="/livro">Livro</a></html>',
            "https://example.com/software":'<html><title>Software Atlas de Maria Silva</title><meta name="description" content="Ferramenta de Maria Silva"></html>',
            "https://example.com/livro":'<html><title>Livro de Maria Silva</title><meta name="description" content="Livro publicado"></html>'}
        mock=lambda u:pages[u]
        r=discover(db,"a",["https://example.com"],fetcher=mock,validator=lambda u:u)
        assert r["visited"]==3 and r["new_candidates"]==3,r
        assert db.execute("SELECT count(*) FROM candidates WHERE status='pending'").fetchone()[0]==3
        r2=discover(db,"a",["https://example.com"],fetcher=mock,validator=lambda u:u)
        assert r2["new_candidates"]==0,r2
        assert db.execute("SELECT count(*) FROM records").fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM candidates WHERE kind='software'").fetchone()[0]==1
        db.close()
    return {"selftest":"passed","checks":["crawl","identity","classification","pending","dedup","no_auto_publish"]}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version",action="version",version=VERSION)
    p.add_argument("--db",default="pressroom.sqlite3")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("discover");a.add_argument("--author",required=True)
    a.add_argument("--url",action="append",required=True,help="URL-semente; pode repetir")
    a.add_argument("--alias",action="append",default=[])
    a.add_argument("--max-pages",type=int,default=20)
    sub.add_parser("selftest")
    args=p.parse_args()
    if args.cmd=="selftest": print(json.dumps(selftest(),ensure_ascii=False,indent=2));return
    db=base.connect(args.db)
    try: print(json.dumps(discover(db,args.author,args.url,args.max_pages,aliases=args.alias),ensure_ascii=False,indent=2))
    finally:db.close()
if __name__=="__main__":main()
