# pandora-geo-local-os
Sistema operacional de auditoria GEO Local, SEO Local e ASO para Google, Google Maps, IAs generativas e agentes digitais.

# PANDORA GEO LOCAL OS

Sistema operacional de auditoria GEO Local, SEO Local e ASO para Google, Google Maps, IAs generativas e agentes digitais.

## Visão geral

O PANDORA GEO LOCAL OS é uma arquitetura técnica para medir se uma empresa local é encontrada, compreendida, citada, confiável e acionável na nova busca digital.

O sistema integra três camadas:

- SEO Local: ser encontrado.
- GEO: ser citado.
- ASO: ser acionado por agentes digitais.

## Documento principal

Leia o documento completo:

[PANDORA_GEO_LOCAL_OS.md](PANDORA_GEO_LOCAL_OS.md)

## Motores

| Motor | Arquivo | Função |
|---|---|---|
| PANDORA HEADING AUDIT Ω v5.0.0 | [`scripts/pandora_heading_audit.py`](scripts/pandora_heading_audit.py) | Auditoria forense e remediação supervisionada de H1/H2/H3 ([documentação](docs/HEADING_AUDIT.md)) |
| PANDORA SITEMAP & LLMS AUDIT Ω v1.0.0 | [`scripts/pandora_sitemap_audit.py`](scripts/pandora_sitemap_audit.py) | robots e bots de IA, sitemaps, saúde de URLs, links internos, llms.txt; gera llms.txt, llms-full.txt e Mapa do site ([documentação](docs/SITEMAP_AUDIT.md)) |
| PANDORA COMPETITOR Ω v3.1.1 | [`scripts/pandora_competitor_omega.py`](scripts/pandora_competitor_omega.py) | Monitoramento semanal de concorrentes: mudanças, autoria declarada, sobreposição temática e histórico forense 30/60/90 dias ([documentação](docs/COMPETITOR_AUDIT.md)) |
| PANDORA ADS Ω v1.0.0 | [`scripts/pandora_ads_omega.py`](scripts/pandora_ads_omega.py) | Auditoria forense de Google Ads (somente leitura): conversões, termos, negativas, qualidade, orçamento, lances, leilão, SEO × Ads e landing pages ([documentação](docs/ADS_OMEGA.md) · [base de conhecimento](docs/ADS_KNOWLEDGE.md)) |

```bash
python scripts/pandora_heading_audit.py audit ./site --json report.json --md report.md
python scripts/pandora_sitemap_audit.py audit https://example.org --json sitemap.json --md sitemap.md
python -m unittest discover tests
```

## Escopo

O sistema cobre:

- Google Search
- Google Maps
- Google Business Profile
- SEO Local
- GEO
- ASO
- LLMs
- AI Overviews
- bots de IA
- reviews
- entidades
- citações
- fontes
- agentes digitais
- conversão local

## Autor

Raphael Sousa Pereira

## Status

Versão inicial do sistema operacional técnico.
