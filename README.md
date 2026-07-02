# Bíblia em Contexto

Plataforma de estudo bíblico em português que coloca o texto no centro: leitura com os originais (hebraico e grego), ferramentas de estudo pessoais e Salas de Estudo em grupo.

**Status: Beta.** O site está em testes públicos no GitHub Pages.

## Recursos

- **Leitura**: 66 livros, capítulo a capítulo, com texto original (Hebraico WLC / Grego Nestle 1904), transliteração e tradução Almeida.
- **Estudo pessoal** (funciona sem conta, salvo no navegador): anotações por versículo, grifo de versículos e palavras (caneta marca-texto com cores), favoritos, planos de estudo e histórico de leitura.
- **Conta opcional**: sincroniza notas, grifos, favoritos e preferências entre dispositivos via Supabase.
- **Comunidade**: Salas de Estudo reais — criar sala, convidar por código, aprovar membros, tópicos e mensagens.
- **Progresso**: missões diárias, sequência de leitura e selos.

## Arquitetura

Site estático gerado por Python, publicado no GitHub Pages. Supabase (Postgres + Auth) atende conta, sincronização, comunidade e gamificação.

```
scripts/build.py         gera todo o HTML de site/ a partir de site/data/
scripts/*.asset.js       fontes JavaScript, copiadas para site/assets/ no build
site/assets/styles.css   estilos, editados à mão
site/data/               dados curados (versículos, artigos, planos)
site/                    saída publicada (páginas geradas não são editadas à mão)
docs/                    arquitetura, pipeline de dados e SQL do Supabase
tests/                   suíte pytest (build, dados, smoke test completo)
```

Regra de ouro: editar `scripts/*.asset.js`, nunca os `site/assets/*.js` gerados; nunca editar à mão as páginas geradas em `site/ler/`, `site/versiculos/` etc.

## Como desenvolver

```bash
pip install -r requirements-dev.txt
python scripts/build.py     # regenera o site
python -m pytest            # roda os testes
python -m http.server -d site   # serve localmente
```

Login e sincronização ficam inativos localmente por design: `site/assets/supabase-config.js` não está no repositório — o deploy o gera a partir do secret `SUPABASE_PUBLISHABLE_KEY`. Para testar com conta, crie o arquivo localmente com a URL e a publishable key do projeto.

## Deploy

Push na `main` dispara `.github/workflows/deploy.yml`: roda os testes (`tests.yml`), gera o `supabase-config.js` e publica `site/` no GitHub Pages. Build quebrado não é publicado.

## Banco de dados

Os esquemas e migrações do Supabase estão documentados em `docs/supabase-*.sql` (comunidade, gamificação, estado de estudo do usuário e endurecimento de segurança).

## Textos e licenças

Almeida 1911, Westminster Leningrad Codex e Nestle 1904 — todos em domínio público.

## Diretriz de produto

A Bíblia é o centro; comunidade, biblioteca e workspace existem ao redor do texto. O site não oferece recursos de IA para o usuário final.
