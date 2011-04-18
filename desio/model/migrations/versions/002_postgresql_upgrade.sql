START TRANSACTION;
    
CREATE TABLE beta_emails (
    id SERIAL PRIMARY KEY,
    eid VARCHAR(6) NOT NULL,
    sid VARCHAR(22) NOT NULL,
    
    email VARCHAR(256) NOT NULL,
    
    creator_id INT REFERENCES users(id),
    
    clicks INT,
    invites INT,
    
    created_date TIMESTAMP
);

CREATE INDEX ix_sid ON beta_emails(sid);
CREATE INDEX ix_eid ON beta_emails(eid);
CREATE INDEX ix_email ON beta_emails(email);

COMMIT;

