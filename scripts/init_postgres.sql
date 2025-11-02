-- PostgreSQL initialization script

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create indexes for better query performance
-- (Tables will be created by SQLAlchemy/Alembic)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;

-- Create schemas if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Set default search path
ALTER DATABASE trading_db SET search_path TO public;


