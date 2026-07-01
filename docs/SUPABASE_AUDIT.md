# Supabase Audit

Project: `bibliaonline` (`pxqhpntifbtjaoqtirao`)
Date: 2026-06-29

## Integration Added

- Added `public.user_study_state` for private per-user sync of:
  - notes
  - verse highlights
  - word highlights
  - favorites
  - reading/UI preferences
- Enabled RLS.
- Revoked public/anon access.
- Granted only `SELECT`, `INSERT`, `UPDATE`, `DELETE` to `authenticated`.
- Added ownership policies using `to authenticated` and `(select auth.uid()) = user_id`.

The SQL applied is recorded in [supabase-user-study-state.sql](supabase-user-study-state.sql).

## Update 2026-07-01 — gamification + hardening

- Added additive gamification/roles schema (see
  [supabase-gamification.sql](supabase-gamification.sql) and
  [gamification.md](gamification.md)): `badges`, `user_badges`,
  `daily_missions`, `user_mission_progress`, `user_gamification`,
  `profiles.platform_role`, `is_platform_mod()`. RLS enabled on all; catalogs
  are public-read, per-user tables are owner-only.
- Applied non-destructive hardening (see
  [supabase-security-hardening.sql](supabase-security-hardening.sql)): revoked
  `EXECUTE` from `anon` on write RPCs and from trigger/audit functions. RLS
  helper functions kept `EXECUTE` (required by policies targeting `public`).
- Result: `anon` SECURITY DEFINER advisor warnings dropped from ~22 to 4
  (`is_staff`, `is_active_member`, `is_group_admin`, `is_group_mod` — used by
  RLS, intentional). Leaked password protection still to enable in Auth panel.

## Remaining Security Findings

Supabase advisors still report issues in the pre-existing collaborative schema:

- `public.feed_on_note` has mutable `search_path`.
  Remediation: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable
- Many `SECURITY DEFINER` functions in `public` are executable by `anon`.
  Examples: `add_post`, `create_group`, `create_topic`, `decide_member`, `delete_post`, `group_brief`, `join_group`, `log_audit`, `save_profile`, `submit_suggestion`.
  Remediation: https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable
- Many of the same `SECURITY DEFINER` functions are executable by `authenticated`.
  Remediation: https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable
- Leaked password protection is disabled in Auth.
  Remediation: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

Do not expose additional UI that calls those RPC functions until each one has been reviewed. For functions that must remain callable, prefer moving privileged code out of `public`, revoking `EXECUTE` from `PUBLIC`/`anon`, setting a fixed `search_path`, and validating `auth.uid()` inside the function.

## Remaining Performance Findings

Supabase performance advisors report:

- Unindexed foreign keys across the collaborative tables (`activity_feed`, `group_members`, `group_notes`, `group_plan_progress`, `group_plans`, `group_topics`, `groups`, `note_comments`, `suggestions`, `topic_posts`).
  Remediation: https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys
- RLS policies using direct `auth.uid()`/helper calls instead of the initplan-friendly `(select auth.uid())` pattern in existing tables.
  Remediation: https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan
- Multiple permissive policies for some tables/actions (`group_plan_progress`, `group_plans`).
  Remediation: https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies

The new `user_study_state` table does not add those advisor warnings.

## Configuration Needed

Local testing needs `site/assets/supabase-config.js`:

```js
window.BEC_SUPABASE_CONFIG = {
  url: "https://pxqhpntifbtjaoqtirao.supabase.co",
  publishableKey: "sb_publishable_..."
};
```

GitHub Pages deployment expects a repository secret named `SUPABASE_PUBLISHABLE_KEY`.
