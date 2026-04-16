-- Migration: Enable Row Level Security on all PostGenie tables
-- Run this in Supabase SQL Editor (copy entire file, paste, Run)
--
-- Why: Supabase Security Advisor flagged these tables as publicly accessible
-- because RLS is disabled. In particular, pg_blog_connections stores OAuth
-- refresh_tokens and WordPress app passwords — absolutely must not be
-- accessible via the anon key.
--
-- Impact: After this migration, the anon key loses all access to these
-- tables. PostGenie itself keeps working because its supabase_client uses
-- SUPABASE_SERVICE_KEY, which bypasses RLS. The service key is only
-- accessible to server-side Streamlit/worker processes, never to browsers.
--
-- This is a deny-all approach by design — no public API access, only
-- server-side via service_role. Matches how the app already operates.

-- ─── Enable RLS on every PostGenie table ───
ALTER TABLE pg_users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_blog_connections   ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_post_schedules     ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_posts              ENABLE ROW LEVEL SECURITY;
ALTER TABLE pg_usage_daily        ENABLE ROW LEVEL SECURITY;

-- ─── (Optional) Force RLS even for table owners ───
-- Uncomment if you want to be extra strict. Not needed for the security
-- warning to clear — plain ENABLE ROW LEVEL SECURITY is enough.
-- ALTER TABLE pg_users            FORCE ROW LEVEL SECURITY;
-- ALTER TABLE pg_blog_connections FORCE ROW LEVEL SECURITY;
-- ALTER TABLE pg_post_schedules   FORCE ROW LEVEL SECURITY;
-- ALTER TABLE pg_posts            FORCE ROW LEVEL SECURITY;
-- ALTER TABLE pg_usage_daily      FORCE ROW LEVEL SECURITY;

-- ─── Verify ───
-- Run this after to confirm:
--   SELECT schemaname, tablename, rowsecurity
--   FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'pg_%';
-- All rows should show rowsecurity = true.
