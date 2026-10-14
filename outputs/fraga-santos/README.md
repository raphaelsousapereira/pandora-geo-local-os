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

## BNI (incluído em 14/10/2026)

- Entrou: membro do **BNI POA Mauá (BNI Brasil) desde 2025, Coordenadora de Educação** — nas bios, na ficha ("Associações"), na cronologia, num tema de fonte e no JSON-LD (`memberOf` com `OrganizationRole`; perfil do BNI em `sameAs`). Status `declared`, com o perfil de membro e a página do grupo como evidência (não conferidos nesta coleta por bloqueio de rede).
- **Não entrou: BNI Global Convention 2026** (Grimaldi Forum, Mônaco, 28–30/10/2026). As fontes mostram o evento, não a participação da Verônica. Se ela for, registrar como participação com confirmação (inscrição, foto ou publicação do BNI); depois do evento, entra na cronologia e em "Na mídia" se houver cobertura.

## Vídeos e entrevistas

| Data | Título | Canal | Link | Status |
|---|---|---|---|---|
| 03/11/2025 | Arquitetura completa:do projeto à execução de obras residenciais e comerciais \| Veronica e Nei Fraga | Beatriz Santanna (entrevista) | https://youtu.be/1mG4sWdH1tA | verified (captura de tela enviada em 14/10/2026) |
| 03/09/2025 | BW CAST - Com Verônica Fraga | Business Women BW (entrevista, 36min20s) | https://www.youtube.com/watch?v=8uTutUXiwHI | verified (capturas de tela enviadas em 14/10/2026); entrevistadora Jenifer Castro, CEO do BW Business Women (bwbusinesswomen.com.br) |
| 14/06/2023 | Confira as dicas para um banheiro dos sonhos com a arquiteta Verônica Fraga | Elevato Pisos e Acabamentos (vídeo com marca) | https://youtu.be/VGxB4dfXNIw | verified (captura de tela enviada em 14/10/2026) |
| 22/01/2026 | A História da Fraga & Santos: 12 Anos de Arquitetura de Alto Padrão, Desafios e Visão para 2026 | Fraga & Santos (entrevista ao Band Mulher, jornalista Regina Lima) | https://youtu.be/pPIFqIy39ZE | verified (captura de tela enviada em 14/10/2026) |
| 14/05/2026 | Casa instagramável vale a pena ou pode atrapalhar a vida real? Arquiteto em Porto Alegre | Fraga & Santos Arquitetura Completa (episódio do Programa da Regina, Regina Lima) | https://youtu.be/LzFBlRtS940 | verified (captura de tela enviada em 14/10/2026) |
| 17/04/2026 | Dopamine Decor em 2026: tendência ou exagero? Fraga & Santos com Regina Lima | Fraga & Santos Arquitetura Completa (entrevista a Regina Lima) | https://youtu.be/Q0VzfRoRSSs | verified (captura de tela enviada em 14/10/2026) |
| 25/08/2026 | Como Funciona uma Obra Completa? Projeto, Execução e Gestão - Arq. Verônica Fraga - Fraga & Santos | BNI Mauá | https://youtu.be/mvNwtPoJkfM | verified (captura de tela enviada em 14/10/2026) |

Entra na cronologia, em "Na mídia e palestras" (cartão com miniatura) e no JSON-LD como `VideoObject` com a Verônica em `actor`. Regina Lima: 3 entrevistas registradas (22/01/2026, Band Mulher; 17/04/2026; 14/05/2026, Programa da Regina). A descrição de 14/05/2026 cita "o canal da Regina no YouTube": pedir a URL desse canal para registrar o programa como veículo. Confirmar se a de 17/04/2026 também foi ao ar no Band Mulher; se sim, e com link da Band, registrar o veículo.

**Canal próprio no YouTube:** a Fraga & Santos tem canal ("Fraga & Santos Arquitetura Completa"). Adicionar a URL do canal ao `sameAs` da organização no site e nesta página reforça a entidade.

**Consistência de nome:** o vídeo de 03/11/2025 chama o sócio de "Nei Fraga"; o site usa "Nei Fernando dos Santos". Para a entidade nas IAs, padronizar o nome nas descrições futuras (ou declarar o nome alternativo no JSON-LD do site com `alternateName`, se for de uso dele).

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
