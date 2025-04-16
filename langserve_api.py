#!/usr/bin/env python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from pydantic import BaseModel, Field
from task_prioritizer import build_task_prioritizer_graph
import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

# Get API key from environment or use a default for development
API_KEY = os.getenv("LANGSERVE_API_KEY", "dev-api-key-change-me")

# Create a FastAPI app
app = FastAPI(
    title="Task Prioritizer API",
    version="1.0",
    description="API for prioritizing tasks using LLMs"
)

# Add CORS middleware to allow requests from the Streamlit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify the API key."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

# Define input and output models for better OpenAPI schema generation
class TaskItem(BaseModel):
    description: str = Field(..., description="Task description")
    due_date: str = Field("", description="Due date for the task")
    tags: List[str] = Field([], description="Tags associated with the task")
    importance: str = Field("", description="Importance level (High, Medium, Low)")
    priority_score: float = Field(0.0, description="Priority score from 1-10")

class TaskPrioritizerInput(BaseModel):
    user_input: str = Field(..., description="Raw user input with tasks")

class TaskPrioritizerOutput(BaseModel):
    output: str = Field(..., description="Formatted prioritized tasks output")
    prioritized_tasks: Optional[List[TaskItem]] = Field(None, description="List of prioritized tasks")

# Create the task prioritizer graph
task_prioritizer = build_task_prioritizer_graph()

# Add a custom endpoint for task prioritization
@app.post("/api/prioritize", dependencies=[Depends(verify_api_key)])
async def prioritize_tasks(input_data: TaskPrioritizerInput):
    """Prioritize tasks using LLMs."""
    # Convert the simplified input to the format expected by the task prioritizer
    full_input = {
        "tasks": [],
        "prioritized_tasks": [],
        "user_input": input_data.user_input,
        "current_step": "",
        "errors": [],
        "output": ""
    }

    # Run the task prioritizer
    try:
        result = task_prioritizer.invoke(full_input)

        # Extract the output
        output = result.get("output", "No output generated.")
        prioritized_tasks = result.get("prioritized_tasks", [])

        # Return the result
        return {
            "output": output,
            "prioritized_tasks": prioritized_tasks
        }
    except Exception as e:
        print(f"Error prioritizing tasks: {str(e)}")
        return {
            "error": str(e),
            "output": "Error occurred while prioritizing tasks.",
            "prioritized_tasks": []
        }

# Add a simple health check endpoint (no authentication required)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Add an endpoint to get API information
@app.get("/api/info", dependencies=[Depends(verify_api_key)])
async def api_info():
    """Get information about the API."""
    return {
        "name": "Task Prioritizer API",
        "version": "1.0",
        "description": "API for prioritizing tasks using LLMs",
        "endpoints": [
            {
                "path": "/api/prioritize",
                "method": "POST",
                "description": "Prioritize tasks using LLMs"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    # Get port from environment or use default
    port = int(os.getenv("LANGSERVE_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
