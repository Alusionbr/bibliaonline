# Guia editorial — Bíblia em Contexto

Regras para quem escreve ou revisa conteúdo do site: panoramas de livros,
verbetes de dicionário, léxico, lugares, temas, artigos e planos de leitura.

## 1. Tom e linguagem

- **Português do Brasil, claro e direto.** Escreva para um leitor curioso, não
  para um especialista. Termos técnicos (ex.: *paralelismo*, *massorético*) são
  bem-vindos, mas devem ser explicados na primeira vez que aparecem.
- **Frases curtas.** Um parágrafo trata de uma ideia.
- **Sem sermão e sem polêmica.** O site explica o texto e o contexto; não
  prega nem ataca tradições.
- **Sem exageros.** Evite "o maior", "o mais importante", "sem dúvida" quando
  não houver base.
- **Palavras originais em itálico na transliteração** (ex.: *hesed*) e com a
  escrita original quando houver campo para isso.

## 2. Divergências de interpretação

Quando estudiosos ou tradições discordam (autoria, data, sentido de uma
passagem), apresente as posições principais de forma justa:

> "A tradição atribui o livro a X. Muitos estudiosos modernos entendem que..."

- Não declare uma posição como a única possível.
- Não ridicularize nenhuma posição.
- Temas sensíveis (escatologia, sacramentos, gênero, política) passam
  obrigatoriamente pela revisão do conselho editorial.

## 3. Fontes

- Todo conteúdo deve se apoiar em fontes verificáveis: léxicos, introduções
  acadêmicas, atlas, comentários reconhecidos.
- Fontes de dados reutilizados (léxicos, mapas, referências cruzadas) precisam
  ter licença compatível e ser registradas em `site/data/sources.json`.
- **Não copie textos protegidos.** Resuma com suas palavras e cite a obra.
- Traduções bíblicas modernas (ARA, NVI, NAA, NVT etc.) são protegidas: só
  podem ser citadas dentro do limite legal e nunca publicadas por inteiro sem
  licença.

## 4. Numeração dos versículos

O texto hebraico (WLC) e a Almeida podem numerar diferente, principalmente nos
Salmos (o título conta como versículo 1 no hebraico) e em alguns capítulos de
profetas. O site segue a numeração do texto original. Antes de citar um
versículo, confira se a referência existe e tem texto em `site/data/verses.json`
— o `scripts/validate_data.py` acusa versículo-chave sem texto.

## 5. Formatos de conteúdo

### Panorama de livro (`site/data/book-intros.json`)

| Campo | Obrigatório | Orientação |
|---|---|---|
| `livro` | sim | Nome exatamente como em `BOOK_ORDER` (`scripts/build_config.py`). |
| `resumo` | sim | 1 frase, até ~40 palavras. |
| `autoria` | sim | Visão tradicional e, se houver, visão acadêmica. |
| `data` | sim | Faixa aproximada, indicando a visão quando houver divergência. |
| `destinatarios` | não | Para quem o livro foi escrito. |
| `genero` | não | Narrativa, poesia, profecia, carta, evangelho etc. |
| `contexto` | sim | 3 a 5 parágrafos curtos. |
| `esboco` | sim | Lista de `{"de": cap, "ate": cap, "titulo": "..."}`. |
| `temas` | sim | 4 a 6 temas. |
| `versiculos_chave` | sim | 4 a 6 referências que existam com texto. |
| `fontes` | não | Tipos de fonte consultados. |

### Verbete de dicionário (`site/data/glossary.json`)

Definição em 1 a 2 frases, mostrando o que a tradução portuguesa não capta.
Inclua 3 a 6 versículos onde a palavra aparece de forma significativa.

### Léxico hebraico (`site/data/hebrew-lexicon.json`)

Chave = número de Strong. Campo `pt` com o sentido básico, curto, separado por
vírgulas; use parênteses para a classe gramatical quando ajudar.

### Lugar (`site/data/places.json`)

Nome, tipo, região, descrição em 1 a 2 frases, coordenadas (latitude e
longitude decimais) e versículos.

### Artigo (`site/data/articles.json`)

Título que responda a uma busca real (ex.: "Salmo 23: contexto e
significado"), resumo de 1 frase, blocos `{"h": "subtítulo", "p": "texto"}`.
Ligue o artigo aos versículos citados pelo campo `artigos` em `verses.json`.

## 6. Fluxo de publicação

1. **Pauta** — definir o tema e a busca que ele atende.
2. **Pesquisa** — reunir e anotar as fontes.
3. **Rascunho** — escrever direto no JSON (ou num documento e depois passar).
4. **Revisão teológica** — obrigatória para temas sensíveis.
5. **Revisão de texto** — ortografia, clareza, tamanho.
6. **Validação** — `python scripts/validate_data.py`.
7. **Build e testes** — `python scripts/build.py` e `python -m pytest`.
8. **Registro** — anotar em `REGISTRO_DE_ALTERACOES.md`.

## 7. Correções

Erros apontados por leitores (botão de reportar problema) têm prioridade sobre
conteúdo novo. Corrija, registre a correção e, se o erro for de conteúdo,
revise as outras páginas que usaram a mesma fonte.
