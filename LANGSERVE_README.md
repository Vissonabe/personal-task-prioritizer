# LangServe Integration for Personal Task Prioritizer

This document explains how to use the LangServe integration with the Personal Task Prioritizer application.

## What is LangServe?

LangServe is a framework developed by LangChain that allows you to deploy LangChain runnables and chains as REST APIs. In this application, we use LangServe to separate the LLM-based task prioritization logic from the Streamlit frontend.

## Benefits

- **Separation of Concerns**: The LLM processing logic is separated from the Streamlit frontend
- **Scalability**: The Streamlit frontend remains lightweight while the LLM processing happens on a separate server
- **Reusability**: The API can be used by other applications or interfaces
- **Monitoring**: Better tracking of usage, errors, and performance

## Setup

1. Make sure you have installed all the required packages:
   ```bash
   pip install langserve fastapi uvicorn
   ```

2. Configure the LangServe API in the `.env` file:
   ```
   LANGSERVE_API_URL=http://localhost:8000
   LANGSERVE_API_KEY=your-api-key-here
   LANGSERVE_PORT=8000
   ```

## Running the Application

### Option 1: Run LangServe API and Streamlit separately

1. Start the LangServe API server:
   ```bash
   python launch_langserve.py
   ```

2. In a separate terminal, start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

### Option 2: Use the combined launcher (if available)

```bash
python launch.py
```

## API Authentication

The LangServe API is protected with a simple API key authentication. Make sure the API key in your Streamlit app matches the one configured for the LangServe API server.

## Endpoints

- **Health Check**: `GET /health` - Check if the API is running
- **Task Prioritization**: `POST /api/prioritize` - Prioritize tasks using LLMs
- **API Info**: `GET /api/info` - Get information about the API

## Fallback Mechanism

If the LangServe API is not available, the application will automatically fall back to local processing using the built-in task prioritizer.

## Troubleshooting

1. **API Not Available**: If you see a warning that the LangServe API is not available, make sure the API server is running and the URL in the `.env` file is correct.

2. **Authentication Error**: If you see an authentication error, make sure the API key in the `.env` file matches the one configured for the LangServe API server.

3. **Port Already in Use**: If the LangServe API server fails to start because the port is already in use, you can either:
   - Use the `launch_langserve.py` script which will detect and handle this situation
   - Manually kill the process using the port: `lsof -i :8000 -t | xargs kill`
   - Change the port in the `.env` file
