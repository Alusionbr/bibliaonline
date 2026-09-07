# Codex agent policy

## Goal
Maintain product correctness and final quality while minimizing context growth and unnecessary GPT-6 Astra usage.

## Repository-specific context discipline
- Treat `CLAUDE.md` as authoritative product guidance, but do not repeatedly load it in full. Read only the section relevant to the current task and retain a concise working summary.
- Prefer source files in `scripts/` and manually maintained styles over generated output.
- Do not manually edit generated files under `site/ler/`, `site/versiculos/`, `site/assets/app.js`, `site/assets/study.js`, or `site/sw.js`; change their sources and rebuild.
- Do not scan `REGISTRO_DE_ALTERACOES.md` or large generated trees unless the task explicitly requires history/output inspection.
- Start with targeted filename/code searches and narrow file ranges. Expand only when evidence requires it.

## Model routing
When selectable subagents/models are available:
- **GPT-6 Astra**: architecture, product-direction conflicts, security/auth/Supabase design, hard cross-system bugs, destructive migrations, and final review of broad/high-risk changes.
- **GPT-5.6 Sol**: default implementation, refactors, normal debugging, test fixes, and code review.
- **GPT-5.6 Terra**: well-scoped implementation with clear acceptance criteria.
- **GPT-5.6 Luna**: repository reconnaissance, search, repetitive edits, formatting, small isolated fixes, and narrow verification.
- Never spend Astra on generated-file inspection, mechanical edits, broad file discovery, or formatting.
- If model-selectable subagents are unavailable, use the same staged workflow without claiming delegation occurred.

## Workflow
1. Identify the user-visible behavior and the smallest source-file scope.
2. Read the relevant `CLAUDE.md` section only when needed.
3. Inspect source files, not the whole generated site.
4. Make a concise plan for non-trivial work.
5. Implement with the least expensive reliable model.
6. Rebuild only when source changes require it.
7. Run targeted checks; for build/CSS/JS-source changes use the repository guidance (`python scripts/build.py`, `python -m pytest`, `git diff --check`) when available in the environment.
8. Use Astra for unresolved complexity or a high-risk final review.

## Quality gate
- Preserve the current product direction from `CLAUDE.md`.
- Do not re-enable paused community functionality or add end-user AI features unless explicitly requested.
- Do not weaken auth, privacy, validation, or tests to save tokens.
- Check the final diff for accidental generated noise and unrelated changes.
- Stop reopening unchanged files or rerunning broad checks once the relevant verification has passed and no unresolved risk remains.
