CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table to store conversations with messages as JSONB
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    messages JSONB DEFAULT '[]'::jsonb
);

-- Index to speed up queries by conversation_id
CREATE INDEX IF NOT EXISTS idx_conversations_id ON conversations(id);