# Registro de Alteracoes

Este arquivo e o caderno de bordo do projeto. Toda alteracao relevante deve
ser registrada aqui antes do commit, junto com o que foi analisado, o que foi
mudado, como foi testado e qual commit publicou a mudanca.

## Protocolo de trabalho

1. Verificar `git status` antes de editar.
2. Ler o historico recente com `git log` e respeitar o que ja existe.
3. Entender os arquivos geradores antes de alterar HTML gerado.
4. Registrar a intencao da mudanca neste arquivo.
5. Alterar somente os arquivos necessarios.
6. Rodar o build/testes aplicaveis.
7. Registrar o resultado da validacao.
8. Fazer commit com mensagem clara e enviar ao GitHub quando aprovado.

## 2026-06-21 - Guia operacional para Claude/Codex

Pedido do usuario: entender se o projeto esta organizado para outros
desenvolvedores e criar um arquivo `CLAUDE.md` para uso com Claude e Codex.

Mudanca:

- Criado `CLAUDE.md` na raiz do repositorio.
- Documentada a estrutura do projeto, fluxo de build, testes, deploy,
  regras para nao editar arquivos gerados diretamente e checklist de validacao
  manual do site publicado.

Validacao:

- Documento criado sem alterar o pipeline de build.
- Nao exige rebuild do `site/`, pois e apenas documentacao.

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
