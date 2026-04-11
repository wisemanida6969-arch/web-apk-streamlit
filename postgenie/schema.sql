-- PostGenie Database Schema
-- Run this in Supabase SQL Editor

-- ─── Users ───
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    picture TEXT,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'basic', 'pro', 'agency')),
    paddle_subscription_id TEXT,
    paddle_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ─── Blog Connections ───
-- Stores OAuth refresh tokens for connected blogs
CREATE TABLE IF NOT EXISTS blog_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('blogger', 'wordpress', 'tistory')),
    blog_id TEXT NOT NULL,
    blog_name TEXT,
    blog_url TEXT,
    -- OAuth credentials (encrypted in production)
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    -- For self-hosted WordPress
    wp_site_url TEXT,
    wp_username TEXT,
    wp_app_password TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blog_connections_user ON blog_connections(user_id);

-- ─── Post Schedules ───
-- User's scheduled posting configuration
CREATE TABLE IF NOT EXISTS post_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    blog_connection_id UUID REFERENCES blog_connections(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    -- Content config
    categories TEXT[] NOT NULL DEFAULT '{}',  -- ['trending', 'tech', 'lifestyle']
    custom_topics TEXT,  -- User-defined topic keywords
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'ko', 'ja', 'es', 'auto')),
    tone TEXT DEFAULT 'friendly',  -- friendly, professional, casual
    word_count INT DEFAULT 1000,
    -- Schedule config
    frequency TEXT DEFAULT 'daily' CHECK (frequency IN ('daily', 'twice_daily', 'weekly', 'custom')),
    custom_cron TEXT,  -- For advanced users
    timezone TEXT DEFAULT 'Asia/Seoul',
    -- State
    enabled BOOLEAN DEFAULT true,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedules_user ON post_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON post_schedules(next_run_at) WHERE enabled = true;

-- ─── Generated Posts ───
-- Track every post generated and published
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES post_schedules(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    language TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'failed')),
    -- Published info
    blog_post_id TEXT,
    blog_post_url TEXT,
    error_message TEXT,
    -- Metadata
    model TEXT DEFAULT 'claude-haiku-4-5',
    token_count INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_schedule ON posts(schedule_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);

-- ─── Usage Tracking ───
-- Daily usage counters for rate limiting
CREATE TABLE IF NOT EXISTS usage_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    date DATE NOT NULL,
    posts_generated INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_usage_user_date ON usage_daily(user_id, date);

-- ─── Row Level Security ───
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE blog_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_daily ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Users view own blog connections" ON blog_connections
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users view own schedules" ON post_schedules
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users view own posts" ON posts
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users view own usage" ON usage_daily
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ─── Helper Functions ───
-- Get user's plan limits
CREATE OR REPLACE FUNCTION get_plan_limits(plan_name TEXT)
RETURNS TABLE(max_blogs INT, max_posts_per_day INT, max_schedules INT) AS $$
BEGIN
    RETURN QUERY SELECT
        CASE plan_name
            WHEN 'free' THEN 1
            WHEN 'basic' THEN 1
            WHEN 'pro' THEN 3
            WHEN 'agency' THEN 10
            ELSE 1
        END,
        CASE plan_name
            WHEN 'free' THEN 1  -- 1 per week, check frequency
            WHEN 'basic' THEN 1
            WHEN 'pro' THEN 3
            WHEN 'agency' THEN 30
            ELSE 1
        END,
        CASE plan_name
            WHEN 'free' THEN 1
            WHEN 'basic' THEN 1
            WHEN 'pro' THEN 3
            WHEN 'agency' THEN 10
            ELSE 1
        END;
END;
$$ LANGUAGE plpgsql;
