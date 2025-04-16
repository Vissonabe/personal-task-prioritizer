
from supabase import create_client
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Redirect URL for OAuth
REDIRECT_URL = os.getenv("REDIRECT_URL", "http://localhost:8501")

def sign_up(email: str, password: str) -> Dict[str, Any]:
    """Register a new user with Supabase Auth."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        return response
    except Exception as e:
        print(f"Error signing up: {str(e)}")
        raise e

def sign_in(email: str, password: str) -> Dict[str, Any]:
    """Sign in an existing user with Supabase Auth."""
    try:
        # Sign in with email and password
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # Print debug info
        print(f"Sign in successful for {email}")
        print(f"Response type: {type(response)}")
        print(f"User: {response.user is not None}")
        print(f"Session: {response.session is not None}")

        # Verify we have a session
        if response.session is None:
            raise ValueError("Authentication succeeded but no session was created")

        # Set the session in the client
        supabase.auth.set_session(response.session.access_token, response.session.refresh_token)

        return response
    except Exception as e:
        print(f"Error signing in: {str(e)}")
        raise e

def sign_out() -> None:
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Error signing out: {str(e)}")
        raise e

def reset_password(email: str) -> Dict[str, Any]:
    """Send a password reset email to the user.

    Args:
        email: The user's email address

    Returns:
        Dict: Response from Supabase
    """
    try:
        response = supabase.auth.reset_password_email(email, {
            "redirect_to": f"{REDIRECT_URL}/reset-password"
        })
        print(f"Password reset email sent to {email}")
        return response
    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")
        raise e

def update_password(new_password: str) -> Dict[str, Any]:
    """Update the user's password after reset.

    Args:
        new_password: The new password

    Returns:
        Dict: Response from Supabase
    """
    try:
        response = supabase.auth.update_user({"password": new_password})
        print("Password updated successfully")
        return response
    except Exception as e:
        print(f"Error updating password: {str(e)}")
        raise e

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current logged-in user."""
    try:
        return supabase.auth.get_user()
    except Exception:
        return None

def sign_in_with_google() -> Dict[str, Any]:
    """Generate a Google OAuth sign-in URL."""
    try:
        auth_url = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": REDIRECT_URL
            }
        })
        print(f"Generated Google auth URL: {auth_url}")
        return auth_url
    except Exception as e:
        print(f"Error generating Google auth URL: {str(e)}")
        raise e

def handle_auth_callback(url_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle the OAuth callback and exchange code for session.

    Args:
        url_params: Dictionary containing URL parameters from the OAuth callback

    Returns:
        Dict or None: User data if successful, None otherwise
    """
    try:
        # Check if we have the necessary parameters
        if 'access_token' in url_params and 'refresh_token' in url_params:
            # Set the session directly
            supabase.auth.set_session(url_params['access_token'], url_params['refresh_token'])
            return supabase.auth.get_user()
        elif 'code' in url_params:
            # Exchange code for session
            auth_response = supabase.auth.exchange_code_for_session(url_params['code'])
            # Set the session in the client
            if hasattr(auth_response, 'session') and auth_response.session:
                supabase.auth.set_session(auth_response.session.access_token, auth_response.session.refresh_token)
            return supabase.auth.get_user()
        else:
            print("Missing required parameters in callback URL")
            return None
    except Exception as e:
        print(f"Error handling auth callback: {str(e)}")
        return None

def save_task(task: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Save a task to Supabase.

    Args:
        task: Dictionary containing task details
        user_id: ID of the user who owns the task

    Returns:
        Dict: The saved task with its ID
    """
    # Convert tags list to JSON string
    if 'tags' in task and isinstance(task['tags'], list):
        task_copy = task.copy()
        task_copy['tags'] = json.dumps(task_copy['tags'])
        task_copy['user_id'] = user_id

        # Add timestamps
        from datetime import datetime
        now = datetime.now().isoformat()
        task_copy['created_at'] = now
        task_copy['updated_at'] = now

        # Print debug info
        print(f"Saving task with user_id: {user_id}")
        print(f"Task data: {task_copy}")

        try:
            # Insert into Supabase
            response = supabase.table('tasks').insert(task_copy).execute()

            # Return the first inserted record
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}
        except Exception as e:
            print(f"Error saving task: {str(e)}")
            # Try to get the current session
            session = supabase.auth.get_session()
            print(f"Current session: {session is not None}")
            if session is None:
                raise ValueError("No active session. Please log in again.")
            raise e
    else:
        raise ValueError("Task must contain a 'tags' field that is a list")

def save_tasks(tasks: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
    """
    Save multiple tasks to Supabase.

    Args:
        tasks: List of task dictionaries
        user_id: ID of the user who owns the tasks

    Returns:
        List[Dict]: The saved tasks with their IDs
    """
    saved_tasks = []
    for task in tasks:
        saved_task = save_task(task, user_id)
        saved_tasks.append(saved_task)

    return saved_tasks

def get_all_tasks(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all tasks for a user from Supabase.

    Args:
        user_id: ID of the user whose tasks to retrieve

    Returns:
        List[Dict]: List of task dictionaries
    """
    response = supabase.table('tasks').select('*').eq('user_id', user_id).order('priority_score', desc=True).execute()

    tasks = []
    for task in response.data:
        # Convert JSON string back to list for tags
        if 'tags' in task and isinstance(task['tags'], str):
            task['tags'] = json.loads(task['tags'])
        tasks.append(task)

    return tasks

def get_task(task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific task by ID.

    Args:
        task_id: ID of the task to retrieve
        user_id: ID of the user who owns the task

    Returns:
        Dict or None: Task dictionary if found, None otherwise
    """
    response = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', user_id).execute()

    if response.data and len(response.data) > 0:
        task = response.data[0]
        # Convert JSON string back to list for tags
        if 'tags' in task and isinstance(task['tags'], str):
            task['tags'] = json.loads(task['tags'])
        return task

    return None

def update_task(task_id: str, task_data: Dict[str, Any], user_id: str) -> bool:
    """
    Update a task in Supabase.

    Args:
        task_id: ID of the task to update
        task_data: Dictionary containing updated task details
        user_id: ID of the user who owns the task

    Returns:
        bool: True if update was successful, False otherwise
    """
    # Prepare update data
    update_data = task_data.copy()

    # Handle tags conversion
    if 'tags' in update_data and isinstance(update_data['tags'], list):
        update_data['tags'] = json.dumps(update_data['tags'])

    # Add updated timestamp
    from datetime import datetime
    update_data['updated_at'] = datetime.now().isoformat()

    # Execute update
    response = supabase.table('tasks').update(update_data).eq('id', task_id).eq('user_id', user_id).execute()

    return len(response.data) > 0

def delete_task(task_id: str, user_id: str) -> bool:
    """
    Delete a task from Supabase.

    Args:
        task_id: ID of the task to delete
        user_id: ID of the user who owns the task

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    response = supabase.table('tasks').delete().eq('id', task_id).eq('user_id', user_id).execute()

    return len(response.data) > 0

def toggle_task_completion(task_id: str, user_id: str) -> bool:
    """
    Toggle the completion status of a task.

    Args:
        task_id: ID of the task to toggle
        user_id: ID of the user who owns the task

    Returns:
        bool: True if toggle was successful, False otherwise
    """
    # Get current task
    task = get_task(task_id, user_id)

    if not task:
        return False

    # Toggle status
    new_status = not task.get('completed', False)

    # Update task
    return update_task(task_id, {'completed': new_status}, user_id)

def clear_all_tasks(user_id: str) -> int:
    """
    Delete all tasks for a user from Supabase.

    Args:
        user_id: ID of the user whose tasks to delete

    Returns:
        int: Number of tasks deleted
    """
    # First, get count of tasks
    count_response = supabase.table('tasks').select('id', count='exact').eq('user_id', user_id).execute()
    count = count_response.count if hasattr(count_response, 'count') else 0

    # Delete all tasks for user
    supabase.table('tasks').delete().eq('user_id', user_id).execute()

    return count

# User preferences functions
def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get user preferences from Supabase.

    Args:
        user_id: ID of the user

    Returns:
        Dict: User preferences
    """
    try:
        print(f"Fetching preferences for user: {user_id}")
        response = supabase.table('user_preferences').select('*').eq('user_id', user_id).execute()

        if response.data and len(response.data) > 0:
            print(f"Found existing preferences: {response.data[0]}")
            return response.data[0]
        else:
            print(f"No preferences found for user {user_id}, creating default")
            # Create default preferences if none exist
            default_prefs = {
                'user_id': user_id,
                'theme': 'default',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            try:
                save_response = supabase.table('user_preferences').insert(default_prefs).execute()
                if save_response.data and len(save_response.data) > 0:
                    print(f"Created default preferences: {save_response.data[0]}")
                    return save_response.data[0]
                else:
                    print(f"No data returned when creating preferences: {save_response}")
                    return default_prefs
            except Exception as insert_error:
                print(f"Error creating default preferences: {str(insert_error)}")
                # Just return the default preferences without saving
                return default_prefs
    except Exception as e:
        print(f"Error getting user preferences: {str(e)}")
        # Print more detailed error information if available
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response details: {e.response.text}")
        # Return default preferences if there's an error
        return {'theme': 'default'}

def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
    """
    Update user preferences in Supabase.

    Args:
        user_id: ID of the user
        preferences: Dictionary containing preference updates

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        # Add updated timestamp
        update_data = preferences.copy()
        update_data['updated_at'] = datetime.now().isoformat()

        # Check if preferences exist
        check_response = supabase.table('user_preferences').select('id').eq('user_id', user_id).execute()

        if check_response.data and len(check_response.data) > 0:
            # Update existing preferences
            response = supabase.table('user_preferences').update(update_data).eq('user_id', user_id).execute()
        else:
            # Create new preferences with explicit user_id
            new_prefs = {
                'user_id': user_id,
                'theme': update_data.get('theme', 'default'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            # Print debug info
            print(f"Creating new preferences for user {user_id}: {new_prefs}")

            # Insert with explicit user_id
            response = supabase.table('user_preferences').insert(new_prefs).execute()

        if response.data and len(response.data) > 0:
            print(f"Successfully updated preferences: {response.data}")
            return True
        else:
            print(f"No data returned from preferences update: {response}")
            return False
    except Exception as e:
        print(f"Error updating user preferences: {str(e)}")
        # Print more detailed error information if available
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response details: {e.response.text}")
        return False

# Analytics functions
def get_task_stats(user_id: str) -> Dict[str, Any]:
    """
    Get statistics about tasks for analytics.

    Args:
        user_id: ID of the user

    Returns:
        Dict: Statistics about tasks
    """
    try:
        # Get all tasks
        tasks = get_all_tasks(user_id)

        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.get('completed', False))
        open_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        # Group tasks by importance
        importance_counts = {
            'High': sum(1 for task in tasks if task.get('importance') == 'High'),
            'Medium': sum(1 for task in tasks if task.get('importance') == 'Medium'),
            'Low': sum(1 for task in tasks if task.get('importance') == 'Low')
        }

        # Group tasks by due date (for calendar view)
        tasks_by_date = {}
        for task in tasks:
            due_date = task.get('due_date')
            if due_date:
                if due_date not in tasks_by_date:
                    tasks_by_date[due_date] = []
                tasks_by_date[due_date].append(task)

        # Calculate completion over time
        # Group tasks by creation date
        completion_by_date = {}
        for task in tasks:
            created_at = task.get('created_at', '').split('T')[0]  # Get just the date part
            if created_at:
                if created_at not in completion_by_date:
                    completion_by_date[created_at] = {'total': 0, 'completed': 0}
                completion_by_date[created_at]['total'] += 1
                if task.get('completed', False):
                    completion_by_date[created_at]['completed'] += 1

        # Sort dates and convert to lists for charting
        dates = sorted(completion_by_date.keys())
        completion_data = {
            'dates': dates,
            'total': [completion_by_date[date]['total'] for date in dates],
            'completed': [completion_by_date[date]['completed'] for date in dates]
        }

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'open_tasks': open_tasks,
            'completion_rate': completion_rate,
            'importance_counts': importance_counts,
            'tasks_by_date': tasks_by_date,
            'completion_data': completion_data
        }
    except Exception as e:
        print(f"Error getting task stats: {str(e)}")
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'open_tasks': 0,
            'completion_rate': 0,
            'importance_counts': {'High': 0, 'Medium': 0, 'Low': 0},
            'tasks_by_date': {},
            'completion_data': {'dates': [], 'total': [], 'completed': []}
        }

def get_tasks_by_date(user_id: str, date_str: str) -> List[Dict[str, Any]]:
    """
    Get tasks for a specific date.

    Args:
        user_id: ID of the user
        date_str: Date string in format YYYY-MM-DD

    Returns:
        List[Dict]: List of tasks for the specified date
    """
    try:
        # Get all tasks
        all_tasks = get_all_tasks(user_id)

        # Filter tasks by due date
        return [task for task in all_tasks if task.get('due_date') == date_str]
    except Exception as e:
        print(f"Error getting tasks by date: {str(e)}")
        return []

