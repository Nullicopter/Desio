START TRANSACTION;

CREATE TABLE invites (
    id SERIAL PRIMARY KEY,
    eid VARCHAR(22) NOT NULL,
    
    role VARCHAR(16) NOT NULL,
    type VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL,
    
    invited_email VARCHAR(256) NOT NULL,
    
    user_id INT REFERENCES users(id) NOT NULL,
    invited_user_id INT REFERENCES users(id),
    
    object_id INT NOT NULL,
    
    created_date TIMESTAMP
);

CREATE INDEX ix_invites_eid ON invites(eid);

CREATE TABLE entity_users (
    id SERIAL PRIMARY KEY,
    
    role VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL,
    
    user_id INT REFERENCES users(id) NOT NULL,
    entity_id INT REFERENCES entities(id) NOT NULL,
    
    created_date TIMESTAMP
);

CREATE INDEX ix_entity_users_user_id ON entity_users(user_id);
CREATE INDEX ix_entity_users_entity_id ON entity_users(entity_id);


UPDATE organization_users set role='read' where role='user';
UPDATE organization_users set role='write' where role='creator';

-- GRANT SELECT, INSERT, UPDATE, DELETE ON invites TO binderado;
-- GRANT SELECT, UPDATE ON invites_id_seq TO binderado;

COMMIT;

