# Ideias de Melhorias para Estudos Bíblicos

Documento com sugestões de funcionalidades para melhorar a experiência de estudo no site **Biblia em Contexto**.

## Status Atual

O site já oferece:
- ✅ Navegação por livros, capítulos e versículos
- ✅ Transliteração do original (hebraico/grego)
- ✅ Anotações persistidas em localStorage
- ✅ Marca-texto (destaques em cores)
- ✅ Grifos de versículos
- ✅ Busca por texto
- ✅ Compartilhamento de versículos
- ✅ Pool de versículos aleatórios
- ✅ Artigos relacionados
- ✅ Linha do tempo

## Melhorias Propostas

### 1. **Referências Cruzadas (Cross-references)**
**Prioridade:** Alta
- Adicionar links para versículos relacionados automaticamente
- Versículos que citam ou ecoam outros
- Implementação: Enriquecer `site/data/*.json` com matriz de referências

**Benefício:** Usuários descobrem conexões entre passagens sem sair da página.

---

### 2. **Modo Escuro / Tema Customizável**
**Prioridade:** Alta
- Tema escuro nativo (melhor para leitura noturna)
- Tamanho de fonte ajustável
- Espaçamento entre linhas configurável
- Persistência em localStorage

**Benefício:** Conforto visual e acessibilidade, especialmente em celulares.

---

### 3. **Histórico de Leitura**
**Prioridade:** Média
- Rastrear posição de leitura (última página lida, scroll position)
- "Continue de onde parou" ao voltar
- Histórico clicável dos últimos 20 capítulos
- Sincronização entre abas

**Benefício:** Fluxo contínuo sem perder o lugar.

---

### 4. **Planos de Leitura Estruturados**
**Prioridade:** Média
- Planos prontos (Novo Testamento em 40 dias, Pentateuco, etc)
- Marcação de "lido hoje"
- Progresso visual (barra de conclusão)
- Notificações do navegador para lembrar (opcional)

**Implementação:** Adicionar `reading_plans` em `site/data/` como JSON estruturado.

**Benefício:** Leitura sistemática e motivação via acompanhamento.

---

### 5. **Dicionário e Glossário Integrado**
**Prioridade:** Média
- Popup ao clicar em palavra (termos teológicos, locais, pessoas)
- Explicações breves sem sair da página
- Mapa de personagens bíblicos
- Timeline de eventos principais

**Implementação:** Enriquecer dados com glossário em `site/data/`.

**Benefício:** Compreensão mais profunda do contexto.

---

### 6. **Mapas e Contexto Geográfico**
**Prioridade:** Baixa
- Mapa interativo dos locais mencionados
- Jornadas de personagens principais
- Contexto histórico-geográfico
- Recursos existentes (seria extensão da linha do tempo)

**Benefício:** Visualização de narrativas e deslocamentos.

---

### 7. **Exportação Avançada de Anotações**
**Prioridade:** Média
- Exportar anotações e grifos em PDF
- Formato Word editável
- Filtrar por livro/período
- QR code para compartilhar lista de versículos

**Implementação:** JavaScript client-side (sem backend).

**Benefício:** Portabilidade e compartilhamento de estudos.

---

### 8. **Comentários Teológicos Curtos**
**Prioridade:** Média-Baixa
- Insights breves por versiculo (max 3 linhas)
- Diferentes perspectivas (literal, contextual, prático)
- Autor/fonte do comentário
- Colapsível por padrão

**Implementação:** Adicionar campo `commentary` em `site/data/verses`.

**Benefício:** Interpretação contextualizada sem saturar a página.

---

### 9. **Busca Avançada**
**Prioridade:** Baixa
- Busca por palavra-chave booleana (AND, OR, NOT)
- Filtrar por livro/período
- Buscar por tema ou tópico
- Histórico de buscas (localStorage)

**Benefício:** Pesquisa mais precisa em textos longos.

---

### 10. **Suporte Offline**
**Prioridade:** Baixa
- Service Worker para cache inteligente
- Sincronizar anotações quando voltar online
- Indicador visual do status offline
- Download parcial de livros

**Benefício:** Uso em transporte/locais sem conexão.

---

### 11. **Versão em Áudio**
**Prioridade:** Muito Baixa
- Leitura em voz alta com Web Audio API
- Sincronização com o texto
- Velocidade ajustável
- Suporte apenas em navegadores modernos

**Benefício:** Acessibilidade e aprendizado auditivo.

---

### 12. **Comparação entre Versões**
**Prioridade:** Muito Baixa
- View lado-a-lado de traduções diferentes
- Highlight de diferenças
- Requer múltiplas traduções no `site/data/`

**Benefício:** Estudo comparativo (foco em português).

---

### 13. **Índice de Tópicos / Temas**
**Prioridade:** Média
- Agrupar versículos por tema (Amor, Fé, Perdão, etc)
- Navegação visual
- Links para passagens relacionadas

**Implementação:** Enriquecer `site/data/` com mapeamento temático.

**Benefício:** Estudo temático, não apenas sequencial.

---

### 14. **Comparações com Outros Versículos**
**Prioridade:** Baixa
- "Versículos paralelos" (Mateus vs Lucas, Reis vs Crônicas)
- Lado-a-lado
- Diferenças destacadas

**Benefício:** Pesquisa de variações textinais.

---

### 15. **Estatísticas Pessoais**
**Prioridade:** Muito Baixa
- Livros mais lidos
- Versículos mais anotados
- Palavras mais destacadas
- Dashboard resumido

**Benefício:** Reflexão sobre padrões de estudo.

---

## Matriz de Priorização

| Funcionalidade | Impacto | Dificuldade | Prioridade |
|---|---|---|---|
| Referências Cruzadas | Alto | Médio | 🔴 Alta |
| Modo Escuro | Alto | Baixo | 🔴 Alta |
| Histórico de Leitura | Alto | Baixo | 🟡 Média |
| Planos de Leitura | Muito Alto | Médio | 🟡 Média |
| Dicionário Integrado | Alto | Alto | 🟡 Média |
| Exportação de Anotações | Médio | Médio | 🟡 Média |
| Mapas Geográficos | Médio | Alto | 🟢 Baixa |
| Comentários Teológicos | Alto | Muito Alto | 🟢 Baixa |
| Busca Avançada | Médio | Médio | 🟢 Baixa |
| Suporte Offline | Médio | Médio | 🟢 Baixa |
| Índice de Tópicos | Alto | Médio | 🟡 Média |

## Próximos Passos Recomendados

1. **Curto prazo (1-2 semanas):**
   - [ ] Implementar Modo Escuro
   - [ ] Adicionar Histórico de Leitura

2. **Médio prazo (1-2 meses):**
   - [ ] Referências Cruzadas
   - [ ] Planos de Leitura básicos
   - [ ] Índice de Tópicos

3. **Longo prazo:**
   - [ ] Comentários Teológicos
   - [ ] Dicionário/Glossário
   - [ ] Mapas e Contexto

## Notas para Implementação

- **Dados:** Usar arquitetura existente em `site/data/` para não quebrar build
- **Performance:** Priorizar carregamento rápido (site estático)
- **Armazenamento:** Continuar usando `localStorage` para dados de usuário
- **Compatibilidade:** Manter suporte a navegadores mais antigos
- **Testes:** Adicionar testes em `tests/` para novas funcionalidades

---

**Última atualização:** 2026-06-23
**Status:** Documento de propostas e ideias
