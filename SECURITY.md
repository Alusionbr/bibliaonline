# Política de Segurança

Obrigado por ajudar a manter o **Bíblia em Contexto** seguro.

## Escopo

Este é um **site estático** publicado via GitHub Pages a partir da pasta
`site/`. Não há backend, banco de dados nem autenticação de usuários. Os dados
de estudo do usuário (anotações, grifos, preferências) ficam apenas no
`localStorage` do navegador — nunca são enviados a um servidor.

Por isso, a superfície de ataque é limitada principalmente a:

- conteúdo gerado (XSS via dados de entrada mal escapados);
- dependências da cadeia de build (`scripts/build.py`, GitHub Actions);
- configuração de publicação (GitHub Pages / workflows);
- recursos de terceiros carregados pelo site (fontes, imagens de manuscrito).

## Versões suportadas

Apenas a versão publicada a partir do branch `main` recebe correções de
segurança.

## Como relatar uma vulnerabilidade

**Não** abra uma issue pública para vulnerabilidades.

Prefira o canal privado do GitHub:

1. Acesse a aba **Security** do repositório.
2. Use **"Report a vulnerability"** (GitHub Private Vulnerability Reporting).

Inclua, se possível:

- descrição do problema e impacto;
- passos para reproduzir;
- página/arquivo afetado;
- sugestão de correção (opcional).

Faremos o possível para responder em até **7 dias úteis**.

## Boas práticas adotadas neste repositório

- `Content-Security-Policy` restritiva via `<meta>` em todas as páginas.
- `Referrer-Policy` conservadora.
- Todo conteúdo dinâmico é escapado (`html.escape`) no gerador.
- Workflows do GitHub Actions com permissões mínimas (`contents: read`) e
  sem persistência de credenciais no checkout.
- Análise estática contínua com **CodeQL** (Python + JavaScript).
- Atualização automática de dependências e actions com **Dependabot**.
- Links externos usam `rel="noopener"`.

## Fora de escopo

- Ausência de cabeçalhos HTTP que o GitHub Pages não permite definir
  (ex.: `X-Frame-Options`, `Strict-Transport-Security` próprio). Mitigações
  equivalentes via `<meta>` são aplicadas quando possível.
- Conteúdo de fontes externas de domínio público (texto bíblico, imagens de
  manuscrito) hospedado por terceiros.
