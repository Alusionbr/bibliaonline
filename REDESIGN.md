# Redesign da jornada de leitura

A home e o Workspace agora destacam a próxima leitura. O usuário pode escolher um plano, acompanhar dias concluídos e abrir cada leitura. O leitor usa uma coluna de texto no celular e ferramentas laterais no desktop, com conclusão conectada ao progresso existente.

## Arquivos fonte

- `scripts/build.py`: estrutura e geração das páginas.
- `scripts/journey.asset.js`: jornada, escolha de plano e conclusão de capítulo.
- `scripts/app.asset.js`: retomada da última leitura.
- `scripts/sw.asset.js`: cache do novo módulo e catálogo de planos.
- `site/assets/styles.css`: estilos responsivos e temas.

Os HTMLs em `site/` foram regenerados. Não editar esses HTMLs manualmente.

## Validar

```sh
python scripts/build.py
python -m pytest -q
python -m http.server 4173 --bind 127.0.0.1 --directory site
```

Validação realizada: build completo, 98 testes passando, dados curados válidos e revisão visual em 320, 390 e 1440 pixels, incluindo os temas claro, sépia e escuro. Foram verificados conclusão de capítulos, retomada da leitura e atualização da jornada. A sincronização autenticada e aparelhos físicos não foram testados.

O fluxo de publicação agora gera o site a partir dos arquivos fonte antes de configurar o cliente Supabase e enviar o artefato ao GitHub Pages. O PR contém os arquivos fonte; as páginas geradas são produzidas no build.

A seleção do plano é uma preferência local (`bec.journeyPlan`); os dados de estudo continuam nos formatos existentes. Pausar a leitura não apaga o progresso. A prévia usa apenas o armazenamento local, sem chaves de produção.
