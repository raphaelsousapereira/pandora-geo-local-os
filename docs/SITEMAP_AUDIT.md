# PANDORA SITEMAP & LLMS AUDIT Ω — motor de descoberta para buscadores e IAs

Motor do ecossistema **PANDORA GEO LOCAL OS** que audita como um site é descoberto por buscadores e agentes de IA, e gera os arquivos que faltam.

- Arquivo: [`scripts/pandora_sitemap_audit.py`](../scripts/pandora_sitemap_audit.py)
- Versão: 1.0.0 · Python 3.10+ · somente stdlib
- Integra o motor de headings ([`HEADING_AUDIT.md`](HEADING_AUDIT.md)): cada página checada também recebe score de H1/H2/H3.

## Onde se encaixa no PANDORA

| Núcleo (seção 7) | Engrenagem | Contribuição |
|---|---|---|
| 7.1 Núcleo técnico | 1. Crawlabilidade · 2. Indexabilidade · 4. Robots e bots de IA · 5. Sitemap, canonical e llms.txt · 7. HTML textual | robots por bot, sitemaps, status/redirect/noindex/canonical, peso do HTML |
| 7.5 Núcleo generativo | Recuperação por IA (8.5) | cobertura e qualidade do llms.txt, geração de llms.txt / llms-full.txt |
| 7.6 Núcleo agentivo | Acesso e rastreabilidade (8.1) | política por agente (busca/resposta vs. treino) |

## O que audita

1. **robots.txt** — existência, `Sitemap:`, bloqueio global e acesso de 20 bots por token (Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User, GPTBot, Claude-SearchBot, Claude-User, ClaudeBot, PerplexityBot, Perplexity-User, Google-Extended, Applebot(-Extended), DuckAssistBot, MistralAI-User, meta-externalagent, Amazonbot, CCBot, Bytespider, cohere-ai). Bloquear bot de **busca/resposta** é achado *high*; bloquear bot de **treino** é *info* (decisão de política).
2. **Sitemaps** — índice e urlset (inclusive `.gz`), XML inválido, limites (50 mil URLs / 50 MB), URLs duplicadas, `lastmod` ausente/inválido/futuro/idêntico, URLs de outro host ou esquema, conteúdo padrão do CMS publicado.
3. **Cada URL** — status, cadeia de redirects, `noindex` (meta e `X-Robots-Tag`) dentro do sitemap, canonical divergente, `<title>` ausente ou igual ao slug, meta description, HTML > 1 MB (com bytes de imagens base64), documento HTML aninhado, texto fino, score de headings.
4. **Links internos** — órfãs (no sitemap sem link interno), URLs linkadas fora do sitemap, links para variante de host (www/não-www) e **links internos quebrados** (4xx/5xx).
5. **llms.txt / llms-full.txt** — H1, resumo em blockquote, seções, cobertura do sitemap, títulos-slug, links sem descrição, conteúdo padrão, links mortos, ausência do llms-full.

## Score (0–1000, normalizado pelas dimensões medidas)

| Dimensão | Máx. |
|---|---|
| robots | 150 |
| sitemap | 250 |
| url_health | 250 (proporcional às páginas checadas) |
| llms | 250 |
| linking | 100 |

Dimensões não medidas (ex.: arquivo não capturado no snapshot) ficam fora da média em vez de zerar o score.

## Comandos

```bash
# Auditoria ao vivo
python scripts/pandora_sitemap_audit.py audit https://example.org --json report.json --md report.md
python scripts/pandora_sitemap_audit.py audit https://example.org --max-urls 500 --delay 1

# Gerar llms.txt, llms-full.txt e mapa-do-site.html (revisar antes de publicar)
python scripts/pandora_sitemap_audit.py generate https://example.org --out-dir ./gerados \
  --site-name "Marca" --summary "Uma frase sobre o que o site é."

# Gate de qualidade
python scripts/pandora_sitemap_audit.py verify https://example.org --min-score 800

# Testes
python scripts/pandora_sitemap_audit.py selftest
python -m unittest discover tests
```

## Modo snapshot (rede bloqueada)

Quando o ambiente não alcança o domínio, os arquivos podem vir de outra fonte (ex.: WPVibe) e ser auditados offline:

```bash
python scripts/pandora_sitemap_audit.py audit https://example.org --snapshot ./snap
```

`./snap/manifest.json` mapeia URL → arquivo/status:

```json
{
  "https://example.org/robots.txt": {"file": "robots.txt", "status": 200, "headers": {"content-type": "text/plain"}},
  "https://example.org/antiga/": {"status": 301, "location": "https://example.org/nova/"}
}
```

URLs fora do manifest contam como "não capturadas": não geram falso 404.

## Geração

- `llms.txt` — H1, resumo, seções (Principal / Artigos, estudos e guias / Institucional), cada link com título legível (og:title → title → H1, descartando títulos-slug) e a meta description como nota. Exclui conteúdo padrão, noindex e páginas com erro.
- `llms-full.txt` — texto integral de cada página (sem nav/header/footer/scripts), com URL, seção, data e resumo. `--full-chars` limita o tamanho por página.
- `mapa-do-site.html` — bloco HTML para colar numa página "Mapa do site" e linkar no rodapé.

## Limites

- Score é proxy técnico de descoberta, não de ranking nem de citação.
- Sem execução de JavaScript.
- `llms.txt` não é padrão oficial; crawlers de IA podem ignorá-lo. robots.txt e HTML continuam decisivos.
- Órfãs e links quebrados são calculados a partir das páginas checadas (`--max-urls`).
