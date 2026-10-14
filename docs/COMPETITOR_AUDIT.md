# PANDORA COMPETITOR Ω — inteligência competitiva semanal

Motor do ecossistema **PANDORA GEO LOCAL OS** que rastreia o site principal e os concorrentes, guarda snapshots e mede, semana a semana, o que mudou, quem assina e onde os temas se sobrepõem.

- Arquivo: [`scripts/pandora_competitor_omega.py`](../scripts/pandora_competitor_omega.py)
- Versão: 3.1.1 · Python 3.10+ · stdlib (opcional: `sentence-transformers` para embeddings, `reportlab` para PDF)
- Configuração: [`config/competitors.json`](../config/competitors.json)

## O que mede

| Camada | Saída | Natureza |
|---|---|---|
| Rastreamento | até `max_pages` por domínio, respeitando robots.txt, mesmo site (www/não-www) | público, HTML estático |
| Mudanças | página nova, texto alterado, metadados, canonical, status de coleta | comparação com o snapshot anterior |
| Autoria | autor declarado (meta + JSON-LD Person), datas de publicação/modificação, troca de autor | declaração do publicador, **não verificada** |
| Sobreposição temática | score 0–1000 (cosseno de termos ponderados: title ×5, H1 ×4, description ×3, corpo ×1) e página própria mais próxima | proxy léxico, **não é competição de SERP** |
| Encaixe editorial | `review_existing_page` / `compare_audience_and_intent` / `validate_business_relevance` | heurística, exige revisão humana |
| Forense | janelas de 30/60/90 dias, SHA-256 do HTML e do texto, manifesto de evidências | só snapshots observados, sem interpolação |

## Uso

```bash
python scripts/pandora_competitor_omega.py selftest
python scripts/pandora_competitor_omega.py scan --config config/competitors.json \
  --db data/competitor.sqlite3 --out outputs/competitor-reports
# opcionais: --embedding-model <modelo sentence-transformers>  --pdf
```

A primeira execução cria a linha de base; mudanças aparecem a partir da segunda. O histórico vive no SQLite (`--db`).

### Rotina mensal

A análise de concorrentes roda **a cada 30 dias** (dia 1 de cada mês) e versiona o banco em `data/competitor.sqlite3`, mantendo só os 4 snapshots mais recentes por domínio (suficiente para as janelas de 30/60/90 dias):

```bash
python scripts/pandora_competitor_omega.py scan --config config/competitors.json \
  --db data/competitor.sqlite3 --out outputs/competitor-reports/AAAA-MM --keep-snapshots 4
```

## Relação com os outros motores

- **Sitemap & llms** ([`SITEMAP_AUDIT.md`](SITEMAP_AUDIT.md)) roda em qualquer domínio: para monitorar robots.txt, bots de IA, sitemap e llms.txt de um concorrente, rode-o com a URL do concorrente.
- **Headings** ([`HEADING_AUDIT.md`](HEADING_AUDIT.md)) avalia a estrutura H1–H3 de qualquer página coletada.

## Correções aplicadas na integração (3.1.0 → 3.1.1)

1. Atributo HTML sem valor (`<link rel>`, `<meta property>`) derrubava a página inteira.
2. O hash usado para detectar mudança era do HTML bruto: nonces e timestamps marcavam **todas** as páginas como alteradas a cada semana. Agora usa o conteúdo extraído; o SHA-256 do HTML bruto segue como evidência (`html_sha256`).
3. Redirecionamento `site.com → www.site.com` derrubava o rastreamento inteiro do domínio; variantes www agora contam como o mesmo site.
4. Comparação de similaridade recalculava os vetores a cada par (150×150 páginas: 17 s → 3 s).
5. Versão, User-Agent e cabeçalhos coerentes; só o relatório final (v31) fica na pasta; erro de configuração sem traceback.

## Limites conhecidos

- Sem execução de JavaScript; sem modo snapshot (precisa de rede até os domínios).
- Se o robots.txt não puder ser lido por erro de rede, o rastreamento segue sem ele.
- Rastreamento limitado: página ausente **não** prova remoção.
- Score de sobreposição não mede ranking, tráfego, backlinks nem mercado real.
- O banco guarda o texto de cada página a cada execução (cresce ~80 KB por página por semana).
