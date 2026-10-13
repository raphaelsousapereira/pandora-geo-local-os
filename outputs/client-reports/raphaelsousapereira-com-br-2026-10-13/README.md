# Auditoria de headings — raphaelsousapereira.com.br

Data: 2026-10-13 · Motor: PANDORA HEADING AUDIT Ω v5.0.0 · URLs: 54 · **Score médio: 975.91/1000**

> Score é proxy técnico estrutural (H1–H3, main, title, lang, IDs), não previsão de ranking.

## Coleta

Ambiente sem acesso HTTP direto ao domínio; HTML obtido via WPVibe. Home, 6 páginas e 2 posts: HTML renderizado completo. Demais 45 páginas: content.rendered da REST API inserido no template real do tema (wpbf), equivalente para hierarquia de headings.

## Prioridades

1. **Documento HTML aninhado (46 URLs)** — o conteúdo de cada página é um documento completo (`<html>`, `<head>`, `<style>`, `<body>`, `<main>`) colado dentro do `<main>` do tema. Resultado: 2× `<main>` e 2× `<title>` (o title extraído fica concatenado, ex.: "metricas de geo - Raphael Sousa PereiraMétricas de GEO | Raphael Sousa Pereira"). **Correção:** manter no editor só o miolo (o que está dentro de `<body>`), trocar o `<main>` interno por `<div>`/`<article>` e mover o `<style>` para CSS do tema ou bloco HTML sem `<head>`. Ganho esperado: +25 pontos por página.
2. **Imagens base64 inline** — `https://raphaelsousapereira.com.br/geo-para-portais-de-noticias-por-que-paginas-de-autores-nao-bastam-para-a-ia-entender-um-acervo-editorial/` (2758 KB), `https://raphaelsousapereira.com.br/qual-e-a-missao-de-uma-plataforma-de-geo-e-ia-no-brasil-geo-ia-laboratorio/` (1445 KB), `https://raphaelsousapereira.com.br/o-que-e-pesquisa-de-geo-e-inteligencia-artificial-no-brasil-e-o-que-significa-ser-pesquisador-nessa-area/` (1445 KB), `https://raphaelsousapereira.com.br/os-6-macrodominios-de-geo-uma-macroarquitetura-para-pesquisa-tecnica-operacao-e-valor-economico-geo-ia/` (1445 KB), `https://raphaelsousapereira.com.br/o-que-e-taxa-de-citabilidade-em-geo/` (1445 KB). **Correção:** subir à biblioteca de mídia e referenciar por URL (WebP, `loading="lazy"`, `width`/`height`).
3. **Duplicidade** — `/sala-de-imprensa/` e `/sala-de-imprensa-2/` têm o mesmo H1 (consolidar + 301); página 139 e post 135 disputam `/dr-luiz-henrique-capaverde/` (despublicar um).
4. **Conteúdo padrão do WordPress publicado** — `/sample-page/` e `/hello-world/`: despublicar ou redirecionar.
5. **Pontuais** — ver tabela abaixo.

## Correções por página

| Score | URL | Achados | Ação |
|---:|---|---|---|
| 932 | https://raphaelsousapereira.com.br/marketing-pessoal-e-construcao-de-referencias-para-respostas-de-inteligencia-artificial/ | MULTIPLE_H1, MULTIPLE_MAIN, DUPLICATE_TEXT · DUPLICATE_TEXT: “Marketing pessoal e construção de referências para respostas de inteligência artificial” | manter um único H1; remover documento/`<main>` aninhado; diferenciar headings repetidos |
| 957 | https://raphaelsousapereira.com.br/sala-de-imprensa/ | MULTIPLE_MAIN, DUPLICATE_TEXT, CROSS_PAGE_H1_DUPLICATE · DUPLICATE_TEXT: “Pesquisa” | remover documento/`<main>` aninhado; diferenciar headings repetidos; consolidar páginas com H1 igual |
| 957 | https://raphaelsousapereira.com.br/via-padova/ | MULTIPLE_MAIN, DUPLICATE_TEXT, TITLE_H1_LOW_LEXICAL_OVERLAP · DUPLICATE_TEXT: “Institucional” | remover documento/`<main>` aninhado; diferenciar headings repetidos; revisar title duplicado/concatenado e coerência com H1 |
| 964 | https://raphaelsousapereira.com.br/como-o-mercado-de-moveis-e-decoracao-de-porto-alegre-e-citado/ | LEVEL_SKIP, DUPLICATE_TEXT · LEVEL_SKIP: “Raphael Sousa Pereira”; DUPLICATE_TEXT: “Raphael Sousa Pereira” | não pular nível (H1→H2→H3); diferenciar headings repetidos |
| 975 | https://raphaelsousapereira.com.br/20-anos-deteccao-spam/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/20-anos-metricas-usabilidade/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/20-anos-redes-neurais-recorrentes/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/a-ia-que-o-ceo-precisa-governar/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/agentes-sites-citacao-ia-tendencia/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/auditoria-defensiva-ia-sicredi-llm-rag-agentes-governanca/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/auditoria-lgpd-agencias-marketing-brasil-2026/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/como-avaliar-plataforma-de-monitoramento-de-geo/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/conteudo-e-commodity/ | MULTIPLE_MAIN, TITLE_H1_LOW_LEXICAL_OVERLAP | remover documento/`<main>` aninhado; revisar title duplicado/concatenado e coerência com H1 |
| 975 | https://raphaelsousapereira.com.br/crawl-budget-quando-importa-quando-e-ruido/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/diagnostico-21-erros-seo-geo/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/dr-luiz-henrique-capaverde/ | MULTIPLE_MAIN, TITLE_H1_LOW_LEXICAL_OVERLAP, CROSS_PAGE_H1_DUPLICATE | remover documento/`<main>` aninhado; revisar title duplicado/concatenado e coerência com H1; consolidar páginas com H1 igual |
| 975 | https://raphaelsousapereira.com.br/dr-luiz-henrique-capaverde/ (post) | MULTIPLE_MAIN, TITLE_H1_LOW_LEXICAL_OVERLAP, CROSS_PAGE_H1_DUPLICATE | remover documento/`<main>` aninhado; revisar title duplicado/concatenado e coerência com H1; consolidar páginas com H1 igual |
| 975 | https://raphaelsousapereira.com.br/drift-linguistico-e-distribucional/ | MULTIPLE_MAIN, TITLE_H1_LOW_LEXICAL_OVERLAP | remover documento/`<main>` aninhado; revisar title duplicado/concatenado e coerência com H1 |
| 975 | https://raphaelsousapereira.com.br/economia-de-agentes-pagamentos-comercio-e-contratacao-maquina-a-maquina/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/engenheiro-de-ia-ai-engineer-guia-2026-2027/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/entidade-em-geo-de-string-a-vetor-relacional-em-producao-geo-ia-laboratorio/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/ferramenta-vs-metodo-linkagem-interna/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/generative-competitive-intelligence-matrix/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/geo-para-portais-de-noticias-por-que-paginas-de-autores-nao-bastam-para-a-ia-entender-um-acervo-editorial/ | MULTIPLE_MAIN · imagens base64 (2758 KB) | remover documento/`<main>` aninhado; mover imagens para mídia |
| 975 | https://raphaelsousapereira.com.br/geo-score-nao-e-unidade-de-medida/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/link-como-aresta-de-entidade/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/mapa-de-perguntas-de-compra-geo/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/matematica-esquecida-do-pagerank/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/metricas-de-geo/ | MULTIPLE_MAIN, TITLE_H1_LOW_LEXICAL_OVERLAP | remover documento/`<main>` aninhado; revisar title duplicado/concatenado e coerência com H1 |
| 975 | https://raphaelsousapereira.com.br/niveis-seo-tecnico/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/o-google-esta-perdendo-a-busca-dados-2026/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/o-que-e-pesquisa-de-geo-e-inteligencia-artificial-no-brasil-e-o-que-significa-ser-pesquisador-nessa-area/ | MULTIPLE_MAIN · imagens base64 (1445 KB) | remover documento/`<main>` aninhado; mover imagens para mídia |
| 975 | https://raphaelsousapereira.com.br/o-que-e-taxa-de-citabilidade-em-geo/ | MULTIPLE_MAIN · imagens base64 (1445 KB) | remover documento/`<main>` aninhado; mover imagens para mídia |
| 975 | https://raphaelsousapereira.com.br/o-que-estudar-sobre-geo-em-2026-e-2027/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/orfa-faceta-profundidade-clique/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/os-6-macrodominios-de-geo-uma-macroarquitetura-para-pesquisa-tecnica-operacao-e-valor-economico-geo-ia/ | MULTIPLE_MAIN · imagens base64 (1445 KB) | remover documento/`<main>` aninhado; mover imagens para mídia |
| 975 | https://raphaelsousapereira.com.br/pandora-ia-simbolica/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/politica-de-conflitos-de-interesse-patrocinio-e-independencia-editorial/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/politica-de-privacidade/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/protocolo-auditoria-site-feito-por-agente/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/publicacoes-em-seo-geo/ | MULTIPLE_MAIN, TITLE_H1_LOW_LEXICAL_OVERLAP | remover documento/`<main>` aninhado; revisar title duplicado/concatenado e coerência com H1 |
| 975 | https://raphaelsousapereira.com.br/qual-e-a-missao-de-uma-plataforma-de-geo-e-ia-no-brasil-geo-ia-laboratorio/ | MULTIPLE_MAIN · imagens base64 (1445 KB) | remover documento/`<main>` aninhado; mover imagens para mídia |
| 975 | https://raphaelsousapereira.com.br/schema-markup-json-ld-entidades-grafo-conhecimento-geo-2026/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/search-engineer-2027/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/seo-tecnico-hands-on/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/tipos-de-presenca-geo/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 975 | https://raphaelsousapereira.com.br/vector-databases-geo-2026/ | MULTIPLE_MAIN | remover documento/`<main>` aninhado |
| 982 | https://raphaelsousapereira.com.br/hello-world/ (post) | LEVEL_SKIP · LEVEL_SKIP: “1 Comentário” | não pular nível (H1→H2→H3) |
| 982 | https://raphaelsousapereira.com.br/sala-de-imprensa-2/ | DUPLICATE_TEXT, CROSS_PAGE_H1_DUPLICATE · DUPLICATE_TEXT: “Institucional” | diferenciar headings repetidos; consolidar páginas com H1 igual |
| 1000 | https://raphaelsousapereira.com.br/ | — | nenhuma |
| 1000 | https://raphaelsousapereira.com.br/enquadramento-de-genero-como-sinal-latente-de-citacao-em-motores-generativos-working-paper/ | — | nenhuma |
| 1000 | https://raphaelsousapereira.com.br/estudo-citado-fonte-inacessivel-geo/ | — | nenhuma |
| 1000 | https://raphaelsousapereira.com.br/estudo-moveis-planejados-porto-alegre/ | — | nenhuma |
| 1000 | https://raphaelsousapereira.com.br/sample-page/ | — | nenhuma |

## Observação de extração

Headings com `<br>` sem espaço geram texto colado na extração (ex.: “Dr. Luiz HenriqueCapaverde”, “DriftLinguísticoe Distribucional”). Navegadores exibem corretamente; para leitores de máquina, prefira espaço antes do `<br>`.

## Limites

HTML estático; sem execução de JavaScript nem CSS computado. Multiple H1 e saltos de nível são sinalizados para revisão, não penalidades do Google.
