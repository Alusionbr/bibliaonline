# Registro de Alteracoes

Este arquivo e o caderno de bordo do projeto. Toda alteracao relevante deve
ser registrada aqui antes do commit, junto com o que foi analisado, o que foi
mudado, como foi testado e qual commit publicou a mudanca.

## Salas de Estudo reais (ligacao Comunidade) - 2026-07-01

Intencao: ligar a pagina /comunidade/salas/ ao banco real (tabela `groups` e
RPCs), saindo dos dados demonstrativos.

Bug encontrado e corrigido (`docs/supabase-fix-join-group.sql`):

- `join_group()` falhava sempre com "column reference group_id is ambiguous"
  (coluna OUT colidia com a coluna no ON CONFLICT). Ninguem conseguia entrar
  numa sala. Corrigido com `#variable_conflict use_column`, API preservada.

Mudancas:

- `scripts/community.asset.js` (novo → `assets/community.js`): app das Salas —
  listar minhas salas, criar sala, entrar por codigo, ver participantes,
  aprovar/recusar (admin), definir moderador, remover, criar discussoes e
  responder. Tudo via cliente Supabase (`window.BEC_ACCOUNT`) com RLS.
- `scripts/build.py`: `/comunidade/salas/` agora renderiza `[data-community-app]`
  em vez de salas fixas; registra `community.js`.
- `scripts/gamification.asset.js`: novo `BEC_GAME.grant()` para conceder a
  medalha `comunidade` ao criar/entrar numa sala.
- `site/assets/styles.css`: estilos das salas, membros, discussoes e posts.

Teste ponta a ponta no banco (transacao revertida, nada persistido):
criar sala → topico → post → entrar por codigo (pendente, RLS bloqueia
topicos) → admin aprova → membro ativo ve topicos e responde. Passou.
`pytest` 84 testes (novo `test_salas_de_estudo_reais`). `git diff --check` OK.

## Gamificacao, selo Beta e revisao do banco - 2026-07-01

Analise do banco (projeto Supabase `pxqhpntifbtjaoqtirao`):

- O backend colaborativo (grupos, membros com papeis, topicos, posts, notas,
  comentarios, planos, feed, sugestoes, staff, audit_log, profiles,
  user_study_state) ja existia e estava mais completo que o front. RLS ligada,
  funcoes `SECURITY DEFINER` validando `auth.uid()` e rate-limit (`rl_guard`).
- Causa dos "bugs quando logado": o front so fazia login + sincronizava
  `user_study_state`. Nao lia/completava `profiles`, nao mostrava Beta e a
  Comunidade era estatica (dados demonstrativos), sem ligacao com `groups`.
- Faltava toda a gamificacao (missoes, medalhas, XP/streak) e um papel de
  moderador de plataforma.

Mudancas aplicadas:

- Banco (aditivo, reversivel — `docs/supabase-gamification.sql`):
  `badges`, `user_badges`, `daily_missions`, `user_mission_progress`,
  `user_gamification`, `profiles.platform_role` e `is_platform_mod()`, com RLS,
  grants e seed (11 medalhas, 5 missoes).
- Seguranca (`docs/supabase-security-hardening.sql`): revogado `EXECUTE` de
  `anon` nas RPCs de escrita e nas funcoes de trigger/auditoria, sem quebrar
  RLS (helpers usados por politicas mantem `EXECUTE`). Avisos de funcao
  executavel por `anon` cairam de ~22 para 4 (helpers de RLS, intencionais).
- Front:
  - `scripts/auth.asset.js`: carrega `profiles` apos login e expoe
    `window.BEC_ACCOUNT` + evento `bec:account`; chip Beta/Moderador/Admin.
  - `scripts/gamification.asset.js` (novo → `assets/game.js`): missoes,
    medalhas, streak e XP; sync best-effort ao Supabase; funciona offline.
  - `scripts/app.asset.js`: envia atividade (`read_chapters`, `meditate`).
  - `scripts/build.py`: registra `game.js`, banner Beta global, selo da conta
    e painel de Progresso no Workspace.
  - `site/assets/styles.css`: estilos do banner, chips, missoes e medalhas.
  - `docs/gamification.md`: documentacao da fundacao.

Como testado:

- `python scripts/build.py` (OK), `python -m pytest` (83 passam, novo teste
  `test_gamificacao_e_beta`), `git diff --check`.
- Supabase: migracao aplicada, seed confirmado (11 badges / 5 missions),
  security advisor reexecutado.

Pendente (proxima fase): ligar Comunidade/Salas reais a UI; ativar no painel
Auth leaked password protection e senha minima >= 8.

## Plataforma de estudo biblico - 2026-07-01

Intencao:

- Reorganizar a interface para parecer uma plataforma de estudo biblico, com a
  Biblia no centro e areas claras: Inicio, Biblia, Estudar, Comunidade e
  Workspace.
- Tirar ferramentas de estudo do contexto da conta e mover a descoberta visual
  para Estudar, Workspace, Biblioteca, Colecoes, Cadernos e Salas de Estudo.
- Manter a conta simples: Meu perfil, Configuracoes, Sincronizacao,
  Privacidade e Sair.
- Nao criar recursos de IA para usuario final.

Arquivos alterados:

- `scripts/build.py`: nova navegacao, barra inferior mobile, home em formato de
  painel, paginas `/estudar/`, `/workspace/`, `/comunidade/`,
  `/comunidade/salas/`, `/biblioteca/`, `/colecoes/`, `/cadernos/` e
  `/privacidade/`, alem de Mapa de Estudos e Mesa de Estudo em paginas de
  livro/capitulo/versiculo.
- `scripts/app.asset.js`: primeira versao local de Criar Plano usando
  `localStorage`.
- `scripts/auth.asset.js`: menu da conta simplificado.
- `site/assets/styles.css`: estilos mobile-first para hubs, cards, mapa,
  mesa de estudo e navegacao inferior.
- `tests/test_build_smoke.py`: cobertura para navegacao, paginas novas,
  sitemap, conta simples e ausencia dos nomes proibidos de IA no HTML gerado.
- `CLAUDE.md`: direcao de produto e comandos de validacao.
- `docs/supabase-community-schema.md`: proposta nao destrutiva para tabelas de
  comunidade/workspace em fase futura.

Decisoes de produto:

- Comunidade deve ser organizada por conteudo estudado, usando Salas de Estudo
  em vez de grupos.
- Perfil passa a ser perfil de estudo, sem seguidores, seguindo ou ranking por
  curtidas.
- Mapa de Estudos e Mesa de Estudo comecam como blocos estruturados com dados
  demonstrativos, prontos para substituir por dados reais via Supabase depois.
- Criar Plano comeca funcional no navegador, sem alterar banco.

Como testar:

```bash
python scripts/build.py
python -m pytest
git diff --check
```

Verificacao manual sugerida:

- `site/index.html`
- `site/estudar/index.html`
- `site/workspace/index.html`
- `site/comunidade/index.html`
- `site/ler/joao/3/index.html`
- `site/versiculos/joao-3-16/index.html`

Proxima fase:

- Conectar Mapa de Estudos, Salas, Colecoes, Cadernos e Planos a tabelas reais
  do Supabase com RLS revisada.
- Implementar moderacao, privacidade por sala e progressos reais.
- Refinar visualmente as paginas de leitura com ferramentas contextuais por
  selecao de versiculo.

## Protocolo de trabalho

1. Verificar `git status` antes de editar.
2. Ler o historico recente com `git log` e respeitar o que ja existe.
3. Entender os arquivos geradores antes de alterar HTML gerado.
4. Registrar a intencao da mudanca neste arquivo.
5. Alterar somente os arquivos necessarios.
6. Rodar o build/testes aplicaveis.
7. Registrar o resultado da validacao.
8. Fazer commit com mensagem clara e enviar ao GitHub quando aprovado.

## Estado atual - 2026-06-17

- Repositorio: `Alusionbr/bibliaonline`
- Branch principal: `main`
- Site publicado: `https://alusionbr.github.io/bibliaonline/`
- Checkout local: `C:\Users\Beto\Downloads\biblia`
- Estado antes deste registro: `git status --short` limpo.
- Commit sincronizado: `4d79fa398e` (`origin/main`)

### Historico recente observado

- `4d79fa398e` - merge do PR #11.
- `dc7bacf906` - ordenacao de livros e pagina Linha do tempo.
- `bde9f1cc01` - ajustes iOS, painel de ferramentas e exportacao de notas.
- `37e751d309` - cartao de compartilhamento, ferramentas ocultas, navegacao entre livros, confirmacao de exclusao, bloqueio de IAs e ajuste do modo noturno.
- `4827047beb` - caneta marca-texto, leitura, doacao e versiculo aleatorio.
- `bdf86f266e` - cache-busting de assets.
- `7b9db48982` - marca-texto por selecao e copia com nota.

### Estrutura respeitada

- `scripts/build.py` e o gerador central do site estatico.
- `site/assets/app.js` e gerado pelo `build.py`.
- `site/assets/study.js` tambem e gerado pelo `build.py`.
- Paginas em `site/versiculos/` e `site/ler/` sao HTML gerado; evitar edicao manual direta nelas.
- O deploy roda pelo GitHub Actions publicando a pasta `site/` no GitHub Pages.

### Proxima solicitacao em analise

Pedido do usuario: adicionar falas/audio para textos em hebraico/original e
portugues, sem interferir em direitos autorais, e permitir salvar favoritos
para aparecerem na pagina inicial.

Direcao tecnica preliminar:

- Usar `speechSynthesis` do navegador para leitura em voz alta, evitando
distribuir arquivos de audio gravados de terceiros.
- Salvar favoritos em `localStorage`, seguindo o padrao ja usado por
anotacoes, marca-texto, ultimo texto lido e preferencias.
- Integrar os botoes pelo `scripts/build.py`, nao editando paginas geradas
uma a uma.
- Antes de implementar, mapear o comportamento atual de `app.js`, `study.js`
e das paginas de versiculo/capitulo.

## Analise tecnica - audio e favoritos - 2026-06-17

Estado antes de editar:

- `git status --short` limpo.
- Branch `main` sincronizada com `origin/main`.
- Commit base: `0a84978398` (`Adiciona registro permanente de alteracoes`).

Arquivos analisados:

- `scripts/build.py`: gera as paginas estaticas, `site/assets/app.js` e
  `site/assets/study.js`.
- `site/assets/app.js`: contem busca, rolagem infinita, ferramentas de leitura,
  continuar lendo, versiculo aleatorio e ordenacao de livros.
- `site/assets/study.js`: contem anotacoes, marca-texto e exportacao, usando
  `localStorage` com prefixo `bec.*`.
- `tests/test_build_smoke.py`: cobre o build integrado e verifica recursos
  gerados em HTML/JS.

Decisoes:

- Audio: usar Web Speech API (`speechSynthesis`) no navegador. Nao hospedar nem
  redistribuir arquivos de audio de terceiros.
- Idiomas de leitura: `he-IL` para hebraico/aramaico, `el-GR` para grego,
  `pt-BR` para portugues.
- Favoritos: salvar em `localStorage` como `bec.favs`, separado de `notes`,
  `vhl` e `whl`.
- UI: adicionar botoes pequenos nos versiculos:
  - `Ouvir original`
  - `Ouvir PT` quando houver texto em portugues
  - `Favoritar`
- Home: mostrar uma secao compacta de favoritos quando houver itens salvos.
- Integracao com rolagem infinita: o handler de clique deve ser delegado no
  documento, funcionando tambem para versiculos inseridos dinamicamente.
- Implementacao deve acontecer no `scripts/build.py`, com regeneracao dos
  assets e paginas pelo build. Nao editar manualmente HTML gerado.

### Implementacao realizada

- `scripts/build.py`
  - adicionados helpers para idioma de fala, botoes de audio e botao de
    favorito;
  - paginas individuais de versiculo passaram a receber `Ouvir original`,
    `Ouvir PT` quando houver traducao, e `Favoritar`;
  - paginas de leitura por capitulo passaram a receber os mesmos controles em
    cada versiculo;
  - home passou a ter area `Favoritos`, exibida apenas quando houver favoritos
    salvos no navegador;
  - `build_app_js()` passou a gerar o JS de `speechSynthesis` e favoritos.
- `site/assets/styles.css`
  - estilos para botoes de audio/favorito e lista compacta de favoritos.
- `tests/test_build_smoke.py`
  - teste de fumaça para garantir os ganchos de audio/favoritos no HTML e JS.

### Validacao realizada

- `python scripts/build.py`: passou.
  - Resultado: `home + 31173 versiculos + 66 livros + 1189 capitulos + 10 artigos`.
- `python -m py_compile scripts\build.py`: passou.
- `python -m py_compile` nos scripts auxiliares principais: passou.
- Verificacao estatica:
  - `site/versiculos/genesis-1-1/index.html` contem `Ouvir original`, `Ouvir PT`
    e `Favoritar`;
  - `site/ler/genesis/1/index.html` contem botoes por versiculo;
  - `site/index.html` contem `favorite-home` e `favorite-list`;
  - `site/assets/app.js` contem `speechSynthesis`, `SpeechSynthesisUtterance` e
    `bec.favs`.

Validacao pendente/inconclusiva:

- `pytest` nao rodou porque o Python local nao tem `pytest` instalado.
- Tentativa de instalar `requirements-dev.txt` falhou por certificado SSL ao
  acessar o PyPI.
- Teste visual pelo navegador interno contra `localhost:8765` ficou inconclusivo:
  o servidor respondeu `200` via PowerShell, mas o navegador interno recebeu
  `ERR_CONNECTION_REFUSED`, aparentemente por isolamento de rede do ambiente.
