CREATE EXTENSION
IF NOT EXISTS "uuid-ossp";

CREATE TABLE conversations
(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP
    WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP
    WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

    -- Create a trigger to automatically update modified_at
    CREATE OR REPLACE FUNCTION update_modified_column
    ()
RETURNS TRIGGER AS $$
    BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
    END;
$$ language 'plpgsql';

    CREATE TRIGGER update_conversations_modified_at
    BEFORE
    UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column
    ();