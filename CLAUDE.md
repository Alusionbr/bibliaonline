# CLAUDE.md

## Direcao atual do produto

O site Biblia em Contexto deve evoluir de um repositorio de paginas biblicas para uma plataforma de estudo biblico. A Biblia continua sendo o centro; biblioteca e workspace existem ao redor do texto, nao como rede social generica.

Comunidade/Salas de Estudo esta pausada por decisao de produto: sera reformulada antes de voltar ao site. O codigo fonte (`scripts/community.asset.js`, com integracao Supabase completa) continua no repositorio para a proxima versao, mas nao e mais gerado nem carregado (`build_community_js()` nao e chamado, sem `<script>` nem secao no Workspace). Nao reativar essa secao sem confirmar com o usuario — quando ela voltar, sera com um desenho novo, nao apenas religando o que existe.

Nao adicionar recursos de IA para o usuario final. Evitar nomes como "IA Biblica", "Biblia com IA" ou "assistente IA".

## Arquivos principais

- `scripts/build.py`: estrutura HTML, rotas estaticas, navegacao e comportamento gerado.
- `scripts/app.asset.js`: JavaScript fonte copiado para `site/assets/app.js`.
- `scripts/auth.asset.js`: conta, login e sincronizacao Supabase.
- `scripts/build_reference.py`: paginas de referencia da Biblioteca (`/temas/`, `/dicionario/`, `/mapas/`, `/lexico/hebraico/`) e o "Panorama do livro" exibido em `/ler/<livro>/`.
- `site/data/book-intros.json`: panorama curado de cada livro (validado por `scripts/validate_data.py`).
- `site/assets/styles.css`: estilos editados manualmente.
- `site/`: saida publicada. As paginas e JS gerados pelo build NAO sao mais versionados (ver `.gitignore`); o deploy gera tudo a partir das fontes. Rode `python scripts/build.py` antes de abrir o site localmente.
- `docs/PLANO_PLATAFORMA.md`: plano estrategico e roadmap por fases. Ao concluir um item, marcar `[x]` e atualizar a secao "Estado do plano".
- `docs/GUIA_EDITORIAL.md`: regras para escrever conteudo (verbetes, panoramas, artigos).

## Areas de navegacao

A navegacao principal deve expor apenas:

- Inicio
- Biblia
- Workspace

Estudar foi fundida como secao do Workspace (`#estudar`, com a aba "Criar
plano" embutida, e `#progresso`). O endereco antigo `/estudar/` segue
existindo como redirect (noindex) para essa secao e nao deve voltar a ser
pagina propria.

`/comunidade/` e `/comunidade/salas/` tambem seguem existindo como redirects
(noindex), mas agora apontam para `workspace/` (nao para uma secao
`#comunidade` — essa secao foi removida, ver "Direcao atual do produto").

A conta deve ficar restrita a:

- Meu perfil
- Configuracoes
- Sincronizacao
- Privacidade
- Sair

Ferramentas como estudos, biblioteca, favoritos, notas, colecoes e cadernos
devem aparecer nas secoes do Workspace.

## Como testar

Depois de mudancas em build, CSS ou JS fonte:

```bash
python scripts/build.py
python -m pytest
git diff --check
```

Verificar manualmente:

- `site/index.html`
- `site/workspace/index.html` (secoes #progresso e #estudar)
- `site/estudar/index.html` e `site/comunidade/index.html` (redirects)
- `site/ler/joao/3/index.html`
- `site/versiculos/joao-3-16/index.html`
