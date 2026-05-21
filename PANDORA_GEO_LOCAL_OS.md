# PANDORA GEO LOCAL & AGENTIC SEARCH OS

> **Sistema operacional de auditoria, medição e otimização para presença local em Google, Google Maps, IAs generativas e agentes digitais.**
>
> Versão 1.0 · 2026-05-21  
> Autor: Raphael Sousa Pereira  
> Projeto: PANDORA GEO LOCAL & AGENTIC SEARCH OS  
> Escopo: SEO Local · GEO · ASO · Google Business Profile · Google Maps · LLMs · agentes digitais · auditoria forense

---

## 0. Resumo executivo

O **PANDORA GEO LOCAL & AGENTIC SEARCH OS** é um sistema operacional técnico e estratégico para medir se uma empresa local é:

1. **Encontrada** em mecanismos de busca e mapas.
2. **Compreendida** como entidade digital.
3. **Citada** por inteligências artificiais e mecanismos generativos.
4. **Confirmada** por múltiplas fontes públicas.
5. **Confiável** do ponto de vista técnico, editorial, local e reputacional.
6. **Acionável** por agentes digitais, assistentes, interfaces conversacionais e fluxos automatizados.
7. **Convertida** em ação mensurável, como ligação, WhatsApp, rota, formulário, agendamento ou compra.

O sistema integra três disciplinas:

| Camada | Função | Pergunta operacional |
|---|---|---|
| SEO Local | Ser encontrado | A empresa aparece para intenções locais relevantes? |
| GEO | Ser citado | A empresa é recuperada, mencionada e usada como referência por IA? |
| ASO | Ser acionado | Um agente digital consegue entender, comparar e iniciar uma ação? |

A tese central do sistema é:

> **SEO Local mede presença. GEO mede citabilidade. ASO mede acionabilidade. O PANDORA mede a integração entre as três camadas.**

---

## 1. Objetivo do sistema

O PANDORA foi projetado para responder perguntas que auditorias tradicionais de SEO ainda não respondem de forma suficiente:

- A empresa aparece no Google, Google Maps e Local Pack?
- O Google Business Profile está semanticamente alinhado ao site?
- A entidade é clara para mecanismos de busca e IAs?
- As avaliações públicas influenciam as respostas generativas?
- As IAs citam a marca espontaneamente em consultas comerciais e locais?
- A marca aparece em diferentes LLMs ou apenas em um?
- A citação permanece ao longo do tempo?
- A resposta da IA usa fontes confiáveis ou fontes fracas?
- O conteúdo é citável, recuperável e tecnicamente acessível?
- Um agente digital consegue identificar o serviço, localização, contato e próximo passo?
- Existe ponte entre presença em IA e conversão real?

---

## 2. Escopo

### 2.1 Incluído

O sistema cobre:

- Sites institucionais.
- Landing pages.
- Subdomínios.
- Google Business Profile.
- Google Maps.
- Local Pack.
- Reviews.
- Conteúdos locais.
- Páginas de serviço.
- Páginas por cidade e bairro.
- Dados estruturados.
- Bots de IA.
- LLM crawler access.
- Respostas de LLMs.
- Citações e menções de marca.
- Fontes usadas por IA.
- Prontidão agentiva.
- Conversão local.

### 2.2 Não incluído por padrão

Não faz parte da versão base:

- Garantia de ranqueamento.
- Garantia de menção por IA.
- Manipulação artificial de respostas generativas.
- Spam de reviews.
- Criação de páginas em massa sem utilidade.
- Automação de ações sem consentimento do usuário.
- Coleta de dados privados sem autorização.
- Scraping contra termos de uso de plataformas.

---

## 3. Definições operacionais

### 3.1 SEO Local

Disciplina que organiza sinais técnicos, editoriais, reputacionais e territoriais para aumentar a visibilidade de uma empresa em buscas locais, Google Maps, Local Pack e consultas com intenção geográfica.

### 3.2 GEO

Generative Engine Optimization. Disciplina que organiza entidades, conteúdo, provas e fontes para aumentar a chance de uma marca, empresa, autor ou página ser recuperada, sintetizada, mencionada e citada por mecanismos generativos de IA.

### 3.3 ASO

Agentic Search Optimization. Disciplina que prepara sites, dados, páginas, formulários e fluxos para que agentes digitais consigam entender, comparar e executar ações em nome de usuários.

### 3.4 Entidade digital

Representação verificável de uma pessoa, empresa, marca, produto, serviço ou organização em diferentes fontes digitais.

### 3.5 Citabilidade

Capacidade de uma entidade ou conteúdo ser usado como referência explícita ou implícita por uma IA, mecanismo de resposta ou sistema generativo.

### 3.6 Acionabilidade

Capacidade de uma página, entidade ou serviço permitir uma próxima ação clara, como contato, orçamento, rota, agendamento, compra ou preenchimento de formulário.

---

## 4. Arquitetura do repositório

Estrutura recomendada:

```bash
/pandora-geo-local-os/
  /docs/
    PANDORA_GEO_LOCAL_OS.md
    METODOLOGIA.md
    STACK_DE_CAMADAS.md
    PLANO_DE_MEDICAO.md
    POLITICA_DE_BOTS.md
    TRUST_SAFETY.md
    DATA_DICTIONARY.md
    LIMITACOES.md

  /data/
    entities.json
    query_templates.yaml
    queries.jsonl
    responses.jsonl
    mentions.jsonl
    sources.jsonl
    gbp_snapshots.jsonl
    maps_snapshots.jsonl
    serp_snapshots.jsonl
    agentic_tests.jsonl
    checksums.sha256
    collection_log.jsonl

  /scripts/
    collect_llm_responses.py
    collect_maps_presence.py
    collect_serp_presence.py
    extract_mentions.py
    extract_sources.py
    calculate_metrics.py
    calculate_entity_clarity.py
    calculate_multi_source_consensus.py
    calculate_citation_persistence.py
    calculate_freshness_propagation.py
    compare_maps_vs_llm.py
    generate_weekly_report.py
    generate_client_report.py
    validate_annotations.py

  /outputs/
    /weekly-reports/
    /monthly-reports/
    /client-reports/
    /dashboards/
    /datasets/
    /exports/

  /notebooks/
    exploratory_analysis.ipynb
    longitudinal_analysis.ipynb
    local_geo_benchmark.ipynb

  /tests/
    test_entity_schema.py
    test_query_schema.py
    test_metrics.py
    test_hash_integrity.py

  README.md
  requirements.txt
  .gitignore
```

---

## 5. Cadência operacional

| Cadência | Ações | Responsável | Saída |
|---|---|---|---|
| Diária | Coleta de queries locais, respostas de LLMs, SERP e Maps quando aplicável | Pipeline | `responses.jsonl`, `collection_log.jsonl` |
| Semanal | Cálculo de métricas, menções, posição, consistência e relatório HTML | Research Ops | `weekly-geo-local-YYYY-MM-DD.html` |
| Quinzenal | Revisão de queries, entidades, concorrentes, fontes e amostra manual | Analista | `validation_batch.jsonl` |
| Mensal | Relatório executivo com tendências, concorrência, lacunas e plano de ação | Lead Analyst | PDF / HTML |
| Trimestral | Revisão metodológica, atualização do stack e publicação de dataset interno | Equipe | Dataset versionado |
| Semestral | Benchmark por vertical, cidade e categoria | Pesquisa | Relatório estratégico |

---

## 6. Stack analítico

O PANDORA opera em cinco níveis.

```text
Nível 1 — Engrenagens principais
Módulos macro de auditoria.

Nível 2 — Camadas analíticas
100+ camadas de leitura técnica, semântica, local, generativa e agentiva.

Nível 3 — Sinais avaliáveis
Critérios, evidências, medições e subitens.

Nível 4 — Evidências forenses
HTML, schema, robots, sitemap, SERP, Maps, GBP, reviews, respostas de LLMs, fontes e logs.

Nível 5 — Interpretação estratégica
Risco, oportunidade, prioridade, maturidade e plano de ação.
```

---

## 7. Engrenagens principais

### 7.1 Núcleo técnico

1. Crawlabilidade técnica.
2. Indexabilidade.
3. Renderização.
4. Robots e bots de IA.
5. Sitemap, canonical e llms.txt.
6. Performance e UX.
7. HTML textual.
8. Dados estruturados.

### 7.2 Núcleo semântico

9. Conteúdo semântico.
10. Cobertura de intenção.
11. Autoridade tópica.
12. Answer capsules.
13. Information gain.
14. Retrieval fitness.
15. Compression fidelity.
16. Semantic coherence.

### 7.3 Núcleo de entidade

17. Entity clarity.
18. Entity verification.
19. Entity disambiguation.
20. Multi-source consensus.
21. Entity-schema alignment.
22. sameAs integrity.
23. Author / organization alignment.
24. Knowledge graph readiness.

### 7.4 Núcleo local

25. Google Business Profile.
26. Maps / Local Pack.
27. NAP consistency.
28. Reviews e reputação.
29. Review-to-answer transfer.
30. Local content depth.
31. City / neighborhood relevance.
32. Maps-to-LLM consistency.

### 7.5 Núcleo generativo

33. Mention rate.
34. Citation readiness.
35. Citation persistence.
36. Citation attribution.
37. Cross-LLM consistency.
38. Position bias.
39. Source eligibility.
40. Query fan-out readiness.

### 7.6 Núcleo agentivo

41. Agent readiness.
42. B2A readiness.
43. Machine legibility.
44. Contact path clarity.
45. Form interpretability.
46. Actionability.
47. Conversion bridge score.
48. Transaction path integrity.

### 7.7 Núcleo de risco

49. Trust & safety compatibility.
50. Adversarial exposure.
51. Zero-click risk.
52. Reputation safety.
53. Spam pattern avoidance.
54. Policy risk.
55. Claim verification.
56. Conflicting source risk.

---

## 8. Camadas analíticas avançadas

O stack expandido reconhece mais de 100 camadas. Lista de referência:

### 8.1 Acesso e rastreabilidade

1. Crawlability.
2. Indexability.
3. Renderability.
4. JavaScript dependency.
5. HTML text availability.
6. Robots policy.
7. Sitemap integrity.
8. Canonical stability.
9. HTTP status health.
10. Redirect hygiene.
11. DNS reliability.
12. SSL integrity.
13. WAF compatibility.
14. Bot access differentiation.
15. Crawler error recovery.

### 8.2 Entidade

16. Entity clarity.
17. Entity verification.
18. Entity disambiguation.
19. Entity consistency.
20. Entity-URL alignment.
21. Entity-schema alignment.
22. Entity-social alignment.
23. Entity-GBP alignment.
24. Entity-author alignment.
25. Entity-organization alignment.
26. Entity-knowledge graph readiness.
27. Entity ambiguity risk.
28. sameAs integrity.
29. Brand-name stability.
30. Founder / author traceability.

### 8.3 Semântica

31. Semantic coherence.
32. Topical authority.
33. Topical coverage.
34. Semantic depth.
35. Intent coverage.
36. Query fan-out readiness.
37. Information gain.
38. Corpus expansion.
39. Conceptual density.
40. Definition quality.
41. Contextual completeness.
42. Entity relationship mapping.
43. Lexical diversity.
44. Terminology consistency.
45. Semantic redundancy control.

### 8.4 Editorial e conhecimento

46. Editorial density.
47. Human expertise signal.
48. Authorial originality.
49. Evidence depth.
50. Source transparency.
51. Methodology clarity.
52. Data freshness.
53. Update history.
54. Versioning.
55. Citation readiness.
56. Answer capsule quality.
57. FAQ utility.
58. Comparative explanation quality.
59. Example quality.
60. Practical application depth.

### 8.5 Recuperação por IA

61. Retrieval fitness.
62. Chunkability.
63. Passage independence.
64. Summary fidelity.
65. Compression fidelity.
66. Embedding compatibility.
67. RAG retrieval readiness.
68. Prompt-query match.
69. Context window efficiency.
70. Answer extraction quality.
71. Multi-intent retrieval.
72. Source eligibility.
73. Snippet integrity.
74. Citation candidate strength.
75. Retrieval layer distribution.

### 8.6 Consenso e validação externa

76. Multi-source consensus.
77. Cross-source consistency.
78. Third-party confirmation.
79. Review consensus.
80. Directory consistency.
81. Social proof alignment.
82. Media mention support.
83. External entity confirmation.
84. Citation graph support.
85. Authority corroboration.
86. Conflicting source risk.
87. Reputation consistency.
88. Public data agreement.
89. Local citation agreement.
90. Knowledge graph corroboration.

### 8.7 Confiança e segurança

91. Trust signal density.
92. E-E-A-T alignment.
93. Trust & safety compatibility.
94. Policy risk.
95. Legal clarity.
96. Contact transparency.
97. Business legitimacy.
98. Author accountability.
99. Review authenticity.
100. Claim verification.
101. Medical / legal / financial risk control.
102. Sensitive topic handling.
103. Spam pattern avoidance.
104. Misleading claim risk.
105. Reputation safety.

### 8.8 Frescor e propagação

106. Freshness signal.
107. Freshness propagation.
108. Update velocity.
109. Content decay risk.
110. Temporal relevance.
111. Last-modified consistency.
112. Sitemap freshness.
113. Schema date alignment.
114. GBP freshness.
115. Review freshness.
116. Social freshness.
117. News / blog freshness.
118. Outdated claim detection.
119. Historical content control.
120. Real-time relevance potential.

### 8.9 Citação e persistência

121. Citation readiness.
122. Citation persistence.
123. Citation stability.
124. Citation attribution.
125. Citation context quality.
126. Citation source diversity.
127. Citation frequency.
128. Citation freshness.
129. Citation position.
130. Citation sentiment.
131. Citation replacement risk.
132. Citation loss risk.
133. Brand mention strength.
134. Source-mention alignment.
135. Answer inclusion probability.

### 8.10 Agentes e ação

136. Agent readiness.
137. B2A readiness.
138. Actionability.
139. Machine legibility.
140. Form interpretability.
141. CTA clarity.
142. Price / offer clarity.
143. Availability clarity.
144. Location actionability.
145. Booking readiness.
146. Contact path clarity.
147. API / structured endpoint readiness.
148. Transaction path integrity.
149. Consideration set eligibility.
150. Agentic trust layer.

---

## 9. Modelo de dados: entidades

Arquivo: `data/entities.json`

```json
{
  "entity_id": "uuid",
  "official_name": "Nome oficial da empresa",
  "alternate_names": ["variação 1", "variação 2"],
  "entity_type": "local_business|person|organization|brand|service",
  "category": "Agência de SEO Local",
  "vertical": "marketing_digital",
  "city": "Porto Alegre",
  "state": "RS",
  "country": "BR",
  "official_website": "https://www.exemplo.com.br",
  "landing_domains": [
    "https://landingpage.exemplo.com.br"
  ],
  "google_business_profile_url": "https://...",
  "place_id": "optional",
  "primary_phone": "+55...",
  "whatsapp": "+55...",
  "email": "contato@exemplo.com.br",
  "address": {
    "street": "Rua Exemplo",
    "number": "123",
    "neighborhood": "Menino Deus",
    "city": "Porto Alegre",
    "state": "RS",
    "postal_code": "90000-000"
  },
  "services": [
    "SEO Local",
    "GEO",
    "Google Business Profile"
  ],
  "same_as": [
    "https://www.instagram.com/...",
    "https://www.linkedin.com/company/..."
  ],
  "eeat_signals": {
    "awards": [],
    "books": [],
    "media_mentions": [],
    "reviews_avg": null,
    "reviews_count": null,
    "certifications": []
  },
  "schema_org_presence": true,
  "last_validated": "2026-05-21T00:00:00-03:00"
}
```

---

## 10. Modelo de dados: queries

Arquivo: `data/query_templates.yaml`

```yaml
query_templates:
  - template_id: "uuid"
    template_text: "Quais são as melhores empresas de {service} em {city}?"
    vertical: "marketing_digital"
    intent_type: "commercial"
    locality_type: "city"
    complexity: "simple"
    expected_entity_type: "local_business"
    validation_criteria: "brand_mention_or_relevant_alternative"

  - template_id: "uuid"
    template_text: "Me ajude a escolher uma empresa de {service} em {neighborhood}, considerando reputação, clareza e próximos passos."
    vertical: "marketing_digital"
    intent_type: "agentic"
    locality_type: "neighborhood"
    complexity: "compound"
    validation_criteria: "actionable_recommendation"
```

### 10.1 Tipos de intenção

```yaml
intent_types:
  informational:
    description: "Busca explicação, definição ou orientação."
  commercial:
    description: "Busca opções, fornecedores ou comparação."
  local:
    description: "Busca empresa, serviço ou solução com localização."
  navigational:
    description: "Busca marca ou entidade específica."
  transactional:
    description: "Busca contratação, compra, orçamento ou contato."
  agentic:
    description: "Solicita decisão, comparação ou próximo passo executável."
```

---

## 11. Modelo de dados: respostas

Arquivo: `data/responses.jsonl`

```json
{
  "response_id": "uuid",
  "query_id": "uuid",
  "query_text": "Quais são as melhores empresas de SEO Local em Porto Alegre?",
  "llm_provider": "openai|anthropic|google|perplexity|microsoft|other",
  "model_name": "model-name",
  "model_version": "version-if-available",
  "temperature": 0,
  "seed": 42,
  "search_enabled": true,
  "response_text": "Texto integral da resposta",
  "sources": [
    {
      "url": "https://...",
      "title": "Fonte citada",
      "source_type": "owned|earned|third_party|directory|social|review"
    }
  ],
  "timestamp_utc": "2026-05-21T12:00:00Z",
  "latency_ms": 1300,
  "tokens_in": 120,
  "tokens_out": 900,
  "response_hash": "sha256"
}
```

---

## 12. Modelo de dados: menções

Arquivo: `data/mentions.jsonl`

```json
{
  "mention_id": "uuid",
  "response_id": "uuid",
  "entity_id": "uuid",
  "mentioned_name": "Nome citado",
  "position": 1,
  "total_entities_mentioned": 5,
  "mention_type": "explicit|implicit|source_only|recommendation",
  "sentiment": "positive|neutral|negative|mixed",
  "context_window": "Trecho ao redor da menção",
  "citation_url": "https://...",
  "attribution_type": "explicit_source|implicit_mention|no_source",
  "actionability": {
    "phone_found": true,
    "website_found": true,
    "maps_found": false,
    "next_step_clear": true
  },
  "validated_by_human": false
}
```

---

## 13. Modelo de dados: Google Business Profile snapshot

Arquivo: `data/gbp_snapshots.jsonl`

```json
{
  "snapshot_id": "uuid",
  "entity_id": "uuid",
  "timestamp_utc": "2026-05-21T12:00:00Z",
  "name": "Nome no Perfil da Empresa",
  "primary_category": "Agência de marketing",
  "secondary_categories": [],
  "rating": 4.9,
  "review_count": 120,
  "review_velocity_90d": 14,
  "owner_response_rate": 0.82,
  "services_count": 12,
  "products_count": 0,
  "photos_count": 80,
  "posts_90d": 8,
  "questions_answers_count": 10,
  "website_url": "https://...",
  "phone": "+55...",
  "address_consistent": true
}
```

---

## 14. Métricas principais

### 14.1 Local Mention Rate

Percentual de queries locais em que a entidade é mencionada.

```text
local_mention_rate = queries_with_entity_mention / total_queries
```

### 14.2 Citation Position Score

Posição normalizada da entidade quando aparece em resposta com múltiplas opções.

```text
position_score = 1 - ((position - 1) / (total_entities_mentioned - 1))
```

Quando há apenas uma entidade mencionada, atribuir posição máxima com observação metodológica.

### 14.3 Cross-LLM Consistency

Mede consistência da menção da entidade entre diferentes LLMs.

```text
cross_llm_consistency = 1 - standard_deviation(mention_rate_by_llm)
```

### 14.4 Maps-to-LLM Consistency

Compara presença no Google Maps / Local Pack com presença em LLMs.

Critérios:

- Aparece no Maps e aparece em LLM.
- Aparece no Maps e não aparece em LLM.
- Não aparece no Maps, mas aparece em LLM.
- Não aparece em nenhum.

### 14.5 Review-to-Answer Transfer

Mede se atributos presentes em reviews aparecem em respostas de IA.

Exemplos de atributos:

- atendimento rápido.
- preço justo.
- qualidade técnica.
- confiança.
- prazo.
- localização.
- equipe.
- pós-venda.

### 14.6 Multi-Source Consensus

Mede concordância entre fontes independentes sobre a mesma entidade.

Fontes possíveis:

- site oficial.
- Google Business Profile.
- redes sociais.
- diretórios locais.
- reviews.
- notícias.
- schema.
- páginas de terceiros.
- vídeos.
- artigos.

### 14.7 Citation Persistence

Mede se a entidade continua sendo citada ao longo do tempo.

Janelas recomendadas:

- 7 dias.
- 30 dias.
- 60 dias.
- 90 dias.

### 14.8 Freshness Propagation

Mede se atualizações se propagam entre:

- site.
- schema.
- sitemap.
- GBP.
- redes sociais.
- diretórios.
- páginas locais.
- respostas de IA.

### 14.9 Trust & Safety Compatibility

Mede risco de a fonte ser evitada por sistemas de IA por falta de confiança, exagero, inconsistência, spam, risco legal, risco médico, risco financeiro ou claims sem prova.

### 14.10 Agentic Actionability

Mede se um agente consegue agir a partir da informação disponível.

Itens:

- serviço identificado.
- localização identificada.
- telefone identificado.
- WhatsApp identificado.
- URL oficial identificada.
- horário identificado.
- preço ou critério identificado.
- formulário encontrado.
- política encontrada.
- próximo passo claro.

### 14.11 Conversion Bridge Score

Mede se existe ponte entre menção/visibilidade e ação mensurável.

Itens:

- CTA.
- telefone clicável.
- WhatsApp.
- rotas.
- formulário.
- evento GA4/GTM.
- UTM.
- CRM.
- conversão rastreada.

---

## 15. Fórmula conceitual de maturidade

O sistema pode consolidar a maturidade em cinco índices:

```text
1. Local Presence Index
2. Entity Trust Index
3. Generative Citation Index
4. Agentic Actionability Index
5. Conversion Bridge Index
```

Score final recomendado:

```text
PANDORA GEO LOCAL SCORE = síntese ponderada dos cinco índices
```

> Observação: os pesos devem ser definidos por contexto, vertical e objetivo. O presente documento não fixa pesos universais.

---

## 16. Query portfolio canônico

### 16.1 Consultas informacionais

```yaml
informational:
  - "O que considerar ao escolher {service} em {city}?"
  - "Como avaliar uma empresa de {service}?"
  - "Quais critérios usar antes de contratar {service}?"
  - "O que diferencia uma boa empresa de {service}?"
  - "Quais erros evitar ao contratar {service}?"
```

### 16.2 Consultas comerciais

```yaml
commercial:
  - "Quais empresas de {service} são referência em {city}?"
  - "Melhores empresas de {service} em {city}"
  - "Empresas bem avaliadas de {service} em {city}"
  - "Agências de {service} confiáveis em {city}"
  - "Quem contratar para {service} em {city}?"
```

### 16.3 Consultas comparativas

```yaml
comparative:
  - "Compare opções de {service} em {city}"
  - "Quais empresas de {service} têm melhor reputação em {city}?"
  - "Qual empresa escolher para {service}: critérios de comparação"
  - "Diferença entre uma agência comum e uma especialista em {service}"
  - "Como comparar fornecedores de {service}?"
```

### 16.4 Consultas locais

```yaml
local:
  - "{service} perto de mim"
  - "{service} em {neighborhood}"
  - "{service} em {city}"
  - "empresa de {service} próxima"
  - "prestador de {service} bem avaliado em {city}"
```

### 16.5 Consultas agentivas

```yaml
agentic:
  - "Me ajude a escolher uma empresa de {service} em {city} e explique os critérios."
  - "Liste opções confiáveis de {service} em {city} com próximo passo para contato."
  - "Compare fornecedores de {service} em {city} considerando reputação, clareza e facilidade de contratação."
  - "Quero contratar {service} em {city}. Quais informações devo verificar antes?"
  - "Encontre uma empresa de {service} em {city} que tenha site claro, boa reputação e contato fácil."
```

---

## 17. Protocolo de coleta

Cada coleta deve registrar:

- query.
- variações de query.
- LLM.
- modelo.
- versão.
- temperatura.
- seed quando disponível.
- data e hora UTC.
- idioma.
- região.
- resposta completa.
- links citados.
- hash da resposta.
- latência.
- tokens.
- estado de busca ativada ou desativada.
- observação de instabilidade.

### 17.1 Acceptance gates

Uma coleta só é aceita quando:

- response não é nula.
- timestamp UTC existe.
- query_id existe.
- response_hash existe.
- provider/model foi registrado.
- erro foi documentado quando houve falha.
- conteúdo sensível foi tratado conforme política.
- duplicidade foi identificada.

---

## 18. Validação humana

Amostra recomendada:

```text
20% das respostas por período de análise.
```

Dois anotadores devem avaliar:

- entidade mencionada corretamente.
- posição correta.
- sentimento correto.
- fonte correta.
- recomendação explícita ou não.
- resposta útil ou não.
- actionability presente ou ausente.

Métrica recomendada:

```text
Cohen's Kappa >= 0.8
```

Quando houver divergência:

- terceiro revisor decide.
- decisão é registrada.
- regras de anotação são atualizadas.

---

## 19. Relatório semanal

Arquivo:

```text
outputs/weekly-reports/weekly-geo-local-YYYY-MM-DD.html
```

Estrutura:

```yaml
weekly_report:
  executive_summary:
    - total_queries
    - total_responses
    - entities_monitored
    - top_movers
    - anomalies
    - major_risks

  local_presence:
    - maps_visibility
    - local_pack_presence
    - gbp_health
    - nap_consistency

  generative_visibility:
    - mention_rate
    - citation_position
    - cross_llm_consistency
    - source_attribution

  entity_trust:
    - entity_clarity
    - multi_source_consensus
    - trust_safety_compatibility
    - conflicting_sources

  agentic_readiness:
    - actionability
    - contact_path
    - form_interpretability
    - conversion_bridge

  recommendations:
    - quick_wins
    - structural_fixes
    - content_plan
    - technical_plan
```

---

## 20. Relatório mensal

Arquivo:

```text
outputs/monthly-reports/monthly-geo-local-YYYY-MM.pdf
```

Estrutura:

1. Resumo executivo.
2. Score geral.
3. Evolução mensal.
4. Comparativo com concorrentes.
5. Presença em Maps.
6. Presença em LLMs.
7. Consistência Maps x LLM.
8. Reviews e influência nas respostas.
9. Fontes usadas por IA.
10. Riscos e anomalias.
11. Oportunidades por query.
12. Plano de ação de 30/60/90 dias.

---

## 21. Dashboard de KPIs

```yaml
kpis:
  local_mention_rate:
    definition: "% de queries locais com menção à entidade"
    target: "crescimento mês a mês"

  citation_position_score:
    definition: "posição média normalizada da entidade nas respostas"
    target: "aproximação de 1.0"

  cross_llm_consistency:
    definition: "estabilidade de menção entre LLMs"
    target: "reduzir variação"

  maps_llm_consistency:
    definition: "alinhamento entre presença em Maps e respostas de LLMs"
    target: "alto alinhamento"

  review_to_answer_transfer:
    definition: "transferência de atributos das reviews para respostas de IA"
    target: "atributos positivos recorrentes"

  multi_source_consensus:
    definition: "consenso entre fontes independentes"
    target: "alta consistência"

  freshness_propagation:
    definition: "propagação de atualizações no ecossistema"
    target: "baixo atraso"

  trust_safety_compatibility:
    definition: "baixo risco de conteúdo ser considerado fraco, enganoso ou inseguro"
    target: "alta compatibilidade"

  agentic_actionability:
    definition: "capacidade de agente iniciar uma ação"
    target: "alta clareza operacional"

  conversion_bridge_score:
    definition: "ponte entre visibilidade e conversão mensurável"
    target: "eventos rastreáveis"
```

---

## 22. Política de bots

O sistema deve registrar e auditar:

- Googlebot.
- GoogleOther.
- Google-Extended.
- GPTBot.
- OAI-SearchBot.
- ChatGPT-User.
- ClaudeBot.
- Claude-SearchBot.
- PerplexityBot.
- Applebot.
- CCBot.
- Bytespider.
- Bingbot.
- Outros user-agents emergentes.

### 22.1 Estratégia recomendada

Não aplicar bloqueio universal sem análise.

Classificar:

```text
1. Bots de busca tradicional.
2. Bots de treinamento.
3. Bots de busca/recuperação.
4. Fetchers acionados por usuário.
5. Agentes de navegação.
```

Para cada classe:

- permitir.
- bloquear.
- limitar.
- monitorar.
- revisar.

---

## 23. Trust & Safety

O PANDORA deve evitar práticas que simulem autoridade de forma artificial.

### 23.1 Riscos avaliados

- claims sem prova.
- promessas exageradas.
- falsos comparativos.
- reviews manipuladas.
- páginas massivas de baixa utilidade.
- entidades falsas.
- conteúdo copiado.
- dados estruturados incoerentes.
- schema não refletido no texto visível.
- conteúdo sensível sem responsabilidade.
- recomendação local enganosa.
- manipulação de listas “melhores empresas”.

### 23.2 Princípio

> A otimização para IA deve aumentar clareza, verificabilidade e utilidade. Não deve tentar manipular recomendações ou respostas.

---

## 24. Ética e limitações

### 24.1 Limitações

- LLMs comerciais mudam sem aviso.
- Temperatura 0 não garante reprodutibilidade absoluta.
- Respostas podem variar por região, conta, idioma, contexto e ferramenta.
- Nem todas as fontes usadas por IA são visíveis.
- Nem toda menção é citação.
- Nem toda citação gera tráfego.
- Nem toda visibilidade gera conversão.
- Resultados não devem ser vendidos como garantia de recomendação.

### 24.2 Boas práticas

- Declarar metodologia.
- Registrar data e modelo.
- Manter logs.
- Distinguir fato, hipótese e interpretação.
- Não inflar achados.
- Documentar incertezas.
- Revisar dados manualmente.
- Evitar claims absolutos.

---

## 25. Loop de otimização

A cada ciclo quinzenal:

```yaml
optimization_sprint:
  step_1_review:
    - revisar métricas
    - identificar quedas
    - identificar ganhos
    - detectar anomalias

  step_2_hypotheses:
    - levantar causas prováveis
    - separar técnico, conteúdo, entidade, reputação, fonte e agente

  step_3_actions:
    - ajustar páginas
    - melhorar schema
    - atualizar GBP
    - responder reviews
    - criar conteúdo citável
    - corrigir NAP
    - melhorar contato e CTA

  step_4_validation:
    - repetir queries
    - comparar antes/depois
    - validar amostra manual
    - documentar evidências

  step_5_report:
    - gerar relatório
    - criar plano da próxima sprint
```

---

## 26. Roadmap

### 26.1 Versão 1.0

- Documento principal.
- Modelo de entidades.
- Query portfolio.
- Métricas principais.
- Relatório semanal.
- Relatório mensal.
- Auditoria de entity clarity.
- Auditoria de GBP.
- Auditoria de citation readiness.

### 26.2 Versão 1.5

- Coleta multi-LLM.
- Extração automática de menções.
- Source attribution graph.
- Maps-to-LLM consistency.
- Review-to-answer transfer.
- Citation persistence.
- Freshness propagation.

### 26.3 Versão 2.0

- Dashboard interativo.
- Benchmark por vertical.
- Benchmark por cidade.
- Relatórios client-facing.
- Exportação JSON, HTML e PDF.
- Dataset interno versionado.
- API simples para consulta.

### 26.4 Versão 3.0

- Agentes de auditoria.
- Testes agentivos reais.
- Integração com CRM.
- Integração com GA4/GTM.
- Simulação de funil.
- Medição de impacto em leads e conversão.
- Modelo preditivo de oportunidade local.

---

## 27. Exemplo de uso

### 27.1 Cenário

Empresa local:

```yaml
entity:
  official_name: "Empresa Exemplo"
  city: "Porto Alegre"
  state: "RS"
  category: "Assistência técnica de celulares"
  services:
    - "troca de tela"
    - "troca de bateria"
    - "conserto de iPhone"
```

### 27.2 Queries

```yaml
queries:
  - "melhor assistência técnica de celular em Porto Alegre"
  - "onde trocar tela de iPhone no Menino Deus"
  - "assistência técnica de celular perto de mim"
  - "empresas confiáveis para conserto de iPhone em Porto Alegre"
  - "me ajude a escolher uma assistência técnica de celular e diga o próximo passo"
```

### 27.3 Métricas

```yaml
expected_outputs:
  local_mention_rate: "percentual de aparição nas queries"
  maps_llm_consistency: "alinhamento Maps x LLM"
  review_to_answer_transfer: "atributos das reviews citados pela IA"
  agentic_actionability: "capacidade de iniciar contato"
  conversion_bridge_score: "ponte para WhatsApp, rota e formulário"
```

---

## 28. Comandos futuros sugeridos

```bash
# coletar respostas de LLMs
python scripts/collect_llm_responses.py --queries data/queries.jsonl --out data/responses.jsonl

# extrair menções
python scripts/extract_mentions.py --responses data/responses.jsonl --entities data/entities.json

# calcular métricas
python scripts/calculate_metrics.py --input data/mentions.jsonl --out outputs/metrics.json

# comparar Maps e LLM
python scripts/compare_maps_vs_llm.py --maps data/maps_snapshots.jsonl --mentions data/mentions.jsonl

# gerar relatório semanal
python scripts/generate_weekly_report.py --metrics outputs/metrics.json --out outputs/weekly-reports/
```

---

## 29. Conclusão

O **PANDORA GEO LOCAL & AGENTIC SEARCH OS** não é apenas uma auditoria de site.

É um sistema operacional para entender a nova busca digital em sua forma completa:

- busca tradicional.
- busca local.
- mapas.
- entidades.
- reviews.
- respostas generativas.
- citações.
- fontes.
- confiança.
- agentes digitais.
- conversão.

Frase oficial:

> **O PANDORA mede se uma empresa local é encontrada, compreendida, citada, confiável e acionável na nova busca digital.**

---

## 30. Licença e autoria

Autor: **Raphael Sousa Pereira**

Uso recomendado:

- pesquisa.
- auditoria.
- documentação técnica.
- desenvolvimento de motor.
- consultoria.
- benchmark.
- educação.
- relatórios executivos.

Aviso:

Este documento descreve uma arquitetura metodológica. A implementação técnica, coleta de dados e uso comercial devem respeitar termos de uso das plataformas, leis aplicáveis, privacidade, direitos autorais e boas práticas de mercado.
