-- Run this in Supabase SQL Editor to add new columns
-- Dashboard > SQL Editor > New Query

-- Add new columns to athletes table
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS role TEXT;
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS sport TEXT;
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS msn_program TEXT;
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS medical_conditions TEXT;
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS dietary_restrictions TEXT;
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS supporters_info TEXT;
ALTER TABLE athletes ADD COLUMN IF NOT EXISTS acceptance_intention TEXT;

-- Add new columns to coaches table
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS msn_program TEXT;
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS birthdate TEXT;
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS gender TEXT;
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS nation TEXT;

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'athletes'
  AND column_name IN ('role', 'sport', 'msn_program', 'medical_conditions', 'dietary_restrictions', 'supporters_info', 'acceptance_intention')
ORDER BY column_name;
