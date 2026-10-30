# Plano da Plataforma — Bíblia em Contexto

> Plano estratégico e operacional para transformar o site em uma grande
> plataforma de estudo bíblico em português, tratado como produto de empresa.
> Documento vivo: atualizar a seção "Estado do plano" a cada entrega.

---

## 0. Sumário executivo

**O que somos hoje:** um site estático (GitHub Pages + Supabase) com a Bíblia
inteira (66 livros, 1.189 capítulos, 31.173 versículos) em português e nos
originais (hebraico WLC / grego Nestle 1904), com transliteração, ferramentas
pessoais de estudo (notas, grifos, favoritos, planos, progresso) e conta
opcional com sincronização.

**O que queremos ser:** a principal plataforma brasileira de **estudo** bíblico
— não só de leitura — onde qualquer pessoa, do leitor iniciante ao estudante de
seminário, consegue entender o texto no seu contexto (língua, história,
geografia, literatura) e organizar o próprio estudo.

**Como chegamos lá (3 movimentos):**

1. **Profundidade de conteúdo** — sair de 10 artigos / 14 verbetes / 22 lugares
   para milhares de páginas curadas (dicionário, personagens, lugares, livros,
   temas, introduções), todas ligadas ao texto.
2. **Workspace de estudo de verdade** — cadernos, coleções, estudos guiados,
   comparação de traduções, exportação; o usuário passa a *produzir* algo.
3. **Distribuição e sustentabilidade** — SEO como canal principal, app nas
   lojas, domínio próprio, e um modelo de apoio que nunca bloqueia o texto
   bíblico.

**Meta-norte (North Star):** *dias de estudo ativos por semana* — usuários que
abriram um capítulo **e** fizeram uma ação de estudo (nota, grifo, plano,
consulta ao original/dicionário) no mesmo dia.

---

## 1. Diagnóstico atual

### 1.1 Ativos

| Área | Situação hoje |
|---|---|
| Texto bíblico | 66 livros completos, Almeida (domínio público), hebraico WLC, grego Nestle 1904, transliteração |
| Páginas geradas | 1.189 capítulos + 31.173 páginas de versículo (ótimas para SEO de cauda longa) |
| Conteúdo editorial | 10 artigos, 12 temas, 14 verbetes de dicionário, 22 lugares, 3 planos de leitura, 82 versículos do dia |
| Dados de estudo | 39 versículos com referências cruzadas, 15 com comentário, léxico hebraico com 462 entradas |
| Ferramentas | Notas, grifos/marca-texto, favoritos, planos, progresso/missões, áudio TTS, modo offline (PWA), busca |
| Conta | Supabase Auth + sincronização entre dispositivos |
| Engenharia | Build Python, testes pytest, CodeQL, deploy automático, CSP |

### 1.2 Pontos fracos

- **Conteúdo raso frente ao texto:** o texto está 100% coberto, mas as camadas
  de estudo cobrem menos de 1% dos versículos.
- **Uma só tradução em português** (Almeida 1911). Traduções modernas (ARA,
  NVI, NAA, NVT) são protegidas por direitos autorais — exigem licença.
- **Grego sem léxico** equivalente ao hebraico.
- **Repositório pesado:** o histórico Git já passa de 1 GB e há ~32 mil arquivos
  gerados versionados. Isso vai travar o crescimento (limites do GitHub e do
  GitHub Pages, builds lentos).
- **Domínio `github.io`:** fraco para marca, SEO e para publicar app nas lojas.
- **Sem métricas de produto:** não sabemos quantos estudam, onde abandonam,
  quais páginas trazem tráfego.
- **Comunidade pausada:** decisão de produto correta, mas deixa o produto sem
  efeito de rede por enquanto.

### 1.3 Oportunidades

- Público brasileiro evangélico e católico enorme, com pouca oferta de estudo
  **sério, gratuito e em português** com acesso aos originais.
- Concorrentes grandes focam em *leitura e devocional* (apps de leitura) ou são
  *caros e técnicos* (softwares acadêmicos em inglês). Existe um espaço no meio:
  **estudo acessível com profundidade**.
- Páginas de versículo indexáveis = canal de aquisição orgânico praticamente
  gratuito.

---

## 2. Visão, missão e princípios

**Missão:** ajudar cada leitor a entender a Bíblia no seu contexto original e a
transformar leitura em estudo.

**Visão (5 anos):** ser a referência em língua portuguesa para estudo bíblico,
usada por leitores, pequenos grupos, igrejas e seminários.

**Princípios inegociáveis:**

1. **A Bíblia é o centro.** Toda funcionalidade nasce de um versículo e volta
   para ele.
2. **O texto é sempre gratuito.** Nenhum paywall sobre o texto bíblico, os
   originais ou as ferramentas básicas de estudo.
3. **Sem recursos de IA para o usuário final.** O conteúdo é curado e assinado
   por pessoas; isso é diferencial de confiança.
4. **Privacidade primeiro.** Funciona sem conta; dados do usuário pertencem ao
   usuário (exportação total, exclusão real, LGPD).
5. **Fontes declaradas.** Todo comentário, verbete e mapa cita sua fonte.
6. **Neutralidade confessional responsável.** Apresentar posições
   interpretativas principais quando houver divergência, sem polemizar.
7. **Rápido em qualquer celular.** Páginas leves, offline, acessíveis.

---

## 3. Público e personas

| Persona | Quem é | O que precisa | Como servimos |
|---|---|---|---|
| **Leitor diário** | Lê a Bíblia no celular, devocional | Constância, leitura fácil, lembrete | Planos, progresso, versículo do dia, retomada |
| **Estudante curioso** | Quer "entender de verdade" | Contexto, palavras originais, explicações | Originais, dicionário, artigos, mapas, linha do tempo |
| **Líder de grupo / professor de EBD** | Prepara estudos semanais | Roteiros prontos, material imprimível | Estudos guiados, cadernos, exportação PDF, (futuro) grupos |
| **Seminarista** | Precisa de ferramenta técnica em PT | Léxico, morfologia, comparação | Interlinear, léxico hebraico/grego, concordância |
| **Igreja / ministério** | Quer ferramenta para a congregação | Planos coletivos, marca própria | Plano Igrejas (fase 4) |

Prioridade de atendimento: **Estudante curioso → Leitor diário → Líder de
grupo → Seminarista → Igreja.** O estudante curioso é quem chega pelo Google e
é quem o nosso diferencial (contexto + originais) converte melhor.

---

## 4. Posicionamento

> **"Leia a Bíblia no contexto em que ela foi escrita."**

| | Apps de leitura/devocional | Softwares acadêmicos | **Bíblia em Contexto** |
|---|---|---|---|
| Idioma | PT | Majoritariamente EN | **PT nativo** |
| Preço | Grátis | Caro | **Grátis (apoio opcional)** |
| Originais | Raso ou ausente | Profundo | **Profundo e explicado** |
| Curva de aprendizado | Baixa | Alta | **Baixa** |
| Foco | Hábito | Pesquisa | **Entendimento** |

---

## 5. Arquitetura do produto (pilares)

A navegação principal continua com **Início · Bíblia · Workspace**. Os
pilares abaixo são organização interna da empresa, não novos itens de menu.

### Pilar A — Ler (Bíblia)
Leitor, capítulos, versículos, originais, áudio, offline.
**Evoluções:** comparação de traduções lado a lado, interlinear palavra a
palavra, áudio sincronizado, modo foco, modo apresentação (projetar em
culto/aula), introdução de cada livro no topo do capítulo 1.

### Pilar B — Entender (Biblioteca)
Dicionário, personagens, lugares/mapas, linha do tempo, temas, artigos,
introduções aos livros, comentário por versículo, referências cruzadas.
**Tudo acessível a partir do versículo** (painel lateral no desktop,
gaveta no celular).

### Pilar C — Estudar (Workspace)
Progresso, planos, criar plano, notas, grifos, favoritos, coleções, cadernos.
**Evoluções:** estudos guiados (roteiros de 4–8 semanas), caderno com blocos
(texto, versículo, pergunta, imagem), exportação PDF/DOCX/Markdown,
estatísticas pessoais, metas.

### Pilar D — Compartilhar (fase futura, reformulado)
Grupos de estudo reformulados (não é rede social). Antes de voltar, precisa de
desenho novo e aprovação explícita de produto. Enquanto isso: compartilhar
versículo como imagem, compartilhar plano/caderno por link somente leitura.

### Pilar E — Plataforma
Conta, sincronização, privacidade, apps (PWA → lojas), API pública de dados,
acessibilidade, desempenho.

---

## 6. Estrutura do site (mapa de URLs alvo)

```
/                                 Início (retomar leitura, plano do dia, versículo do dia)
/ler/                             Índice dos livros
/ler/{livro}/                     Introdução do livro + capítulos
/ler/{livro}/{cap}/               Leitor
/versiculos/{livro-cap-vs}/       Página do versículo (SEO)
/comparar/{livro}/{cap}/          Comparação de traduções            [novo]
/interlinear/{livro}/{cap}/       Interlinear palavra a palavra      [novo]

/biblioteca/                      Hub da biblioteca
/biblioteca/livros/{livro}/       Introdução: autor, data, contexto, esboço  [novo]
/dicionario/{termo}/              Verbetes (hebraico, grego, conceitos)
/lexico/hebraico/{strong}/        Léxico hebraico                    [novo, dados já existem]
/lexico/grego/{strong}/           Léxico grego                       [novo]
/personagens/{nome}/              Personagens bíblicos               [novo]
/mapas/{lugar}/                   Lugares
/linha-do-tempo/                  Linha do tempo
/temas/{tema}/                    Temas
/artigos/{slug}/                  Artigos
/estudos/{slug}/                  Estudos guiados (série de lições)  [novo]

/workspace/                       Progresso, planos, notas, coleções, cadernos
/planos/{slug}/                   Planos públicos
/conta/                           Perfil, configurações, sincronização, privacidade
/apoie/                           Apoio financeiro e transparência   [novo]
/sobre/                           Sobre, fontes, equipe editorial, contato [novo]
```

Regra: toda página de Biblioteca precisa listar os versículos relacionados, e
todo versículo citado precisa linkar para `/versiculos/...` (malha interna de
links = SEO + navegação de estudo).

---

## 7. Roadmap por fases

As datas são estimativas para uma equipe pequena (1–2 devs + editores
voluntários). Cada fase só termina quando os **critérios de saída** forem
cumpridos.

### Fase 1 — Fundação (meses 1–3)
Objetivo: base técnica e de marca para escalar sem dívida.

- [ ] **Domínio próprio** (ex.: `bibliaemcontexto.com.br`) com redirecionamento
      301 do `github.io`, atualização de `BASE_URL`, canonical e sitemap.
- [ ] **Parar de versionar páginas geradas** (`site/ler/`, `site/versiculos/`
      etc.): o deploy já gera tudo a partir do fonte. Adicionar ao `.gitignore`
      e, se necessário, limpar o histórico em operação planejada.
- [ ] **Métricas com privacidade** (ferramenta sem cookies, ex.: Plausible ou
      Umami auto-hospedado) + eventos de estudo (abrir capítulo, criar nota,
      concluir dia de plano). Atualizar a página de privacidade.
- [ ] **Google Search Console + Bing Webmaster**, dados estruturados revisados.
- [ ] **Páginas institucionais:** `/sobre/`, `/apoie/`, termos de uso,
      política de privacidade revisada (LGPD), contato.
- [ ] **Guia de estilo editorial** (tom, citação de fontes, como tratar
      divergências) em `docs/GUIA_EDITORIAL.md`.
- [ ] **Divisão do `build.py`** em módulos (`build/leitor.py`,
      `build/biblioteca.py`, `build/workspace.py`...) — hoje tem 1.700+ linhas.

**Critérios de saída:** domínio no ar, build e deploy sem páginas geradas no
Git, painel de métricas com 30 dias de dados, guia editorial aprovado.

### Fase 2 — Profundidade de conteúdo (meses 3–8)
Objetivo: cada capítulo ter pelo menos uma camada de estudo.

- [ ] **Introdução dos 66 livros** (autor, data, destinatários, contexto,
      esboço, temas, versículos-chave).
- [ ] **Léxico hebraico público** (`/lexico/hebraico/`) a partir das 462
      entradas existentes, crescendo para as palavras mais frequentes.
- [ ] **Léxico grego** com base em dados de domínio público/licença aberta.
- [ ] **Personagens bíblicos** — 150 principais, com linha do tempo e mapa.
- [ ] **Lugares** — de 22 para 150, com coordenadas e versículos.
- [ ] **Dicionário** — de 14 para 300 verbetes.
- [ ] **Referências cruzadas** em escala, usando base aberta (ex.: dados
      públicos do tipo Treasury of Scripture Knowledge) adaptada para a
      numeração da Almeida.
- [ ] **Artigos** — ritmo de 4 por mês, guiados por pesquisa de palavras-chave.
- [ ] **Painel de estudo no versículo**: originais, dicionário, referências,
      comentário, lugares e personagens em um só lugar.

**Critérios de saída:** 100% dos livros com introdução, 1.000+ páginas novas de
biblioteca indexadas, tráfego orgânico 3× o do início da fase.

### Fase 3 — Workspace de estudo (meses 6–12)
Objetivo: o usuário produz e volta.

- [ ] **Estudos guiados** (`/estudos/`): séries de lições com leitura,
      explicação, perguntas e anotação integrada. Começar com 6 séries.
- [ ] **Cadernos com blocos** e inserção de versículo com um toque.
- [ ] **Exportação** de notas/cadernos em PDF, DOCX e Markdown; exportação
      total da conta (JSON) para portabilidade.
- [ ] **Comparação de traduções** (Almeida 1911 + outras de domínio público ou
      licenciadas).
- [ ] **Interlinear** palavra a palavra com morfologia.
- [ ] **Lembretes** (notificação web/push) para plano de leitura.
- [ ] **Estatísticas pessoais** (livros lidos, mapa de leitura da Bíblia).
- [ ] **Compartilhar por link** (somente leitura) plano, coleção e caderno.

**Critérios de saída:** 25% dos usuários com conta usam o Workspace toda semana;
retenção D30 de quem começa plano ≥ 20%.

### Fase 4 — Distribuição e sustentabilidade (meses 10–18)
Objetivo: crescer além do Google e se sustentar.

- [ ] **App nas lojas** (Android via TWA/Capacitor a partir do PWA; iOS em
      seguida), com offline completo.
- [ ] **Programa de apoio** (doação única e mensal, transparência de custos).
- [ ] **Plano Igrejas/Ministérios**: planos coletivos, página da igreja,
      relatórios de engajamento agregados (sem dados pessoais).
- [ ] **Newsletter** semanal (versículo + estudo da semana).
- [ ] **API pública de dados** (somente conteúdo de domínio público/próprio)
      para desenvolvedores e parceiros.
- [ ] **Licenciamento de tradução moderna** (negociação com detentores de
      direitos).

**Critérios de saída:** custos operacionais cobertos por apoio recorrente;
app publicado com avaliação ≥ 4,5.

### Fase 5 — Comunidade reformulada (após fase 3, com aprovação)
Somente depois de desenho novo aprovado: grupos pequenos centrados em um plano
ou estudo guiado, com moderação, sem feed público. O código antigo
(`scripts/community.asset.js`) serve só como referência técnica.

---

## 8. Estratégia de conteúdo (redação)

### 8.1 Linhas editoriais
1. **Contexto de passagens famosas** ("João 3:16 no contexto") — maior volume
   de busca.
2. **Palavras originais** ("o que significa *hesed*") — diferencial.
3. **Temas da vida** (ansiedade, perdão, casamento) — porta de entrada.
4. **Introduções e panoramas** (livros, períodos, personagens).
5. **Ferramentas de estudo** (como estudar, como usar concordância).

### 8.2 Processo editorial
`Pauta → Pesquisa (fontes) → Rascunho → Revisão teológica → Revisão de texto
→ Dados JSON → Build → Publicação → Atualização anual`

- Cada peça tem **autor e revisor nomeados** e lista de fontes.
- Conteúdo entra como dado curado em `site/data/*.json` validado por
  `scripts/validate_data.py` (nunca HTML solto).
- **Conselho editorial** de 3–5 pessoas de tradições diferentes para revisar
  temas sensíveis.

### 8.3 Metas de volume (12 meses)

| Tipo | Hoje | Meta 12 meses |
|---|---|---|
| Introduções de livros | 0 | 66 |
| Artigos | 10 | 60 |
| Dicionário | 14 | 300 |
| Personagens | 0 | 150 |
| Lugares | 22 | 150 |
| Planos de leitura | 3 | 25 |
| Estudos guiados | 0 | 6 |
| Versículos com referências cruzadas | 39 | 20.000+ |

---

## 9. Tecnologia

### 9.1 Arquitetura alvo
Manter o modelo que funciona — **site estático + Supabase** — porque é barato,
rápido e seguro. Evoluir em pontos específicos:

| Tema | Hoje | Alvo |
|---|---|---|
| Hospedagem | GitHub Pages | Cloudflare Pages ou Netlify (sem limite de 1 GB, CDN global, redirecionamentos, cabeçalhos de segurança reais) |
| Artefatos gerados | Versionados no Git | Gerados só no CI |
| Build | `build.py` monolítico | Pacote `scripts/build/` modular + build incremental |
| Busca | Índice JSON no cliente | Índice fragmentado por livro (ou Pagefind) |
| Dados | JSON em `site/data/` | JSON curado + esquema validado (JSON Schema) |
| Conta | Supabase Auth | Igual, com RLS revisado a cada fase |
| Apps | PWA | PWA + TWA (Android) + Capacitor (iOS) |
| Observabilidade | Nenhuma | Métricas sem cookies + monitor de erros JS |

### 9.2 Qualidade
- Testes continuam obrigatórios no CI (`python -m pytest`).
- Orçamento de desempenho: página de capítulo < 100 KB de HTML+CSS no primeiro
  carregamento, LCP < 2,5 s em 4G.
- Acessibilidade: WCAG 2.1 AA (contraste, teclado, leitor de tela, RTL do
  hebraico).
- Decisões de arquitetura registradas em `docs/decisoes/NNN-titulo.md` (ADR).

---

## 10. Aquisição e crescimento

1. **SEO (canal nº 1):** páginas de versículo, capítulos, dicionário, lugares,
   personagens. Malha interna de links, dados estruturados, sitemaps por
   seção, títulos pensados para busca ("Salmo 23 explicado: contexto e
   significado").
2. **Compartilhamento:** imagem do versículo gerada no navegador, link do
   plano, convite para ler junto.
3. **Newsletter** e lembretes de plano.
4. **Parcerias** com igrejas, professores de EBD, seminários e criadores de
   conteúdo cristão (material gratuito para usarem em aula).
5. **Redes sociais:** cortes curtos de "palavra do original da semana".
6. **Lojas de apps** (fase 4).

---

## 11. Modelo de negócio

Princípio: **o texto e o estudo básico são gratuitos para sempre**.

| Fonte | Descrição | Fase |
|---|---|---|
| Apoio voluntário | Doação única/mensal com página de transparência de custos | 4 |
| Plano Apoiador | Benefícios de conforto (temas extras, exportação avançada, mais armazenamento), nunca conteúdo bíblico | 4 |
| Plano Igrejas | Planos coletivos, página da igreja, painel agregado | 4 |
| Materiais impressos/PDF | Estudos guiados em PDF diagramado | 4 |
| Licença da API/dados próprios | Para apps e editoras parceiras | 5 |

**Não faremos:** anúncios intrusivos, venda de dados, paywall sobre o texto.

**Formalização:** quando houver receita recorrente, abrir CNPJ (MEI → ME) ou
associação sem fins lucrativos, conforme o modelo escolhido; conta bancária
própria; contabilidade.

---

## 12. Métricas (painel da empresa)

| Nível | Métrica |
|---|---|
| North Star | Dias de estudo ativos por semana |
| Aquisição | Visitas orgânicas, páginas indexadas, CTR no Search Console |
| Ativação | % de visitantes que abrem 2+ capítulos ou usam uma ferramenta de estudo |
| Engajamento | Planos iniciados/concluídos, notas criadas, consultas ao original |
| Retenção | D7 / D30 de quem iniciou plano |
| Conta | Contas criadas, % com sincronização ativa |
| Qualidade | LCP, erros JS, testes no CI, notas de acessibilidade |
| Sustentabilidade | Apoiadores ativos, custo mensal vs. receita |

Revisão: **semanal** (engajamento) e **mensal** (painel completo).

---

## 13. Organização (como empresa)

### 13.1 Papéis (podem ser acumulados no início)
- **Produto (dono):** prioriza o roadmap, aprova escopo, guarda os princípios.
- **Engenharia:** build, front-end, Supabase, apps, CI.
- **Editorial:** pauta, redação, curadoria de dados.
- **Revisão teológica:** conselho editorial.
- **Design/UX:** jornadas, componentes, acessibilidade.
- **Crescimento:** SEO, newsletter, parcerias, redes.

### 13.2 Rituais
- **Planejamento mensal:** escolhe as entregas do mês dentro da fase.
- **Revisão semanal:** métricas + o que saiu + bloqueios.
- **Retro por fase:** o que manter, o que mudar.

### 13.3 Gestão do trabalho no GitHub
- Um **Milestone por fase** (Fase 1 … Fase 5).
- **Labels:** `pilar:ler`, `pilar:biblioteca`, `pilar:workspace`,
  `pilar:plataforma`, `tipo:conteudo`, `tipo:bug`, `tipo:melhoria`,
  `prioridade:alta|media|baixa`.
- Toda issue tem: problema, proposta, critério de aceite, arquivos afetados.
- Toda entrega é registrada em `REGISTRO_DE_ALTERACOES.md`.

---

## 14. Jurídico e conformidade

- **Textos bíblicos:** Almeida 1911, WLC e Nestle 1904 são domínio público.
  Traduções modernas (ARA, ARC revisada, NVI, NAA, NVT etc.) **exigem licença**
  — não publicar sem contrato.
- **Dados de terceiros** (léxicos, mapas, referências cruzadas): só usar com
  licença compatível e registrar em `site/data/sources.json`.
- **LGPD:** base legal, exportação e exclusão de conta funcionais, política de
  privacidade clara, encarregado (DPO) indicado quando houver receita.
- **Termos de uso** e política de conteúdo (para quando a comunidade voltar).
- **Marca:** verificar e registrar o nome no INPI quando o domínio for
  definido.

---

## 15. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Repositório e site estourarem limites do GitHub | Alto | Fase 1: parar de versionar gerados, migrar hospedagem |
| Conteúdo teológico contestado | Alto | Conselho editorial, fontes declaradas, apresentar posições |
| Falta de licença para traduções modernas | Médio | Começar com domínio público; negociar em paralelo |
| Dependência de uma pessoa | Alto | Documentação, ADRs, este plano, testes automatizados |
| Custos do Supabase com crescimento | Médio | Dados pesados no estático; Supabase só para dados do usuário |
| Concorrência de apps grandes | Médio | Diferencial claro: estudo + contexto + originais em PT |
| Vazamento de dados de usuário | Alto | RLS revisado, auditoria de segurança por fase, chaves fora do repositório |

---

## 16. Orçamento estimado (mensal, por fase)

| Item | Fase 1–2 | Fase 3–4 |
|---|---|---|
| Domínio | ~R$ 5 (R$ 40/ano) | ~R$ 5 |
| Hospedagem estática | R$ 0 (plano gratuito) | R$ 0–120 |
| Supabase | R$ 0 (gratuito) | ~R$ 130 (plano Pro) |
| Métricas sem cookies | R$ 0 (auto-hospedado) a ~R$ 50 | ~R$ 50 |
| E-mail/newsletter | R$ 0 | R$ 0–100 |
| Contas de desenvolvedor (lojas) | — | Google: taxa única ~US$ 25; Apple: ~US$ 99/ano |
| Revisão editorial | Voluntária | Remunerada por peça (definir) |

Valores aproximados; revisar antes de contratar.

---

## 17. Próximos 90 dias (backlog acionável)

Ordem sugerida — cada item vira uma issue:

1. Escolher e registrar domínio; configurar DNS e redirecionamento 301.
2. Mover `BASE_URL` para variável de ambiente no build.
3. Adicionar páginas geradas ao `.gitignore` e remover do índice do Git
   (o deploy já gera tudo).
4. Instalar métricas sem cookies e definir os eventos de estudo.
5. Search Console + sitemap por seção.
6. Criar `/sobre/` e `/apoie/` (apoie pode começar só com transparência).
7. Escrever `docs/GUIA_EDITORIAL.md`.
8. Dividir `scripts/build.py` em módulos, sem mudar a saída (testes provam).
9. Publicar `/lexico/hebraico/` com os dados existentes.
10. Criar esquema JSON para "introdução de livro" e publicar as 5 primeiras
    (Gênesis, Salmos, Isaías, João, Romanos).
11. Painel de estudo no versículo (unir originais, dicionário, referências e
    comentário).
12. Criar milestones e labels no GitHub conforme a seção 13.3.

---

## 18. Estado do plano

| Data | Fase | Situação |
|---|---|---|
| 2026-10-30 | — | Plano criado. Nenhum item iniciado. |

---

## 19. Como dar continuidade (para qualquer desenvolvedor ou ferramenta)

Este documento é o ponto de partida para quem assumir o projeto.

1. **Leia primeiro:** `README.md`, `CLAUDE.md` (diretrizes de produto e
   arquivos principais), `docs/ARCHITECTURE.md` e este plano.
2. **Regras que não podem ser quebradas:**
   - Navegação principal: só Início, Biblia e Workspace.
   - Sem recursos de IA para o usuário final.
   - Comunidade/Salas continua pausada até haver novo desenho aprovado.
   - Nunca editar arquivos gerados em `site/` (ler, versiculos, `app.js`,
     `study.js`, `sw.js`); editar as fontes em `scripts/` e rodar o build.
3. **Para pegar a próxima tarefa:** vá à seção 17 (próximos 90 dias) ou à fase
   atual na seção 7, escolha o primeiro item não marcado e transforme em issue
   com critério de aceite.
4. **Para validar qualquer mudança:**
   ```bash
   python scripts/build.py
   python -m pytest
   git diff --check
   ```
5. **Ao terminar uma entrega:** marque o item `[x]` na seção 7, adicione uma
   linha na seção 18 e registre em `REGISTRO_DE_ALTERACOES.md`.
6. **Conteúdo novo** sempre entra como JSON em `site/data/`, validado por
   `scripts/validate_data.py`, com fonte registrada.
7. **Decisões grandes** (hospedagem, licenças, retorno da comunidade, modelo
   de receita) exigem aprovação do dono do produto antes de implementar.
