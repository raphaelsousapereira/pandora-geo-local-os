#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PANDORA PRESS-CONSOLE Ω v0.1.0 — painel local integrado, revisão humana.
Executar em localhost; não publicar na internet. Sem autenticação de usuários.
"""
import argparse, html, importlib.util, json, secrets, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import discovery, inventory, press

E=lambda x:html.escape(str(x if x is not None else ''),quote=True)

class Console(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,db_path):
        super().__init__(address,Handler)
        self.db_path=db_path;self.csrf=secrets.token_urlsafe(32)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def headers_out(self,mime='text/html; charset=utf-8',length=None):
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        if length is not None:self.send_header('Content-Length',str(length))
        self.end_headers()
    def send_page(self,body):
        raw=body.encode('utf-8');self.headers_out(length=len(raw));self.wfile.write(raw)
    def redirect(self,url):
        self.send_response(303);self.send_header('Location',url);self.send_header('Cache-Control','no-store');self.end_headers()
    def error_page(self,message):self.send_page(self.wrap('<h2>Operação não concluída</h2><p>'+E(message)+'</p>'))
    def db(self):return press.connect(self.server.db_path)
    def wrap(self,body):
        return '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PANDORA PRESS-CONSOLE Ω</title><style>
        :root{color-scheme:dark}*{box-sizing:border-box}body{font:15px system-ui;background:#0d1110;color:#e9eeeb;max-width:1200px;margin:0 auto;padding:24px}a{color:#a1e9b3}h1{font-size:29px;letter-spacing:-1px}h2{margin-top:28px}nav{display:flex;gap:14px;flex-wrap:wrap;padding:12px 0;border-bottom:1px solid #3b4b43}.card{background:#18221e;border:1px solid #33483d;border-radius:13px;padding:17px;margin:10px 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px}.big{font-size:29px;font-weight:750}small,.muted{color:#aebdb4}input,select,button,textarea{font:inherit;background:#26332b;color:white;border:1px solid #536b5c;border-radius:7px;padding:9px;max-width:100%}button{cursor:pointer;background:#a1e9b3;color:#12251b;font-weight:700}form{display:inline-block;margin:6px 8px 6px 0}label{display:inline-block;margin:5px}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #33483d;padding:9px;vertical-align:top;overflow-wrap:anywhere}th{color:#a1e9b3}code{overflow-wrap:anywhere}a:focus,button:focus{outline:2px solid #a1e9b3}@media(max-width:650px){body{padding:12px}table{font-size:12px}}
        </style></head><body><h1>PANDORA <span style="color:#a1e9b3">PRESS-CONSOLE Ω</span></h1><p class="muted">Sala de Imprensa · Inventário · Descoberta · Revisão humana</p><nav><a href="/">Painel</a><a href="/candidates">Revisão de candidatos</a><a href="/timeline">Cronologia</a></nav>'''+body+'''<footer><p class="muted">Protótipo local. Menções não comprovam autoria. Candidatos nunca são verificados automaticamente.</p></footer></body></html>'''
    def host_ok(self):
        port=self.server.server_address[1]
        allowed={f'127.0.0.1:{port}',f'localhost:{port}'}
        if (self.headers.get('Host') or '').lower() in allowed:return True
        self.send_error(403,'Host não permitido');return False
    def get_params(self):return {k:v[0] for k,v in urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).items()}
    def author_select(self,db,selected,route='/'):
        authors=db.execute('SELECT id,name FROM authors ORDER BY name').fetchall()
        return '<form method="get" action="'+E(route)+'"><label>Autor <select name="author">'+''.join('<option value="'+E(a['id'])+'" '+('selected' if a['id']==selected else '')+'>'+E(a['name'])+'</option>' for a in authors)+'</select></label><button>Selecionar</button></form>'
    def hidden(self,author):return '<input type="hidden" name="token" value="'+E(self.server.csrf)+'"><input type="hidden" name="author" value="'+E(author)+'">'
    def do_GET(self):
        if not self.host_ok():return
        path=urllib.parse.urlsplit(self.path).path
        q=self.get_params()
        db=self.db()
        try:
            author=q.get('author') or (db.execute('SELECT id FROM authors ORDER BY created_at LIMIT 1').fetchone() or [''])[0]
            if path=='/download':
                if not author:raise ValueError('Cadastre um autor')
                kind=q.get('type','')
                if kind not in ('inventory-json','inventory-csv','inventory-pdf','chronology-pdf'):raise ValueError('Tipo de relatório inválido')
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    ext='pdf' if kind.endswith('pdf') else 'csv' if kind.endswith('csv') else 'json'
                    output=str(Path(td)/('pressroom-'+author+'.'+ext))
                    if kind=='chronology-pdf':press.report_pdf(db,author,output)
                    else:inventory.export(inventory.inventory(db,author),output,ext)
                    data=Path(output).read_bytes()
                self.headers_out({'pdf':'application/pdf','csv':'text/csv; charset=utf-8','json':'application/json; charset=utf-8'}[ext],len(data));self.wfile.write(data);return
            if path not in ('/','/timeline','/candidates'):raise ValueError('Página não encontrada')
            if not author:
                self.send_page(self.wrap('<h2>Primeiro acesso</h2><p>Cadastre um autor abaixo.</p>'+self.author_form()));return
            info=inventory.inventory(db,author)
            base='?author='+urllib.parse.quote(author)
            head=self.author_select(db,author,path)+'<p class="muted">'+E(info['author']['url'] or '')+'</p>'
            if path=='/':
                stats=[('Registros',info['total_records']),('Evidências',info['total_evidence']),('Sem evidências',info['without_evidence']),('Sem data',info['without_date']),('Candidatos pendentes',info['candidates_separate'].get('pending',0))]
                body=head+'<section class="cards">'+''.join('<div class="card"><div class="big">'+str(n)+'</div><small>'+E(t)+'</small></div>' for t,n in stats)+'</section>'
                body+='<h2>Inventário por segmento</h2><div class="cards">'+''.join('<div class="card"><div class="big">'+str(n)+'</div>'+E(k)+'</div>' for k,n in info['by_kind'].items())+'</div>'
                body+='<h2>Distribuição por ano</h2><div class="card">'+(', '.join(E(y)+': '+str(n) for y,n in info['by_year'].items()) or 'Nenhum registro')+'</div>'
                body+='<h2>Relatórios</h2><div class="card">'+''.join('<p><a href="/download'+base+'&type='+t+'">'+E(label)+'</a></p>' for t,label in [('inventory-json','Inventário JSON'),('inventory-csv','Inventário CSV'),('inventory-pdf','Inventário PDF'),('chronology-pdf','Relatório cronológico PDF')])+'</div>'
                body+='<h2>Descoberta supervisionada</h2><div class="card"><p>Informe uma URL pública. A coleta cria candidatos, não registros verificados.</p><form method="post" action="/collect">'+self.hidden(author)+'<label>Site <input type="url" name="url" required placeholder="https://exemplo.com"></label><label>Páginas <input type="number" name="max_pages" min="1" max="20" value="8"></label><button>Coletar</button></form></div>'
                body+='<h2>Cadastrar autor</h2>'+self.author_form()
            elif path=='/timeline':
                body=head+'<h2>Cronologia</h2><table><tr><th>Data</th><th>Realização</th><th>Categoria</th><th>Status</th><th>Fonte</th></tr>'
                for r in info['timeline']:
                    link='<a href="'+E(r['url'])+'" rel="noreferrer noopener">Abrir</a>' if r['url'] else '—'
                    body+='<tr><td>'+E(r['date'] or 'Sem data')+'</td><td>'+E(r['title'])+'</td><td>'+E(r['kind'])+'</td><td>'+E(r['status'])+'</td><td>'+link+'</td></tr>'
                body+='</table>'
            else:
                candidates=db.execute('SELECT * FROM candidates WHERE author_id=? ORDER BY discovered_at DESC LIMIT 300',(author,)).fetchall()
                body=head+'<h2>Candidatos encontrados ('+str(len(candidates))+')</h2>'
                for c in candidates:
                    body+='<article class="card"><strong>'+E(c['title'])+'</strong><p class="muted">'+E(c['kind'])+' · '+E(c['candidate_date'] or 'Sem data')+' · '+E(c['status'])+'</p><p>'+E(c['excerpt'][:550])+'</p><a href="'+E(c['source_url'])+'" rel="noreferrer noopener">Fonte original</a>'
                    if c['status']=='pending':
                        body+='<div><form method="post" action="/approve">'+self.hidden(author)+'<input type="hidden" name="id" value="'+E(c['id'])+'"><label>Categoria <select name="kind">'+''.join('<option value="'+E(k)+'" '+('selected' if k==c['kind'] else '')+'>'+E(k)+'</option>' for k in press.KINDS)+'</select></label><label>Data <input name="date" value="'+E(c['candidate_date'] or '')+'" placeholder="AAAA-MM-DD"></label><button>Aprovar como pendente</button></form>'
                        body+='<form method="post" action="/reject">'+self.hidden(author)+'<input type="hidden" name="id" value="'+E(c['id'])+'"><label>Motivo <input name="reason" maxlength="500" required></label><button>Rejeitar</button></form></div>'
                    body+='</article>'
            self.send_page(self.wrap(body))
        except (ValueError,RuntimeError,OSError) as exc:self.error_page(str(exc))
        finally:db.close()
    def author_form(self):
        return '<div class="card"><form method="post" action="/author">'+self.hidden('')+'<label>Nome <input name="name" required></label><label>Site <input name="url" type="url" placeholder="https://..."></label><button>Cadastrar autor</button></form></div>'
    def do_POST(self):
        if not self.host_ok():return
        path=urllib.parse.urlsplit(self.path).path
        if path not in ('/author','/collect','/approve','/reject'):
            self.send_error(404);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=8192:raise ValueError('Formulário inválido ou muito grande')
            fields=urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'),keep_blank_values=True)
            form={k:v[0] for k,v in fields.items()}
            if not secrets.compare_digest(form.get('token',''),self.server.csrf):raise ValueError('Token de formulário inválido')
            author=form.get('author','')
            db=self.db()
            try:
                if path=='/author':
                    import uuid
                    name=form.get('name','').strip()
                    if not name:raise ValueError('Nome obrigatório')
                    author=str(uuid.uuid4())
                    with db:db.execute('INSERT INTO authors VALUES(?,?,?,?,?)',(author,name,press.validate_url(form.get('url')),None,press.now()))
                elif path=='/collect':
                    url=form.get('url','')
                    max_pages=int(form.get('max_pages','8'))
                    if not 1<=max_pages<=20:raise ValueError('Limite de páginas inválido')
                    discovery.discover(db,author,[url],max_pages=max_pages)
                elif path=='/approve':
                    press.approve_candidate(db,author,form.get('id'),form.get('kind'),form.get('date') or None)
                elif path=='/reject':
                    reason=form.get('reason','').strip()[:500]
                    if not reason:raise ValueError('Justificativa obrigatória')
                    with db:
                        cur=db.execute("UPDATE candidates SET status='rejected' WHERE id=? AND author_id=? AND status='pending'",(form.get('id'),author))
                        if cur.rowcount!=1:raise ValueError('Candidato indisponível para rejeição')
                        db.execute('INSERT INTO candidate_reviews(candidate_id,action,reason,reviewed_at) VALUES(?,?,?,?)',(form['id'],'rejected',reason,press.now()))
            finally:db.close()
            target='/candidates' if path in ('/collect','/approve','/reject') else '/'
            self.redirect(target+'?author='+urllib.parse.quote(author))
        except (ValueError,OSError,TypeError) as exc:self.error_page(str(exc))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='pressroom.sqlite3');p.add_argument('--port',type=int,default=8765)
    args=p.parse_args()
    if not 1024<=args.port<=65535:p.error('Porta deve estar entre 1024 e 65535')
    db=press.connect(args.db);db.close()
    server=Console(('127.0.0.1',args.port),args.db)
    print('PANDORA PRESS-CONSOLE Ω: http://127.0.0.1:'+str(args.port),flush=True)
    print('Somente localhost. Não exponha via proxy/túnel.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
