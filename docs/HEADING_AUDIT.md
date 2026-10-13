# PANDORA HEADING AUDIT Ω — motor de auditoria H1/H2/H3

Motor do ecossistema **PANDORA GEO LOCAL OS** responsável pela auditoria forense e remediação supervisionada da hierarquia de títulos (H1/H2/H3).

- Arquivo: [`scripts/pandora_heading_audit.py`](../scripts/pandora_heading_audit.py)
- Versão: 5.0.0
- Dependências: nenhuma (Python 3.10+, apenas stdlib)

## Onde se encaixa no PANDORA

| Núcleo (seção 7) | Engrenagem | Contribuição do motor |
|---|---|---|
| 7.1 Núcleo técnico | 7. HTML textual | Presença, hierarquia e integridade de H1–H3 no HTML estático |
| 7.2 Núcleo semântico | 9. Conteúdo semântico · 16. Semantic coherence | Sobreposição lexical tópico/title/H1, redundância de H2, H1 duplicado entre páginas |
| 7.6 Núcleo agentivo | Legibilidade por agentes | Estrutura navegável por leitores de tela, crawlers e agentes |

## Comandos

```bash
# Auditoria (diretório local, arquivo ou URL)
python scripts/pandora_heading_audit.py audit ./site --json outputs/heading-report.json --md outputs/heading-report.md
python scripts/pandora_heading_audit.py audit https://example.org --max-pages 20 --topic "dentista em Fortaleza"

# Correção segura (somente headings literalmente vazios, com backup .pandora.bak)
python scripts/pandora_heading_audit.py fix ./site --dry-run --diff changes.patch
python scripts/pandora_heading_audit.py fix ./site --apply

# Gate de qualidade para CI
python scripts/pandora_heading_audit.py verify ./site --min-score 800

# Revisão semântica supervisionada (propor → revisar → aprovar → aplicar)
python scripts/pandora_heading_audit.py propose ./site --output proposals.json
python scripts/pandora_heading_audit.py generate-semantic ./site --output proposals.json --provider anthropic --model <modelo>
python scripts/pandora_heading_audit.py review-proposals proposals.json --diff review.patch
python scripts/pandora_heading_audit.py apply-proposals proposals.json

# Testes
python scripts/pandora_heading_audit.py selftest
python scripts/pandora_heading_audit.py selftest-v4
python -m unittest discover tests
```

`generate-semantic` exige `ANTHROPIC_API_KEY` (ou `OPENAI_API_KEY` com `--provider openai-compatible`). As propostas nunca são aplicadas automaticamente: cada item precisa de `approved: true`, justificativa e evidência literal da página.

## Score (0–1000)

| Dimensão | Máx. | Exemplos de deduções |
|---|---|---|
| presence | 250 | MISSING_H1, NO_HEADINGS, MULTIPLE_H1, FIRST_NOT_H1 |
| hierarchy | 250 | LEVEL_SKIP, NESTED_HEADING, UNCLOSED_HEADING, MULTIPLE_MAIN |
| content | 200 | EMPTY_HEADING, DUPLICATE_TEXT, LONG_HEADING |
| accessibility | 150 | HIDDEN_HEADING, ARIA_HIDDEN_HEADING, MISSING_LANG, H1_OUTSIDE_MAIN |
| document_context | 150 | MISSING_TITLE, DUPLICATE_ID |

## Limites

- O score é um **proxy técnico estrutural**, não uma previsão de ranking.
- Analisa HTML estático: não renderiza JavaScript, CSS externo nem shadow DOM.
- Múltiplos H1 e saltos de nível são sinalizados para revisão contextual, não tratados como penalidade do Google.
- O modo URL é somente leitura.
