# Base de conhecimento — Google Ads (PANDORA ADS Ω)

Regras usadas pelo motor, com origem e grau de certeza. Fontes internas: *Google Ads Masterclass — Formação de Analista Profissional* (Verbo Vivo, 2025), motores **Adverum Engine v3.1** e **Motor de Tráfego Pago 2026**. Classificação: `VERIFICADO` (comportamento documentado da plataforma), `HIPÓTESE` (prática de mercado).

## Leilão e qualidade

| Regra | Classe | Uso no motor |
|---|---|---|
| Ad Rank combina lance, qualidade, impacto dos ativos, contexto e limiares | VERIFICADO | texto das ações de concorrência paga |
| QS visível (1–10) é média histórica de diagnóstico, não o valor do leilão | VERIFICADO | base dos achados de qualidade |
| QS maior reduz CPC na mesma posição | HIPÓTESE quanto à magnitude ("QS 10 paga 1/3 do QS 3" é simplificação didática) | prioridade, não cálculo |
| Prioridade = palavras com muitas impressões e QS baixo | HIPÓTESE (prática) | `LOW_QS_HIGH_VOLUME` |
| Grupos de 5–15 palavras da mesma intenção | HIPÓTESE | `AD_GROUP_TOO_BROAD` (> 20) |

## Correspondência e negativas

| Regra | Classe | Uso |
|---|---|---|
| Negativa exata bloqueia a consulta idêntica; frase, os termos contíguos na ordem; ampla, todas as palavras em qualquer ordem | VERIFICADO | `negative_blocks()` |
| **Negativas não pegam sinônimos nem variações próximas** (ampla negativa ≠ ampla positiva) | VERIFICADO | corrige a Masterclass cap. 2.2, que diz que a negativa ampla bloqueia sinônimos |
| Intenção não comercial: grátis, download, tutorial, o que é, vagas, emprego… | HIPÓTESE (depende do negócio) | sugestão de negativa, ajustável por `allow_terms`/`waste_patterns` |
| Negativas muito amplas podem bloquear tráfego valioso; preferir a mais específica | HIPÓTESE (prática) | sugestões em frase/exata |
| Corrigido do Adverum: "processo", "desconto", "barato" não são negativas universais (bloqueiam advocacia e varejo) | — | removidos da lista padrão |

## Termos de pesquisa

| Regra | Classe | Uso |
|---|---|---|
| Triagem: irrelevante → negativa; converte barato → exata; CTR alto sem conversão → página | HIPÓTESE (método) | `WASTED_…`, `CONVERTING_…`, `HIGH_CTR_…` |
| Relatório omite consultas de baixo volume | VERIFICADO | limite declarado |
| Cadência: semanal nos 2 primeiros meses, depois quinzenal | HIPÓTESE | rotina recomendada |

## Lances e orçamento

| Regra | Classe | Uso |
|---|---|---|
| Gasto diário pode chegar a 2× o orçamento; teto mensal 30,4 × diário | VERIFICADO | `BUDGET_BELOW_GOAL` |
| Orçamento de trás para frente: meta × CPA alvo | — (aritmética) | `BUDGET_BELOW_GOAL` |
| Aprendizado de ~2 semanas após mudança de estratégia; evitar mudanças > 30% de orçamento nesse período | HIPÓTESE | texto das ações |
| Mínimo de conversões para Smart Bidding: Masterclass 30–50/mês, Motor de Tráfego 100/mês, Google sem mínimo oficial | HIPÓTESE (fontes divergem) | alerta só abaixo de 15 no período |
| CPA alvo começa 15–20% acima do histórico | HIPÓTESE | `MANUAL_WITH_ENOUGH_SIGNAL` |
| Campanha eficiente limitada por orçamento recebe verba das acima do CPA | HIPÓTESE (prática) | `EFFICIENT_…`, `CAMPAIGN_ABOVE_CPA` |
| Corrigido do Motor de Tráfego: alocação fixa 45/35% (somava 115% em B2B) | — | não usada |

## Conversões

| Regra | Classe | Uso |
|---|---|---|
| Uma ação primária por evento; GA4 importado + tag direta = contagem dupla | VERIFICADO (comportamento) | `POSSIBLE_DOUBLE_COUNT` |
| Compras com ID de transação para deduplicar; valor e moeda dinâmicos | VERIFICADO | ação recomendada |
| Leads e ligações com contagem "Uma" | HIPÓTESE (prática) | `LEAD_COUNTED_EVERY` |
| Janela reflete o ciclo de decisão (7 / 30 / 60–90 dias) | HIPÓTESE | `WINDOW_SHORTER_THAN_CYCLE` |
| Divergência > 20% entre Ads e CRM indica problema | HIPÓTESE | `CRM_DISCREPANCY` |
| Conversão crítica depende do negócio (compra não é exigida de lead-gen) | — | corrige o Adverum (exigia compra e app de qualquer conta) |

## SEO × Ads

| Regra | Classe | Uso |
|---|---|---|
| Posição orgânica 1 consolidada → retorno marginal decrescente do pago; testar com Experimento | HIPÓTESE | `PAID_WHERE_ORGANIC_TOP` |
| Orgânico 4–10 → pago compra o topo enquanto o SEO trabalha | HIPÓTESE | `ORGANIC_4_10_NO_PAID` |
| Consultas que convertem no pago são pauta prioritária de conteúdo | HIPÓTESE | `CONVERTING_PAID_NO_ORGANIC` (liga ao llms.txt) |

## Automação

| Regra | Classe | Uso |
|---|---|---|
| Checar diariamente se as URLs finais respondem 200 | prática | `--check-landing-pages` (motor de sitemap) |
| Regras automáticas: testar com alerta antes de ativar ação | prática | o motor nunca executa ações |
| Corrigido do Adverum: script de lances parava no primeiro anúncio sem conversão; filtro de CTR comparava texto; relatório AWQL legado | — | não reaproveitados |

## Descartado

- "Quality Score semântico" do Adverum: usava vetores aleatórios gerados por hash (sem significado).
- Estimativa de gasto do concorrente por parcela de impressões (ignora CPC).
- Estatísticas de mercado sem fonte (ex.: "CPCs em alta em 86% das indústrias").
