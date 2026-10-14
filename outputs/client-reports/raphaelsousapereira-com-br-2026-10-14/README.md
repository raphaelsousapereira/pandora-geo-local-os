# Auditoria de sitemap, robots e llms.txt — raphaelsousapereira.com.br

Data: 2026-10-14 · Motor: PANDORA SITEMAP & LLMS AUDIT Ω v1.0.0 (integrado ao HEADING AUDIT Ω) · **Score: 630/1000**

| Dimensão | Score |
|---|---:|
| robots | 140/150 |
| sitemap | 205/250 |
| llms | 34/250 |
| url_health | 179/250 |
| linking | 72/100 |

URLs nos sitemaps: 55 · páginas checadas: 55 · score médio de headings: 975.92/1000

## Coleta

A rede do ambiente bloqueia o domínio; os arquivos vieram do WordPress via WPVibe e foram auditados no **modo snapshot**. robots.txt, sitemaps, llms.txt e os metadados Yoast são reais; 43 páginas usam o conteúdo real inserido no template do tema (canonical/og ajustados com os valores do Yoast). Links internos fora do sitemap **não puderam ser testados** (status desconhecido) — rodar em modo ao vivo quando a rede for liberada.

## O que está bem

- `robots.txt` libera todos os 20 bots de busca e de IA avaliados e declara o sitemap.
- O sitemap do Yoast é válido: as 52 páginas publicadas estão nele, com `lastmod` real.

## Prioridades

1. **llms.txt fraco (34/250)** — o arquivo automático do Yoast lista 9 links e cobre **12%** das páginas; sem resumo, sem descrições, títulos-slug e “Hello world!”/“Uncategorized” incluídos; `llms-full.txt` não existe (404). **Correção pronta:** `gerados/llms.txt` (53 links com títulos e descrições) e `gerados/llms-full.txt` (texto integral de 51 páginas).
2. **24 páginas com `<title>` igual ao slug** — é o título exibido no Google e nas respostas de IA. Ajustar o título SEO no Yoast de cada uma (lista abaixo).
3. **Links internos suspeitos (46)** — 15 apontam para `www.raphaelsousapereira.com.br` (variante de host; 6 terminam em `.html`, provável sobra de site antigo), 29 para caminhos que não existem como página publicada (ex.: `/contato/`, `/correcoes/`, `/metodologia/`, páginas de cirurgia) e o tema linka arquivos por data (`/2026/08/`) em quase todas as páginas. Verificar e corrigir/redirecionar.
4. **Documento HTML aninhado em 49 páginas** e **5 páginas acima de 1 MB** (imagens base64) — mesmas correções do relatório de headings de 2026-10-13.
5. **Duplicidade e conteúdo padrão** — `/dr-luiz-henrique-capaverde/` aparece no sitemap de páginas e no de posts; `sample-page`, `hello-world` e `category/uncategorized` estão publicados e no sitemap. `via-padova` está órfã (nenhum link interno).
6. **Política explícita para IA** — o robots.txt não cita nenhum bot de IA; tudo herda de `*`. Opcional: declarar os bots de busca/resposta explicitamente para deixar a política auditável.

## Rodapé (pedido do Raphael)

Adicionar ao rodapé: **Mapa do site** (página com o conteúdo de `gerados/mapa-do-site.html`) e **Para IAs (llms.txt)** apontando para `/llms.txt` — depois de substituir o llms.txt do Yoast pelo gerado (desativar o llms.txt do Yoast e publicar o arquivo estático, ou ajustar a seleção manual no Yoast).

## Títulos SEO a corrigir

- `/ferramenta-vs-metodo-linkagem-interna/` → “ferramenta vs metodo linkagem interna - Raphael Sousa Pereira”
- `/crawl-budget-quando-importa-quando-e-ruido/` → “crawl budget quando importa quando e ruido - Raphael Sousa Pereira”
- `/orfa-faceta-profundidade-clique/` → “orfa faceta profundidade clique - Raphael Sousa Pereira”
- `/link-como-aresta-de-entidade/` → “link como aresta de entidade - Raphael Sousa Pereira”
- `/matematica-esquecida-do-pagerank/` → “matematica esquecida do pagerank - Raphael Sousa Pereira”
- `/20-anos-metricas-usabilidade/` → “20 anos metricas usabilidade - Raphael Sousa Pereira”
- `/20-anos-redes-neurais-recorrentes/` → “20 anos redes neurais recorrentes - Raphael Sousa Pereira”
- `/20-anos-deteccao-spam/` → “20 anos deteccao spam - Raphael Sousa Pereira”
- `/conteudo-e-commodity/` → “conteudo e commodity - Raphael Sousa Pereira”
- `/search-engineer-2027/` → “search engineer 2027 - Raphael Sousa Pereira”
- `/niveis-seo-tecnico/` → “niveis seo tecnico - Raphael Sousa Pereira”
- `/diagnostico-21-erros-seo-geo/` → “diagnostico 21 erros seo geo - Raphael Sousa Pereira”
- `/seo-tecnico-hands-on/` → “seo tecnico hands on - Raphael Sousa Pereira”
- `/metricas-de-geo/` → “metricas de geo - Raphael Sousa Pereira”
- `/auditoria-defensiva-ia-sicredi-llm-rag-agentes-governanca/` → “auditoria defensiva ia sicredi llm rag agentes governanca - Raphael Sousa Pereira”
- `/estudo-citado-fonte-inacessivel-geo/` → “estudo citado fonte inacessivel geo - Raphael Sousa Pereira”
- `/vector-databases-geo-2026/` → “vector databases geo 2026 - Raphael Sousa Pereira”
- `/como-avaliar-plataforma-de-monitoramento-de-geo/` → “como avaliar plataforma de monitoramento de geo - Raphael Sousa Pereira”
- `/o-google-esta-perdendo-a-busca-dados-2026/` → “o google esta perdendo a busca dados 2026 - Raphael Sousa Pereira”
- `/geo-score-nao-e-unidade-de-medida/` → “geo score nao e unidade de medida - Raphael Sousa Pereira”
- `/mapa-de-perguntas-de-compra-geo/` → “mapa de perguntas de compra geo - Raphael Sousa Pereira”
- `/agentes-sites-citacao-ia-tendencia/` → “agentes sites citacao ia tendencia - Raphael Sousa Pereira”
- `/engenheiro-de-ia-ai-engineer-guia-2026-2027/` → “engenheiro de ia ai engineer guia 2026 2027 - Raphael Sousa Pereira”
- `/auditoria-lgpd-agencias-marketing-brasil-2026/` → “auditoria lgpd agencias marketing brasil 2026 - Raphael Sousa Pereira”

## Links internos fora do sitemap

- `https://raphaelsousapereira.com.br/2026/08/`
- `https://raphaelsousapereira.com.br/2026/09/`
- `https://raphaelsousapereira.com.br/artigos/`
- `https://raphaelsousapereira.com.br/cirurgia-aparelho-digestivo-porto-alegre/`
- `https://raphaelsousapereira.com.br/cirurgia-bariatrica-porto-alegre/`
- `https://raphaelsousapereira.com.br/cirurgia-robotica-diastase-abdominal/`
- `https://raphaelsousapereira.com.br/cirurgia-robotica-porto-alegre/`
- `https://raphaelsousapereira.com.br/colunistas/`
- `https://raphaelsousapereira.com.br/contato/`
- `https://raphaelsousapereira.com.br/correcoes/`
- `https://raphaelsousapereira.com.br/diastase-abdominal-porto-alegre/`
- `https://raphaelsousapereira.com.br/diastase-ou-hernia/`
- `https://raphaelsousapereira.com.br/diastase-pos-bariatrica/`
- `https://raphaelsousapereira.com.br/dr-luiz-henrique-bastos-capaverde/`
- `https://raphaelsousapereira.com.br/fontes-e-evidencias/`
- `https://raphaelsousapereira.com.br/geo-ia/autoria-e-colunistas/`
- `https://raphaelsousapereira.com.br/geo-ia/cookies/`
- `https://raphaelsousapereira.com.br/geo-ia/correcoes/`
- `https://raphaelsousapereira.com.br/geo-ia/institucional/`
- `https://raphaelsousapereira.com.br/geo-ia/termos-de-uso/`
- `https://raphaelsousapereira.com.br/geo-ia/uso-de-inteligencia-artificial/`
- `https://raphaelsousapereira.com.br/livro-harness-a-camada-invisivel/`
- `https://raphaelsousapereira.com.br/locais-de-atendimento/`
- `https://raphaelsousapereira.com.br/metodologia/`
- `https://raphaelsousapereira.com.br/parede-abdominal/`
- `https://raphaelsousapereira.com.br/pesquisa-e-metodologia/`
- `https://raphaelsousapereira.com.br/politica-de-Conflitos-de-interesse/`
- `https://raphaelsousapereira.com.br/politica-editorial/`
- `https://raphaelsousapereira.com.br/quando-operar-diastase/`
- `https://raphaelsousapereira.com.br/recuperacao-cirurgia-diastase/`
- `https://raphaelsousapereira.com.br/uso-de-inteligencia-artificial/`
- `https://www.raphaelsousapereira.com.br/`
- `https://www.raphaelsousapereira.com.br/agentes-sites-citacao-ia-tendencia.html`
- `https://www.raphaelsousapereira.com.br/auditar-site-nao-e-auditar-entidade`
- `https://www.raphaelsousapereira.com.br/auditoria-de-geo-pesquisa.html`
- `https://www.raphaelsousapereira.com.br/caso-site-feito-por-agente-citacao-ia.html`
- `https://www.raphaelsousapereira.com.br/concorrencia-de-nicho-nao-de-setor`
- `https://www.raphaelsousapereira.com.br/estudos/`
- `https://www.raphaelsousapereira.com.br/geo-score-nao-e-unidade-de-medida`
- `https://www.raphaelsousapereira.com.br/governanca-e-geo-continuo`
- `https://www.raphaelsousapereira.com.br/mapa-de-perguntas-de-compra-geo`
- `https://www.raphaelsousapereira.com.br/metodo.html`
- `https://www.raphaelsousapereira.com.br/paineis-oficiais-de-geo-search-console-bing`
- `https://www.raphaelsousapereira.com.br/protocolo-auditoria-site-feito-por-agente.html`
- `https://www.raphaelsousapereira.com.br/publicacoes.html`
- `https://www.raphaelsousapereira.com.br/serie-cargos-2026/`

## Arquivos

- `sitemap-audit.json` — relatório completo do motor
- `sitemap-audit.md` — relatório técnico
- `gerados/llms.txt`, `gerados/llms-full.txt`, `gerados/mapa-do-site.html` — prontos para revisão e publicação
