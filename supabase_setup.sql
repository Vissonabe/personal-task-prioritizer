-- Create the tasks table if it doesn't exist
CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL,
  description TEXT NOT NULL,
  due_date TEXT,
  tags TEXT,
  importance TEXT,
  priority_score REAL,
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the user_preferences table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL UNIQUE,
  theme TEXT DEFAULT 'default',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Drop existing RLS policies if they exist
DROP POLICY IF EXISTS "Users can only access their own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can insert their own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can update their own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can delete their own tasks" ON tasks;

-- Enable Row Level Security
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Create policies for different operations
-- Policy for SELECT operations
CREATE POLICY "Users can only access their own tasks"
ON tasks FOR SELECT
USING (auth.uid() = user_id);

-- Policy for INSERT operations
CREATE POLICY "Users can insert their own tasks"
ON tasks FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy for UPDATE operations
CREATE POLICY "Users can update their own tasks"
ON tasks FOR UPDATE
USING (auth.uid() = user_id);

-- Policy for DELETE operations
CREATE POLICY "Users can delete their own tasks"
ON tasks FOR DELETE
USING (auth.uid() = user_id);

-- Grant necessary permissions to authenticated users
GRANT ALL ON tasks TO authenticated;
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
