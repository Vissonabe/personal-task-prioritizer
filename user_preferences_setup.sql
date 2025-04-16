-- Create the user_preferences table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL UNIQUE,
  theme TEXT DEFAULT 'default',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security for user_preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Grant necessary permissions to authenticated users
GRANT ALL ON user_preferences TO authenticated;

-- Drop existing RLS policies for user_preferences if they exist
DROP POLICY IF EXISTS "Users can only access their own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Users can insert their own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Users can update their own preferences" ON user_preferences;

-- Create policies for user_preferences
-- Policy for SELECT operations
CREATE POLICY "Users can only access their own preferences"
  ON user_preferences
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy for INSERT operations
CREATE POLICY "Users can insert their own preferences"
  ON user_preferences
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy for UPDATE operations
CREATE POLICY "Users can update their own preferences"
  ON user_preferences
  FOR UPDATE
  USING (auth.uid() = user_id);
