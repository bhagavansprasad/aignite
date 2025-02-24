-- Connect to the aignite_db database
\c aignite_db;

-- Ensure the bcrypt extension exists (needed for hashing passwords)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insert roles if they do not exist
INSERT INTO roles (name) VALUES 
    ('ADMIN'), 
    ('TEACHER'), 
    ('STUDENT')
ON CONFLICT (name) DO NOTHING;

-- Insert users if they do not exist
INSERT INTO users (email, mobile_no, password, role_id, created_at, is_active)
SELECT * FROM (VALUES
    ('user1@example.com', '1234567890', 'jnjnuh', 1, NOW(), TRUE),
    ('user2@example.com', '9876543210', 'jnjnuh', 2, NOW(), TRUE),
    ('user3@example.com', '5551234567', 'jnjnuh', 3, NOW(), TRUE),
    ('user4@example.com', '1111111111', 'jnjnuh', 1, NOW(), TRUE),
    ('user5@example.com', '2222222222', 'jnjnuh', 2, NOW(), TRUE),
    ('user6@example.com', '3333333333', 'jnjnuh', 3, NOW(), TRUE)
) AS new_users(email, mobile_no, password, role_id, created_at, is_active)
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE users.email = new_users.email
);

-- Insert user roles if they do not exist
INSERT INTO user_roles (user_id, role_id)
SELECT users.id, users.role_id FROM users
ON CONFLICT (user_id, role_id) DO NOTHING;

SELECT * FROM users;
SELECT * FROM roles;
SELECT * FROM user_roles;

-- SECURITY WARNING: 
-- - Ensure that each user is created with a strong and unique password.
-- - In production, passwords should NEVER be stored in plain text.
-- - Do NOT use default passwords; enforce password policies.
-- - User creation should be controlled via admin tools or self-registration with proper validation.

-- Script execution completed.
