# PANDORA ADS Ω v1.0.0 — Exemplo — Escritório de advocacia (dados fictícios)

Período: set/2026 · Gerado (UTC): 2026-10-14T02:54:46.440039+00:00 · Modo: **somente leitura**

**Score de higiene: 282/1000** (proxy, não previsão de resultado)

| Dimensão | Score |
|---|---:|
| rastreamento | 70/250 |
| desperdicio | 10/200 |
| qualidade | 140/200 |
| orcamento_lances | 20/200 |
| landing_pages | não medido/150 |

Campanhas: 2 · Custo: R$ 2.700,00 · Conversões: 33 · CPA: R$ 81,82

## O que aconteceu, por quê e o que fazer

### 1. [ALTO] 2 palavras com Índice de qualidade ≤ 5
*QUALIDADE · LOW_QS_HIGH_VOLUME · em jogo: R$ 2.000,00*

Concentram 74% do custo das palavras com QS. Componentes "abaixo da média": CTR esperada (2), experiência da página (1), relevância do anúncio (1).

**Ações:**
- Relevância: grupos menores (5–15 palavras da mesma intenção) e palavra-chave no título.
- CTR esperada: títulos específicos, benefício concreto e chamada para ação.
- Página: continuidade da promessa do anúncio, velocidade no celular (ver auditoria de landing pages).

**Evidências:**
- keyword: escritório de advocacia · qs: 3 · impressions: 8000 · cost: R$ 1.200,00
- keyword: processo trabalhista · qs: 4 · impressions: 6000 · cost: R$ 800,00

**Base:** [VERIFICADO] QS e componentes por palavra · [VERIFICADO] QS visível é diagnóstico (média histórica), não o valor do leilão (Google Ads Help) · [HIPÓTESE] QS maior tende a reduzir CPC na mesma posição (Masterclass cap. 1.4 — magnitude varia)

### 2. [ALTO] Campanhas acima do CPA de referência
*ORÇAMENTO · CAMPAIGN_ABOVE_CPA · em jogo: R$ 1.200,00*

R$ 1.200,00 em campanhas com CPA > 1,3 × referência ou sem conversão com custo ≥ 1 CPA.

**Ações:**
- Revisar termos, landing page e lances destas campanhas; candidatas a doar verba.

**Evidências:**
- campaign: Institucional · cost: R$ 1.200,00 · conversions: 3 · cpa: R$ 400,00 · lost_is_budget: 0 · limited: False

**Base:** [VERIFICADO] Custo e conversões por campanha · [HIPÓTESE] Corte de 1,3 × CPA de referência

### 3. [ALTO] 3 termos sem conversão candidatos a negativa
*TERMOS DE PESQUISA · WASTED_SEARCH_TERMS · em jogo: R$ 350,00*

R$ 350,00 (52% do custo dos termos) foram para termos sem conversão com padrão de intenção não comercial ou custo ≥ 1 CPA.

**Ações:**
- Revisar a lista e negativar o que não for do negócio (preferir frase/exata, a mais específica).
- Adicionar em lista compartilhada de negativas; reauditar a lista a cada 6 meses.

**Evidências:**
- term: escritório advocacia centro · cost: R$ 200,00 · reason: gastou ≥ 1 CPA de referência sem converter · suggest: [escritorio advocacia centro] (exata) após revisão
- term: vagas advogado trabalhista · cost: R$ 90,00 · reason: emprego: "vagas" · suggest: "vagas" (frase)
- term: modelo de petição grátis · cost: R$ 60,00 · reason: gratuidade: "gratis" · suggest: "grátis" (frase)

**Base:** [VERIFICADO] Custo e conversões por termo · [HIPÓTESE] Padrões de intenção não comercial (Masterclass cap. 2.2) · [VERIFICADO] Relatório de termos omite buscas de baixo volume (política de privacidade do Google Ads)

### 4. [ALTO] Possível contagem dupla de conversões
*CONVERSÕES · POSSIBLE_DOUBLE_COUNT*

Ações repetidas ou a mesma intenção primária vinda de origens diferentes (ex.: GA4 importado + tag direta).

**Ações:**
- Manter só uma ação primária por evento de negócio; a outra como secundária.
- Em compras, enviar o ID da transação para deduplicar.

**Evidências:**
- mesma_intencao_varias_origens: {"lead": ["Formulário de contato", "Formulário de contato (GA4)"]}

**Base:** [VERIFICADO] Nomes/origens das ações · [INFERIDO] Duplicidade presumida pela origem

### 5. [ALTO] Ads e CRM divergem mais de 20%
*CONVERSÕES · CRM_DISCREPANCY*

Ads registra 33 conversões; CRM informa 20. Diferença de 65%.

**Ações:**
- Auditar disparo da tag, duplicidade e conversões offline antes de mexer em lances.

**Base:** [VERIFICADO] Conversões no período (campanhas) · [VERIFICADO] Número do CRM informado na configuração · [HIPÓTESE] Divergência > 20% indica problema de rastreio (Masterclass cap. 7.1)

### 6. [ALTO] 1 negativas bloqueiam palavras-chave ativas
*NEGATIVAS · NEGATIVE_BLOCKS_KEYWORD*

A negativa impede que a própria palavra-chave seja exibida.

**Ações:**
- Remover ou tornar a negativa mais específica (exata) onde há conflito.

**Evidências:**
- negative: processo · match: Ampla · blocks_keyword: processo trabalhista · campaign: Advogado Trabalhista

**Base:** [VERIFICADO] Regra de correspondência de negativas (exata/frase/ampla, sem sinônimos) (documentação do Google Ads)

### 7. [ALTO] Orçamento não cabe na meta
*ORÇAMENTO · BUDGET_BELOW_GOAL*

Meta 80 conversões × CPA alvo R$ 60,00 = R$ 4.800,00/mês; orçamentos ativos somam R$ 2.736,00/mês (R$ 90,00/dia).

**Ações:**
- Ou ajustar a meta para ~45 conversões/mês, ou o orçamento para ~R$ 157,89/dia.

**Base:** [VERIFICADO] Orçamentos diários exportados · [VERIFICADO] Teto mensal = 30,4 × diário (Google Ads Help) · [VERIFICADO] Meta e CPA alvo informados na configuração

### 8. [ALTO] Campanhas eficientes perdendo impressões por orçamento
*ORÇAMENTO · EFFICIENT_CAMPAIGN_BUDGET_LIMITED*

CPA dentro da referência e parcela perdida por orçamento ≥ 10% (ou status limitada).

**Ações:**
- Remanejar verba das campanhas acima do CPA para estas antes de aumentar o total.
- Mudanças > 30% no orçamento podem reiniciar o aprendizado do Smart Bidding: subir em degraus.

**Evidências:**
- campaign: Advogado Trabalhista · cost: R$ 1.500,00 · conversions: 30 · cpa: R$ 50,00 · lost_is_budget: 35% · limited: True

**Base:** [VERIFICADO] Custo, conversões e parcela perdida · [HIPÓTESE] Degrau de 30% (Masterclass cap. 4.1)

### 9. [MÉDIO] 1 buscas pagas onde você já é 1º no orgânico
*SEO × ADS · PAID_WHERE_ORGANIC_TOP · em jogo: R$ 300,00*

R$ 300,00 em cliques pagos para consultas com posição orgânica média ≤ 1,5.

**Ações:**
- Rodar Experimento reduzindo lance nesses termos e medir conversões totais (pago + orgânico) — não cortar no escuro.

**Evidências:**
- query: advogado trabalhista porto alegre · organic_position: 1.2 · paid_cost: R$ 300,00 · paid_conversions: 8

**Base:** [VERIFICADO] Custo pago e posição orgânica por consulta · [HIPÓTESE] Retorno marginal decrescente com dupla presença (Masterclass cap. 11.1; depende da concorrência na SERP)

### 10. [MÉDIO] Janela curta: Formulário de contato
*CONVERSÕES · WINDOW_SHORTER_THAN_CYCLE*

Janela de 7 dias para ciclo de venda informado de 30 dias.

**Ações:**
- Ampliar a janela para cobrir o ciclo (até 30 dias).

**Base:** [VERIFICADO] Janela = 7 dias · [HIPÓTESE] Janela deve refletir o ciclo de decisão (Masterclass cap. 7.1)

### 11. [MÉDIO] Lead contado "todas": Formulário de contato
*CONVERSÕES · LEAD_COUNTED_EVERY*

Leads contados a cada evento inflam conversões quando a mesma pessoa envia duas vezes.

**Ações:**
- Usar contagem "Uma" para leads e ligações.

**Base:** [VERIFICADO] Contagem configurada

### 12. [MÉDIO] 1 termos que convertem ainda não são palavras-chave
*TERMOS DE PESQUISA · CONVERTING_TERMS_NOT_KEYWORDS*

Termos descobertos por correspondência ampla/frase convertendo dentro do CPA de referência.

**Ações:**
- Adicionar como correspondência exata no grupo de intenção correspondente.
- Usar como pauta de conteúdo orgânico (SEO/GEO).

**Evidências:**
- term: advogado trabalhista porto alegre · conversions: 8 · cpa: R$ 37,50

**Base:** [VERIFICADO] Conversões e custo por termo

### 13. [MÉDIO] CTR alto sem conversão
*TERMOS DE PESQUISA · HIGH_CTR_NO_CONVERSION*

Anúncio atrai (CTR ≥ 2× a média) mas a página não converte para essas buscas.

**Ações:**
- Verificar se a landing page responde à intenção desses termos; testar página específica.

**Evidências:**
- term: calcular rescisão · clicks: 60 · ctr: 15%

**Base:** [VERIFICADO] CTR e conversões por termo · [INFERIDO] Problema provável na página

### 14. [MÉDIO] 1 concorrentes dominando o leilão
*CONCORRÊNCIA PAGA · AUCTION_THREATS*

Aparecem acima de você em > 60% dos leilões em comum ou têm parcela de impressões 20 p.p. maior.

**Ações:**
- Antes de subir lance: melhorar Índice de qualidade e extensões (Ad Rank sem pagar mais).
- Cruzar com o monitoramento orgânico do concorrente (PANDORA COMPETITOR Ω).

**Evidências:**
- domain: concorrente.com.br · impression_share: 70% · position_above_rate: 65% · outranking_share: 30%

**Base:** [VERIFICADO] Métricas do Auction Insights · [VERIFICADO] Gasto do concorrente não é observável

### 15. [BAIXO] Termos com gasto que a lista de negativas atual bloquearia
*NEGATIVAS · NEGATIVE_NOT_EFFECTIVE*

Negativas adicionadas depois do período ou em outro nível (campanha × grupo).

**Ações:**
- Conferir o nível de aplicação das negativas.

**Evidências:**
- modelo de petição grátis

**Base:** [INFERIDO] Comparação termo × negativa pela regra de correspondência

### 16. [BAIXO] 1 consultas orgânicas entre 4ª e 10ª sem anúncio
*SEO × ADS · ORGANIC_4_10_NO_PAID*

O pago pode comprar o topo enquanto o SEO trabalha a posição.

**Ações:**
- Avaliar teste pago nas de intenção comercial.

**Evidências:**
- query: direitos na demissão · organic_position: 6.4 · impressions: 2500

**Base:** [VERIFICADO] Posição e impressões orgânicas

## Não medido

- landing_pages (use --check-landing-pages)

## Limites

- Somente leitura: nenhuma alteração é feita na conta
- Score é proxy de higiene da conta, não previsão de resultado
- Relatório de termos de pesquisa omite buscas de baixo volume
- Limiares marcados como HIPÓTESE são práticas de mercado, não regras do Google
- Performance Max não expõe Índice de qualidade por palavra-chave
