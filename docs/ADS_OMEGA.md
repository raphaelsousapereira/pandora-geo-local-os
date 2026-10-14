# PANDORA ADS Ω — auditor forense de Google Ads

Motor do ecossistema **PANDORA GEO LOCAL OS** que audita contas de Google Ads a partir de relatórios exportados e cruza o pago com SEO, GEO e a qualidade das landing pages.

- Arquivo: [`scripts/pandora_ads_omega.py`](../scripts/pandora_ads_omega.py) · v1.0.0 · Python 3.10+ · stdlib
- **Somente leitura por construção:** não há nenhum código que altere a conta. O motor produz achados e recomendações; aplicar é decisão humana.
- Base de regras: [`ADS_KNOWLEDGE.md`](ADS_KNOWLEDGE.md)

## Engrenagens

| Engrenagem | O que detecta |
|---|---|
| Conversões | conversão-chave ausente **conforme o tipo de negócio**, contagem dupla (mesma intenção de origens diferentes, ex.: GA4 + tag), nenhuma primária, janela menor que o ciclo de venda, lead contado "todas", divergência > 20% com o CRM |
| Termos de pesquisa | desperdício (intenção não comercial ou custo ≥ 1 CPA sem conversão), termos que convertem e ainda não são palavra-chave, CTR alto sem conversão (problema de página) |
| Negativas | negativas que bloqueiam palavras-chave ativas, com a semântica real (exata = idêntica; frase = contígua; ampla = todas as palavras, **sem sinônimos**) |
| Qualidade | palavras com Índice de qualidade ≤ 5 ordenadas por volume, componente "abaixo da média" dominante, grupos com palavras demais |
| Orçamento | orçamento × meta (meta × CPA alvo vs. 30,4 × diário), campanhas eficientes limitadas por orçamento, campanhas acima do CPA (doadoras de verba) |
| Lances | lance com alvo e pouco sinal; lance manual com volume para Smart Bidding |
| Concorrência paga | Auction Insights: quem aparece acima e com mais parcela de impressões (sem "estimar gasto" do concorrente) |
| SEO × Ads | pago onde você já é 1º no orgânico; consultas que convertem no pago sem presença orgânica (pauta de conteúdo/GEO); orgânico 4–10 sem anúncio |
| Landing pages | URLs finais com erro e estrutura fraca (usa os motores de sitemap e de headings) |

Cada achado traz **severidade, diagnóstico, ações, evidências** e a **base epistêmica** de cada afirmação: `VERIFICADO` (lido nos dados), `INFERIDO` (derivado por regra), `HIPÓTESE` (prática de mercado, não regra do Google).

Score 0–1000 por dimensão (rastreamento 250, desperdício 200, qualidade 200, orçamento e lances 200, landing pages 150): proxy de higiene; dimensões sem dados ficam "não medido" em vez de zerar.

## Como exportar os dados do Google Ads

Em cada relatório da interface, ajuste o período, inclua as colunas abaixo e use **Download → CSV**. Cabeçalhos em português ou inglês e as linhas de título/total são reconhecidos automaticamente.

| Arquivo (`sources`) | Onde | Colunas |
|---|---|---|
| `campaigns` | Campanhas | Campanha, Status, Orçamento, Tipo de estratégia de lances, Impr., Cliques, Custo, Conversões, Parcela de impressões de pesquisa perdidas (orçamento) |
| `keywords` | Palavras-chave de pesquisa | Palavra-chave, Tipo de correspondência, Campanha, Grupo de anúncios, Índice de qualidade, CTR esperada, Relevância do anúncio, Experiência na página de destino, Impr., Custo, Conversões, URL final |
| `search_terms` | Termos de pesquisa | Termo de pesquisa, Palavra-chave, Campanha, Impr., Cliques, Custo, Conversões |
| `negatives` | Palavras-chave negativas | Palavra-chave negativa, Tipo de correspondência, Campanha |
| `conversions` | Metas → Conversões | Ação de conversão, Origem, Contagem, Janela de conversão de clique, Incluir em "Conversões" |
| `auction` | Informações do leilão | Domínio de exibição do URL, Parcela de impressões, Taxa de sobreposição, Taxa de posição acima, Parcela de superação |
| `search_console` | Search Console → Desempenho → Consultas | Consultas principais, Cliques, Impressões, CTR, Posição |

Qualquer arquivo pode faltar: a engrenagem correspondente fica "não medida".

## Configuração

Ver [`examples/ads/config.json`](../examples/ads/config.json):

```json
{
  "account_name": "Cliente", "period": "set/2026", "currency": "R$",
  "business_type": "leadgen",          // ecommerce | leadgen | local | saas | app | b2b
  "target_cpa": 60, "monthly_conversion_goal": 80,
  "crm_conversions_month": 20, "sales_cycle_days": 30,
  "own_domain": "você",                // como sua conta aparece no Auction Insights
  "allow_terms": ["vagas"],            // termos que NÃO são desperdício neste negócio
  "waste_patterns": {"categoria": ["termo"]},  // substitui a lista padrão
  "sources": {"campaigns": "campanhas.csv", "...": "..."}
}
```

## Uso

```bash
python scripts/pandora_ads_omega.py audit --config examples/ads/config.json --md relatorio.md --json relatorio.json
python scripts/pandora_ads_omega.py audit --config cfg.json --check-landing-pages   # acessa as URLs finais
python scripts/pandora_ads_omega.py selftest
```

Exemplo de saída com dados fictícios: [`examples/ads/relatorio-exemplo.md`](../examples/ads/relatorio-exemplo.md).

## Próximos passos

1. Leitura direta pela **API do Google Ads (GAQL, somente leitura)**, com credenciais nos segredos do ambiente, para entrar nas rotinas mensais.
2. Engrenagens de Performance Max, Shopping/Merchant Center, YouTube e Meta (arquitetura dos motores Adverum e Tráfego Pago).
3. Histórico entre auditorias (o que melhorou desde o mês anterior).

## Limites

- Somente leitura; score é proxy, não previsão.
- O relatório de termos de pesquisa omite buscas de baixo volume.
- Performance Max não expõe Índice de qualidade por palavra-chave.
- Limiares `HIPÓTESE` são práticas de mercado; o Google não publica mínimos fixos (ex.: conversões para Smart Bidding).
