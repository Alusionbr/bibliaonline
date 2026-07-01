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

## Dados por usuario (privados, RLS por dono)

- `public.user_gamification` — XP, nivel, streak, ultimo dia ativo.
- `public.user_mission_progress` — progresso por missao e por dia.
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
- **Missoes de leitura/meditacao**: creditadas por eventos explicitos que o
  `app.asset.js` envia via `gameRecord('read_chapters' | 'meditate')`.
- **Medalhas**: avaliadas a partir de contagens de vida, streak e missoes
  concluidas. Ao logar, o modulo puxa do servidor e mantem o maior valor, para
  nao perder progresso entre aparelhos.

Tudo e best-effort e envolto em try/catch: sem login ou sem rede, o site
continua funcionando e o progresso fica salvo localmente.

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
