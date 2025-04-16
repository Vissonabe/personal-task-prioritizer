import streamlit as st
import supabase_client as sb

st.set_page_config(
    page_title="Reset Password - Personal Task Prioritizer",
    page_icon="🔑"
)

st.title("Reset Your Password")

# Get URL parameters
query_params = st.query_params

# Check if we have the recovery token
if 'type' in query_params and query_params.get('type') == 'recovery':
    # Extract token from URL
    token = None
    if 'token' in query_params:
        token = query_params.get('token')

    if token:
        st.session_state.recovery_token = token
        st.success("Password reset link verified!")

    # Show password reset form
    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit = st.form_submit_button("Reset Password")

        if submit:
            if not new_password:
                st.error("Please enter a new password")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    # Update the password
                    response = sb.update_password(new_password)
                    st.success("Password has been reset successfully!")
                    st.info("You can now return to the main app and log in with your new password.")

                    # Add a button to go back to the main app
                    if st.button("Return to Login"):
                        # Clear query parameters
                        for param in st.query_params.keys():
                            del st.query_params[param]
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to reset password: {str(e)}")
                    st.info("Please try again or contact support if the issue persists.")
else:
    st.warning("Invalid or missing recovery token. Please use the link from your email.")
    st.info("If you need a new password reset link, please go back to the main app and request one.")

    # Add a button to go back to the main app
    if st.button("Return to Main App"):
        st.switch_page("app.py")
