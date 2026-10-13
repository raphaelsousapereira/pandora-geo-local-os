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

```bash
python scripts/pandora_heading_audit.py audit ./site --json report.json --md report.md
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
