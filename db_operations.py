import sqlite3
import json
from typing import List, Dict, Optional, Any
import os
from datetime import datetime

# Database file path
DB_FILE = "tasks.db"

def init_db():
    """Initialize the database with required tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        due_date TEXT,
        tags TEXT,
        importance TEXT,
        priority_score REAL,
        completed BOOLEAN DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def save_task(task: Dict[str, Any]) -> int:
    """
    Save a task to the database.
    
    Args:
        task: Dictionary containing task details
        
    Returns:
        int: ID of the inserted task
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Convert tags list to JSON string
    tags_json = json.dumps(task.get('tags', []))
    
    cursor.execute('''
    INSERT INTO tasks (description, due_date, tags, importance, priority_score, completed, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        task.get('description', ''),
        task.get('due_date', ''),
        tags_json,
        task.get('importance', ''),
        task.get('priority_score', 0.0),
        task.get('completed', False),
        now,
        now
    ))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return task_id

def save_tasks(tasks: List[Dict[str, Any]]) -> List[int]:
    """
    Save multiple tasks to the database.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        List[int]: List of inserted task IDs
    """
    task_ids = []
    for task in tasks:
        task_id = save_task(task)
        task_ids.append(task_id)
    
    return task_ids

def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Retrieve all tasks from the database.
    
    Returns:
        List[Dict]: List of task dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks ORDER BY priority_score DESC')
    rows = cursor.fetchall()
    
    tasks = []
    for row in rows:
        task = dict(row)
        # Convert JSON string back to list
        task['tags'] = json.loads(task['tags'])
        # Convert SQLite integer to boolean
        task['completed'] = bool(task['completed'])
        tasks.append(task)
    
    conn.close()
    return tasks

def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific task by ID.
    
    Args:
        task_id: ID of the task to retrieve
        
    Returns:
        Dict or None: Task dictionary if found, None otherwise
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    
    if row:
        task = dict(row)
        task['tags'] = json.loads(task['tags'])
        task['completed'] = bool(task['completed'])
        conn.close()
        return task
    
    conn.close()
    return None

def update_task(task_id: int, task_data: Dict[str, Any]) -> bool:
    """
    Update a task in the database.
    
    Args:
        task_id: ID of the task to update
        task_data: Dictionary containing updated task details
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if task exists
    cursor.execute('SELECT id FROM tasks WHERE id = ?', (task_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Prepare update data
    update_fields = []
    params = []
    
    for key, value in task_data.items():
        if key == 'tags' and isinstance(value, list):
            update_fields.append(f"{key} = ?")
            params.append(json.dumps(value))
        elif key in ['description', 'due_date', 'importance', 'priority_score', 'completed']:
            update_fields.append(f"{key} = ?")
            params.append(value)
    
    # Add updated_at timestamp
    update_fields.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    
    # Add task_id to params
    params.append(task_id)
    
    # Execute update
    query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(query, params)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def delete_task(task_id: int) -> bool:
    """
    Delete a task from the database.
    
    Args:
        task_id: ID of the task to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def toggle_task_completion(task_id: int) -> bool:
    """
    Toggle the completion status of a task.
    
    Args:
        task_id: ID of the task to toggle
        
    Returns:
        bool: True if toggle was successful, False otherwise
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get current completion status
    cursor.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    # Toggle status
    new_status = not bool(row[0])
    
    # Update task
    cursor.execute(
        'UPDATE tasks SET completed = ?, updated_at = ? WHERE id = ?',
        (new_status, datetime.now().isoformat(), task_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def clear_all_tasks() -> int:
    """
    Delete all tasks from the database.
    
    Returns:
        int: Number of tasks deleted
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tasks')
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

# Initialize the database when the module is imported
init_db()
