# Gamificacao, missoes diarias e papeis

Fundacao da experiencia de estudo com recompensas, pensada para ser barata
(roda no Supabase existente) e facil de ajustar por humanos.

## Fonte da verdade

O catalogo de missoes e medalhas vive no banco, nao no codigo:

- `public.badges` — catalogo de medalhas (leitura publica).
- `public.daily_missions` — catalogo de missoes diarias (leitura publica).

Para mudar textos, icones, metas ou pontos, edite essas tabelas. O front usa
o catalogo do banco quando ha conexao e cai para um espelho embutido em
`scripts/gamification.asset.js` (constante `FALLBACK`) quando offline. Mantenha
os dois em sincronia; o SQL de seed esta em `docs/supabase-gamification.sql`.

## Missoes semanais

Alem das diarias, ha um catalogo de missoes semanais em `public.weekly_missions`
(mesmo padrao de RLS: leitura publica, escrita por staff). O fallback embutido
fica em `scripts/gamification.asset.js` (`FALLBACK.weekly`) e o SQL em
`docs/supabase-gamification-weekly.sql`. Elas reiniciam a cada semana ISO
(`YYYY-Www`) e acumulam progresso ao longo da semana, com baseline proprio
(`weekBase`), separado do baseline diario.

## Dados por usuario (privados, RLS por dono)

- `public.user_gamification` — XP, nivel, streak, ultimo dia ativo.
- `public.user_mission_progress` — progresso por missao diaria e por dia.
- `public.user_weekly_mission_progress` — progresso por missao semanal e por semana.
- `public.user_badges` — medalhas conquistadas.

Todas seguem o mesmo padrao de RLS de `user_study_state`: o dono le/escreve
apenas a propria linha (`(select auth.uid()) = user_id`), `anon` sem acesso.

## Papeis de plataforma

- `public.staff` — administradores da plataforma (ja existia).
- `public.profiles.platform_role` — `user` (padrao), `moderator` ou `admin`.
- `public.is_platform_mod()` — helper usado nas politicas de escrita dos
  catalogos; retorna verdadeiro para moderador/admin/staff.

Papeis por grupo continuam em `group_members.role` (`admin`/`moderator`/`member`).

## Como o progresso e calculado (client-side)

`scripts/gamification.asset.js` (`window.BEC_GAME`):

- **Streak**: abrir o site conta como dia de estudo; dias consecutivos somam,
  um dia pulado reinicia. Guardado em `bec.game` (localStorage) e sincronizado.
- **Missoes de nota/favorito/grifo**: creditadas comparando as contagens do
  localStorage com o baseline do inicio do dia (so conta atividade nova de hoje).
- **Missao de leitura**: creditada por evento real — abrir o capitulo nao conta;
  a missao avanca quando o usuario marca um trecho como lido (`bec.readingRanges`,
  uma vez por capitulo por dia via `gameRecord('read_chapters')`).
- **Missao de meditacao**: creditada quando o usuario abre um versiculo aleatorio
  para meditar (`gameRecord('meditate')`).
- **Medalhas**: avaliadas a partir de contagens de vida, streak e missoes
  concluidas. Ao logar, o modulo puxa do servidor e mantem o maior valor, para
  nao perder progresso entre aparelhos.

Tudo e best-effort e envolto em try/catch: sem login ou sem rede, o site
continua funcionando e o progresso fica salvo localmente.

## Fonte da verdade autoritativa (servidor)

Para o usuario logado, XP/missoes/medalhas passam a ser **derivados no servidor**
a partir de eventos validados, evitando que o front forje progresso pelo
devtools. Ver `docs/supabase-gamification-authoritative.sql`:

- `public.user_events` — log append-only, escrito **so** pela RPC.
- `public.record_event(metric, dedup_key, payload)` (SECURITY DEFINER) — valida
  a metrica, registra o evento (idempotente por `dedup_key`) e recomputa.
- `public.recompute_gamification(uid)` — deriva progresso diario/semanal, streak,
  medalhas e o XP (= pontos de missoes concluidas + medalhas, com piso `legacy_xp`).

O cliente faz **dual-write**: mantem o motor local para a UI instantanea e para
visitante/offline, e emite o evento real via `record_event` quando logado,
adotando os valores autoritativos devolvidos. A fase final (revogar a escrita
direta nas tabelas) e uma decisao humana, aplicada so depois de validar a RPC em
producao.

## Selo Beta

`profiles.is_beta` (padrao `true`) marca contas em teste. O front mostra:

- um **chip** ("Beta teste", "Moderador" ou "Admin") no menu da conta e ao lado
  do botao Entrar;
- um **banner** global de versao de testes, dispensavel (`bec.betaDismiss`).

## Proximas fases sugeridas

- Ligar a Comunidade/Salas reais (`groups`, `group_members`, `group_plans`) a
  UI, concedendo a medalha `comunidade` ao entrar numa sala.
- Missoes semanais e missoes de comunidade (estudo em grupo).
- Painel de administracao/moderacao usando `platform_role` e `staff`.
- Ativar no painel Auth: leaked password protection e senha minima >= 8.
