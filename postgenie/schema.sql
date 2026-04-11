-- PostGenie Database Schema (with pg_ prefix to share with existing Supabase project)
-- Run this in Supabase SQL Editor

-- ─── Users ───
CREATE TABLE IF NOT EXISTS pg_users (
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

CREATE INDEX IF NOT EXISTS idx_pg_users_email ON pg_users(email);

-- ─── Blog Connections ───
CREATE TABLE IF NOT EXISTS pg_blog_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES pg_users(id) ON DELETE CASCADE NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('blogger', 'wordpress', 'tistory')),
    blog_id TEXT NOT NULL,
    blog_name TEXT,
    blog_url TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    wp_site_url TEXT,
    wp_username TEXT,
    wp_app_password TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pg_blog_connections_user ON pg_blog_connections(user_id);

-- ─── Post Schedules ───
CREATE TABLE IF NOT EXISTS pg_post_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES pg_users(id) ON DELETE CASCADE NOT NULL,
    blog_connection_id UUID REFERENCES pg_blog_connections(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    categories TEXT[] NOT NULL DEFAULT '{}',
    custom_topics TEXT,
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'ko', 'ja', 'es', 'auto')),
    tone TEXT DEFAULT 'friendly',
    word_count INT DEFAULT 1000,
    frequency TEXT DEFAULT 'daily' CHECK (frequency IN ('daily', 'twice_daily', 'weekly', 'custom')),
    custom_cron TEXT,
    timezone TEXT DEFAULT 'Asia/Seoul',
    enabled BOOLEAN DEFAULT true,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pg_schedules_user ON pg_post_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_pg_schedules_next_run ON pg_post_schedules(next_run_at) WHERE enabled = true;

-- ─── Generated Posts ───
CREATE TABLE IF NOT EXISTS pg_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES pg_post_schedules(id) ON DELETE CASCADE,
    user_id UUID REFERENCES pg_users(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    language TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'failed')),
    blog_post_id TEXT,
    blog_post_url TEXT,
    error_message TEXT,
    model TEXT DEFAULT 'claude-haiku-4-5',
    token_count INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pg_posts_user ON pg_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_pg_posts_schedule ON pg_posts(schedule_id);
CREATE INDEX IF NOT EXISTS idx_pg_posts_status ON pg_posts(status);

-- ─── Usage Tracking ───
CREATE TABLE IF NOT EXISTS pg_usage_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES pg_users(id) ON DELETE CASCADE NOT NULL,
    date DATE NOT NULL,
    posts_generated INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_pg_usage_user_date ON pg_usage_daily(user_id, date);
