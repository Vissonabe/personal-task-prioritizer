import streamlit as st
from task_prioritizer import run_task_prioritizer
from graph_visualization import visualize_graph
import base64
import supabase_client as sb
from datetime import datetime
import langserve_client as lsc

# Define theme configurations
def get_theme_config(theme_name):
    themes = {
        "default": {
            "primaryColor": "#FF4B4B",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#F0F2F6",
            "textColor": "#31333F",
            "font": "sans serif"
        },
        "dark": {
            "primaryColor": "#FF4B4B",
            "backgroundColor": "#0E1117",
            "secondaryBackgroundColor": "#262730",
            "textColor": "#FAFAFA",
            "font": "sans serif"
        },
        "light": {
            "primaryColor": "#FF4B4B",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#F0F2F6",
            "textColor": "#31333F",
            "font": "sans serif"
        },
        "custom": {
            "primaryColor": "#4287F5",
            "backgroundColor": "#F0F8FF",
            "secondaryBackgroundColor": "#E1F1FF",
            "textColor": "#0A2F5E",
            "font": "sans serif"
        }
    }
    return themes.get(theme_name, themes["default"])

# Set up the Streamlit page
st.set_page_config(
    page_title="Personal Task Prioritizer",
    page_icon="📋",
    layout="wide"  # Use wide layout for better task display
)

# Apply theme from session state if available
if 'user_preferences' in st.session_state and 'theme' in st.session_state.user_preferences:
    theme_name = st.session_state.user_preferences['theme']
    theme_config = get_theme_config(theme_name)

    # Apply the theme using Streamlit's theming system
    for key, value in theme_config.items():
        st.config.set_option(f"theme.{key}", value)

# Create the main UI
st.title("📋 Personal Task Prioritizer")

# Authentication handling
if "user" not in st.session_state:
    # Show tabs for login/signup
    auth_tab1, auth_tab2, auth_tab3, auth_tab4 = st.tabs(["Login", "Sign Up", "Login with Google", "Reset Password"])

    with auth_tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            cols = st.columns([1, 1])
            with cols[0]:
                login_button = st.form_submit_button("Login")
            with cols[1]:
                st.markdown("<div style='padding-top: 10px;'><a href='#' onclick=\"document.querySelector('[data-baseweb=\\\'tab\\\']').click()\">Forgot password?</a></div>", unsafe_allow_html=True)

            if login_button:
                try:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        response = sb.sign_in(email, password)
                        if hasattr(response, 'user') and response.user:
                            st.session_state.user = response.user
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: Invalid response from authentication service")
                            st.info(f"Response structure: {type(response).__name__}")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"### Login Error\n\n**Error Type:** {type(e).__name__}\n\n**Error Message:** {str(e)}\n\n**Stack Trace:**\n```python\n{error_details}\n```")
                    st.info("Check your credentials and make sure your Supabase project is properly configured.")

    with auth_tab3:
        st.write("Sign in with your Google account")
        if st.button("Sign in with Google"):
            try:
                auth_url = sb.sign_in_with_google()
                if auth_url and 'data' in auth_url and 'url' in auth_url['data']:
                    # Open in new tab
                    st.markdown(f"""<a href='{auth_url['data']['url']}' target='_blank'>Click here to sign in with Google</a>""", unsafe_allow_html=True)

                    # Provide instructions
                    st.info("After signing in with Google, you'll be redirected back to this app. If the automatic redirect doesn't work, copy the URL from your browser and paste it below.")

                    # Add a field to paste the callback URL
                    callback_url = st.text_input("Paste callback URL here (if not automatically redirected)")
                    if callback_url:
                        # Extract parameters from URL
                        try:
                            from urllib.parse import urlparse, parse_qs
                            parsed_url = urlparse(callback_url)
                            params = parse_qs(parsed_url.fragment.lstrip('#'))

                            # Convert to the format expected by handle_auth_callback
                            flat_params = {k: v[0] for k, v in params.items()}

                            # Process the callback
                            user_data = sb.handle_auth_callback(flat_params)
                            if user_data and hasattr(user_data, 'user') and user_data.user:
                                st.session_state.user = user_data.user
                                st.success("Google login successful!")
                                st.rerun()
                            else:
                                st.error("Failed to process Google login. Please try again.")
                        except Exception as e:
                            st.error(f"Error processing callback URL: {str(e)}")
                else:
                    st.error("Failed to generate Google sign-in URL. Please try again later.")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                st.error(f"### Google Login Error\n\n**Error Type:** {type(e).__name__}\n\n**Error Message:** {str(e)}\n\n**Stack Trace:**\n```python\n{error_details}\n```")

    with auth_tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_button = st.form_submit_button("Sign Up")

            if signup_button:
                if not new_email:
                    st.error("Please enter an email address")
                elif not new_password or not confirm_password:
                    st.error("Please enter and confirm your password")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        response = sb.sign_up(new_email, new_password)
                        if response and hasattr(response, 'user') and response.user:
                            st.success(f"Sign up successful! User {new_email} has been created.")
                            st.info("Please check your email for verification if required by your Supabase settings.")

                            # Show details about what to do next
                            with st.expander("What's next?"):
                                st.markdown("""
                                1. Check your email for a verification link (if required)
                                2. Go to the Login tab to sign in with your new account
                                3. Start adding and prioritizing your tasks!
                                """)
                        else:
                            st.warning(f"Sign up may have been successful, but the response was unexpected.")
                            st.info(f"Response type: {type(response).__name__}")
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        st.error(f"### Sign Up Error\n\n**Error Type:** {type(e).__name__}\n\n**Error Message:** {str(e)}\n\n**Stack Trace:**\n```python\n{error_details}\n```")

                        # Provide helpful troubleshooting tips
                        with st.expander("Troubleshooting Tips"):
                            st.markdown("""
                            - Make sure your email format is valid
                            - Password should meet minimum requirements (usually 6+ characters)
                            - Check that your Supabase project is properly configured
                            - The email might already be registered
                            """)

    with auth_tab4:
        st.subheader("Reset Your Password")

        # Check if we're in password reset mode (after clicking link in email)
        query_params = st.query_params
        if 'type' in query_params and query_params.get('type') == 'recovery':
            # Show password reset form
            st.info("Enter your new password below.")

            with st.form("new_password_form"):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                reset_button = st.form_submit_button("Reset Password")

                if reset_button:
                    if not new_password or not confirm_password:
                        st.error("Please enter and confirm your new password")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        try:
                            response = sb.update_password(new_password)
                            st.success("Password has been reset successfully!")
                            st.info("You can now log in with your new password.")
                        except Exception as e:
                            st.error(f"Failed to reset password: {str(e)}")
        else:
            # Show request password reset form
            st.write("Forgot your password? Enter your email to receive a password reset link.")

            with st.form("reset_password_form"):
                email = st.text_input("Email")
                reset_button = st.form_submit_button("Send Reset Link")

                if reset_button:
                    if not email:
                        st.error("Please enter your email address")
                    else:
                        try:
                            response = sb.reset_password(email)
                            st.success("Password reset link has been sent to your email!")
                            st.info("Please check your email and click on the reset link.")

                            # Show additional instructions
                            with st.expander("What to do next"):
                                st.markdown("""
                                1. Check your email inbox (and spam folder) for the reset link
                                2. Click on the link in the email
                                3. You'll be redirected back to this app to set a new password
                                4. After setting a new password, you can log in with it
                                """)
                        except Exception as e:
                            st.error(f"Failed to send reset link: {str(e)}")
else:
    # User is logged in, show user info and settings in sidebar
    user_id = st.session_state.user.id

    # Get user preferences
    if 'user_preferences' not in st.session_state:
        # Print user info for debugging
        print(f"Current user: {user_id}, {st.session_state.user.email}")
        st.session_state.user_preferences = sb.get_user_preferences(user_id)

    st.sidebar.write(f"Logged in as: {st.session_state.user.email}")

    # Theme selection
    st.sidebar.divider()
    st.sidebar.subheader("Theme Settings")

    # Define available themes
    themes = {
        "default": "Default",
        "dark": "Dark Mode",
        "light": "Light Mode",
        "custom": "Custom Blue"
    }

    # Get current theme
    current_theme = st.session_state.user_preferences.get('theme', 'default')

    # Create theme selector
    selected_theme = st.sidebar.selectbox(
        "Select Theme",
        options=list(themes.keys()),
        format_func=lambda x: themes[x],
        index=list(themes.keys()).index(current_theme) if current_theme in themes else 0,
        key="theme_selector"
    )

    # Show theme preview
    theme_configs = {
        "default": get_theme_config("default"),
        "dark": get_theme_config("dark"),
        "light": get_theme_config("light"),
        "custom": get_theme_config("custom")
    }

    # Display a preview of the selected theme
    theme = theme_configs.get(selected_theme, theme_configs["default"])
    st.sidebar.markdown(
        f"""<div style="padding: 10px; border-radius: 5px; background-color: {theme['backgroundColor']}; color: {theme['textColor']}; margin-top: 10px;">
            <div style="font-weight: bold; margin-bottom: 5px;">Theme Preview</div>
            <div style="display: flex; gap: 5px;">
                <div style="width: 20px; height: 20px; background-color: {theme['primaryColor']}; border-radius: 3px;"></div>
                <div style="width: 20px; height: 20px; background-color: {theme['secondaryBackgroundColor']}; border: 1px solid #ccc; border-radius: 3px;"></div>
                <div style="width: 20px; height: 20px; color: {theme['textColor']}; text-align: center; font-weight: bold;">T</div>
            </div>
        </div>""",
        unsafe_allow_html=True
    )

    # Add debug option
    if st.sidebar.checkbox("Show Debug Info", key="show_debug"):
        st.sidebar.json({
            "user_id": user_id,
            "email": st.session_state.user.email,
            "current_theme": current_theme,
            "auth_status": "Authenticated" if sb.get_current_user() else "Not authenticated"
        })

    # Update theme if changed
    if selected_theme != current_theme:
        # Show a spinner while updating
        with st.spinner("Updating theme..."):
            if sb.update_user_preferences(user_id, {'theme': selected_theme}):
                st.session_state.user_preferences['theme'] = selected_theme

                # Apply the theme immediately
                theme_config = get_theme_config(selected_theme)
                for key, value in theme_config.items():
                    st.config.set_option(f"theme.{key}", value)

                st.sidebar.success("Theme updated!")
                # Force a rerun to ensure all components update
                st.rerun()
            else:
                st.sidebar.error("Failed to update theme. See console for details.")

    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        sb.sign_out()
        del st.session_state.user
        if 'user_preferences' in st.session_state:
            del st.session_state.user_preferences
        st.rerun()

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Add Tasks", "Manage Tasks", "Analytics", "Calendar"])

    # Get task statistics for analytics and calendar views
    if 'task_stats' not in st.session_state or st.session_state.get('refresh_stats', False):
        st.session_state.task_stats = sb.get_task_stats(user_id)
        st.session_state.refresh_stats = False

    with tab1:
        st.markdown("""
        This app helps you prioritize your tasks using AI.
        Enter your tasks below, one per line, and add tags using #hashtags.
        """)

        # Example for the user
        with st.expander("See example input"):
            st.code("""
        1. Finish quarterly report, due tomorrow #work
        2. Call mom for her birthday #personal #important
        3. Review pull requests #work #urgent
        4. Schedule dentist appointment #health
        5. Prepare presentation for client meeting on Friday #work #client
            """)

        # Get user input
        user_input = st.text_area("Enter your tasks (one per line):",
                                height=200,
                                placeholder="1. Finish report due tomorrow #work\n2. Call mom #personal")

        # Initialize session state to store graph
        if 'graph' not in st.session_state:
            st.session_state.graph = None

        # Check if LangServe API is available
        api_available = lsc.check_api_health()

        # Show API status
        api_status = st.empty()
        if not api_available:
            api_status.warning("⚠️ LangServe API is not available. Using local processing instead.")
        else:
            api_status.success("✅ LangServe API is available")

        # Process when the button is clicked
        if st.button("Prioritize My Tasks", key="prioritize_button"):
            if user_input:
                with st.spinner("Prioritizing your tasks..."):
                    try:
                        # Try to use LangServe API if available, otherwise fall back to local processing
                        if api_available:
                            result, graph = lsc.call_task_prioritizer_api(user_input)
                            st.session_state.graph = None  # No graph available from API
                        else:
                            result, graph = run_task_prioritizer(user_input)
                            st.session_state.graph = graph  # Store graph in session state

                        st.session_state.last_result = result  # Store result for display

                        # Display the result
                        st.markdown(result)

                        # Save prioritized tasks to Supabase
                        if 'prioritized_tasks' in st.session_state:
                            try:
                                # Save tasks to Supabase
                                user_id = st.session_state.user.id

                                # Display user info for debugging
                                with st.expander("Debug Info (User)"):
                                    st.write(f"User ID: {user_id}")
                                    st.write(f"User Email: {st.session_state.user.email}")
                                    st.write(f"Auth Status: {sb.get_current_user() is not None}")

                                # Try to save tasks
                                task_ids = sb.save_tasks(st.session_state.prioritized_tasks, user_id)
                                st.success(f"Saved {len(task_ids)} tasks to your account!")
                            except Exception as e:
                                if 'violates row-level security policy' in str(e):
                                    st.error("### Authentication Error\n\nUnable to save tasks due to security policy restrictions. This usually happens when:\n\n1. Your session has expired\n2. You don't have permission to write to this table\n3. The RLS policies are not set up correctly")

                                    # Show SQL setup instructions
                                    with st.expander("How to Fix RLS Issues"):
                                        st.markdown("""To fix Row Level Security (RLS) issues in Supabase, run the SQL in the `supabase_setup.sql` file in your Supabase SQL editor.""")
                                        with open('supabase_setup.sql', 'r') as f:
                                            sql_content = f.read()
                                        st.code(sql_content, language='sql')
                                else:
                                    # Re-raise for the general exception handler
                                    raise e
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        st.error(f"### Error Details\n\n**Error Type:** {type(e).__name__}\n\n**Error Message:** {str(e)}\n\n**Stack Trace:**\n```python\n{error_details}\n```")
                        st.warning("If this error persists, please contact support with the error details above.")
            else:
                st.warning("Please enter some tasks to prioritize.")

        # Show visualization button only when graph is available
        if st.session_state.graph is not None:
            if st.button("Visualize Graph", key="visualize_button"):
                with st.spinner("Generating graph visualization..."):
                    try:
                        img_bytes = visualize_graph(st.session_state.graph)
                        b64_img = base64.b64encode(img_bytes).decode()
                        st.markdown(
                            f'<img src="data:image/png;base64,{b64_img}" alt="Graph Visualization"/>',
                            unsafe_allow_html=True
                        )
                        st.download_button(
                            "Download Graph",
                            img_bytes,
                            "graph.png",
                            "image/png"
                        )
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        st.error(f"### Graph Visualization Error\n\n**Error Type:** {type(e).__name__}\n\n**Error Message:** {str(e)}\n\n**Stack Trace:**\n```python\n{error_details}\n```")
                        st.info("The graph visualization failed, but your tasks have still been prioritized successfully.")

    with tab2:
        st.header("Manage Your Tasks")

        # Fetch all tasks from Supabase
        user_id = st.session_state.user.id

        # Get tasks from Supabase
        tasks = sb.get_all_tasks(user_id)

        # If we have cached tasks, update the fetched tasks with the cached versions
        # This ensures immediate UI updates after editing
        if 'tasks_cache' in st.session_state and st.session_state.tasks_cache:
            for i, task in enumerate(tasks):
                if task['id'] in st.session_state.tasks_cache:
                    # Update with cached version
                    tasks[i] = st.session_state.tasks_cache[task['id']]

        if not tasks:
            st.info("No tasks found. Add some tasks to get started!")
        else:
            # Display tasks with editing and status controls
            st.write(f"You have {len(tasks)} tasks:")

            # Create a table-like view with CSS
            st.markdown("""
            <style>
            .task-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 10px;
            }
            .task-table th {
                background-color: var(--secondary-background-color);
                padding: 8px 12px;
                text-align: left;
                font-weight: bold;
                border-bottom: 1px solid rgba(0,0,0,0.1);
            }
            .task-table td {
                padding: 12px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                vertical-align: middle;
            }
            .task-description {
                font-weight: 500;
            }
            .task-due-date {
                color: #666;
                font-size: 0.9em;
                font-style: italic;
            }
            .task-tags {
                margin-top: 4px;
            }
            .task-tag {
                background-color: #e0e0e0;
                padding: 2px 6px;
                border-radius: 10px;
                margin-right: 5px;
                font-size: 0.8em;
            }
            .importance-high {
                color: #dc3545;
                font-weight: bold;
            }
            .importance-medium {
                color: #ffc107;
                font-weight: bold;
            }
            .importance-low {
                color: #28a745;
                font-weight: bold;
            }
            .task-score {
                color: #666;
                font-size: 0.9em;
            }
            </style>

            <table class="task-table">
                <thead>
                    <tr>
                        <th style="width: 5%;">Status</th>
                        <th style="width: 55%;">Task</th>
                        <th style="width: 15%;">Priority</th>
                        <th style="width: 15%;">Due Date</th>
                        <th style="width: 10%;">Actions</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)

            # Create task rows
            for task in tasks:
                # Create a unique key for tracking delete operation state
                delete_key = f"delete_state_{task['id']}"

                # Initialize the delete state if it doesn't exist
                if delete_key not in st.session_state:
                    st.session_state[delete_key] = "idle"

                # Create a row for each task
                cols = st.columns([0.05, 0.55, 0.15, 0.15, 0.1])

                # Column 1: Checkbox for completion status
                with cols[0]:
                    completed = st.checkbox(
                        "",
                        value=task['completed'],
                        key=f"task_{task['id']}",
                        help="Mark as completed"
                    )

                    # Update task completion status if changed
                    if completed != task['completed']:
                        if sb.update_task(task['id'], {'completed': completed}, user_id):
                            # Set flag to refresh stats
                            st.session_state.refresh_stats = True
                            st.rerun()

                # Column 2: Task description and tags
                with cols[1]:
                    st.markdown(f"**{task['description']}**")

                    # Display tags as pills
                    if task['tags']:
                        tags_md = " ".join([f":pill[#{tag}]" for tag in task['tags']])
                        st.markdown(tags_md)

                # Column 3: Importance and priority score
                with cols[2]:
                    importance_color = {
                        'High': 'red',
                        'Medium': 'orange',
                        'Low': 'green'
                    }.get(task['importance'], 'gray')

                    st.markdown(
                        f'<span style="color: {importance_color}; font-weight: bold;">{task["importance"]}</span> '
                        f'<span style="color: gray;">({task["priority_score"]:.1f})</span>',
                        unsafe_allow_html=True
                    )

                # Column 4: Due date
                with cols[3]:
                    if task['due_date']:
                        st.write(task['due_date'])
                    else:
                        st.write("—")

                # Column 5: Action buttons
                with cols[4]:
                    col5_1, col5_2 = st.columns(2)
                    with col5_1:
                        if st.button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                            st.session_state.editing_task = task
                    with col5_2:
                        # Show different buttons based on the state
                        if st.session_state[delete_key] == "idle":
                            if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                                # Set state to deleting and rerun to show spinner
                                st.session_state[delete_key] = "deleting"
                                st.rerun()
                        elif st.session_state[delete_key] == "deleting":
                            with st.spinner("Deleting..."):
                                try:
                                    if sb.delete_task(task['id'], user_id):
                                        st.session_state[delete_key] = "idle"
                                        st.success("Task deleted!")
                                        # Set flag to refresh stats
                                        st.session_state.refresh_stats = True
                                        st.rerun()
                                    else:
                                        st.session_state[delete_key] = "idle"
                                        st.error("Failed to delete task. Please try again.")
                                        st.rerun()
                                except Exception as e:
                                    st.session_state[delete_key] = "idle"
                                    st.error(f"Error deleting task: {str(e)}")
                                    st.rerun()

                # Add a separator between tasks
                st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)

            # Close the table
            st.markdown("</tbody></table>", unsafe_allow_html=True)

            # Clear all tasks button
            if st.button("Clear All Tasks", key="clear_all"):
                if st.checkbox("I understand this will delete all tasks permanently", key="confirm_clear"):
                    deleted = sb.clear_all_tasks(user_id)
                    st.success(f"Deleted {deleted} tasks!")
                    st.rerun()

        # Task editing form
        if 'editing_task' in st.session_state:
            task = st.session_state.editing_task
            st.subheader("Edit Task")

            with st.form(key=f"edit_form_{task['id']}"):
                description = st.text_input("Description", value=task['description'])

                # Convert existing due date to datetime object if it exists
                default_date = None
                if task['due_date']:
                    try:
                        from datetime import datetime
                        # Try to parse the date in various formats
                        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y"]:
                            try:
                                default_date = datetime.strptime(task['due_date'], fmt).date()
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass

                # Use date picker instead of text input
                due_date_obj = st.date_input("Due Date", value=default_date)
                # Convert the date object to string format
                due_date = due_date_obj.strftime("%Y-%m-%d") if due_date_obj else ""

                # Convert tags list to comma-separated string for editing
                tags_str = ", ".join(task['tags'])
                tags_input = st.text_input("Tags (comma-separated)", value=tags_str)

                importance = st.selectbox(
                    "Importance",
                    options=["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(task['importance']) if task['importance'] in ["High", "Medium", "Low"] else 0
                )

                priority_score = st.slider("Priority Score", min_value=1.0, max_value=10.0, value=float(task['priority_score']), step=0.1)
                completed = st.checkbox("Completed", value=task['completed'])

                submit = st.form_submit_button("Save Changes")
                cancel = st.form_submit_button("Cancel")

                if submit:
                    # Create a unique key for tracking update operation state
                    update_key = f"update_state_{task['id']}"

                    # Initialize the update state if it doesn't exist
                    if update_key not in st.session_state:
                        st.session_state[update_key] = "updating"

                        # Process tags - split by comma and strip whitespace
                        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

                        # Show updating spinner
                        with st.spinner("Updating task..."):
                            try:
                                # Update task
                                updated = sb.update_task(task['id'], {
                                    'description': description,
                                    'due_date': due_date,
                                    'tags': tags,
                                    'importance': importance,
                                    'priority_score': priority_score,
                                    'completed': completed
                                }, user_id)

                                if updated:
                                    # Update the task in session state to reflect changes immediately
                                    if 'tasks_cache' not in st.session_state:
                                        st.session_state.tasks_cache = {}

                                    # Update the cached task
                                    st.session_state.tasks_cache[task['id']] = {
                                        'id': task['id'],
                                        'description': description,
                                        'due_date': due_date,
                                        'tags': tags,
                                        'importance': importance,
                                        'priority_score': priority_score,
                                        'completed': completed,
                                        'user_id': user_id
                                    }

                                    st.success("Task updated successfully!")
                                    # Remove editing state and refresh
                                    del st.session_state.editing_task
                                    del st.session_state[update_key]
                                    # Set flag to refresh stats
                                    st.session_state.refresh_stats = True
                                    st.rerun()
                                else:
                                    st.error("Failed to update task.")
                                    del st.session_state[update_key]
                            except Exception as e:
                                st.error(f"Error updating task: {str(e)}")
                                del st.session_state[update_key]

                if cancel:
                    del st.session_state.editing_task
                    st.rerun()

    # Analytics Tab
    with tab3:
        st.header("Task Analytics")

        # Get stats from session state
        stats = st.session_state.task_stats

        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tasks", stats['total_tasks'])
        with col2:
            st.metric("Completed", stats['completed_tasks'])
        with col3:
            st.metric("Open", stats['open_tasks'])
        with col4:
            st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")

        # Create charts
        st.subheader("Task Status")

        # Task status pie chart
        if stats['total_tasks'] > 0:
            import altair as alt
            import pandas as pd

            # Create data for pie chart
            status_data = pd.DataFrame({
                'Status': ['Completed', 'Open'],
                'Count': [stats['completed_tasks'], stats['open_tasks']]
            })

            # Create pie chart
            pie_chart = alt.Chart(status_data).mark_arc().encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Status", type="nominal", scale=alt.Scale(
                    domain=['Completed', 'Open'],
                    range=['#28a745', '#dc3545']
                )),
                tooltip=['Status', 'Count']
            ).properties(width=300, height=300)

            # Display chart
            st.altair_chart(pie_chart, use_container_width=True)
        else:
            st.info("No tasks available for analysis. Add some tasks to see statistics.")

        # Task importance distribution
        st.subheader("Task Importance Distribution")
        if stats['total_tasks'] > 0:
            # Create data for bar chart
            importance_data = pd.DataFrame({
                'Importance': list(stats['importance_counts'].keys()),
                'Count': list(stats['importance_counts'].values())
            })

            # Create bar chart
            bar_chart = alt.Chart(importance_data).mark_bar().encode(
                x=alt.X('Importance:N', sort=['High', 'Medium', 'Low']),
                y='Count:Q',
                color=alt.Color('Importance:N', scale=alt.Scale(
                    domain=['High', 'Medium', 'Low'],
                    range=['#dc3545', '#ffc107', '#28a745']
                )),
                tooltip=['Importance', 'Count']
            ).properties(width=500)

            # Display chart
            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.info("No tasks available for analysis. Add some tasks to see statistics.")

        # Task completion over time
        st.subheader("Task Completion Over Time")
        if stats['completion_data']['dates']:
            # Create data for line chart
            dates = stats['completion_data']['dates']
            total = stats['completion_data']['total']
            completed = stats['completion_data']['completed']

            # Create DataFrame
            time_data = pd.DataFrame({
                'Date': dates * 2,
                'Count': total + completed,
                'Type': ['Total'] * len(dates) + ['Completed'] * len(dates)
            })

            # Create line chart
            line_chart = alt.Chart(time_data).mark_line(point=True).encode(
                x='Date:T',
                y='Count:Q',
                color=alt.Color('Type:N', scale=alt.Scale(
                    domain=['Total', 'Completed'],
                    range=['#007bff', '#28a745']
                )),
                tooltip=['Date', 'Type', 'Count']
            ).properties(width=600, height=300)

            # Display chart
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.info("Not enough historical data available. Add more tasks over time to see trends.")

    # Calendar View Tab
    with tab4:
        st.header("Task Calendar")

        # Get tasks by date from session state
        tasks_by_date = st.session_state.task_stats['tasks_by_date']

        # Create calendar view
        st.subheader("Select a date to view tasks")

        # Date picker for selecting a date
        selected_date = st.date_input("Select Date", value=datetime.now().date())
        selected_date_str = selected_date.strftime("%Y-%m-%d")

        # Display tasks for selected date
        st.subheader(f"Tasks for {selected_date_str}")

        # Get tasks for the selected date
        date_tasks = sb.get_tasks_by_date(user_id, selected_date_str)

        if date_tasks:
            for task in date_tasks:
                with st.expander(f"{task['description']} ({task['importance']})"):
                    st.write(f"**Priority Score:** {task['priority_score']:.1f}")
                    st.write(f"**Status:** {'Completed' if task['completed'] else 'Open'}")
                    if task['tags']:
                        st.write(f"**Tags:** {', '.join(['#' + tag for tag in task['tags']])}")

                    # Add quick actions
                    cols = st.columns(2)
                    with cols[0]:
                        if st.button("Mark Complete", key=f"complete_{task['id']}"):
                            if sb.update_task(task['id'], {'completed': True}, user_id):
                                st.success("Task marked as complete!")
                                # Set flag to refresh stats
                                st.session_state.refresh_stats = True
                                st.rerun()
                    with cols[1]:
                        if st.button("Edit", key=f"cal_edit_{task['id']}"):
                            st.session_state.editing_task = task
                            # Switch to Manage Tasks tab
                            st.query_params['tab'] = "manage"
                            st.rerun()
        else:
            st.info(f"No tasks due on {selected_date_str}. Select another date or add tasks with this due date.")

        # Calendar heatmap
        st.subheader("Task Distribution Calendar")

        # Create a heatmap of tasks by date
        if tasks_by_date:
            import altair as alt
            import pandas as pd
            from datetime import datetime, timedelta

            # Get the current month's date range
            today = datetime.now().date()
            start_of_month = today.replace(day=1)
            end_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Create date range for the current month
            date_range = [start_of_month + timedelta(days=i) for i in range((end_of_month - start_of_month).days + 1)]
            date_strs = [d.strftime("%Y-%m-%d") for d in date_range]

            # Count tasks for each date
            task_counts = [len(tasks_by_date.get(d, [])) for d in date_strs]

            # Create DataFrame for heatmap
            calendar_data = pd.DataFrame({
                'date': date_strs,
                'count': task_counts,
                'weekday': [datetime.strptime(d, "%Y-%m-%d").strftime("%a") for d in date_strs],
                'week': [(datetime.strptime(d, "%Y-%m-%d").day - 1) // 7 + 1 for d in date_strs],
                'day': [datetime.strptime(d, "%Y-%m-%d").day for d in date_strs]
            })

            # Create heatmap
            heatmap = alt.Chart(calendar_data).mark_rect().encode(
                x=alt.X('weekday:O', title='Day of Week', sort=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
                y=alt.Y('week:O', title='Week of Month'),
                color=alt.Color('count:Q', scale=alt.Scale(scheme='blues'), title='Task Count'),
                tooltip=['date', 'count']
            ).properties(width=600, height=300)

            # Display heatmap
            st.altair_chart(heatmap, use_container_width=True)

            # Add note about clicking on dates
            st.info("💡 Tip: Use the date picker above to select a specific date and view tasks due on that date.")
        else:
            st.info("No tasks with due dates available. Add tasks with due dates to see the calendar view.")

# Add footer
st.markdown("---")
st.markdown("Made with LangGraph and Streamlit")
