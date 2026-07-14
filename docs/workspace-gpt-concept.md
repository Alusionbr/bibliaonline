# Workspace Bíblico Adaptativo — esboço conceitual

Este documento não define uma implementação final. Ele organiza uma possível evolução do Workspace atual preservando a arquitetura existente, o conteúdo bíblico, a gamificação, as salas e o Supabase.

## Ideia central

Transformar o Workspace em uma central de estudo adaptativa. Em vez de apresentar muitas ferramentas independentes, o sistema monta uma próxima sessão curta com base no capítulo atual, histórico de leitura, notas, dúvidas e missões.

## Nova hierarquia

1. **Hoje** — mostra uma sessão recomendada, tempo estimado, sequência e missões.
2. **Ler** — mantém o modo de leitura atual, foco progressivo e marcação de capítulo.
3. **Trilhas** — combina leitura, contexto, palavras originais, conexões e revisão.
4. **Caderno vivo** — agrupa notas, perguntas e destaques por tema e referência.
5. **Mapa bíblico** — apresenta domínio por livros, capítulos, temas, personagens e lugares.
6. **Comunidade** — sugere salas relacionadas ao trecho estudado.
7. **Biblioteca** — reúne artigos, fontes, mapas, manuscritos e materiais salvos.

## Funcionalidades propostas

### Sessão inteligente

- Plano de 5, 10 ou 20 minutos.
- Retoma exatamente do último ponto significativo.
- Alterna leitura, contexto e revisão para evitar sobrecarga.
- Mostra o motivo de cada recomendação.

### Trilhas adaptativas

- Trilha por livro, tema, personagem ou pergunta.
- Próximo passo muda conforme erros, dúvidas e notas.
- Etapas: leitura, contexto, termos-chave, paralelos, síntese e aplicação.

### Caderno vivo

- Conecta anotações automaticamente por referência e assunto.
- Mantém perguntas abertas separadas de conclusões.
- Gera uma visão de temas recorrentes sem substituir a interpretação do usuário.

### Revisão espaçada

- Reapresenta conceitos estudados antes que sejam esquecidos.
- Usa cartões curtos, perguntas e referências cruzadas.
- Pode gerar missões reais de revisão, sem premiar cliques vazios.

### Mapa de domínio

- Visualização do progresso por livro e capítulo.
- Diferencia leitura superficial, estudo contextual e revisão concluída.
- Permite localizar lacunas sem transformar a Bíblia em simples porcentagem.

### Assistente contextual

- Atua apenas sobre o trecho aberto.
- Distingue texto bíblico, contexto histórico, hipótese acadêmica e aplicação.
- Mostra fontes e níveis de confiança.
- Sugere perguntas melhores em vez de entregar respostas fechadas.

### Quests com propósito

- Recompensam leitura, síntese, conexão e revisão.
- Evitam XP por ações repetitivas sem valor.
- Conquistas refletem hábitos reais: constância, contexto, comparação e participação.

## Reuso da base existente

O conceito aproveita recursos já presentes no projeto:

- modo de leitura e foco progressivo;
- progresso por capítulo;
- gamificação autoritativa via `record_event`;
- missões, níveis e medalhas;
- notas, destaques e favoritos;
- salas abertas relacionadas a referências bíblicas;
- geração estática pelo `scripts/build.py`;
- assets separados em `scripts/*.asset.js`.

## Estratégia segura de implementação

1. Validar primeiro a nova navegação e hierarquia.
2. Reusar dados existentes antes de criar novas tabelas.
3. Implementar o painel **Hoje** como camada de composição.
4. Adicionar trilhas e revisão espaçada em etapas pequenas.
5. Manter cada módulo removível por feature flag.
6. Não alterar o branch principal até revisão visual e funcional.

## Protótipo

Arquivo: `prototypes/workspace-gpt/index.html`

O protótipo é estático, responsivo e isolado. Serve para avaliar direção visual, organização, densidade e prioridade das funcionalidades antes de integrar ao gerador real.