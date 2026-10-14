#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PANDORA SITEMAP & LLMS AUDIT Ω v1.0.0 — auditor de descoberta para buscadores e IAs.

Arquivo único, stdlib only, Python 3.10+. Integra-se ao motor de headings
(scripts/pandora_heading_audit.py) quando ele está no mesmo diretório.

Cobre: robots.txt (incluindo bots de IA por token), sitemaps XML (índice,
urlset, .gz), saúde de cada URL (status, redirects, noindex, canonical, peso,
documento HTML aninhado, headings), cruzamento sitemap × links internos
(órfãs) e a camada GEO: llms.txt e llms-full.txt (estrutura, cobertura,
qualidade de títulos e descrições). Também gera llms.txt, llms-full.txt e uma
página HTML "Mapa do site" a partir do que foi auditado.

Comandos:
 python scripts/pandora_sitemap_audit.py audit https://example.org --json report.json --md report.md
 python scripts/pandora_sitemap_audit.py audit https://example.org --max-urls 500 --delay 1
 python scripts/pandora_sitemap_audit.py audit https://example.org --snapshot ./snap
 python scripts/pandora_sitemap_audit.py generate https://example.org --out-dir ./llms --site-name "Marca"
 python scripts/pandora_sitemap_audit.py verify https://example.org --min-score 800
 python scripts/pandora_sitemap_audit.py selftest

Modo snapshot: um diretório com manifest.json no formato
 {"https://example.org/robots.txt": {"file": "robots.txt", "status": 200,
   "headers": {"content-type": "text/plain"}},
  "https://example.org/old/": {"status": 301, "location": "https://example.org/new/"}}
URLs ausentes do manifest são tratadas como "não capturadas" (sem penalidade
de status). Útil quando a rede bloqueia o domínio e o HTML vem de outra fonte.

LIMITES: score é proxy técnico de descoberta/rastreabilidade, não previsão de
ranking nem de citação. Não executa JavaScript. A presença de llms.txt não
garante leitura por crawlers de IA; robots.txt e HTML continuam decisivos.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import gzip
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser
import unicodedata
import xml.etree.ElementTree as ET

VERSION = '1.0.0'
UA = 'PandoraSitemapAudit/' + VERSION + ' (+technical-audit)'
MAX_SITEMAP_URLS = 50_000
MAX_SITEMAP_BYTES = 50 * 1024 * 1024
SPACE = re.compile(r'\s+')
B64 = re.compile(r'data:[a-z]+/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]{200,}', re.I)
DEFAULT_CONTENT = ('/sample-page/', '/hello-world/', '/pagina-exemplo/', '/ola-mundo/', '/category/uncategorized/',
                   '/category/sem-categoria/')
NON_HTML_EXT = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.zip', '.js', '.css', '.xml', '.txt',
                '.json', '.mp4', '.mp3', '.ico', '.woff', '.woff2')

# Tokens de user-agent relevantes. role: search = busca/resposta em tempo real (bloquear tira a
# marca das respostas); training = coleta para treino (bloqueio é decisão de política, não erro).
AI_BOTS = [
    ('Googlebot', 'Google', 'search'), ('Bingbot', 'Microsoft', 'search'),
    ('OAI-SearchBot', 'OpenAI', 'search'), ('ChatGPT-User', 'OpenAI', 'search'), ('GPTBot', 'OpenAI', 'training'),
    ('Claude-SearchBot', 'Anthropic', 'search'), ('Claude-User', 'Anthropic', 'search'),
    ('ClaudeBot', 'Anthropic', 'training'),
    ('PerplexityBot', 'Perplexity', 'search'), ('Perplexity-User', 'Perplexity', 'search'),
    ('Google-Extended', 'Google', 'training'), ('Applebot', 'Apple', 'search'),
    ('Applebot-Extended', 'Apple', 'training'), ('DuckAssistBot', 'DuckDuckGo', 'search'),
    ('MistralAI-User', 'Mistral', 'search'), ('meta-externalagent', 'Meta', 'training'),
    ('Amazonbot', 'Amazon', 'search'), ('CCBot', 'Common Crawl', 'training'),
    ('Bytespider', 'ByteDance', 'training'), ('cohere-ai', 'Cohere', 'training'),
]


# ---------------------------------------------------------------- fetch layer
@dataclass
class Response:
    url: str
    status: int | None
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b''
    final_url: str = ''
    redirects: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    captured: bool = True

    def text(self) -> str:
        charset = 'utf-8'
        m = re.search(r'charset=([\w-]+)', self.headers.get('content-type', ''), re.I)
        if m: charset = m.group(1)
        try: return self.body.decode(charset, errors='replace')
        except LookupError: return self.body.decode('utf-8', errors='replace')


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LiveFetcher:
    def __init__(self, timeout=15.0, max_bytes=8_000_000, delay=0.5):
        self.timeout, self.max_bytes, self.delay = timeout, max_bytes, delay
        self.opener = build_opener(_NoRedirect)
        self._last = 0.0
        self.cache: dict[str, Response] = {}

    def _one(self, url):
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0: time.sleep(wait)
        self._last = time.monotonic()
        req = Request(url, headers={'User-Agent': UA, 'Accept': '*/*', 'Accept-Encoding': 'identity'})
        try:
            with self.opener.open(req, timeout=self.timeout) as r:
                body = r.read(self.max_bytes + 1)
                return r.status, {k.lower(): v for k, v in r.headers.items()}, body[:self.max_bytes], None
        except HTTPError as e:
            return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, b'', None
        except (URLError, TimeoutError, OSError, ValueError) as e:
            return None, {}, b'', f'{type(e).__name__}: {getattr(e, "reason", e)}'

    def get(self, url):
        if url in self.cache: return self.cache[url]
        chain = []; current = url
        for _ in range(10):
            status, headers, body, err = self._one(current)
            if status in (301, 302, 303, 307, 308) and headers.get('location'):
                nxt = urljoin(current, headers['location'])
                chain.append({'from': current, 'to': nxt, 'status': status})
                current = nxt; continue
            resp = Response(url, status, headers, body, current, chain, err)
            break
        else:
            resp = Response(url, None, {}, b'', current, chain, 'Redirect loop (>10)')
        self.cache[url] = resp
        return resp


class SnapshotFetcher:
    def __init__(self, directory):
        self.dir = Path(directory)
        self.manifest = json.loads((self.dir / 'manifest.json').read_text(encoding='utf-8'))

    def get(self, url):
        chain = []; current = url
        for _ in range(10):
            entry = self.manifest.get(current)
            if entry is None:
                return Response(url, None, {}, b'', current, chain, 'not captured', captured=False)
            status = entry.get('status', 200)
            if status in (301, 302, 303, 307, 308) and entry.get('location'):
                nxt = urljoin(current, entry['location'])
                chain.append({'from': current, 'to': nxt, 'status': status}); current = nxt; continue
            body = (self.dir / entry['file']).read_bytes() if entry.get('file') else b''
            headers = {k.lower(): v for k, v in entry.get('headers', {}).items()}
            return Response(url, status, headers, body, current, chain, None)
        return Response(url, None, {}, b'', current, chain, 'Redirect loop (>10)')


# ---------------------------------------------------------------- parsers
class PageParser(HTMLParser):
    SKIP = {'script', 'style', 'template', 'noscript', 'svg', 'title'}
    BOILER = {'nav', 'header', 'footer', 'aside'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []; self.titles = 0; self._in_title = False
        self.meta: dict[str, str] = {}; self.canonical = None; self.lang = None
        self.links: list[str] = []; self.html_tags = 0; self.main_count = 0
        self.h1: list[str] = []; self._h1 = None
        self.text_parts: list[str] = []; self._skip = 0; self._boiler = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or '') for k, v in attrs}
        if tag == 'html':
            self.html_tags += 1
            if self.lang is None: self.lang = a.get('lang')
        elif tag == 'title':
            self.titles += 1; self._in_title = self.titles == 1
        elif tag == 'meta':
            key = (a.get('name') or a.get('property') or '').lower()
            if key and key not in self.meta: self.meta[key] = a.get('content', '')
        elif tag == 'link' and 'canonical' in a.get('rel', '').lower().split() and self.canonical is None:
            self.canonical = a.get('href')
        elif tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        elif tag == 'main':
            self.main_count += 1
        elif tag == 'h1':
            self._h1 = []
        if tag in self.SKIP: self._skip += 1
        if tag in self.BOILER: self._boiler += 1
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'h4', 'tr', 'section', 'article', 'blockquote', 'br'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag == 'title': self._in_title = False
        if tag in self.SKIP: self._skip = max(0, self._skip - 1)
        if tag in self.BOILER: self._boiler = max(0, self._boiler - 1)
        if tag == 'h1' and self._h1 is not None:
            self.h1.append(SPACE.sub(' ', ''.join(self._h1)).strip()); self._h1 = None

    def handle_data(self, data):
        if self._in_title: self.title_parts.append(data)
        if self._skip: return
        if self._h1 is not None: self._h1.append(data)
        if not self._boiler: self.text_parts.append(data)

    @property
    def title(self):
        return SPACE.sub(' ', ''.join(self.title_parts)).strip()

    def text(self):
        lines = [SPACE.sub(' ', x).strip() for x in ''.join(self.text_parts).split('\n')]
        return '\n'.join(x for x in lines if x)


def local(tag):
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def parse_sitemap(body: bytes):
    if body[:2] == b'\x1f\x8b': body = gzip.decompress(body)
    root = ET.fromstring(body)
    kind = local(root.tag)
    entries = []
    for node in root:
        if local(node.tag) not in ('url', 'sitemap'): continue
        e = {'loc': None, 'lastmod': None, 'images': 0, 'alternates': 0}
        for child in node:
            name = local(child.tag)
            if name == 'loc': e['loc'] = (child.text or '').strip()
            elif name == 'lastmod': e['lastmod'] = (child.text or '').strip()
            elif name == 'image': e['images'] += 1
            elif name == 'link': e['alternates'] += 1
        entries.append(e)
    return kind, entries


def parse_w3c_date(value):
    if not value: return None
    v = value.strip().replace('Z', '+00:00')
    for fmt in (None, '%Y-%m-%d', '%Y-%m'):
        try:
            d = datetime.fromisoformat(v) if fmt is None else datetime.strptime(v, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError: continue
    return None


LLMS_LINK = re.compile(r'^\s*[-*]\s*\[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\)\s*(?::\s*(?P<notes>.+))?$')


def parse_llms(text):
    lines = text.lstrip('﻿').splitlines()
    first = next((l for l in lines if l.strip()), '')
    result = {'h1': first[2:].strip() if first.startswith('# ') else None,
              'summary': None, 'sections': [], 'links': []}
    section = None
    for line in lines:
        if line.startswith('> ') and result['summary'] is None: result['summary'] = line[2:].strip()
        elif line.startswith('## '):
            section = line[3:].strip(); result['sections'].append(section)
        else:
            m = LLMS_LINK.match(line)
            if m:
                result['links'].append({'name': m.group('name').replace('\\', ''), 'url': m.group('url'),
                                        'notes': (m.group('notes') or '').strip(), 'section': section})
    return result


def norm_url(u):
    u = urldefrag(u)[0]
    p = urlparse(u)
    path = p.path or '/'
    return f'{p.scheme.lower()}://{p.netloc.lower()}{path}' + (f'?{p.query}' if p.query else '')


def slug_words(url):
    path = urlparse(url).path.strip('/').rsplit('/', 1)[-1]
    return path.replace('-', ' ').replace('_', ' ').lower()


def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s.casefold()) if not unicodedata.combining(c))


def slug_like(title, url):
    """Título que é só o slug (minúsculo, sem acento/pontuação) — rótulo pobre para LLMs."""
    t = SPACE.sub(' ', title).strip()
    return bool(t) and t == t.lower() and fold(t).replace('-', ' ') == slug_words(url) and ' ' in t


def slug_like_loose(title, url):
    """Versão tolerante para geração: ignora caixa e acentos (ex.: "Publicações em SEO GEO")."""
    t = SPACE.sub(' ', title).strip()
    return bool(t) and fold(t).replace('-', ' ') == slug_words(url)


def load_heading_engine():
    path = Path(__file__).with_name('pandora_heading_audit.py')
    if not path.exists(): return None
    spec = importlib.util.spec_from_file_location('pandora_heading_audit', path)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod
    try: spec.loader.exec_module(mod)
    except Exception: return None
    return mod


# ---------------------------------------------------------------- audit
class Audit:
    def __init__(self, base, fetcher, max_urls=200, check_urls=True, headings=True):
        p = urlparse(base)
        if p.scheme not in ('http', 'https') or not p.hostname: raise ValueError('URL base http(s) inválida')
        self.origin = f'{p.scheme}://{p.netloc}'
        self.host = p.hostname.lower().removeprefix('www.')
        self.fetcher, self.max_urls, self.check_urls = fetcher, max_urls, check_urls
        self.heading = load_heading_engine() if headings else None
        self.issues: list[dict[str, Any]] = []
        self.report: dict[str, Any] = {}

    def issue(self, code, severity, dimension, message, evidence=None, url=None):
        self.issues.append({'code': code, 'severity': severity, 'dimension': dimension,
                            'message': message, 'url': url, 'evidence': evidence})

    def same_site(self, url):
        h = (urlparse(url).hostname or '').lower().removeprefix('www.')
        return h == self.host

    # robots ------------------------------------------------------------
    def robots(self):
        url = self.origin + '/robots.txt'
        r = self.fetcher.get(url)
        out = {'url': url, 'status': r.status, 'captured': r.captured, 'sitemaps': [], 'bots': []}
        if not r.captured:
            self.issue('ROBOTS_NOT_CAPTURED', 'info', 'robots', 'robots.txt não capturado no snapshot', url=url)
            return out
        if r.status != 200:
            self.issue('ROBOTS_MISSING', 'medium', 'robots', 'robots.txt ausente ou com erro', r.status, url)
            return out
        text = r.text()
        out['sitemaps'] = re.findall(r'(?im)^\s*sitemap\s*:\s*(\S+)', text)
        named = {m.lower() for m in re.findall(r'(?im)^\s*user-agent\s*:\s*(\S+)', text)}
        rp = RobotFileParser(); rp.parse(text.splitlines())
        home = self.origin + '/'
        for token, vendor, role in AI_BOTS:
            allowed = rp.can_fetch(token, home)
            out['bots'].append({'token': token, 'vendor': vendor, 'role': role, 'allowed': allowed,
                                'explicit': token.lower() in named})
            if not allowed:
                if role == 'search':
                    self.issue('SEARCH_BOT_BLOCKED', 'high', 'robots',
                               f'{token} ({vendor}) bloqueado: a marca some das respostas/buscas desse agente',
                               url=url)
                else:
                    self.issue('TRAINING_BOT_BLOCKED', 'info', 'robots',
                               f'{token} ({vendor}) bloqueado para treino (decisão de política, não erro)', url=url)
        if not rp.can_fetch('*', home):
            self.issue('ROBOTS_BLOCKS_ALL', 'critical', 'robots', 'User-agent * bloqueado na raiz', url=url)
        if not out['sitemaps']:
            self.issue('ROBOTS_NO_SITEMAP', 'medium', 'robots', 'robots.txt não declara Sitemap:', url=url)
        if not any(b['explicit'] for b in out['bots'] if b['token'] not in ('Googlebot', 'Bingbot', 'Applebot')):
            self.issue('ROBOTS_NO_AI_POLICY', 'low', 'robots',
                       'Nenhum bot de IA citado explicitamente; política para IA fica implícita (herdada de *)',
                       url=url)
        return out

    # sitemaps ----------------------------------------------------------
    def sitemaps(self, declared):
        seeds = [s for s in declared if s] or [self.origin + '/sitemap_index.xml', self.origin + '/sitemap.xml']
        queue = list(dict.fromkeys(seeds)); seen = set(); files = []; urls: dict[str, dict] = {}
        fallback = not declared
        while queue:
            sm = queue.pop(0)
            if sm in seen: continue
            seen.add(sm)
            r = self.fetcher.get(sm)
            rec = {'url': sm, 'status': r.status, 'kind': None, 'entries': 0, 'bytes': len(r.body)}
            files.append(rec)
            if not r.captured:
                rec['error'] = 'não capturado'; continue
            if r.status != 200:
                if not (fallback and sm.endswith('/sitemap.xml') and urls):
                    self.issue('SITEMAP_UNREACHABLE', 'high', 'sitemap', 'Sitemap inacessível', r.status, sm)
                continue
            if r.redirects:
                self.issue('SITEMAP_REDIRECTS', 'low', 'sitemap', 'Sitemap atende via redirect', r.redirects, sm)
            if len(r.body) > MAX_SITEMAP_BYTES:
                self.issue('SITEMAP_TOO_LARGE', 'high', 'sitemap', 'Sitemap acima de 50 MB', len(r.body), sm)
            try:
                kind, entries = parse_sitemap(r.body)
            except (ET.ParseError, OSError, EOFError) as e:
                rec['error'] = str(e)
                self.issue('SITEMAP_INVALID_XML', 'high', 'sitemap', 'XML de sitemap inválido', str(e), sm)
                continue
            rec['kind'] = kind; rec['entries'] = len(entries)
            if len(entries) > MAX_SITEMAP_URLS:
                self.issue('SITEMAP_TOO_MANY_URLS', 'high', 'sitemap', 'Mais de 50.000 entradas', len(entries), sm)
            if kind == 'sitemapindex':
                queue.extend(e['loc'] for e in entries if e['loc'])
                continue
            if kind != 'urlset':
                self.issue('SITEMAP_UNKNOWN_ROOT', 'high', 'sitemap', 'Raiz XML não é urlset/sitemapindex', kind, sm)
                continue
            fallback = False
            for e in entries:
                loc = e['loc']
                if not loc:
                    self.issue('SITEMAP_EMPTY_LOC', 'medium', 'sitemap', 'Entrada sem <loc>', url=sm); continue
                key = norm_url(loc)
                if key in urls:
                    urls[key]['duplicates'] += 1; continue
                urls[key] = {'loc': loc, 'lastmod': e['lastmod'], 'images': e['images'],
                             'sitemap': sm, 'duplicates': 0}
        self.sitemap_files = files
        return urls

    def sitemap_checks(self, urls):
        if not urls:
            self.issue('SITEMAP_NO_URLS', 'critical', 'sitemap', 'Nenhuma URL encontrada em sitemaps'); return
        now = datetime.now(timezone.utc)
        dups = [u for u, v in urls.items() if v['duplicates']]
        if dups: self.issue('SITEMAP_DUPLICATE_URLS', 'medium', 'sitemap', 'URLs repetidas nos sitemaps', dups[:20])
        missing = [u for u, v in urls.items() if not v['lastmod']]
        if missing:
            self.issue('LASTMOD_MISSING', 'low', 'sitemap', f'{len(missing)} URLs sem <lastmod>', missing[:20])
        bad, future, dates = [], [], []
        for u, v in urls.items():
            if not v['lastmod']: continue
            d = parse_w3c_date(v['lastmod'])
            if d is None: bad.append(u)
            elif d > now: future.append(u)
            else: dates.append(d)
        if bad: self.issue('LASTMOD_INVALID', 'medium', 'sitemap', 'lastmod fora do formato W3C', bad[:20])
        if future: self.issue('LASTMOD_FUTURE', 'medium', 'sitemap', 'lastmod no futuro', future[:20])
        if len(dates) >= 5 and len(set(dates)) == 1:
            self.issue('LASTMOD_ALL_IDENTICAL', 'medium', 'sitemap',
                       'Todos os lastmod idênticos: sinal de data gerada, não de alteração real', dates[0].isoformat())
        offsite = [v['loc'] for v in urls.values() if not self.same_site(v['loc'])]
        if offsite: self.issue('SITEMAP_OFFSITE_URLS', 'high', 'sitemap', 'URLs de outro host', offsite[:20])
        scheme = urlparse(self.origin).scheme
        mixed = [v['loc'] for v in urls.values() if urlparse(v['loc']).scheme != scheme]
        if mixed: self.issue('SITEMAP_SCHEME_MISMATCH', 'medium', 'sitemap', 'Esquema http/https misturado', mixed[:20])
        defaults = [v['loc'] for v in urls.values() if any(urlparse(v['loc']).path.endswith(d) for d in DEFAULT_CONTENT)]
        if defaults:
            self.issue('DEFAULT_CONTENT_PUBLISHED', 'medium', 'sitemap',
                       'Conteúdo padrão do CMS publicado e listado no sitemap', defaults)

    # pages -------------------------------------------------------------
    def pages(self, urls):
        pages = {}
        targets = [v['loc'] for v in urls.values() if self.same_site(v['loc'])
                   and not urlparse(v['loc']).path.lower().endswith(NON_HTML_EXT)]
        home = self.origin + '/'
        if norm_url(home) not in {norm_url(t) for t in targets}: targets.insert(0, home)
        if len(targets) > self.max_urls:
            self.issue('URL_SAMPLE_LIMIT', 'info', 'url_health',
                       f'Checadas {self.max_urls} de {len(targets)} URLs (--max-urls)', len(targets))
            targets = targets[:self.max_urls]
        for loc in targets:
            r = self.fetcher.get(loc)
            page = {'url': loc, 'status': r.status, 'captured': r.captured, 'final_url': r.final_url,
                    'redirects': r.redirects, 'error': r.error, 'bytes': len(r.body)}
            pages[norm_url(loc)] = page
            if not r.captured or r.status != 200 or 'html' not in r.headers.get('content-type', 'text/html'):
                continue
            html = r.text()
            pp = PageParser()
            try: pp.feed(html); pp.close()
            except Exception as e: page['parse_error'] = str(e)
            robots_meta = (pp.meta.get('robots', '') + ',' + r.headers.get('x-robots-tag', '')).lower()
            canonical = urljoin(r.final_url or loc, pp.canonical) if pp.canonical else None
            page.update({'title': pp.title, 'titles': pp.titles, 'description': pp.meta.get('description', ''),
                         'og_title': pp.meta.get('og:title', ''), 'h1': pp.h1, 'lang': pp.lang,
                         'canonical': canonical, 'noindex': 'noindex' in robots_meta,
                         'html_tags': pp.html_tags, 'main_count': pp.main_count,
                         'base64_bytes': sum(len(m) for m in B64.findall(html)),
                         'links': sorted({norm_url(urljoin(r.final_url or loc, h)) for h in pp.links
                                          if urlparse(urljoin(loc, h)).scheme in ('http', 'https')}),
                         'text': pp.text(), 'lastmod': urls.get(norm_url(loc), {}).get('lastmod')})
            if self.heading:
                try:
                    hr = self.heading.analyze(loc, html)
                    page['heading_score'] = hr['score']
                    page['heading_issues'] = sorted({i['code'] for i in hr['issues']})
                except Exception as e:
                    page['heading_error'] = str(e)
        return pages

    def page_checks(self, urls, pages):
        checked = [p for p in pages.values() if p['captured'] and p['status'] is not None]
        in_sitemap = set(urls)
        for p in pages.values():
            u = p['url']; key = norm_url(u)
            if not p['captured']: continue
            if p['status'] is None:
                self.issue('URL_FETCH_ERROR', 'high', 'url_health', 'Falha ao acessar URL', p['error'], u); continue
            if key in in_sitemap and p['redirects']:
                self.issue('SITEMAP_URL_REDIRECTS', 'medium', 'url_health',
                           'URL do sitemap redireciona; liste a URL final', p['redirects'], u)
            if p['status'] >= 400:
                self.issue('URL_ERROR_STATUS', 'high', 'url_health', f'Status {p["status"]}', p['status'], u)
                continue
            if p['status'] != 200 or 'title' not in p: continue
            if p['noindex'] and key in in_sitemap:
                self.issue('NOINDEX_IN_SITEMAP', 'high', 'url_health', 'Página noindex listada no sitemap', url=u)
            if p['canonical'] and norm_url(p['canonical']) != norm_url(p['final_url'] or u):
                self.issue('CANONICAL_MISMATCH', 'medium', 'url_health',
                           'Canonical aponta para outra URL', p['canonical'], u)
            if p['html_tags'] > 1 or p['titles'] > 1:
                self.issue('NESTED_HTML_DOCUMENT', 'medium', 'url_health',
                           'Documento HTML aninhado (vários <html>/<title>): metadados ambíguos para crawlers',
                           {'html': p['html_tags'], 'title': p['titles'], 'main': p['main_count']}, u)
            if p['bytes'] > 1_000_000:
                self.issue('HEAVY_HTML', 'medium', 'url_health', 'HTML acima de 1 MB',
                           {'bytes': p['bytes'], 'base64_bytes': p['base64_bytes']}, u)
            if not p['title']:
                self.issue('MISSING_TITLE', 'medium', 'url_health', '<title> ausente', url=u)
            elif slug_like(re.split(r'\s+[-|–—·]\s+', p['title'])[0], p['final_url'] or u):
                self.issue('TITLE_SLUG_LIKE', 'medium', 'url_health',
                           '<title> é só o slug (minúsculo, sem acento): rótulo pobre na SERP e nas respostas de IA',
                           p['title'], u)
            if not p['description']:
                self.issue('MISSING_META_DESCRIPTION', 'low', 'url_health', 'Meta description ausente', url=u)
            if len(p['text']) < 300:
                self.issue('THIN_TEXT', 'low', 'url_health', 'Pouco texto extraível sem JavaScript',
                           len(p['text']), u)
        # órfãs: URLs do sitemap sem link de nenhuma outra página checada
        html_pages = [p for p in checked if 'links' in p]
        if len(html_pages) >= 3:
            inbound = Counter()
            for p in html_pages:
                for l in set(p['links']):
                    if l != norm_url(p['url']): inbound[l] += 1
            home = norm_url(self.origin + '/')
            orphans = [urls[k]['loc'] for k in urls if k != home and inbound[k] == 0 and k in pages]
            self.orphans = orphans
            if orphans:
                self.issue('ORPHAN_URLS', 'medium', 'linking',
                           f'{len(orphans)} URLs do sitemap sem link interno a partir das páginas checadas',
                           orphans[:50])
            linked = sorted(l for l in inbound if self.same_site(l) and l not in in_sitemap
                            and not urlparse(l).path.lower().endswith(NON_HTML_EXT)
                            and not re.search(r'/(wp-|feed|comments|tag/|author/|page/\d)', urlparse(l).path)
                            and not urlparse(l).query)
            self.linked_not_in_sitemap = linked
            if linked:
                self.issue('LINKED_NOT_IN_SITEMAP', 'low', 'linking',
                           f'{len(linked)} URLs internas linkadas que não estão no sitemap', linked[:100])
            origin_netloc = urlparse(self.origin).netloc.lower()
            variants = sorted({l for l in inbound if self.same_site(l) and urlparse(l).netloc != origin_netloc})
            if variants:
                self.issue('INTERNAL_LINK_HOST_VARIANT', 'medium', 'linking',
                           f'{len(variants)} links internos apontam para outra variante de host (www/não-www): '
                           'custam redirect e podem quebrar', variants[:50])
            broken = []
            for l in linked[:100]:
                r = self.fetcher.get(l)
                if r.captured and (r.status is None or r.status >= 400):
                    broken.append({'url': l, 'status': r.status, 'linked_from': inbound[l]})
            self.broken_links = broken
            if broken:
                self.issue('BROKEN_INTERNAL_LINKS', 'high', 'linking',
                           f'{len(broken)} links internos quebrados (4xx/5xx/erro)', broken[:50])
        else:
            self.orphans = None; self.linked_not_in_sitemap = None
        self.broken_links = getattr(self, 'broken_links', None)

    # llms --------------------------------------------------------------
    def llms(self, urls, pages):
        out = {}
        r = self.fetcher.get(self.origin + '/llms.txt')
        out['llms_txt'] = {'status': r.status, 'captured': r.captured, 'bytes': len(r.body)}
        rf = self.fetcher.get(self.origin + '/llms-full.txt')
        out['llms_full_txt'] = {'status': rf.status, 'captured': rf.captured, 'bytes': len(rf.body)}
        if not r.captured:
            self.issue('LLMS_NOT_CAPTURED', 'info', 'llms', 'llms.txt não capturado no snapshot')
            return out
        if r.status != 200 or not r.body.strip():
            self.issue('LLMS_MISSING', 'high', 'llms', 'llms.txt ausente (GEO: índice curado para agentes/LLMs)')
            return out
        parsed = parse_llms(r.text())
        out['llms_txt'].update({'h1': parsed['h1'], 'summary': parsed['summary'],
                                'sections': parsed['sections'], 'links': len(parsed['links'])})
        if 'yoast' in r.text().lower():
            out['llms_txt']['generator'] = 'Yoast SEO (automático)'
        if not parsed['h1']: self.issue('LLMS_NO_H1', 'medium', 'llms', 'llms.txt não começa com "# Nome"')
        if not parsed['summary']:
            self.issue('LLMS_NO_SUMMARY', 'medium', 'llms', 'Sem resumo em blockquote ("> ...") após o H1')
        links = parsed['links']
        indexable = {k for k, v in urls.items() if self.same_site(v['loc'])
                     and not any(urlparse(v['loc']).path.endswith(d) for d in DEFAULT_CONTENT)
                     and not pages.get(k, {}).get('noindex')
                     and pages.get(k, {}).get('status', 200) in (200, None)}
        listed = {norm_url(l['url']) for l in links}
        coverage = len(listed & indexable) / len(indexable) if indexable else 0.0
        out['llms_txt']['coverage'] = round(coverage, 3)
        out['llms_txt']['missing_from_llms'] = sorted(urls[k]['loc'] for k in indexable - listed)
        if coverage < 0.8:
            self.issue('LLMS_LOW_COVERAGE', 'high' if coverage < 0.3 else 'medium', 'llms',
                       f'llms.txt cobre {coverage:.0%} das URLs indexáveis do sitemap',
                       {'listed': len(listed & indexable), 'indexable': len(indexable)})
        slugs = [l for l in links if slug_like(l['name'], l['url'])]
        if slugs:
            self.issue('LLMS_SLUG_TITLES', 'medium', 'llms', 'Títulos no formato de slug (rótulo pobre para LLMs)',
                       [l['name'] for l in slugs][:20])
        no_notes = [l for l in links if not l['notes']]
        if links and len(no_notes) / len(links) > 0.5:
            self.issue('LLMS_NO_DESCRIPTIONS', 'low', 'llms',
                       f'{len(no_notes)}/{len(links)} links sem descrição (": nota" após o link)')
        defaults = [l['url'] for l in links if any(urlparse(l['url']).path.endswith(d) for d in DEFAULT_CONTENT)]
        if defaults: self.issue('LLMS_DEFAULT_CONTENT', 'medium', 'llms', 'llms.txt lista conteúdo padrão', defaults)
        dead = [l['url'] for l in links if pages.get(norm_url(l['url']), {}).get('status') not in (None, 200)]
        if dead: self.issue('LLMS_DEAD_LINKS', 'high', 'llms', 'Links do llms.txt com erro/redirect', dead[:20])
        if rf.captured and (rf.status != 200 or not rf.body.strip()):
            self.issue('LLMS_FULL_MISSING', 'low', 'llms',
                       'llms-full.txt ausente (texto integral para agentes de documentação/pesquisa)')
        return out

    # score -------------------------------------------------------------
    PENALTY = {
        'robots': (150, {'ROBOTS_MISSING': 60, 'ROBOTS_BLOCKS_ALL': 150, 'SEARCH_BOT_BLOCKED': 25,
                         'ROBOTS_NO_SITEMAP': 25, 'ROBOTS_NO_AI_POLICY': 10}),
        'sitemap': (250, {'SITEMAP_NO_URLS': 250, 'SITEMAP_UNREACHABLE': 60, 'SITEMAP_INVALID_XML': 80,
                          'SITEMAP_TOO_LARGE': 50, 'SITEMAP_TOO_MANY_URLS': 50, 'SITEMAP_UNKNOWN_ROOT': 60,
                          'SITEMAP_EMPTY_LOC': 10, 'SITEMAP_DUPLICATE_URLS': 25, 'LASTMOD_MISSING': 20,
                          'LASTMOD_INVALID': 25, 'LASTMOD_FUTURE': 25, 'LASTMOD_ALL_IDENTICAL': 25,
                          'SITEMAP_OFFSITE_URLS': 50, 'SITEMAP_SCHEME_MISMATCH': 30,
                          'DEFAULT_CONTENT_PUBLISHED': 20, 'SITEMAP_REDIRECTS': 10}),
        'llms': (250, {'LLMS_MISSING': 200, 'LLMS_NO_H1': 20, 'LLMS_NO_SUMMARY': 20, 'LLMS_SLUG_TITLES': 35,
                       'LLMS_NO_DESCRIPTIONS': 25, 'LLMS_DEFAULT_CONTENT': 20, 'LLMS_DEAD_LINKS': 40,
                       'LLMS_FULL_MISSING': 30}),
    }

    def score(self, pages, llms_info):
        dims = {}
        for name, (maxi, table) in self.PENALTY.items():
            codes = [i['code'] for i in self.issues if i['dimension'] == name]
            loss = sum(table.get(c, 0) for c in codes)
            if name == 'llms' and 'coverage' in llms_info.get('llms_txt', {}):
                cov = llms_info['llms_txt']['coverage']
                loss += round(max(0.0, 0.8 - cov) / 0.8 * 100)
            measured = not (name == 'llms' and not llms_info.get('llms_txt', {}).get('captured', True)) and \
                not (name == 'robots' and any(i['code'] == 'ROBOTS_NOT_CAPTURED' for i in self.issues))
            dims[name] = {'score': max(0, maxi - loss) if measured else None, 'max': maxi,
                          'deductions': min(maxi, loss), 'measured': measured}
        # saúde de URLs: proporcional às páginas checadas
        checked = [p for p in pages.values() if p['captured'] and p['status'] is not None]
        if self.check_urls and checked:
            n = len(checked)
            def share(code): return len({i['url'] for i in self.issues if i['code'] == code}) / n
            loss = (share('URL_ERROR_STATUS') * 150 + share('URL_FETCH_ERROR') * 150 +
                    share('SITEMAP_URL_REDIRECTS') * 60 + share('NOINDEX_IN_SITEMAP') * 120 +
                    share('CANONICAL_MISMATCH') * 80 + share('NESTED_HTML_DOCUMENT') * 50 +
                    share('HEAVY_HTML') * 60 + share('MISSING_TITLE') * 60 + share('TITLE_SLUG_LIKE') * 40 +
                    share('MISSING_META_DESCRIPTION') * 20 + share('THIN_TEXT') * 20)
            dims['url_health'] = {'score': max(0, round(250 - loss)), 'max': 250,
                                  'deductions': min(250, round(loss)), 'measured': True, 'checked': n}
        else:
            dims['url_health'] = {'score': None, 'max': 250, 'deductions': 0, 'measured': False}
        if self.orphans is not None and pages:
            n = max(1, len(pages))
            broken = len(getattr(self, 'broken_links', None) or [])
            variant = any(i['code'] == 'INTERNAL_LINK_HOST_VARIANT' for i in self.issues)
            loss = round(len(self.orphans) / n * 50 + min(15, len(self.linked_not_in_sitemap or [])) +
                         min(40, broken * 5) + (10 if variant else 0))
            dims['linking'] = {'score': max(0, 100 - loss), 'max': 100, 'deductions': min(100, loss),
                               'measured': True}
        else:
            dims['linking'] = {'score': None, 'max': 100, 'deductions': 0, 'measured': False}
        measured = [d for d in dims.values() if d['measured']]
        total = round(sum(d['score'] for d in measured) / sum(d['max'] for d in measured) * 1000) if measured else 0
        return total, dims

    def run(self):
        robots = self.robots()
        urls = self.sitemaps(robots.get('sitemaps', []))
        self.sitemap_checks(urls)
        pages = self.pages(urls) if self.check_urls else {}
        self.orphans = None; self.linked_not_in_sitemap = None
        if self.check_urls: self.page_checks(urls, pages)
        llms_info = self.llms(urls, pages)
        total, dims = self.score(pages, llms_info)
        headings = [p['heading_score'] for p in pages.values() if 'heading_score' in p]
        sev = Counter(i['severity'] for i in self.issues)
        self.report = {
            'engine': 'PANDORA SITEMAP & LLMS AUDIT Ω', 'version': VERSION,
            'generated_at': datetime.now(timezone.utc).isoformat(), 'target': self.origin,
            'score': total, 'max_score': 1000, 'dimensions': dims, 'severity_counts': dict(sev),
            'robots': robots, 'sitemap_files': self.sitemap_files,
            'sitemap_url_count': len(urls), 'llms': llms_info,
            'heading_engine': {'available': self.heading is not None,
                               'average_score': round(sum(headings) / len(headings), 2) if headings else None,
                               'pages_scored': len(headings)},
            'orphans': self.orphans, 'linked_not_in_sitemap': self.linked_not_in_sitemap,
            'broken_internal_links': getattr(self, 'broken_links', None),
            'pages': [{k: v for k, v in p.items() if k not in ('text', 'links')} | {'internal_links': len(p.get('links', []))}
                      for p in pages.values()],
            'issues': self.issues,
            'limitations': ['Sem execução de JavaScript', 'Score é proxy técnico de descoberta, não de ranking/citação',
                            'llms.txt não é padrão oficial; crawlers de IA podem ignorá-lo',
                            'Órfãs calculadas só a partir das páginas checadas']}
        self._pages, self._urls = pages, urls
        return self.report


# ---------------------------------------------------------------- generation
INSTITUTIONAL = re.compile(r'(privacidade|privacy|termos|terms|cookies|conflito|politica|imprensa|press|contato|'
                           r'contact|sobre|about|quem-somos)', re.I)


def clean_title(page, site_name):
    candidates = [page.get('og_title', ''), page.get('title', '')] + list(page.get('h1') or [])
    for t in candidates:
        t = SPACE.sub(' ', t or '').strip()
        if site_name:
            t = re.sub(r'\s*[-|–—·]\s*' + re.escape(site_name) + r'\s*$', '', t, flags=re.I)
        if t and not slug_like_loose(t, page['url']): return t
    return SPACE.sub(' ', (page.get('h1') or [page['url']])[0]).strip() or page['url']


def md_escape(s):
    return s.replace('[', '\\[').replace(']', '\\]')


def generate(audit: Audit, out_dir, site_name, summary=None, full_chars=0):
    pages = audit._pages
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    home = norm_url(audit.origin + '/')
    good = [p for k, p in pages.items() if p.get('status') == 200 and 'title' in p and not p.get('noindex')
            and not any(urlparse(p['url']).path.endswith(d) for d in DEFAULT_CONTENT)]
    good.sort(key=lambda p: (norm_url(p['url']) != home, p.get('lastmod') or '', p['url']))
    groups = {'Principal': [], 'Artigos, estudos e guias': [], 'Institucional': []}
    for p in good:
        k = norm_url(p['url'])
        if k == home: groups['Principal'].append(p)
        elif INSTITUTIONAL.search(urlparse(p['url']).path): groups['Institucional'].append(p)
        else: groups['Artigos, estudos e guias'].append(p)
    groups['Artigos, estudos e guias'].sort(key=lambda p: p.get('lastmod') or '', reverse=True)
    home_page = pages.get(home, {})
    summary = summary or home_page.get('description') or ''
    name = site_name or clean_title(home_page, '') if home_page else site_name
    lines = [f'# {name}', '']
    if summary: lines += [f'> {summary}', '']
    lines += [f'Gerado por PANDORA SITEMAP & LLMS AUDIT Ω v{VERSION} em '
              f'{datetime.now(timezone.utc).date().isoformat()} a partir do sitemap auditado. Revisar antes de publicar.', '']
    for section, items in groups.items():
        if not items: continue
        lines += [f'## {section}', '']
        for p in items:
            desc = SPACE.sub(' ', p.get('description') or '').strip()
            lines.append(f'- [{md_escape(clean_title(p, site_name))}]({p["final_url"] or p["url"]})' +
                         (f': {desc}' if desc else ''))
        lines.append('')
    sitemap_url = next(iter(audit.report.get('robots', {}).get('sitemaps') or []),
                       (audit.sitemap_files[0]['url'] if audit.sitemap_files else audit.origin + '/sitemap.xml'))
    lines += ['## Optional', '', f'- [Sitemap XML]({sitemap_url})',
              f'- [Texto integral]({audit.origin}/llms-full.txt)', '']
    (out / 'llms.txt').write_text('\n'.join(lines), encoding='utf-8')
    full = [f'# {name}', '']
    if summary: full += [f'> {summary}', '']
    for section, items in groups.items():
        for p in items:
            text = p.get('text', '')
            if full_chars and len(text) > full_chars: text = text[:full_chars].rsplit(' ', 1)[0] + ' […]'
            full += [f'## {clean_title(p, site_name)}', '', f'URL: {p["final_url"] or p["url"]}',
                     f'Seção: {section}'] + ([f'Atualizado: {p["lastmod"]}'] if p.get('lastmod') else []) + \
                    ([f'Resumo: {p["description"]}'] if p.get('description') else []) + ['', text, '', '---', '']
    (out / 'llms-full.txt').write_text('\n'.join(full), encoding='utf-8')
    from html import escape
    h = ['<!-- Mapa do site gerado por PANDORA SITEMAP & LLMS AUDIT Ω. Cole num bloco HTML personalizado. -->',
         '<nav class="pandora-sitemap" aria-label="Mapa do site">', f'<h1>Mapa do site</h1>']
    for section, items in groups.items():
        if not items: continue
        h.append(f'<h2>{escape(section)}</h2>\n<ul>')
        for p in items:
            desc = escape(p.get('description') or '')
            h.append(f'  <li><a href="{escape(p["final_url"] or p["url"])}">{escape(clean_title(p, site_name))}</a>'
                     + (f' — {desc}' if desc else '') + '</li>')
        h.append('</ul>')
    h += [f'<p><a href="{audit.origin}/llms.txt">llms.txt</a> · <a href="{audit.origin}/llms-full.txt">llms-full.txt</a>'
          f' · <a href="{sitemap_url}">Sitemap XML</a></p>', '</nav>']
    (out / 'mapa-do-site.html').write_text('\n'.join(h) + '\n', encoding='utf-8')
    return {'llms.txt': len(good), 'groups': {k: len(v) for k, v in groups.items()}, 'out_dir': str(out)}


# ---------------------------------------------------------------- output
def render_md(r):
    d = r['dimensions']
    L = [f'# PANDORA SITEMAP & LLMS AUDIT Ω v{r["version"]}', '',
         f'Alvo: {r["target"]} · Data UTC: {r["generated_at"]}', '',
         f'**Score: {r["score"]}/1000** (proxy técnico de descoberta para buscadores e IAs)', '',
         '| Dimensão | Score | Máx. |', '|---|---:|---:|']
    for k, v in d.items():
        L.append(f'| {k} | {v["score"] if v["measured"] else "não medido"} | {v["max"]} |')
    L += ['', f'URLs nos sitemaps: {r["sitemap_url_count"]} · Páginas checadas: {len(r["pages"])}']
    if r['heading_engine']['average_score'] is not None:
        L.append(f'Score médio de headings (motor PANDORA HEADING AUDIT): {r["heading_engine"]["average_score"]}/1000')
    L += ['', '## Robôs (robots.txt)', '', '| Bot | Empresa | Função | Acesso | Citado explicitamente |', '|---|---|---|---|---|']
    for b in r['robots'].get('bots', []):
        L.append(f'| {b["token"]} | {b["vendor"]} | {"busca/resposta" if b["role"] == "search" else "treino"} | '
                 f'{"liberado" if b["allowed"] else "BLOQUEADO"} | {"sim" if b["explicit"] else "não"} |')
    lt = r['llms'].get('llms_txt', {})
    L += ['', '## llms.txt', '', f'Status: {lt.get("status")} · Links: {lt.get("links", 0)} · '
          f'Cobertura do sitemap: {lt.get("coverage", "—") if "coverage" not in lt else f"{lt["coverage"]:.0%}"} · '
          f'Gerador: {lt.get("generator", "—")}',
          f'llms-full.txt: status {r["llms"].get("llms_full_txt", {}).get("status")}', '']
    order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    L += ['## Achados', '']
    for i in sorted(r['issues'], key=lambda i: (order.get(i['severity'], 9), i['code'])):
        L.append(f'- **{i["severity"]} / {i["code"]}** — {i["message"]}' + (f' · {i["url"]}' if i['url'] else ''))
    L += ['', '## Limites', ''] + [f'- {x}' for x in r['limitations']] + ['']
    return '\n'.join(L)


def write(path, text):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')


# ---------------------------------------------------------------- selftest
def selftest():
    import tempfile, unittest

    def snap(d, files):
        manifest = {}
        for i, (url, (status, ctype, body)) in enumerate(files.items()):
            entry = {'status': status, 'headers': {'content-type': ctype}}
            if status in (301, 302): entry['location'] = body
            else:
                name = f'f{i}'; (Path(d) / name).write_text(body, encoding='utf-8'); entry['file'] = name
            manifest[url] = entry
        (Path(d) / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        return SnapshotFetcher(d)

    B = 'https://ex.com'
    page = lambda t, links='', extra='': (f'<html lang="pt-BR"><head><title>{t}</title><meta name="description" '
                                          f'content="Sobre {t}"></head><body><main><h1>{t}</h1><p>' + 'texto ' * 80 +
                                          f'</p>{links}{extra}</main></body></html>')

    class T(unittest.TestCase):
        def site(self, d, robots='User-agent: *\nDisallow:\nSitemap: https://ex.com/sitemap.xml\n', llms=None):
            files = {
                B + '/robots.txt': (200, 'text/plain', robots),
                B + '/sitemap.xml': (200, 'application/xml',
                    '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    '<url><loc>https://ex.com/</loc><lastmod>2026-01-01</lastmod></url>'
                    '<url><loc>https://ex.com/a/</loc><lastmod>2026-01-02</lastmod></url>'
                    '<url><loc>https://ex.com/b/</loc><lastmod>2026-01-03</lastmod></url>'
                    '<url><loc>https://ex.com/hello-world/</loc><lastmod>2026-01-04</lastmod></url>'
                    '</urlset>'),
                B + '/': (200, 'text/html', page('Início', '<a href="/a/">a</a><a href="/b/">b</a><a href="/x/">x</a><a href="https://www.ex.com/a/">w</a>')),
                B + '/a/': (200, 'text/html', page('Artigo A', '<a href="/">home</a>')),
                B + '/b/': (301, '', B + '/b2/'),
                B + '/b2/': (200, 'text/html', page('Artigo B')),
                B + '/hello-world/': (200, 'text/html', page('Hello world', '', '<html><title>x</title></html>')),
                B + '/llms-full.txt': (404, 'text/plain', ''),
                B + '/x/': (404, 'text/html', ''),
            }
            if llms is not None: files[B + '/llms.txt'] = (200, 'text/plain', llms)
            else: files[B + '/llms.txt'] = (404, 'text/plain', '')
            return snap(d, files)

        def run_audit(self, **kw):
            with tempfile.TemporaryDirectory() as d:
                a = Audit(B, self.site(d, **kw), headings=False); r = a.run()
                return a, r, {i['code'] for i in r['issues']}

        def test_core_findings(self):
            _, r, codes = self.run_audit()
            for c in ('INTERNAL_LINK_HOST_VARIANT', 'DEFAULT_CONTENT_PUBLISHED', 'SITEMAP_URL_REDIRECTS', 'NESTED_HTML_DOCUMENT', 'LLMS_MISSING',
                      'ROBOTS_NO_AI_POLICY'):
                self.assertIn(c, codes)
            self.assertEqual(r['sitemap_url_count'], 4)
            self.assertNotIn('TITLE_SLUG_LIKE', codes)
            self.assertTrue(slug_like(re.split(r'\s+[-|–—·]\s+', 'metricas de geo - Raphael')[0], 'https://x/metricas-de-geo/'))
            self.assertTrue(0 < r['score'] < 1000)

        def test_search_bot_blocked(self):
            _, r, codes = self.run_audit(robots='User-agent: *\nDisallow:\n\nUser-agent: OAI-SearchBot\nDisallow: /\n'
                                                'User-agent: GPTBot\nDisallow: /\nSitemap: https://ex.com/sitemap.xml\n')
            self.assertIn('SEARCH_BOT_BLOCKED', codes); self.assertIn('TRAINING_BOT_BLOCKED', codes)
            bots = {b['token']: b for b in r['robots']['bots']}
            self.assertFalse(bots['OAI-SearchBot']['allowed']); self.assertTrue(bots['ClaudeBot']['allowed'])

        def test_llms_quality(self):
            llms = '# Ex\n\n## Páginas\n- [Artigo A](https://ex.com/a/)\n- [artigo velho](https://ex.com/artigo-velho/)\n- [Hello world](https://ex.com/hello-world/)\n'
            _, r, codes = self.run_audit(llms=llms)
            self.assertIn('LLMS_SLUG_TITLES', codes); self.assertIn('LLMS_NO_SUMMARY', codes)
            self.assertIn('LLMS_DEFAULT_CONTENT', codes); self.assertIn('LLMS_LOW_COVERAGE', codes)
            self.assertIn('LLMS_FULL_MISSING', codes)

        def test_orphans_and_linked(self):
            a, r, codes = self.run_audit()
            self.assertIn('LINKED_NOT_IN_SITEMAP', codes); self.assertIn('BROKEN_INTERNAL_LINKS', codes)
            self.assertEqual(r['broken_internal_links'][0]['url'], 'https://ex.com/x/')
            self.assertIn('https://ex.com/hello-world/', a.orphans)

        def test_generate(self):
            with tempfile.TemporaryDirectory() as d:
                a = Audit(B, self.site(d), headings=False); a.run()
                info = generate(a, Path(d) / 'out', 'Ex')
                llms = (Path(d) / 'out' / 'llms.txt').read_text(encoding='utf-8')
                self.assertIn('- [Artigo A](https://ex.com/a/): Sobre Artigo A', llms)
                self.assertNotIn('hello-world', llms)
                self.assertIn('https://ex.com/b2/', llms)
                self.assertTrue(parse_llms(llms)['summary'])
                self.assertIn('texto texto', (Path(d) / 'out' / 'llms-full.txt').read_text(encoding='utf-8'))
                self.assertEqual(info['groups']['Principal'], 1)

        def test_sitemap_index_and_gzip(self):
            with tempfile.TemporaryDirectory() as d:
                gz = Path(d) / 'g'; gz.write_bytes(gzip.compress(
                    b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://ex.com/</loc></url></urlset>'))
                files = {B + '/robots.txt': (200, 'text/plain', 'User-agent: *\nDisallow:\nSitemap: https://ex.com/i.xml\n'),
                         B + '/i.xml': (200, 'application/xml', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                        '<sitemap><loc>https://ex.com/s.xml.gz</loc></sitemap></sitemapindex>')}
                f = snap(d, files); f.manifest[B + '/s.xml.gz'] = {'file': 'g', 'status': 200}
                r = Audit(B, f, check_urls=False, headings=False).run()
                self.assertEqual(r['sitemap_url_count'], 1)
                self.assertIn('LASTMOD_MISSING', {i['code'] for i in r['issues']})

        def test_slug_like(self):
            self.assertTrue(slug_like('auditoria lgpd agencias 2026', 'https://x/auditoria-lgpd-agencias-2026/'))
            self.assertFalse(slug_like('Auditoria LGPD em agências', 'https://x/auditoria-lgpd-agencias/'))

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    return 0 if result.wasSuccessful() else 1


# ---------------------------------------------------------------- cli
def main(argv=None):
    ap = argparse.ArgumentParser(description='PANDORA SITEMAP & LLMS AUDIT Ω v' + VERSION)
    sub = ap.add_subparsers(dest='command', required=True)
    for cmd in ('audit', 'generate', 'verify'):
        p = sub.add_parser(cmd)
        p.add_argument('target', help='URL base do site (https://...)')
        p.add_argument('--snapshot', help='Diretório com manifest.json (modo offline)')
        p.add_argument('--max-urls', type=int, default=200)
        p.add_argument('--no-check-urls', action='store_true', help='Não visitar as URLs do sitemap')
        p.add_argument('--no-headings', action='store_true', help='Não usar o motor de headings')
        p.add_argument('--timeout', type=float, default=15)
        p.add_argument('--delay', type=float, default=0.5, help='Segundos entre requisições (cortesia)')
        p.add_argument('--json'); p.add_argument('--md')
        if cmd == 'generate':
            p.add_argument('--out-dir', required=True)
            p.add_argument('--site-name', default='')
            p.add_argument('--summary', help='Resumo em 1 frase para o blockquote do llms.txt')
            p.add_argument('--full-chars', type=int, default=0, help='Limite de caracteres por página no llms-full')
        if cmd == 'verify': p.add_argument('--min-score', type=int, default=800)
    sub.add_parser('selftest')
    args = ap.parse_args(argv)
    if args.command == 'selftest': return selftest()
    if args.max_urls < 1 or args.timeout <= 0 or args.delay < 0: ap.error('Limites inválidos')
    try:
        fetcher = SnapshotFetcher(args.snapshot) if args.snapshot else LiveFetcher(args.timeout, delay=args.delay)
        audit = Audit(args.target, fetcher, args.max_urls, not args.no_check_urls, not args.no_headings)
        if args.command == 'generate' and args.no_check_urls: ap.error('generate precisa visitar as URLs')
        report = audit.run()
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print('ERRO:', e, file=sys.stderr); return 2
    if args.json: write(args.json, json.dumps(report, ensure_ascii=False, indent=2))
    if args.md: write(args.md, render_md(report))
    dims = ' | '.join(f'{k} {v["score"] if v["measured"] else "—"}/{v["max"]}' for k, v in report['dimensions'].items())
    print(f'PANDORA SITEMAP & LLMS AUDIT Ω {VERSION} | {report["target"]} | score {report["score"]}/1000')
    print(f'  {dims}')
    print(f'  URLs no sitemap: {report["sitemap_url_count"]} | páginas checadas: {len(report["pages"])} | '
          f'achados: {len(report["issues"])} {report["severity_counts"]}')
    if args.command == 'generate':
        info = generate(audit, args.out_dir, args.site_name, args.summary, args.full_chars)
        print(f'  Gerados em {info["out_dir"]}: llms.txt, llms-full.txt, mapa-do-site.html ({info["llms.txt"]} páginas)')
    if args.command == 'verify' and report['score'] < args.min_score: return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
