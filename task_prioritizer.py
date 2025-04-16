import os
from typing import List, Dict, Annotated, Sequence
from typing_extensions import TypedDict  # Use typing_extensions instead of typing
from datetime import datetime

# Import necessary packages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field  # Import directly from pydantic
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define our task structure
class TaskItem(TypedDict):
    description: str
    due_date: str
    tags: List[str]
    importance: str
    priority_score: float

# Define our application state
class TaskPrioritizerState(TypedDict):
    tasks: List[TaskItem]
    prioritized_tasks: List[TaskItem]
    user_input: str
    current_step: str
    errors: List[str]
    output: str

# Initialize the LLM (Language Model)
llm = ChatOpenAI(model="gpt-3.5-turbo")

# Define the task parsing function
def parse_tasks(state):
    """Parse the user input into structured task items."""
    # Create a copy of the state so we don't modify the original
    new_state = state.copy()

    if not state["user_input"]:
        new_state["errors"].append("No tasks provided.")
        return new_state

    # Create a prompt for the AI to parse tasks
    system_prompt = """
    You are a task parser. Parse the user's input into a list of tasks.
    Extract the task description, due date (if provided), and any tags (prefixed with #).
    Return the tasks as a list of JSON objects.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Parse these tasks: {state['user_input']}")
    ]

    # Get response from the language model
    response = llm.invoke(messages)

    try:
        import json
        import re

        # Get the response content
        content = response.content

        # Debug information
        debug_info = f"\nResponse type: {type(response)}\nContent type: {type(content)}\nContent length: {len(content)}"

        # Try to extract JSON from the response if it's not already valid JSON
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            # Found JSON in code block
            content = json_match.group(1).strip()
        else:
            # Try to find JSON array directly
            json_match = re.search(r'\[\s*{[\s\S]*}\s*\]', content)
            if json_match:
                content = json_match.group(0)

        # Extract tasks from AI response
        try:
            tasks_data = json.loads(content)
        except json.JSONDecodeError as json_err:
            # If still failing, try a more aggressive approach to fix common JSON issues
            fixed_content = content.replace("'", '"')  # Replace single quotes with double quotes
            fixed_content = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', fixed_content)  # Add quotes to keys

            try:
                tasks_data = json.loads(fixed_content)
            except json.JSONDecodeError:
                # If still failing, raise a more detailed error
                error_msg = f"JSON parsing failed: {str(json_err)}\nRaw content: {content[:100]}...{debug_info}"
                raise ValueError(error_msg)

        # Validate tasks_data is a list
        if not isinstance(tasks_data, list):
            raise TypeError(f"Expected a list of tasks, got {type(tasks_data)}")

        # Format tasks properly
        parsed_tasks = []
        for task in tasks_data:
            # Ensure task is a dictionary
            if not isinstance(task, dict):
                raise TypeError(f"Expected dictionary for task, got {type(task)}")

            # Ensure tags is a list
            tags = task.get("tags", [])
            if not isinstance(tags, list):
                if isinstance(tags, str):
                    # Convert comma-separated string to list or extract hashtags
                    if ',' in tags:
                        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
                    else:
                        # Extract hashtags
                        hashtags = re.findall(r'#(\w+)', tags)
                        if hashtags:
                            tags = hashtags
                        else:
                            tags = [tags]  # Use the whole string as a single tag
                else:
                    tags = []

            parsed_task = TaskItem(
                description=task.get("description", ""),
                due_date=task.get("due_date", ""),
                tags=tags,
                importance="",  # Will be filled in later
                priority_score=0.0  # Will be filled in later
            )
            parsed_tasks.append(parsed_task)

        new_state["tasks"] = parsed_tasks
        new_state["current_step"] = "tasks_parsed"
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f"Failed to parse tasks: {str(e)}\nTrace: {error_trace[:500]}"
        new_state["errors"].append(error_msg)

    return new_state

# Define the prioritization function
def prioritize_tasks(state):
    """Analyze and prioritize the tasks based on various factors."""
    new_state = state.copy()

    if not state["tasks"]:
        new_state["errors"].append("No tasks to prioritize.")
        return new_state

    system_prompt = """
    You are a task prioritization expert. Your job is to analyze tasks and assign:
    1. An importance level (High, Medium, Low)
    2. A priority score from 1-10 (10 being highest priority)

    Consider the following factors:
    - Due date: more urgent dates should have higher priority
    - Tags: certain tags like #urgent or #important should increase priority
    - Task description: look for keywords indicating importance or urgency

    Return the tasks in JSON format with added importance and priority_score fields.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Prioritize these tasks: {state['tasks']}")
    ]

    response = llm.invoke(messages)

    try:
        import json
        import re

        # Get the response content
        content = response.content

        # Debug information
        debug_info = f"\nResponse type: {type(response)}\nContent type: {type(content)}\nContent length: {len(content)}"

        # Try to extract JSON from the response if it's not already valid JSON
        # Sometimes the LLM might wrap the JSON in markdown code blocks or add extra text
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            # Found JSON in code block
            content = json_match.group(1).strip()
        else:
            # Try to find JSON array directly
            json_match = re.search(r'\[\s*{[\s\S]*}\s*\]', content)
            if json_match:
                content = json_match.group(0)

        # Extract prioritized tasks from AI response
        try:
            prioritized_tasks_data = json.loads(content)
        except json.JSONDecodeError as json_err:
            # If still failing, try a more aggressive approach to fix common JSON issues
            fixed_content = content.replace("'", '"')  # Replace single quotes with double quotes
            fixed_content = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', fixed_content)  # Add quotes to keys

            try:
                prioritized_tasks_data = json.loads(fixed_content)
            except json.JSONDecodeError:
                # If still failing, raise a more detailed error
                error_msg = f"JSON parsing failed: {str(json_err)}\nRaw content: {content[:100]}...{debug_info}"
                raise ValueError(error_msg)

        # Format tasks properly
        prioritized_tasks = []
        for task in prioritized_tasks_data:
            # Ensure task is a dictionary
            if not isinstance(task, dict):
                raise TypeError(f"Expected dictionary for task, got {type(task)}")

            # Get priority score with fallback and validation
            try:
                priority_score = float(task.get("priority_score", 0))
            except (ValueError, TypeError):
                priority_score = 5.0  # Default to middle priority if invalid

            # Ensure tags is a list
            tags = task.get("tags", [])
            if not isinstance(tags, list):
                if isinstance(tags, str):
                    # Convert comma-separated string to list
                    tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
                else:
                    tags = []

            prioritized_task = TaskItem(
                description=task.get("description", ""),
                due_date=task.get("due_date", ""),
                tags=tags,
                importance=task.get("importance", ""),
                priority_score=priority_score
            )
            prioritized_tasks.append(prioritized_task)

        # Sort by priority score (descending)
        prioritized_tasks.sort(key=lambda x: x["priority_score"], reverse=True)

        new_state["prioritized_tasks"] = prioritized_tasks
        new_state["current_step"] = "tasks_prioritized"
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f"Failed to prioritize tasks: {str(e)}\nTrace: {error_trace[:500]}"
        new_state["errors"].append(error_msg)

    return new_state

# Function to format the final output
def format_output(state):
    """Format the prioritized tasks into a readable output."""
    new_state = state.copy()

    system_prompt = """
    You are a personal assistant presenting prioritized tasks.
    Format the list of prioritized tasks in a clear, organized way.
    Include a helpful summary of why tasks were prioritized as they were.
    Use markdown for formatting to make it easy to read.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Format these prioritized tasks for presentation to the user: {state['prioritized_tasks']}")
    ]

    response = llm.invoke(messages)
    new_state["output"] = response.content
    new_state["current_step"] = "output_formatted"

    return new_state

# Define router function to determine next steps
def router(state):
    if state["errors"]:
        return "handle_errors"

    current_step = state.get("current_step", "")

    # We no longer need to check for empty current_step since we set an entry point
    if current_step == "tasks_parsed":
        return "prioritize_tasks"
    elif current_step == "tasks_prioritized":
        return "format_output"
    else:
        return END

# Function to handle errors
def handle_errors(state):
    new_state = state.copy()

    error_message = "The following errors occurred:\n" + "\n".join(state["errors"])
    new_state["output"] = error_message

    return new_state

# Build the graph
def build_task_prioritizer_graph():
    # Initialize the graph
    workflow = StateGraph(TaskPrioritizerState)

    # Add nodes
    workflow.add_node("parse_tasks", parse_tasks)
    workflow.add_node("prioritize_tasks", prioritize_tasks)
    workflow.add_node("format_output", format_output)
    workflow.add_node("handle_errors", handle_errors)

    # Add edges - use router to determine the first step
    workflow.set_entry_point("parse_tasks")
    workflow.add_conditional_edges("parse_tasks", router)
    workflow.add_conditional_edges("prioritize_tasks", router)
    workflow.add_conditional_edges("format_output", lambda _: END)
    workflow.add_conditional_edges("handle_errors", lambda _: END)

    # Compile the graph
    return workflow.compile()

# Function to run the Task Prioritizer
def run_task_prioritizer(user_input):
    # Initialize the graph
    graph = build_task_prioritizer_graph()

    # Initialize the state
    initial_state = TaskPrioritizerState(
        tasks=[],
        prioritized_tasks=[],
        user_input=user_input,
        current_step="",
        errors=[],
        output=""
    )

    # Run the graph
    outputs = []
    for output_step in graph.stream(initial_state):
        outputs.append(output_step)

    # Get the final state from the last output
    if not outputs:
        raise ValueError("No outputs generated from the graph execution. Check your graph configuration.")

    final_output = outputs[-1]  # Get the last output

    try:
        # Handle different output structures that might come from LangGraph
        if hasattr(final_output, 'values') and callable(final_output.values):
            # If values is a method, call it
            values = final_output.values()
            if values and len(list(values)) > 0:
                # Convert dict_values to list before accessing
                final_state = list(values)[0]
            else:
                raise ValueError("No values returned from final_output.values()")
        elif isinstance(final_output, dict):
            # If it's a dictionary, check for known keys
            if 'handle_errors' in final_output:
                # This is the error state, use it directly
                final_state = final_output['handle_errors']
            elif 'format_output' in final_output:
                # This is the output state, use it directly
                final_state = final_output['format_output']
            elif len(final_output) == 1:
                # If there's only one key, use its value
                final_state = list(final_output.values())[0]
            else:
                # Just use the whole dict as the state
                final_state = final_output
        else:
            # Try to convert to dict if possible
            final_state = dict(final_output)
    except (AttributeError, TypeError, IndexError, ValueError) as e:
        error_msg = f"Error accessing final state: {str(e)}\nOutput type: {type(final_output)}\nOutput value: {final_output}"
        raise RuntimeError(error_msg)

    # Store prioritized tasks in session state if available
    import streamlit as st
    if "prioritized_tasks" in final_state and final_state["prioritized_tasks"]:
        st.session_state.prioritized_tasks = final_state["prioritized_tasks"]

    # Return both the final output and the graph object
    return final_state.get("output", "No output generated."), graph

# Example usage
if __name__ == "__main__":
    example_input = """
    1. Finish the quarterly report, due tomorrow #work
    2. Call mom for her birthday #personal #important
    3. Review pull requests #work #urgent
    4. Schedule dentist appointment #health
    5. Prepare presentation for client meeting on Friday #work #client
    """

    result, graph = run_task_prioritizer(example_input)
    print(result)