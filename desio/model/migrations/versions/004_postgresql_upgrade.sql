START TRANSACTION;

ALTER TABLE changes ADD COLUMN parse_type VARCHAR(16) NOT NULL DEFAULT 'imagemagick';
ALTER TABLE changes ADD COLUMN parse_status VARCHAR(16) NOT NULL DEFAULT 'completed';

INSERT INTO users (email, username, display_username, password, role, is_active, first_name, last_name, default_timezone, created_date, updated_date)
        VALUES ('robot@binder.io', 'robot@binder.io', 'robot@binder.io', '7a46cb782290371c6c8f6bcc1100560f', 'robot', true, 'Robot', 'Robotterson', 'US/Pacific', now(), now());

COMMIT;

