-- Migration 003: Add explicit RLS policies for PostGenie tables
-- Run AFTER 002_enable_rls.sql in Supabase SQL Editor.
--
-- ── Architecture context ────────────────────────────────────────────────
-- PostGenie uses its own Google OAuth (not Supabase Auth) and connects to
-- the database via SUPABASE_SERVICE_KEY on the server side only. The
-- service_role automatically BYPASSES RLS regardless of any policies, so
-- the app keeps working after this migration.
--
-- Policies below provide defense-in-depth:
--   * anon role          → no policy = NO ACCESS (deny-all by default)
--   * authenticated role → scoped to own rows via auth.jwt() ->> 'email'
--                          (active only if Supabase Auth is integrated later)
--   * service_role       → bypasses RLS (no policy needed)
--
-- For pg_blog_connections we deliberately DO NOT create authenticated-role
-- policies because that table holds OAuth refresh tokens and WordPress app
-- passwords. Only server-side service_role should ever touch it. If a UI
-- feature later needs to display non-secret metadata, create a SECURITY
-- DEFINER view (or column-filtered view) and grant SELECT on the view.
-- ────────────────────────────────────────────────────────────────────────

-- ─── Make sure RLS is on (idempotent re-affirm of migration 002) ───
ALTER TABLE pg_users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_blog_connections   ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_post_schedules     ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_posts              ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_usage_daily        ENABLE ROW LEVEL SECURITY;

-- ─── Drop any pre-existing policies on these tables (idempotent rerun) ───
DO $$
DECLARE pol record;
BEGIN
    FOR pol IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public' AND tablename LIKE 'pg_%'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I',
                       pol.policyname, pol.schemaname, pol.tablename);
    END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════════════
-- pg_users — a user can read/update only their own row
-- ════════════════════════════════════════════════════════════════════════
CREATE POLICY pg_users_self_select ON pg_users
    FOR SELECT TO authenticated
    USING (email = auth.jwt() ->> 'email');

CREATE POLICY pg_users_self_update ON pg_users
    FOR UPDATE TO authenticated
    USING      (email = auth.jwt() ->> 'email')
    WITH CHECK (email = auth.jwt() ->> 'email');

-- INSERT and DELETE on pg_users are server-only (service_role bypass).

-- ════════════════════════════════════════════════════════════════════════
-- pg_blog_connections — SECRETS TABLE: server-side only
-- No authenticated-role policies on purpose. service_role bypasses RLS.
-- ════════════════════════════════════════════════════════════════════════
-- (intentionally empty)

-- ════════════════════════════════════════════════════════════════════════
-- pg_post_schedules — user can manage only their own schedules
-- ════════════════════════════════════════════════════════════════════════
CREATE POLICY pg_schedules_owner_select ON pg_post_schedules
    FOR SELECT TO authenticated
    USING (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

CREATE POLICY pg_schedules_owner_insert ON pg_post_schedules
    FOR INSERT TO authenticated
    WITH CHECK (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

CREATE POLICY pg_schedules_owner_update ON pg_post_schedules
    FOR UPDATE TO authenticated
    USING      (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ))
    WITH CHECK (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

CREATE POLICY pg_schedules_owner_delete ON pg_post_schedules
    FOR DELETE TO authenticated
    USING (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

-- ════════════════════════════════════════════════════════════════════════
-- pg_posts — user can read their own posts; writes are worker-only
-- ════════════════════════════════════════════════════════════════════════
CREATE POLICY pg_posts_owner_select ON pg_posts
    FOR SELECT TO authenticated
    USING (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

CREATE POLICY pg_posts_owner_delete ON pg_posts
    FOR DELETE TO authenticated
    USING (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

-- INSERT/UPDATE on pg_posts are server-only (worker creates/publishes posts
-- via service_role which bypasses RLS).

-- ════════════════════════════════════════════════════════════════════════
-- pg_usage_daily — user can read their own usage; writes are server-only
-- ════════════════════════════════════════════════════════════════════════
CREATE POLICY pg_usage_owner_select ON pg_usage_daily
    FOR SELECT TO authenticated
    USING (user_id IN (
        SELECT id FROM pg_users WHERE email = auth.jwt() ->> 'email'
    ));

-- ════════════════════════════════════════════════════════════════════════
-- Verify
-- ════════════════════════════════════════════════════════════════════════
-- Run AFTER the migration to confirm:
--
--   SELECT schemaname, tablename, rowsecurity
--   FROM   pg_tables
--   WHERE  schemaname = 'public' AND tablename LIKE 'pg_%';
--   -- expect: rowsecurity = true on all 5 rows
--
--   SELECT tablename, policyname, cmd, roles
--   FROM   pg_policies
--   WHERE  schemaname = 'public' AND tablename LIKE 'pg_%'
--   ORDER  BY tablename, policyname;
--   -- expect: policies on pg_users (2), pg_post_schedules (4),
--   --         pg_posts (2), pg_usage_daily (1); none on pg_blog_connections.
