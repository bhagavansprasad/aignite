-- Prompt a warning to the user
-- This is just a comment, you should manually check before running the script
-- CAUTION: This script will drop the existing database and tables if they exist.
-- Please ensure you have a backup if necessary.

-- Check if the database exists, and drop it if it does
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'aignite_db') THEN
        RAISE NOTICE 'Database "aignite_db" exists. Dropping it...';
        DROP DATABASE aignite_db WITH (FORCE); -- Disconnect users and drop
    END IF;
END $$;

-- 1. Create the database
CREATE DATABASE aignite_db;

-- Connect to the new database
\c aignite_db;

-- 2. Create the users and assign privileges
CREATE USER bhagavan WITH PASSWORD 'jnjnuh'; -- Replace 'your_bhagavan_password' with a strong password
CREATE USER dheeraj WITH PASSWORD 'jnjnuh';   -- Replace 'your_dheeraj_password' with a strong password

-- Check if the extension exists, and create it if it doesn't
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function to drop table if exists (idempotent)
CREATE OR REPLACE FUNCTION drop_if_exists(p_table_name text) RETURNS void AS
$func$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = p_table_name) THEN
    EXECUTE format('DROP TABLE public.%I CASCADE', p_table_name);
    RAISE NOTICE 'Table "%" exists. Dropping it...', p_table_name;
  END IF;
END
$func$ LANGUAGE plpgsql;

-- Drop tables if they exist
SELECT drop_if_exists('tokens');
SELECT drop_if_exists('user_roles');
SELECT drop_if_exists('users');
SELECT drop_if_exists('roles');

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert default roles
INSERT INTO roles (name) VALUES ('ADMIN'), ('TEACHER'), ('STUDENT');

-- 4. Create the users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    mobile_no VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,  
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes on users table
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_mobile_no ON users (mobile_no);
CREATE INDEX idx_users_role_id ON users (role_id);

-- 5. Create the user_roles table (Many-to-Many relationship)
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Create the tokens table
CREATE TABLE tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create index on tokens table
CREATE INDEX idx_tokens_user_id ON tokens (user_id);
CREATE INDEX idx_tokens_expires_at ON tokens (expires_at);

-- 6. Grant privileges to bhagavan
GRANT CONNECT ON DATABASE aignite_db TO bhagavan;
GRANT USAGE ON SCHEMA public TO bhagavan;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bhagavan;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bhagavan; -- For auto-increment columns

-- 7. Grant privileges to dheeraj
GRANT CONNECT ON DATABASE aignite_db TO dheeraj;
GRANT USAGE ON SCHEMA public TO dheeraj;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dheeraj;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dheeraj; -- For auto-increment columns

-- Optionally, restrict permissions based on roles (example: read-only for students)
-- REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM dheeraj;

-- ********************* Debugging Activities *********************

-- 1. List the database that is created (within psql - this won't work in a SQL script)
-- \l

-- 2. List all tables in the database
\dt public.*

-- 3. List the schema of all tables created

-- Schema for roles table
\d roles

-- Schema for users table
\d users

-- Schema for user_roles table
\d user_roles

-- Schema for tokens table
\d tokens