START TRANSACTION;

CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    type VARCHAR(32) NOT NULL,
    extra TEXT,
    
    user_id INT REFERENCES users(id) NOT NULL,
    organization_id INT REFERENCES organizations(id) NOT NULL,
    project_id INT REFERENCES projects(id),
    entity_id INT REFERENCES entities(id),
    
    object_id INT,
    object_type VARCHAR(32),
    
    created_date TIMESTAMP
);

CREATE INDEX ix_activities_user_id ON activities(user_id);
CREATE INDEX ix_activities_org_id ON activities(organization_id);
CREATE INDEX ix_activities_project_id ON activities(project_id);
CREATE INDEX ix_activities_entity_id ON activities(entity_id);
CREATE INDEX ix_activities_created_date ON activities(created_date);

COMMIT;

