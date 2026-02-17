-- PostgreSQL initialization script
-- Auto-executed by postgres container on first start

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT DEFAULT '',
    role TEXT DEFAULT 'user',
    receive_email INTEGER DEFAULT 1,
    tech_stack JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pushed_repos (
    repo_name TEXT PRIMARY KEY,
    first_seen DATE,
    last_pushed DATE,
    push_count INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE UNIQUE,
    report_html TEXT,
    report_json JSONB,
    project_count INTEGER,
    email_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value JSONB
);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    type TEXT DEFAULT 'suggestion',
    content TEXT NOT NULL,
    reply TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_hidden_reports (
    user_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, report_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pushed_repos_last_pushed ON pushed_repos(last_pushed);
CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
