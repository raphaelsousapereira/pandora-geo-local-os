#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PANDORA ADS Ω v1.0.0 — auditor forense de Google Ads integrado ao ecossistema Pandora.

Arquivo único, stdlib only, Python 3.10+. SOMENTE LEITURA por construção: o motor
nunca altera a conta; ele lê relatórios exportados e produz achados e recomendações.

Entradas (CSV exportados da interface do Google Ads, em português ou inglês; as
linhas de título/período no topo do arquivo são ignoradas automaticamente):
  campaigns      Campanhas (orçamento, custo, conversões, status, parcela perdida)
  keywords       Palavras-chave de pesquisa (Índice de qualidade e componentes, URL final)
  search_terms   Termos de pesquisa
  negatives      Palavras-chave negativas
  conversions    Ações de conversão
  auction        Informações do leilão (Auction Insights)
  search_console Consultas do Google Search Console (cruzamento SEO × Ads)

Configuração (JSON): ver examples/ads/config.json e docs/ADS_OMEGA.md.

Comandos:
 python scripts/pandora_ads_omega.py audit --config examples/ads/config.json --json r.json --md r.md
 python scripts/pandora_ads_omega.py audit --config cfg.json --check-landing-pages
 python scripts/pandora_ads_omega.py selftest

Cada achado carrega a base epistêmica de suas afirmações:
  VERIFICADO  fato lido nos dados exportados
  INFERIDO    conclusão derivada dos dados por regra explícita
  HIPÓTESE    limiar ou prática de mercado, não garantida pelo Google
Score 0–1000 = proxy de higiene da conta, não previsão de resultado.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unicodedata

VERSION = '1.0.0'
DAYS_PER_MONTH = 30.4  # o Google limita o gasto mensal a 30,4 × orçamento diário

# --------------------------------------------------------------------- modelo
VERIFICADO, INFERIDO, HIPOTESE = 'VERIFICADO', 'INFERIDO', 'HIPÓTESE'
SEV_ORDER = {'CRÍTICO': 0, 'ALTO': 1, 'MÉDIO': 2, 'BAIXO': 3, 'INFO': 4}


@dataclass
class Claim:
    statement: str
    basis: str  # VERIFICADO | INFERIDO | HIPÓTESE
    source: str = ''


@dataclass
class Finding:
    gear: str
    code: str
    severity: str
    title: str
    diagnosis: str
    prescription: list[str]
    claims: list[Claim] = field(default_factory=list)
    evidence: object = None
    cost_at_stake: float | None = None  # custo observado no período (VERIFICADO), não projeção


# ------------------------------------------------------------ normalização
def fold(s: str) -> str:
    s = unicodedata.normalize('NFKD', str(s).casefold())
    return ''.join(c for c in s if not unicodedata.combining(c))


def tokens(s: str) -> list[str]:
    return re.findall(r'[a-z0-9]+', fold(s))


def norm_text(s: str) -> str:
    return ' '.join(tokens(s))


def parse_number(v) -> float | None:
    """Aceita '1.234,56', '1,234.56', '12,5%', 'R$ 3,20', '--', ' < 10%'."""
    if v is None: return None
    s = str(v).strip()
    if s in ('', '--', '—', '-', ' --'): return None
    s = re.sub(r'[^\d,.\-]', '', s)
    if not s or s in ('-', '.', ','): return None
    if ',' in s and '.' in s:  # o último separador é o decimal
        s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
    elif re.fullmatch(r'-?\d{1,3}([.,]\d{3})+', s):  # 12.000 / 1,234 → milhar
        s = s.replace('.', '').replace(',', '')
    else:  # 35,20 / 1.5 → decimal
        s = s.replace(',', '.')
    try: return float(s)
    except ValueError: return None


def parse_pct(v) -> float | None:
    """Percentual como fração (12,5% → 0.125). '< 10%' → 0.1 (limite superior informado)."""
    n = parse_number(v)
    if n is None: return None
    return n / 100 if ('%' in str(v) or n > 1) else n


# --------------------------------------------------------------- leitura CSV
ALIASES = {
    'campaign': ['campanha', 'campaign'],
    'ad_group': ['grupo de anuncios', 'ad group'],
    'status': ['status da campanha', 'campaign status', 'status', 'estado'],
    'budget': ['orcamento', 'budget', 'orcamento diario', 'daily budget'],
    'bid_strategy': ['tipo de estrategia de lances', 'bid strategy type', 'estrategia de lances', 'bid strategy'],
    'impressions': ['impr', 'impressoes', 'impressions', 'impr.'],
    'clicks': ['cliques', 'clicks'],
    'cost': ['custo', 'cost'],
    'ctr': ['ctr'],
    'conversions': ['conversoes', 'conversions', 'conv'],
    'conv_value': ['valor conv', 'valor da conv', 'valor de conv', 'conv value', 'conversion value', 'valor das conversoes'],
    'lost_is_budget': ['parcela de impressoes de pesquisa perdidas orcamento', 'parcela perdida de impressoes de pesquisa orcamento',
                       'search lost is budget', 'search lost impression share budget', 'is perdida orcamento'],
    'lost_is_rank': ['parcela de impressoes de pesquisa perdidas classificacao', 'search lost is rank',
                     'search lost impression share rank'],
    'search_is': ['parcela de impressoes de pesquisa', 'search impr share', 'search impression share'],
    'keyword': ['palavra chave', 'keyword', 'palavra chave de pesquisa', 'search keyword'],
    'match_type': ['tipo de correspondencia', 'match type', 'correspondencia da palavra chave', 'keyword match type'],
    'quality_score': ['indice de qualidade', 'quality score', 'qs'],
    'exp_ctr': ['ctr esperada', 'exp ctr', 'expected ctr'],
    'ad_relevance': ['relevancia do anuncio', 'ad relevance'],
    'lp_experience': ['experiencia na pagina de destino', 'landing page exp', 'landing page experience'],
    'final_url': ['url final', 'final url', 'urls finais', 'final urls'],
    'search_term': ['termo de pesquisa', 'search term', 'termos de pesquisa'],
    'negative': ['palavra chave negativa', 'negative keyword', 'palavras chave negativas'],
    'level': ['nivel', 'level', 'lista de palavras chave negativas', 'negative keyword list'],
    'conversion_action': ['acao de conversao', 'conversion action', 'nome', 'name'],
    'category': ['categoria', 'category', 'meta', 'goal'],
    'count': ['contagem', 'count'],
    'window': ['janela de conversao de clique', 'click through conversion window', 'janela de conversao', 'conversion window'],
    'include_in_conversions': ['incluir em conversoes', 'include in conversions', 'acao primaria', 'primary action', 'otimizacao', 'optimization'],
    'source': ['origem', 'source'],
    'domain': ['dominio de exibicao do url', 'display url domain', 'dominio', 'domain'],
    'impression_share': ['parcela de impressoes', 'impression share'],
    'overlap_rate': ['taxa de sobreposicao', 'overlap rate'],
    'position_above': ['taxa de posicao acima', 'position above rate'],
    'top_of_page': ['taxa de topo da pagina', 'top of page rate'],
    'outranking_share': ['parcela de superacao', 'outranking share'],
    'query': ['consultas principais', 'top queries', 'consulta', 'query'],
    'position': ['posicao', 'position', 'posicao media'],
}


def _key(h: str) -> str:
    return ' '.join(tokens(h))


def _map_header(header: list[str]) -> dict[int, str]:
    mapping = {}
    for i, h in enumerate(header):
        k = _key(h)
        for name, aliases in ALIASES.items():
            if name in mapping.values(): continue
            if any(k == _key(a) for a in aliases):
                mapping[i] = name; break
    # segunda passada: prefixo (ex.: "Custo / conv." não deve virar custo) — só exato acima
    return mapping


def read_report(path_or_text, required: tuple[str, ...]) -> list[dict]:
    """Lê CSV/TSV do Google Ads, pulando linhas de título até achar o cabeçalho."""
    if isinstance(path_or_text, Path) or (isinstance(path_or_text, str) and '\n' not in path_or_text):
        raw = Path(path_or_text).read_bytes()
        encs = ('utf-16',) if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else ('utf-8-sig', 'cp1252', 'latin-1')
        for enc in encs:
            try: text = raw.decode(enc); break
            except UnicodeDecodeError: continue
    else:
        text = path_or_text
    sample = text[:4096]
    delim = '\t' if sample.count('\t') > sample.count(',') and sample.count('\t') > sample.count(';') else \
        (';' if sample.count(';') > sample.count(',') else ',')
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    for idx, row in enumerate(rows[:15]):
        mapping = _map_header(row)
        if all(r in mapping.values() for r in required):
            out = []
            for r in rows[idx + 1:]:
                if not any(c.strip() for c in r): continue
                rec = {name: (r[i].strip() if i < len(r) else '') for i, name in mapping.items()}
                first = fold(r[0]) if r else ''
                if first.startswith(('total', 'totais')): continue  # linhas de total
                out.append(rec)
            return out
    raise ValueError(f'Cabeçalho não reconhecido; colunas obrigatórias: {", ".join(required)}')


# ----------------------------------------------------------- regras / listas
# Padrões de intenção não comercial (HIPÓTESE; o operador ajusta por negócio em config.waste_patterns).
DEFAULT_WASTE_PATTERNS = {
    'gratuidade': ['gratis', 'gratuito', 'gratuita', 'free', 'de graca'],
    'download/pirataria': ['download', 'baixar', 'torrent', 'crack', 'pdf gratis'],
    'aprendizado': ['tutorial', 'como fazer', 'o que e', 'significado', 'definicao', 'apostila', 'curso gratis'],
    'emprego': ['vaga', 'vagas', 'emprego', 'empregos', 'salario', 'curriculo', 'estagio', 'trainee', 'trabalhe conosco'],
}
CRITICAL_BY_BUSINESS = {
    'ecommerce': ['purchase'], 'leadgen': ['lead'], 'local': ['lead', 'phone_call'],
    'saas': ['lead', 'signup'], 'app': ['app_install'], 'b2b': ['lead'],
}
CATEGORY_HINTS = {
    'purchase': ['compra', 'purchase', 'venda', 'checkout'],
    'lead': ['lead', 'formulario', 'form', 'contato', 'orcamento', 'submit', 'whatsapp', 'agendamento', 'cadastro'],
    'phone_call': ['ligacao', 'phone', 'call', 'telefone', 'chamada'],
    'signup': ['signup', 'sign up', 'inscricao', 'registro', 'trial'],
    'app_install': ['instalacao', 'install', 'app'],
}


def contains_phrase(text_tokens: list[str], phrase_tokens: list[str]) -> bool:
    n = len(phrase_tokens)
    return n > 0 and any(text_tokens[i:i + n] == phrase_tokens for i in range(len(text_tokens) - n + 1))


def original_span(text: str, phrase_tokens: list[str]) -> str:
    """Devolve o trecho com a grafia original (acentos) que corresponde a phrase_tokens."""
    words = re.findall(r'\w+', text.lower())
    folded = [fold(w) for w in words]
    n = len(phrase_tokens)
    for i in range(len(folded) - n + 1):
        if folded[i:i + n] == phrase_tokens: return ' '.join(words[i:i + n])
    return ' '.join(phrase_tokens)


def negative_blocks(neg_text: str, neg_match: str, query: str) -> bool:
    """Semântica real das negativas no Google Ads (sem variantes próximas):
    exata: consulta idêntica; frase: termos contíguos na ordem; ampla: todos os termos, qualquer ordem.
    Negativa ampla NÃO bloqueia sinônimos nem variações."""
    nt, qt = tokens(neg_text), tokens(query)
    m = fold(neg_match)
    if not nt: return False
    if 'exat' in m or 'exact' in m or neg_text.strip().startswith('['):
        return nt == qt
    if 'frase' in m or 'phrase' in m or neg_text.strip().startswith('"'):
        return contains_phrase(qt, nt)
    return set(nt) <= set(qt)


def _f(row, k, default=0.0):
    v = parse_number(row.get(k))
    return default if v is None else v


def _money(v: float, cur: str) -> str:
    return f'{cur} {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


# ------------------------------------------------------------------ engine
class AdsAudit:
    def __init__(self, cfg: dict, base_dir: Path | None = None):
        self.cfg = cfg
        self.base = base_dir or Path('.')
        self.cur = cfg.get('currency', 'R$')
        self.findings: list[Finding] = []
        self.data: dict[str, list[dict]] = {}
        self.not_measured: list[str] = []
        self.landing: list[dict] = []

    # -------------------------------------------------------------- dados
    REQUIRED = {
        'campaigns': ('campaign', 'cost'), 'keywords': ('keyword', 'impressions'),
        'search_terms': ('search_term', 'cost'), 'negatives': ('negative',),
        'conversions': ('conversion_action',), 'auction': ('domain', 'impression_share'),
        'search_console': ('query', 'position'),
    }

    def load(self, inline: dict | None = None):
        sources = self.cfg.get('sources', {})
        for name, req in self.REQUIRED.items():
            if inline and name in inline:
                self.data[name] = read_report(inline[name], req)
            elif sources.get(name):
                p = Path(sources[name]); p = p if p.is_absolute() else self.base / p
                self.data[name] = read_report(p, req)
            else:
                self.data[name] = []
                self.not_measured.append(name)

    def add(self, *a, **kw):
        self.findings.append(Finding(*a, **kw))

    # ---------------------------------------------------- engrenagens
    def gear_conversions(self):
        rows = self.data['conversions']
        if 'conversions' in self.not_measured: return
        biz = self.cfg.get('business_type', 'leadgen')
        cycle = int(self.cfg.get('sales_cycle_days', 30))
        if not rows:
            self.add('CONVERSÕES', 'NO_CONVERSION_ACTIONS', 'CRÍTICO', 'Nenhuma ação de conversão',
                     'Sem conversões o Smart Bidding otimiza às cegas e não há como medir retorno.',
                     ['Implementar a conversão principal do negócio (GTM ou tag do Google) antes de investir mais.'],
                     [Claim('Relatório de ações de conversão vazio', VERIFICADO)])
            return
        def kind(r):
            text = fold(r.get('conversion_action', '') + ' ' + r.get('category', ''))
            return next((k for k, hints in CATEGORY_HINTS.items() if any(h in text for h in hints)), 'other')
        kinds = {kind(r) for r in rows}
        missing = [k for k in CRITICAL_BY_BUSINESS.get(biz, ['lead']) if k not in kinds]
        if missing and not (biz == 'local' and ('lead' in kinds or 'phone_call' in kinds)):
            self.add('CONVERSÕES', 'CRITICAL_CONVERSION_MISSING', 'ALTO', 'Conversão-chave do negócio não identificada',
                     f'Tipo de negócio "{biz}" sem ação reconhecível de: {", ".join(missing)}.',
                     ['Confirmar se a conversão existe com outro nome; se não existir, implementar.'],
                     [Claim('Nomes/categorias das ações exportadas', VERIFICADO),
                      Claim('Classificação por palavras no nome da ação', INFERIDO)], evidence=sorted(kinds))
        names = Counter(norm_text(r.get('conversion_action', '')) for r in rows)
        dups = [n for n, c in names.items() if c > 1]
        # mesma intenção vinda de origens diferentes (ex.: GA4 + tag do Google Ads), ambas primárias
        by_kind = defaultdict(list)
        for r in rows:
            prim = fold(r.get('include_in_conversions', 'sim'))
            if prim in ('', 'sim', 'yes', 'true', 'primaria', 'primary', 'principal'):
                by_kind[kind(r)].append(r)
        multi = {k: [r.get('conversion_action') for r in v] for k, v in by_kind.items()
                 if k != 'other' and len({fold(r.get('source', '')) for r in v}) > 1}
        if dups or multi:
            self.add('CONVERSÕES', 'POSSIBLE_DOUBLE_COUNT', 'ALTO', 'Possível contagem dupla de conversões',
                     'Ações repetidas ou a mesma intenção primária vinda de origens diferentes (ex.: GA4 importado + tag direta).',
                     ['Manter só uma ação primária por evento de negócio; a outra como secundária.',
                      'Em compras, enviar o ID da transação para deduplicar.'],
                     [Claim('Nomes/origens das ações', VERIFICADO), Claim('Duplicidade presumida pela origem', INFERIDO)],
                     evidence={'nomes_repetidos': dups, 'mesma_intencao_varias_origens': multi})
        if by_kind == {} or all(fold(r.get('include_in_conversions', 'sim')) in ('nao', 'no', 'false', 'secundaria', 'secondary')
                               for r in rows):
            self.add('CONVERSÕES', 'NO_PRIMARY_CONVERSION', 'CRÍTICO', 'Nenhuma conversão primária usada nos lances',
                     'Nenhuma ação está marcada para entrar em "Conversões".',
                     ['Marcar a conversão principal do negócio como primária.'], [Claim('Coluna de inclusão', VERIFICADO)])
        for r in rows:
            k = kind(r); w = parse_number(r.get('window'))
            cnt = fold(r.get('count', ''))
            if w and w < min(cycle, 30) and k in ('lead', 'purchase', 'phone_call'):
                self.add('CONVERSÕES', 'WINDOW_SHORTER_THAN_CYCLE', 'MÉDIO', f'Janela curta: {r.get("conversion_action")}',
                         f'Janela de {int(w)} dias para ciclo de venda informado de {cycle} dias.',
                         [f'Ampliar a janela para cobrir o ciclo (até {max(30, min(cycle, 90))} dias).'],
                         [Claim(f'Janela = {int(w)} dias', VERIFICADO), Claim('Janela deve refletir o ciclo de decisão', HIPOTESE, 'Masterclass cap. 7.1')])
            if k in ('lead', 'phone_call') and cnt and any(x in cnt for x in ('toda', 'every', 'many')):
                self.add('CONVERSÕES', 'LEAD_COUNTED_EVERY', 'MÉDIO', f'Lead contado "todas": {r.get("conversion_action")}',
                         'Leads contados a cada evento inflam conversões quando a mesma pessoa envia duas vezes.',
                         ['Usar contagem "Uma" para leads e ligações.'], [Claim('Contagem configurada', VERIFICADO)])
        crm = self.cfg.get('crm_conversions_month'); ads_conv = sum(_f(r, 'conversions') for r in self.data['campaigns'])
        if crm and ads_conv:
            diff = abs(ads_conv - crm) / max(crm, 1)
            if diff > 0.20:
                self.add('CONVERSÕES', 'CRM_DISCREPANCY', 'ALTO', 'Ads e CRM divergem mais de 20%',
                         f'Ads registra {ads_conv:.0f} conversões; CRM informa {crm}. Diferença de {diff:.0%}.',
                         ['Auditar disparo da tag, duplicidade e conversões offline antes de mexer em lances.'],
                         [Claim('Conversões no período (campanhas)', VERIFICADO), Claim('Número do CRM informado na configuração', VERIFICADO),
                          Claim('Divergência > 20% indica problema de rastreio', HIPOTESE, 'Masterclass cap. 7.1')])

    def gear_search_terms(self):
        rows = self.data['search_terms']
        if 'search_terms' in self.not_measured or not rows: return
        target_cpa = self.cfg.get('target_cpa')
        tot_cost = sum(_f(r, 'cost') for r in rows); tot_conv = sum(_f(r, 'conversions') for r in rows)
        acc_cpa = tot_cost / tot_conv if tot_conv else None
        ref_cpa = target_cpa or acc_cpa
        clicks = sum(_f(r, 'clicks') for r in rows); impr = sum(_f(r, 'impressions') for r in rows)
        acc_ctr = clicks / impr if impr else None
        patterns = self.cfg.get('waste_patterns') or DEFAULT_WASTE_PATTERNS
        allow = [tokens(a) for a in self.cfg.get('allow_terms', [])]
        kw = {norm_text(r.get('keyword', '')) for r in self.data['keywords']}
        negs = self.data['negatives']
        waste, winners, lp_suspects, blocked_but_spent = [], [], [], []
        for r in rows:
            term = r.get('search_term', ''); tt = tokens(term)
            cost, conv, clk = _f(r, 'cost'), _f(r, 'conversions'), _f(r, 'clicks')
            if any(contains_phrase(tt, a) for a in allow if a): continue
            hit = next(((cat, p) for cat, ps in patterns.items() for p in ps if contains_phrase(tt, tokens(p))), None)
            if conv == 0 and cost > 0 and hit:
                waste.append({'term': term, 'cost': cost, 'reason': f'{hit[0]}: "{hit[1]}"',
                              'suggest': f'"{original_span(term, tokens(hit[1]))}" (frase)'})
            elif conv == 0 and ref_cpa and cost >= ref_cpa:
                waste.append({'term': term, 'cost': cost, 'reason': f'gastou ≥ 1 CPA de referência sem converter',
                              'suggest': f'[{norm_text(term)}] (exata) após revisão'})
            if conv >= 2 and norm_text(term) not in kw and (not ref_cpa or cost / conv <= ref_cpa):
                winners.append({'term': term, 'conversions': conv, 'cpa': round(cost / conv, 2)})
            ctr = clk / _f(r, 'impressions') if _f(r, 'impressions') else 0
            if acc_ctr and clk >= 20 and conv == 0 and ctr >= 2 * acc_ctr:
                lp_suspects.append({'term': term, 'clicks': clk, 'ctr': round(ctr, 4)})
            if cost > 0 and any(negative_blocks(n.get('negative', ''), n.get('match_type', ''), term) for n in negs):
                blocked_but_spent.append(term)
        if waste:
            spent = sum(w['cost'] for w in waste)
            self.add('TERMOS DE PESQUISA', 'WASTED_SEARCH_TERMS', 'ALTO' if spent > 0.05 * tot_cost else 'MÉDIO',
                     f'{len(waste)} termos sem conversão candidatos a negativa',
                     f'{_money(spent, self.cur)} ({spent / tot_cost:.0%} do custo dos termos) foram para termos sem conversão '
                     'com padrão de intenção não comercial ou custo ≥ 1 CPA.',
                     ['Revisar a lista e negativar o que não for do negócio (preferir frase/exata, a mais específica).',
                      'Adicionar em lista compartilhada de negativas; reauditar a lista a cada 6 meses.'],
                     [Claim('Custo e conversões por termo', VERIFICADO), Claim('Padrões de intenção não comercial', HIPOTESE, 'Masterclass cap. 2.2'),
                      Claim('Relatório de termos omite buscas de baixo volume', VERIFICADO, 'política de privacidade do Google Ads')],
                     evidence=sorted(waste, key=lambda w: -w['cost'])[:50], cost_at_stake=round(spent, 2))
        if winners:
            self.add('TERMOS DE PESQUISA', 'CONVERTING_TERMS_NOT_KEYWORDS', 'MÉDIO',
                     f'{len(winners)} termos que convertem ainda não são palavras-chave',
                     'Termos descobertos por correspondência ampla/frase convertendo dentro do CPA de referência.',
                     ['Adicionar como correspondência exata no grupo de intenção correspondente.',
                      'Usar como pauta de conteúdo orgânico (SEO/GEO).'],
                     [Claim('Conversões e custo por termo', VERIFICADO)], evidence=sorted(winners, key=lambda w: -w['conversions'])[:50])
        if lp_suspects:
            self.add('TERMOS DE PESQUISA', 'HIGH_CTR_NO_CONVERSION', 'MÉDIO', 'CTR alto sem conversão',
                     'Anúncio atrai (CTR ≥ 2× a média) mas a página não converte para essas buscas.',
                     ['Verificar se a landing page responde à intenção desses termos; testar página específica.'],
                     [Claim('CTR e conversões por termo', VERIFICADO), Claim('Problema provável na página', INFERIDO)], evidence=lp_suspects[:30])
        if blocked_but_spent:
            self.add('NEGATIVAS', 'NEGATIVE_NOT_EFFECTIVE', 'BAIXO', 'Termos com gasto que a lista de negativas atual bloquearia',
                     'Negativas adicionadas depois do período ou em outro nível (campanha × grupo).', ['Conferir o nível de aplicação das negativas.'],
                     [Claim('Comparação termo × negativa pela regra de correspondência', INFERIDO)], evidence=blocked_but_spent[:30])

    def gear_negative_conflicts(self):
        negs, kws = self.data['negatives'], self.data['keywords']
        if not negs or not kws: return
        conflicts = []
        for n in negs:
            for k in kws:
                if negative_blocks(n.get('negative', ''), n.get('match_type', ''), k.get('keyword', '')):
                    same_scope = not n.get('campaign') or not k.get('campaign') or n.get('campaign') == k.get('campaign')
                    if same_scope:
                        conflicts.append({'negative': n.get('negative'), 'match': n.get('match_type'), 'blocks_keyword': k.get('keyword'),
                                          'campaign': k.get('campaign')})
        if conflicts:
            self.add('NEGATIVAS', 'NEGATIVE_BLOCKS_KEYWORD', 'ALTO', f'{len(conflicts)} negativas bloqueiam palavras-chave ativas',
                     'A negativa impede que a própria palavra-chave seja exibida.',
                     ['Remover ou tornar a negativa mais específica (exata) onde há conflito.'],
                     [Claim('Regra de correspondência de negativas (exata/frase/ampla, sem sinônimos)', VERIFICADO, 'documentação do Google Ads')],
                     evidence=conflicts[:50])

    def gear_quality(self):
        rows = self.data['keywords']
        if 'keywords' in self.not_measured or not rows: return
        scored = [r for r in rows if parse_number(r.get('quality_score')) is not None]
        if not scored:
            self.not_measured.append('quality_score (coluna ausente ou campanhas sem QS, ex.: Performance Max)'); return
        tot_cost = sum(_f(r, 'cost') for r in scored) or 1
        low = [r for r in scored if _f(r, 'quality_score') <= 5]
        low.sort(key=lambda r: -_f(r, 'impressions'))
        if low:
            comp = Counter()
            for r in low:
                for c in ('exp_ctr', 'ad_relevance', 'lp_experience'):
                    if 'abaixo' in fold(r.get(c, '')) or 'below' in fold(r.get(c, '')): comp[c] += 1
            labels = {'exp_ctr': 'CTR esperada', 'ad_relevance': 'relevância do anúncio', 'lp_experience': 'experiência da página'}
            cost_low = sum(_f(r, 'cost') for r in low)
            rx = []
            if comp['ad_relevance']: rx.append('Relevância: grupos menores (5–15 palavras da mesma intenção) e palavra-chave no título.')
            if comp['exp_ctr']: rx.append('CTR esperada: títulos específicos, benefício concreto e chamada para ação.')
            if comp['lp_experience']: rx.append('Página: continuidade da promessa do anúncio, velocidade no celular (ver auditoria de landing pages).')
            self.add('QUALIDADE', 'LOW_QS_HIGH_VOLUME', 'ALTO' if cost_low > 0.25 * tot_cost else 'MÉDIO',
                     f'{len(low)} palavras com Índice de qualidade ≤ 5',
                     f'Concentram {cost_low / tot_cost:.0%} do custo das palavras com QS. Componentes "abaixo da média": '
                     + (', '.join(f'{labels[k]} ({v})' for k, v in comp.most_common()) or 'não informados') + '.',
                     rx or ['Exportar as colunas de componentes do QS para diagnosticar.'],
                     [Claim('QS e componentes por palavra', VERIFICADO), Claim('QS visível é diagnóstico (média histórica), não o valor do leilão', VERIFICADO, 'Google Ads Help'),
                      Claim('QS maior tende a reduzir CPC na mesma posição', HIPOTESE, 'Masterclass cap. 1.4 — magnitude varia')],
                     evidence=[{'keyword': r.get('keyword'), 'qs': _f(r, 'quality_score'), 'impressions': _f(r, 'impressions'),
                                'cost': _f(r, 'cost')} for r in low[:30]], cost_at_stake=round(cost_low, 2))
        groups = Counter((r.get('campaign'), r.get('ad_group')) for r in rows if r.get('ad_group'))
        big = {f'{c} › {g}': n for (c, g), n in groups.items() if n > 20}
        if big:
            self.add('QUALIDADE', 'AD_GROUP_TOO_BROAD', 'BAIXO', 'Grupos de anúncios com muitas palavras',
                     'Grupos com mais de 20 palavras costumam misturar intenções e baixar a relevância.',
                     ['Dividir por intenção específica.'], [Claim('Contagem por grupo', VERIFICADO), Claim('Faixa de 5–15 palavras por grupo', HIPOTESE, 'Masterclass cap. 1.4')],
                     evidence=big)

    def gear_budget(self):
        rows = self.data['campaigns']
        if 'campaigns' in self.not_measured or not rows: return
        target_cpa = self.cfg.get('target_cpa'); goal = self.cfg.get('monthly_conversion_goal')
        daily = sum(_f(r, 'budget') for r in rows if 'pausad' not in fold(r.get('status', '')) and 'paused' not in fold(r.get('status', '')))
        if goal and target_cpa and daily:
            need = goal * target_cpa; have = daily * DAYS_PER_MONTH
            if have < 0.9 * need:
                self.add('ORÇAMENTO', 'BUDGET_BELOW_GOAL', 'ALTO', 'Orçamento não cabe na meta',
                         f'Meta {goal} conversões × CPA alvo {_money(target_cpa, self.cur)} = {_money(need, self.cur)}/mês; '
                         f'orçamentos ativos somam {_money(have, self.cur)}/mês ({_money(daily, self.cur)}/dia).',
                         [f'Ou ajustar a meta para ~{int(have / target_cpa)} conversões/mês, ou o orçamento para ~{_money(need / DAYS_PER_MONTH, self.cur)}/dia.'],
                         [Claim('Orçamentos diários exportados', VERIFICADO), Claim('Teto mensal = 30,4 × diário', VERIFICADO, 'Google Ads Help'),
                          Claim('Meta e CPA alvo informados na configuração', VERIFICADO)])
        perf = []
        for r in rows:
            cost, conv = _f(r, 'cost'), _f(r, 'conversions')
            cpa = cost / conv if conv else None
            lost = parse_pct(r.get('lost_is_budget')) or 0
            limited = 'limitad' in fold(r.get('status', '')) or 'limited' in fold(r.get('status', ''))
            perf.append({'campaign': r.get('campaign'), 'cost': cost, 'conversions': conv, 'cpa': cpa, 'lost_is_budget': lost, 'limited': limited})
        ref = target_cpa or (sum(p['cost'] for p in perf) / max(1, sum(p['conversions'] for p in perf)))
        scale = [p for p in perf if (p['limited'] or p['lost_is_budget'] >= 0.10) and p['cpa'] and p['cpa'] <= ref]
        drain = [p for p in perf if p['cost'] > 0 and (p['conversions'] == 0 and p['cost'] >= ref or (p['cpa'] and p['cpa'] > 1.3 * ref))]
        if scale:
            self.add('ORÇAMENTO', 'EFFICIENT_CAMPAIGN_BUDGET_LIMITED', 'ALTO', 'Campanhas eficientes perdendo impressões por orçamento',
                     'CPA dentro da referência e parcela perdida por orçamento ≥ 10% (ou status limitada).',
                     ['Remanejar verba das campanhas acima do CPA para estas antes de aumentar o total.',
                      'Mudanças > 30% no orçamento podem reiniciar o aprendizado do Smart Bidding: subir em degraus.'],
                     [Claim('Custo, conversões e parcela perdida', VERIFICADO), Claim('Degrau de 30%', HIPOTESE, 'Masterclass cap. 4.1')],
                     evidence=[{k: (round(v, 2) if isinstance(v, float) else v) for k, v in p.items()} for p in scale])
        if drain:
            spent = sum(p['cost'] for p in drain)
            self.add('ORÇAMENTO', 'CAMPAIGN_ABOVE_CPA', 'ALTO' if scale else 'MÉDIO', 'Campanhas acima do CPA de referência',
                     f'{_money(spent, self.cur)} em campanhas com CPA > 1,3 × referência ou sem conversão com custo ≥ 1 CPA.',
                     ['Revisar termos, landing page e lances destas campanhas; candidatas a doar verba.'],
                     [Claim('Custo e conversões por campanha', VERIFICADO), Claim('Corte de 1,3 × CPA de referência', HIPOTESE)],
                     evidence=[{k: (round(v, 2) if isinstance(v, float) else v) for k, v in p.items()} for p in drain], cost_at_stake=round(spent, 2))

    def gear_bidding(self):
        rows = self.data['campaigns']
        if 'campaigns' in self.not_measured: return
        weak, upgrade = [], []
        for r in rows:
            strat = fold(r.get('bid_strategy', '')); conv = _f(r, 'conversions')
            target_based = any(x in strat for x in ('cpa', 'roas', 'alvo', 'target'))
            if target_based and conv < 15:
                weak.append({'campaign': r.get('campaign'), 'strategy': r.get('bid_strategy'), 'conversions': conv})
            if any(x in strat for x in ('clique', 'click', 'manual', 'cpc')) and conv >= 30:
                upgrade.append({'campaign': r.get('campaign'), 'strategy': r.get('bid_strategy'), 'conversions': conv})
        if weak:
            self.add('LANCES', 'TARGET_BIDDING_LOW_SIGNAL', 'MÉDIO', 'Lance com alvo e pouco sinal de conversão',
                     'CPA/ROAS alvo com menos de 15 conversões no período: o algoritmo tem pouco dado para aprender.',
                     ['Considerar Maximizar conversões até acumular volume, ou consolidar campanhas para somar sinal.'],
                     [Claim('Estratégia e conversões', VERIFICADO),
                      Claim('Não há mínimo oficial; 15/30–50 por mês são faixas de mercado', HIPOTESE, 'Masterclass cap. 4.1; materiais divergem')], evidence=weak)
        if upgrade:
            self.add('LANCES', 'MANUAL_WITH_ENOUGH_SIGNAL', 'BAIXO', 'Lance manual/cliques com volume para Smart Bidding',
                     '30+ conversões no período com estratégia que não usa conversões.',
                     ['Testar via Experimento: Maximizar conversões → CPA alvo ~15–20% acima do histórico; aprendizado de ~2 semanas sem mexer.'],
                     [Claim('Estratégia e conversões', VERIFICADO), Claim('Sequência de transição', HIPOTESE, 'Masterclass cap. 4.1')], evidence=upgrade)

    def gear_auction(self):
        rows = self.data['auction']
        if 'auction' in self.not_measured or not rows: return
        own_domain = fold(self.cfg.get('own_domain', ''))
        own = next((r for r in rows if own_domain and own_domain in fold(r.get('domain', ''))) or
                   (r for r in rows if fold(r.get('domain', '')) in ('voce', 'you', 'sua conta')), None)
        own_is = parse_pct(own.get('impression_share')) if own else None
        threats = []
        for r in rows:
            if r is own: continue
            pa, isr = parse_pct(r.get('position_above')) or 0, parse_pct(r.get('impression_share')) or 0
            if pa > 0.6 or (own_is is not None and isr - own_is > 0.20):
                threats.append({'domain': r.get('domain'), 'impression_share': isr, 'position_above_rate': pa,
                                'outranking_share': parse_pct(r.get('outranking_share'))})
        if threats:
            self.add('CONCORRÊNCIA PAGA', 'AUCTION_THREATS', 'MÉDIO', f'{len(threats)} concorrentes dominando o leilão',
                     'Aparecem acima de você em > 60% dos leilões em comum ou têm parcela de impressões 20 p.p. maior.',
                     ['Antes de subir lance: melhorar Índice de qualidade e extensões (Ad Rank sem pagar mais).',
                      'Cruzar com o monitoramento orgânico do concorrente (PANDORA COMPETITOR Ω).'],
                     [Claim('Métricas do Auction Insights', VERIFICADO), Claim('Gasto do concorrente não é observável', VERIFICADO)], evidence=threats)

    def gear_seo_ads(self):
        gsc, st = self.data['search_console'], self.data['search_terms']
        if not gsc or not st: return
        org = {norm_text(r.get('query', '')): r for r in gsc}
        double, content, only_org = [], [], []
        for r in st:
            q = norm_text(r.get('search_term', '')); o = org.get(q)
            cost, conv = _f(r, 'cost'), _f(r, 'conversions')
            pos = parse_number(o.get('position')) if o else None
            if o and pos is not None and pos <= 1.5 and cost > 0:
                double.append({'query': r.get('search_term'), 'organic_position': pos, 'paid_cost': cost, 'paid_conversions': conv})
            if conv > 0 and (not o or (pos or 99) > 10):
                content.append({'query': r.get('search_term'), 'paid_conversions': conv, 'organic_position': pos})
        paid = {norm_text(r.get('search_term', '')) for r in st}
        for q, o in org.items():
            pos = parse_number(o.get('position'))
            if pos and 4 <= pos <= 10 and q not in paid and _f(o, 'impressions') >= 100:
                only_org.append({'query': o.get('query'), 'organic_position': pos, 'impressions': _f(o, 'impressions')})
        if double:
            spent = sum(d['paid_cost'] for d in double)
            self.add('SEO × ADS', 'PAID_WHERE_ORGANIC_TOP', 'MÉDIO', f'{len(double)} buscas pagas onde você já é 1º no orgânico',
                     f'{_money(spent, self.cur)} em cliques pagos para consultas com posição orgânica média ≤ 1,5.',
                     ['Rodar Experimento reduzindo lance nesses termos e medir conversões totais (pago + orgânico) — não cortar no escuro.'],
                     [Claim('Custo pago e posição orgânica por consulta', VERIFICADO), Claim('Retorno marginal decrescente com dupla presença', HIPOTESE, 'Masterclass cap. 11.1; depende da concorrência na SERP')],
                     evidence=sorted(double, key=lambda d: -d['paid_cost'])[:40], cost_at_stake=round(spent, 2))
        if content:
            self.add('SEO × ADS', 'CONVERTING_PAID_NO_ORGANIC', 'MÉDIO', f'{len(content)} consultas que convertem no pago sem presença orgânica',
                     'Intenção comprovada pelo pago e ausente (ou além da 10ª posição) no orgânico.',
                     ['Pauta prioritária de conteúdo (SEO/GEO): página que responda essa intenção; incluir no llms.txt.'],
                     [Claim('Conversões pagas e posição orgânica', VERIFICADO)], evidence=content[:40])
        if only_org:
            self.add('SEO × ADS', 'ORGANIC_4_10_NO_PAID', 'BAIXO', f'{len(only_org)} consultas orgânicas entre 4ª e 10ª sem anúncio',
                     'O pago pode comprar o topo enquanto o SEO trabalha a posição.',
                     ['Avaliar teste pago nas de intenção comercial.'], [Claim('Posição e impressões orgânicas', VERIFICADO)],
                     evidence=sorted(only_org, key=lambda d: -d['impressions'])[:40])

    def gear_landing_pages(self, fetcher=None):
        urls = sorted({r.get('final_url', '').strip() for r in self.data['keywords'] if r.get('final_url', '').startswith('http')})
        if not urls:
            self.not_measured.append('landing_pages (sem coluna URL final)'); return
        if fetcher is None:
            self.not_measured.append('landing_pages (use --check-landing-pages)'); return
        heading = _load_sibling('pandora_heading_audit.py')
        broken, slow_struct = [], []
        for u in urls[:int(self.cfg.get('max_landing_pages', 50))]:
            r = fetcher.get(u)
            rec = {'url': u, 'status': r.status, 'redirects': len(r.redirects), 'error': r.error}
            if r.status == 200 and heading:
                try:
                    h = heading.analyze(u, r.text()); rec['heading_score'] = h['score']
                    rec['h1'] = [x['text'] for x in h['headings'] if x['level'] == 1][:2]
                except Exception as e: rec['heading_error'] = str(e)
            self.landing.append(rec)
            if not r.captured: continue
            if r.status is None or r.status >= 400: broken.append(rec)
            elif rec.get('heading_score', 1000) < 800: slow_struct.append(rec)
        if broken:
            self.add('LANDING PAGES', 'BROKEN_FINAL_URL', 'CRÍTICO', f'{len(broken)} URLs finais com erro',
                     'Anúncios levando a páginas com erro desperdiçam 100% do clique.',
                     ['Corrigir a página ou a URL final imediatamente; manter checagem diária.'],
                     [Claim('Status HTTP no momento da auditoria', VERIFICADO)], evidence=broken)
        if slow_struct:
            self.add('LANDING PAGES', 'WEAK_LANDING_STRUCTURE', 'BAIXO', f'{len(slow_struct)} landing pages com estrutura fraca',
                     'Score de headings < 800 (motor PANDORA HEADING AUDIT): mensagem pouco clara para usuário, Google e IAs.',
                     ['Garantir H1 que repita a promessa do anúncio; ver relatório de headings.'],
                     [Claim('Score estrutural da página', VERIFICADO), Claim('Estrutura influencia experiência da página', HIPOTESE)], evidence=slow_struct)

    # ------------------------------------------------------------- score
    DIMENSIONS = {
        'rastreamento': (250, ['CONVERSÕES'], 'conversions'),
        'desperdicio': (200, ['TERMOS DE PESQUISA', 'NEGATIVAS'], 'search_terms'),
        'qualidade': (200, ['QUALIDADE'], 'keywords'),
        'orcamento_lances': (200, ['ORÇAMENTO', 'LANCES'], 'campaigns'),
        'landing_pages': (150, ['LANDING PAGES'], None),
    }
    PENALTY = {'CRÍTICO': 120, 'ALTO': 60, 'MÉDIO': 30, 'BAIXO': 10, 'INFO': 0}

    def score(self):
        dims = {}
        for name, (maxi, gears, src) in self.DIMENSIONS.items():
            measured = (src not in self.not_measured) if src else bool(self.landing)
            loss = sum(self.PENALTY[f.severity] for f in self.findings if f.gear in gears)
            dims[name] = {'score': max(0, maxi - loss) if measured else None, 'max': maxi, 'measured': measured}
        m = [d for d in dims.values() if d['measured']]
        total = round(sum(d['score'] for d in m) / sum(d['max'] for d in m) * 1000) if m else None
        return total, dims

    def run(self, inline=None, fetcher=None):
        self.load(inline)
        for gear in (self.gear_conversions, self.gear_search_terms, self.gear_negative_conflicts, self.gear_quality,
                     self.gear_budget, self.gear_bidding, self.gear_auction, self.gear_seo_ads):
            gear()
        self.gear_landing_pages(fetcher)
        self.findings.sort(key=lambda f: (SEV_ORDER[f.severity], -(f.cost_at_stake or 0)))
        total, dims = self.score()
        camp = self.data['campaigns']
        cost = sum(_f(r, 'cost') for r in camp); conv = sum(_f(r, 'conversions') for r in camp)
        return {
            'engine': 'PANDORA ADS Ω', 'version': VERSION, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'account': self.cfg.get('account_name', ''), 'period': self.cfg.get('period', ''), 'currency': self.cur,
            'mode': 'read_only', 'score': total, 'max_score': 1000, 'dimensions': dims,
            'summary': {'campaigns': len(camp), 'cost': round(cost, 2), 'conversions': round(conv, 2),
                        'cpa': round(cost / conv, 2) if conv else None, 'findings': len(self.findings),
                        'severity': dict(Counter(f.severity for f in self.findings))},
            'findings': [asdict(f) for f in self.findings], 'landing_pages': self.landing,
            'not_measured': self.not_measured,
            'limitations': ['Somente leitura: nenhuma alteração é feita na conta',
                            'Score é proxy de higiene da conta, não previsão de resultado',
                            'Relatório de termos de pesquisa omite buscas de baixo volume',
                            'Limiares marcados como HIPÓTESE são práticas de mercado, não regras do Google',
                            'Performance Max não expõe Índice de qualidade por palavra-chave'],
        }


def _load_sibling(name):
    p = Path(__file__).with_name(name)
    if not p.exists(): return None
    spec = importlib.util.spec_from_file_location(p.stem, p)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod
    try: spec.loader.exec_module(mod)
    except Exception: return None
    return mod


# ------------------------------------------------------------------- saída
def _fmt(v, cur=None):
    if isinstance(v, float):
        if cur: return _money(v, cur)
        return f'{v:.0%}' if 0 < v < 1 else f'{v:g}'
    if isinstance(v, (list, dict)): return json.dumps(v, ensure_ascii=False)
    return str(v)


def render_md(r):
    cur = r['currency']
    s = r['summary']
    L = [f'# PANDORA ADS Ω v{r["version"]} — {r["account"] or "conta"}', '',
         f'Período: {r["period"] or "não informado"} · Gerado (UTC): {r["generated_at"]} · Modo: **somente leitura**', '',
         f'**Score de higiene: {r["score"] if r["score"] is not None else "N/A"}/1000** (proxy, não previsão de resultado)', '',
         '| Dimensão | Score |', '|---|---:|']
    for k, d in r['dimensions'].items():
        L.append(f'| {k} | {d["score"] if d["measured"] else "não medido"}/{d["max"]} |')
    L += ['', f'Campanhas: {s["campaigns"]} · Custo: {_money(s["cost"], cur)} · Conversões: {s["conversions"]:g} · '
              f'CPA: {_money(s["cpa"], cur) if s["cpa"] else "—"}', '',
          '## O que aconteceu, por quê e o que fazer', '']
    for i, f in enumerate(r['findings'], 1):
        at = f' · em jogo: {_money(f["cost_at_stake"], cur)}' if f.get('cost_at_stake') else ''
        L += [f'### {i}. [{f["severity"]}] {f["title"]}', f'*{f["gear"]} · {f["code"]}{at}*', '', f['diagnosis'], '', '**Ações:**']
        L += [f'- {p}' for p in f['prescription']]
        ev = f.get('evidence')
        if ev:
            L += ['', '**Evidências:**']
            items = list(ev.items()) if isinstance(ev, dict) else list(ev)
            for item in items[:8]:
                if isinstance(item, dict):
                    L.append('- ' + ' · '.join(f'{k}: {_fmt(v, cur) if k in ("cost", "paid_cost", "cpa") else _fmt(v)}' for k, v in item.items() if v not in (None, '', [])))
                elif isinstance(item, tuple):
                    if item[1] not in (None, '', [], {}): L.append(f'- {item[0]}: {_fmt(item[1])}')
                else:
                    L.append(f'- {item}')
            if len(items) > 8: L.append(f'- … e mais {len(items) - 8} (ver JSON)')
        L += ['', '**Base:** ' + ' · '.join(f'[{c["basis"]}] {c["statement"]}' + (f' ({c["source"]})' if c['source'] else '') for c in f['claims']), '']
    if r['not_measured']:
        L += ['## Não medido', ''] + [f'- {x}' for x in r['not_measured']] + ['']
    L += ['## Limites', ''] + [f'- {x}' for x in r['limitations']] + ['']
    return '\n'.join(L)


# ---------------------------------------------------------------- selftest
SAMPLE = {
    'campaigns': 'Relatório de campanhas\n1 de set de 2026 - 30 de set de 2026\n'
                 'Campanha,Status da campanha,Orçamento,Tipo de estratégia de lances,Impr.,Cliques,Custo,Conversões,'
                 'Parcela de impressões de pesquisa perdidas (orçamento)\n'
                 'Advogado Trabalhista,Qualificada (limitada pelo orçamento),"50,00",CPA desejado,"12.000",600,"1.500,00",30,"35,20%"\n'
                 'Institucional,Qualificada,"40,00",Maximizar cliques,"8.000",400,"1.200,00",3,"0,00%"\n'
                 'Total: conta,,,,,,"2.700,00",33,\n',
    'keywords': 'Palavra-chave,Tipo de correspondência,Campanha,Grupo de anúncios,Índice de qualidade,CTR esperada,'
                'Relevância do anúncio,Experiência na página de destino,Impr.,Custo,Conversões,URL final\n'
                'advogado trabalhista,Exata,Advogado Trabalhista,Trabalhista,8,Acima da média,Acima da média,Média,"5.000","700,00",20,https://ex.com/trabalhista\n'
                'processo trabalhista,Frase,Advogado Trabalhista,Trabalhista,4,Abaixo da média,Abaixo da média,Média,"6.000","800,00",10,https://ex.com/trabalhista\n'
                'escritório de advocacia,Ampla,Institucional,Geral,3,Abaixo da média,Média,Abaixo da média,"8.000","1.200,00",3,https://ex.com/\n',
    'search_terms': 'Termo de pesquisa,Palavra-chave,Campanha,Impr.,Cliques,Custo,Conversões\n'
                    'advogado trabalhista porto alegre,advogado trabalhista,Advogado Trabalhista,"2.000",150,"300,00",8\n'
                    'vagas advogado trabalhista,advogado trabalhista,Advogado Trabalhista,800,40,"90,00",0\n'
                    'modelo de petição grátis,processo trabalhista,Advogado Trabalhista,500,30,"60,00",0\n'
                    'calcular rescisão,processo trabalhista,Advogado Trabalhista,400,60,"20,00",0\n'
                    'escritório advocacia centro,escritório de advocacia,Institucional,"1.000",50,"200,00",0\n',
    'negatives': 'Palavra-chave negativa,Tipo de correspondência,Campanha\n'
                 'processo,Ampla,Advogado Trabalhista\n'
                 'grátis,Frase,Advogado Trabalhista\n',
    'conversions': 'Ação de conversão,Origem,Contagem,Janela de conversão de clique,Incluir em "Conversões"\n'
                   'Formulário de contato,Website,Todas,7 dias,Sim\n'
                   'Formulário de contato (GA4),Google Analytics 4,Uma,30 dias,Sim\n',
    'auction': 'Domínio de exibição do URL,Parcela de impressões,Taxa de sobreposição,Taxa de posição acima,Parcela de superação\n'
               'Você,"45,00%",--,--,--\nconcorrente.com.br,"70,00%","60,00%","65,00%","30,00%"\n',
    'search_console': 'Consultas principais,Cliques,Impressões,CTR,Posição\n'
                      'advogado trabalhista porto alegre,120,"3.000","4%","1,2"\n'
                      'direitos na demissão,30,"2.500","1,2%","6,4"\n',
}


def selftest():
    import unittest

    class T(unittest.TestCase):
        def run_sample(self, **cfg):
            base = {'account_name': 'Teste', 'business_type': 'leadgen', 'target_cpa': 60, 'monthly_conversion_goal': 80,
                    'crm_conversions_month': 20, 'sales_cycle_days': 30, 'own_domain': 'você'}
            base.update(cfg)
            a = AdsAudit(base); return a, a.run(inline=SAMPLE)

        def codes(self, r): return {f['code'] for f in r['findings']}

        def test_numbers(self):
            self.assertEqual(parse_number('1.500,00'), 1500.0); self.assertEqual(parse_number('1,234.5'), 1234.5)
            self.assertEqual(parse_number('35,20%'), 35.2); self.assertAlmostEqual(parse_pct('35,20%'), 0.352)
            self.assertIsNone(parse_number('--')); self.assertEqual(parse_number('12.000'), 12000.0)

        def test_negative_semantics(self):
            self.assertTrue(negative_blocks('processo', 'Ampla', 'processo trabalhista'))
            self.assertTrue(negative_blocks('vaga emprego', 'Ampla', 'emprego de vaga'))
            self.assertFalse(negative_blocks('vaga emprego', 'Frase', 'emprego de vaga'))
            self.assertFalse(negative_blocks('free', 'Ampla', 'freelancer'))
            self.assertFalse(negative_blocks('gratis', 'Ampla', 'gratuito'))  # ampla não pega variações
            self.assertTrue(negative_blocks('[advogado]', '', 'advogado')); self.assertFalse(negative_blocks('[advogado]', '', 'advogado sp'))

        def test_full_audit(self):
            a, r = self.run_sample()
            c = self.codes(r)
            for code in ('NEGATIVE_BLOCKS_KEYWORD', 'WASTED_SEARCH_TERMS', 'CONVERTING_TERMS_NOT_KEYWORDS', 'LOW_QS_HIGH_VOLUME',
                         'BUDGET_BELOW_GOAL', 'EFFICIENT_CAMPAIGN_BUDGET_LIMITED', 'CAMPAIGN_ABOVE_CPA', 'POSSIBLE_DOUBLE_COUNT',
                         'WINDOW_SHORTER_THAN_CYCLE', 'LEAD_COUNTED_EVERY', 'CRM_DISCREPANCY', 'AUCTION_THREATS',
                         'PAID_WHERE_ORGANIC_TOP', 'ORGANIC_4_10_NO_PAID'):
                self.assertIn(code, c, code)
            self.assertNotIn('CRITICAL_CONVERSION_MISSING', c)  # leadgen com formulário: não exigir compra
            self.assertEqual(r['summary']['campaigns'], 2)  # linha de total ignorada
            self.assertTrue(0 < r['score'] < 1000)
            waste = next(f for f in r['findings'] if f['code'] == 'WASTED_SEARCH_TERMS')
            self.assertIn('vagas advogado trabalhista', [w['term'] for w in waste['evidence']])
            self.assertIn('"grátis" (frase)', [w['suggest'] for w in waste['evidence']])
            self.assertTrue(all(c['basis'] in (VERIFICADO, INFERIDO, HIPOTESE) for f in r['findings'] for c in f['claims']))

        def test_allow_terms(self):
            a, r = self.run_sample(allow_terms=['vagas'])
            waste = next(f for f in r['findings'] if f['code'] == 'WASTED_SEARCH_TERMS')
            self.assertNotIn('vagas advogado trabalhista', [w['term'] for w in waste['evidence']])

        def test_ecommerce_requires_purchase(self):
            a, r = self.run_sample(business_type='ecommerce')
            self.assertIn('CRITICAL_CONVERSION_MISSING', self.codes(r))

        def test_missing_sources_not_penalized(self):
            a = AdsAudit({'business_type': 'leadgen'})
            r = a.run(inline={'campaigns': SAMPLE['campaigns']})
            self.assertFalse(r['dimensions']['rastreamento']['measured'])
            self.assertIn('conversions', r['not_measured'])
            self.assertIn('# PANDORA ADS', render_md(r))

        def test_encodings(self):
            import tempfile, os
            body = 'Termo de pesquisa\tCusto\tConversões\nmodelo grátis\t1,50\t0\n'
            for enc in ('utf-16', 'cp1252', 'utf-8-sig'):
                with tempfile.NamedTemporaryFile('wb', suffix='.csv', delete=False) as f:
                    f.write(body.encode(enc)); name = f.name
                try:
                    rows = read_report(name, ('search_term', 'cost'))
                    self.assertEqual(rows[0]['search_term'], 'modelo grátis', enc)
                    self.assertEqual(parse_number(rows[0]['cost']), 1.5)
                finally: os.unlink(name)

        def test_header_detection_tsv(self):
            rows = read_report('Search term\tCost\tConversions\nfoo bar\t1.5\t0\n', ('search_term', 'cost'))
            self.assertEqual(rows[0]['search_term'], 'foo bar')

    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    return 0 if res.wasSuccessful() else 1


# ---------------------------------------------------------------------- cli
def write(path, text):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')


def main(argv=None):
    ap = argparse.ArgumentParser(description='PANDORA ADS Ω v' + VERSION + ' (somente leitura)')
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('audit')
    p.add_argument('--config', required=True, help='JSON com metas, tipo de negócio e caminhos dos CSV')
    p.add_argument('--json'); p.add_argument('--md')
    p.add_argument('--check-landing-pages', action='store_true', help='Acessa as URLs finais (rede) e roda o motor de headings')
    p.add_argument('--snapshot', help='Diretório snapshot (formato do motor de sitemap) para checar landing pages offline')
    sub.add_parser('selftest')
    args = ap.parse_args(argv)
    if args.command == 'selftest': return selftest()
    try:
        cfg_path = Path(args.config)
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        fetcher = None
        if args.check_landing_pages or args.snapshot:
            sm = _load_sibling('pandora_sitemap_audit.py')
            if sm is None: raise ValueError('pandora_sitemap_audit.py não encontrado ao lado deste script')
            fetcher = sm.SnapshotFetcher(args.snapshot) if args.snapshot else sm.LiveFetcher(delay=0.5)
        report = AdsAudit(cfg, cfg_path.parent).run(fetcher=fetcher)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print('ERRO:', e, file=sys.stderr); return 2
    if args.json: write(args.json, json.dumps(report, ensure_ascii=False, indent=2))
    if args.md: write(args.md, render_md(report))
    s = report['summary']
    print(f'PANDORA ADS Ω {VERSION} | {report["account"]} | score {report["score"]}/1000 | '
          f'custo {_money(s["cost"], report["currency"])} | conv {s["conversions"]:g} | achados {s["findings"]} {s["severity"]}')
    for f in report['findings'][:10]:
        print(f'  [{f["severity"]}] {f["title"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
