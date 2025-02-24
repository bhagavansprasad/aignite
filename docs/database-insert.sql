-- Connect to the aignite_db database
\c aignite_db;

-- Ensure the bcrypt extension exists (needed for hashing passwords)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insert roles if they do not exist
INSERT INTO roles (name) VALUES 
    ('ADMIN'),  
    ('TEACHER'), 
    ('STUDENT');


-- Insert users if they do not exist
INSERT INTO users (full_name, email, mobile_no, password, role_id, is_active)
SELECT * FROM (VALUES
    ('user1', 'user1@example.com', '1234567890', 'jnjnuh', 1, TRUE),
    ('user2', 'user2@example.com', '9876543210', 'jnjnuh', 2, TRUE),
    ('user3', 'user3@example.com', '5551234567', 'jnjnuh', 3, TRUE),
    ('user4', 'user4@example.com', '1111111111', 'jnjnuh', 1, TRUE),
    ('user5', 'user5@example.com', '2222222222', 'jnjnuh', 2, TRUE),
    ('user6', 'user6@example.com', '3333333333', 'jnjnuh', 3, TRUE)
) AS new_users(email, mobile_no, password, role_id, is_active)
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE users.email = new_users.email
);

-- Insert user roles if they do not exist

SELECT * FROM users;
SELECT * FROM roles;

-- SECURITY WARNING: 
-- - Ensure that each user is created with a strong and unique password.
-- - In production, passwords should NEVER be stored in plain text.
-- - Do NOT use default passwords; enforce password policies.
-- - User creation should be controlled via admin tools or self-registration with proper validation.

-- Script execution completed.
