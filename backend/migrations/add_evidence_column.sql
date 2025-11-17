-- Migration: Add evidence column to citation_treatment table
-- Date: 2025-11-17
-- Description: Adds JSONB evidence column to store classification examples and keywords

-- Add evidence column
ALTER TABLE citation_treatment
ADD COLUMN IF NOT EXISTS evidence JSONB;

-- Create index on evidence for faster JSON queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_treatment_evidence ON citation_treatment USING GIN (evidence);

-- Verify the column was added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'citation_treatment'
  AND column_name = 'evidence';
