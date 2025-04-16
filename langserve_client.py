import requests
import os
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API URL and key from environment or use defaults
LANGSERVE_API_URL = os.getenv("LANGSERVE_API_URL", "http://localhost:8000")
LANGSERVE_API_KEY = os.getenv("LANGSERVE_API_KEY", "dev-api-key-change-me")

def call_task_prioritizer_api(user_input: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Call the LangServe API to prioritize tasks.
    
    Args:
        user_input: The user's task input
        
    Returns:
        Tuple containing:
        - The prioritized tasks output as a string
        - None (since we're not returning the graph)
    """
    api_url = f"{LANGSERVE_API_URL}/api/prioritize"
    
    # Prepare the headers with API key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": LANGSERVE_API_KEY
    }
    
    # Prepare the input for the API
    payload = {
        "input": {
            "tasks": [],
            "prioritized_tasks": [],
            "user_input": user_input,
            "current_step": "",
            "errors": [],
            "output": ""
        }
    }
    
    try:
        # Call the API
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse the response
        result = response.json()
        
        # Extract the output
        if "output" in result:
            output = result["output"].get("output", "No output generated.")
            return output, None
        else:
            return "Error: Unexpected API response format", None
    except requests.exceptions.RequestException as e:
        return f"Error calling task prioritizer API: {str(e)}", None

def check_api_health() -> bool:
    """
    Check if the LangServe API is healthy.
    
    Returns:
        bool: True if the API is healthy, False otherwise
    """
    try:
        response = requests.get(f"{LANGSERVE_API_URL}/health")
        return response.status_code == 200
    except:
        return False
