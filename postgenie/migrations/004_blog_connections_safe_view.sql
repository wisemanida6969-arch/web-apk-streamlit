-- Migration 004: Safe metadata view for pg_blog_connections
-- Run AFTER 003_rls_policies.sql in Supabase SQL Editor.
--
-- ── Why ─────────────────────────────────────────────────────────────────
-- pg_blog_connections holds OAuth refresh_token, OAuth access_token, and
-- WordPress wp_app_password. We deliberately leave that table with NO
-- authenticated-role RLS policy (migration 003) so clients can never read
-- those columns directly.
--
-- This view exposes ONLY non-secret metadata so the UI can show "your
-- connected blogs" without ever touching credential columns.
--
-- ── How it works ────────────────────────────────────────────────────────
-- The view runs with the creator's privileges (security_invoker = false),
-- so it bypasses RLS on the underlying table. Access control lives in the
-- view's WHERE clause, which restricts rows to the caller's own user_id
-- via auth.jwt() ->> 'email'. The view is granted to `authenticated` only;
-- `anon` cannot select from it.
--
-- Currently the app uses service_role and reads pg_blog_connections
-- directly, so this view is only meaningful once Supabase Auth is wired
-- into PostGenie. Until then it just sits idle — no behaviour change.
-- ────────────────────────────────────────────────────────────────────────

DROP VIEW IF EXISTS pg_blog_connections_public;

CREATE VIEW pg_blog_connections_public
    WITH (security_invoker = false) AS
SELECT
    id,
    user_id,
    platform,
    blog_id,
    blog_name,
    blog_url,
    token_expires_at,
    wp_site_url,
    wp_username,
    created_at,
    updated_at
FROM pg_blog_connections
WHERE user_id IN (
    SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
);

COMMENT ON VIEW pg_blog_connections_public IS
    'Safe (no-secret) metadata view of pg_blog_connections. '
    'Excludes access_token, refresh_token, wp_app_password. '
    'WHERE clause limits rows to the caller''s own user_id via JWT email. '
    'Grant to authenticated only; service_role accesses base table directly.';

-- ─── Lock down grants: nobody by default, then authenticated SELECT only ───
REVOKE ALL ON pg_blog_connections_public FROM PUBLIC;
REVOKE ALL ON pg_blog_connections_public FROM anon;
GRANT  SELECT ON pg_blog_connections_public TO authenticated;
GRANT  SELECT ON pg_blog_connections_public TO service_role;

-- ════════════════════════════════════════════════════════════════════════
-- Verify
-- ════════════════════════════════════════════════════════════════════════
-- Confirm columns (should NOT contain access_token / refresh_token /
-- wp_app_password):
--
--   SELECT column_name
--   FROM   information_schema.columns
--   WHERE  table_schema = 'public'
--     AND  table_name   = 'pg_blog_connections_public'
--   ORDER  BY ordinal_position;
--
-- Confirm grants (should be: authenticated SELECT, service_role SELECT,
-- nothing for anon):
--
--   SELECT grantee, privilege_type
--   FROM   information_schema.role_table_grants
--   WHERE  table_schema = 'public'
--     AND  table_name   = 'pg_blog_connections_public';
