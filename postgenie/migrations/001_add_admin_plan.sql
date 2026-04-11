-- Migration: Add 'admin' to allowed plans + promote current user
-- Run this in Supabase SQL Editor

-- 1) Drop existing check constraint and add new one with 'admin'
ALTER TABLE pg_users DROP CONSTRAINT IF EXISTS pg_users_plan_check;
ALTER TABLE pg_users ADD CONSTRAINT pg_users_plan_check
    CHECK (plan IN ('free', 'basic', 'pro', 'agency', 'admin'));

-- 2) Promote admin user
UPDATE pg_users
SET plan = 'admin', updated_at = NOW()
WHERE email = 'wisemanida6969@gmail.com';
