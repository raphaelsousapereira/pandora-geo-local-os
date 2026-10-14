# Sala de Imprensa — Verônica Fraga / Fraga & Santos

Gerada com o PANDORA PRESS-SUITE Ω em 14/10/2026 a partir das páginas oficiais do site (`/veronica-fraga/` e `/parcerias-e-fornecedores/`, revisadas pelo escritório em 13/10/2026).

## Arquivos

| Arquivo | Uso |
|---|---|
| `sala-de-imprensa.html` | Conteúdo da página: colar num bloco **HTML personalizado** de uma página nova com slug `sala-de-imprensa` (mesmo visual das páginas da Verônica, inclui o JSON-LD) |
| `records.jsonld` | Registros da suíte em JSON-LD (referência; o JSON-LD publicado está dentro do HTML) |
| `../../data/pressroom-fraga.sqlite3` | Base da suíte: autora, 4 registros, 6 evidências, histórico com cadeia de hash verificada |

## O que a página contém

Resposta direta citável · biografias curta/média/completa com botão de copiar · ficha verificável (CAU, CNPJ, endereço, redes) · 6 temas em que a Verônica pode ser fonte · números do escritório (rotulados como informados pelo escritório) · cronologia · seção "Na mídia" que só aceita registros com link · foto oficial com crédito · contato para jornalistas.

JSON-LD: `WebPage` da sala de imprensa com `about`/`mainEntity` apontando para a **mesma entidade** `#veronica-fraga` já publicada no site (consolida a entidade em vez de criar outra), `LocalBusiness`, `ImageObject` com crédito e `BreadcrumbList`.

Validação: motor de headings 1000/1000 (1 H1, 9 H2); JSON-LD válido; sem estouro horizontal no celular.

## Decisões de honestidade

- Nenhum campo vazio ou "PREENCHER" visível.
- "c. 2013" é estimativa a partir dos "13 anos de escritório"; a parceria Simonetto "desde 2023" vem de "há mais de 3 anos".
- Registro CAU fica `pending` na base até ser conferido no Ache um Arquiteto (CAU/BR).
- "Na mídia" começa sem itens: nenhum registro de imprensa verificável foi encontrado no site.

## Para completar (enviar quando houver)

1. Matérias, entrevistas, palestras ou prêmios, cada um com link e data.
2. Formação (instituição e ano) e especializações (ex.: neuroarquitetura, perícia).
3. E-mail para imprensa, se houver, além do WhatsApp.
4. Logo e 2–3 fotos de projetos com autorização e crédito.
5. Ano exato de fundação do escritório (substitui o "c. 2013").

## Achados no site durante a coleta

- A consulta de **posts** pela API respondeu com a página de erro "ConnectYourDomain" do **Wix**: parte das requisições ao domínio ainda resolve para o Wix. Vale revisar o DNS (registros A/CNAME, `www`) no registrador.
- Página "Marketing Digital em Porto Alegre" publicada no site de arquitetura: conferir se pertence a este domínio.
- Títulos de páginas em minúsculas no formato de endereço (ex.: "arquiteto porto alegre projetos residenciais personalizados"), mesmo problema do outro site.
