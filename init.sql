-- PostgreSQL Initialization Script for AI Portfolio Site
-- This script runs when the PostgreSQL container is first created

-- Enable the vector extension for pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Create additional extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO portfolio_user;

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization completed successfully';
    RAISE NOTICE 'Vector extension enabled for pgvector support';
    RAISE NOTICE 'UUID extension enabled for UUID generation';
END $$;
