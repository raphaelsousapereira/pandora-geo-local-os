# PANDORA PRESS-SUITE Ω — Sala de Imprensa auditável

Suíte do ecossistema **PANDORA GEO LOCAL OS** para manter a cronologia citável de um autor (livros, papers, entrevistas, palestras, software…) com evidências, histórico à prova de adulteração e exportação em HTML e JSON-LD — a camada de **entidade e autoria** que IAs e buscadores usam para entender quem é o autor.

- Pacote: [`scripts/pandora_press/`](../scripts/pandora_press/) · atalho: [`scripts/pandora_press_suite.py`](../scripts/pandora_press_suite.py)
- Versão da suíte: 1.1.0 (Pressroom 1.3.0 · Inventory 0.1.0 · Discovery 0.1.0 · Console 0.1.0)
- Python 3.10+, stdlib; PDF requer `reportlab`

## Módulos

| Módulo | Função |
|---|---|
| `press` (PRESSROOM) | autores, registros, evidências, histórico com cadeia SHA-256 (`history-verify`, `evidence-verify`), coleta de candidatos, aprovação manual, exportação JSON / JSON-LD / HTML / CSV / PDF |
| `inventory` | totais por tipo, ano, status e evidência; CSV e PDF |
| `discovery` | descoberta supervisionada a partir de URLs-semente: candidatos ficam **pendentes**, com sinal de identidade (`mention` / `ambiguous` / `unknown`) guardado à parte |
| `console` | painel local (127.0.0.1) para revisar candidatos, ver cronologia e baixar relatórios |

## Uso

```bash
python scripts/pandora_press_suite.py selftest
python scripts/pandora_press_suite.py press --db press.sqlite3 author-add --name "Raphael Sousa Pereira" --url https://raphaelsousapereira.com.br
python scripts/pandora_press_suite.py discovery --db press.sqlite3 discover --author <ID> --url https://raphaelsousapereira.com.br --max-pages 20
python scripts/pandora_press_suite.py console --db press.sqlite3 --port 8765      # http://127.0.0.1:8765
python scripts/pandora_press_suite.py press --db press.sqlite3 export --author <ID> --format jsonld --out press.jsonld
python scripts/pandora_press_suite.py press --db press.sqlite3 export --author <ID> --format html --out sala-de-imprensa.html --only-verified
```

## Garantias

- Nada é verificado ou publicado automaticamente: descoberta gera candidatos; aprovação cria registro `pending`.
- Toda alteração de registro e toda evidência entram numa cadeia de hash verificável.
- Coleta só em hosts públicos (validação de DNS, sem credenciais na URL, portas 80/443, sem seguir redirecionamentos).
- Exportações públicas (HTML/JSON-LD) excluem `conflicted` e `retracted`; `--only-verified` publica só `verified`/`corrected`.

## Correções aplicadas na integração (1.0.0 → 1.1.0)

| Problema | Efeito | Correção |
|---|---|---|
| Proveniência da descoberta gravada dentro do resumo | ao aprovar, `[DISCOVERY] {"identity_signal": …}` ia para o HTML público e o JSON-LD | sinal guardado em `candidate_signals`; aprovação limpa resumos antigos |
| JSON-LD sem filtro de status | itens retratados/em conflito publicados como obras do autor | filtro padrão + `--only-verified` |
| `Event` com `creator` | propriedade inválida para eventos no schema.org | `performer` para palestras/eventos/workshops |
| `@id` repetido quando dois registros usam a mesma URL | nós fundidos no grafo | `@id` único por registro |
| Painel sem checagem de `Host` | DNS rebinding: site malicioso lia o token CSRF e acionava coletas/aprovações | só `127.0.0.1:porta`/`localhost:porta`; demais → 403 |
| Palavras-chave sobrescreviam o tipo vindo do JSON-LD | "Sistema editorial" com `@type: Book` virava software | JSON-LD tem prioridade |
| `www.` tratado como outro site | descoberta parava na raiz | variantes www/não-www seguidas |
| Código embutido em strings e executado com `exec` | difícil de revisar, testar e analisar | pacote Python normal com imports explícitos |
| Charset ignorado; User-Agent 1.2 | texto corrompido em páginas não UTF-8 | charset da resposta; versão real |

## Limites

- Validação de DNS sem pinagem de IP (TOCTOU/rebinding no coletor): rodar a coleta em rede isolada.
- Painel sem autenticação de usuário: só para uso local.
- Status `verified` é decisão humana; o sistema não comprova fatos.
