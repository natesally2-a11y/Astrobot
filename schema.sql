-- Stellarium AI — схема базы данных (PostgreSQL 15)
-- Соответствует ORM-моделям в app/database/models.py.
-- В MVP таблицы создаются автоматически при старте приложения
-- (app.database.init_models), этот файл — справочный / для ручного деплоя.

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    first_name VARCHAR(100),
    username VARCHAR(50),
    language_code VARCHAR(8) DEFAULT 'ru',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    subscription_type VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    gdpr_consent BOOLEAN DEFAULT FALSE,
    gdpr_consent_date TIMESTAMPTZ,
    ask_count INTEGER DEFAULT 0,
    ask_count_date DATE,
    referred_by BIGINT,
    referral_count INTEGER DEFAULT 0
);

-- Натальные данные
CREATE TABLE IF NOT EXISTS birth_data (
    user_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    birth_date DATE NOT NULL,
    birth_time TIME,
    time_is_exact BOOLEAN DEFAULT TRUE,
    birth_place VARCHAR(200) NOT NULL,
    latitude NUMERIC(10,6),
    longitude NUMERIC(11,6),
    timezone VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- История чтений
CREATE TABLE IF NOT EXISTS readings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    reading_type VARCHAR(50),
    question TEXT,
    ai_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Подписки
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    plan_type VARCHAR(20),
    stars_amount INTEGER DEFAULT 0,
    telegram_charge_id VARCHAR(128),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    auto_renew BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_readings_user ON readings(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
