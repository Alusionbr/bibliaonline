# CLAUDE.md

## Direcao atual do produto

O site Biblia em Contexto deve evoluir de um repositorio de paginas biblicas para uma plataforma de estudo biblico. A Biblia continua sendo o centro; comunidade, biblioteca e workspace existem ao redor do texto, nao como rede social generica.

Nao adicionar recursos de IA para o usuario final. Evitar nomes como "IA Biblica", "Biblia com IA" ou "assistente IA".

## Arquivos principais

- `scripts/build.py`: estrutura HTML, rotas estaticas, navegacao e comportamento gerado.
- `scripts/app.asset.js`: JavaScript fonte copiado para `site/assets/app.js`.
- `scripts/auth.asset.js`: conta, login e sincronizacao Supabase.
- `site/assets/styles.css`: estilos editados manualmente.
- `site/`: saida publicada. Nao editar manualmente arquivos gerados em `site/ler/`, `site/versiculos/`, `site/assets/app.js`, `site/assets/study.js` ou `site/sw.js`.

## Areas de navegacao

A navegacao principal deve expor:

- Inicio
- Biblia
- Estudar
- Comunidade
- Workspace

A conta deve ficar restrita a:

- Meu perfil
- Configuracoes
- Sincronizacao
- Privacidade
- Sair

Ferramentas como estudos, biblioteca, favoritos, notas, colecoes, cadernos e salas devem aparecer em Estudar, Workspace ou Comunidade.

## Como testar

Depois de mudancas em build, CSS ou JS fonte:

```bash
python scripts/build.py
python -m pytest
git diff --check
```

Verificar manualmente:

- `site/index.html`
- `site/estudar/index.html`
- `site/workspace/index.html`
- `site/comunidade/index.html`
- `site/ler/joao/3/index.html`
- `site/versiculos/joao-3-16/index.html`
