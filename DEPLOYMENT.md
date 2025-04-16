# Deployment Guide for Personal Task Prioritizer

This guide provides instructions for deploying your Personal Task Prioritizer application to various platforms.

## Prerequisites

- Git repository with your application code
- Supabase account and project
- OpenAI API key

## Option 1: Streamlit Cloud Deployment

### Step 1: Prepare Your Repository

Ensure your repository includes:
- app.py
- requirements.txt
- .streamlit/config.toml (optional)

### Step 2: Deploy on Streamlit Cloud

1. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud) and sign up
2. Connect your GitHub repository
3. Set the main file path to "app.py"
4. Add your environment variables in the Streamlit Cloud secrets section:
   ```
   OPENAI_API_KEY=your-openai-api-key
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key
   LANGSERVE_API_URL=your-langserve-api-url
   LANGSERVE_API_KEY=your-langserve-api-key
   REDIRECT_URL=your-app-url
   SITE_URL=your-app-url
   ```
5. Deploy your app

### Step 3: Deploy LangServe API (if needed)

If you need the LangServe API as a separate service:
1. Use a platform like Render.com or Heroku to deploy langserve_api.py
2. Update the LANGSERVE_API_URL in your Streamlit Cloud secrets

## Option 2: Render.com Deployment

### Step 1: Deploy the LangServe API

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `python langserve_api.py`
5. Add environment variables from your .env file
6. Deploy

### Step 2: Deploy the Streamlit App

1. Create another Web Service
2. Connect the same GitHub repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `streamlit run app.py`
5. Add environment variables, including the URL of your LangServe API
6. Deploy

## Option 3: Heroku Deployment

### Step 1: Install Heroku CLI

```bash
brew install heroku/brew/heroku  # For macOS
```

### Step 2: Deploy to Heroku

```bash
heroku login
heroku create your-app-name
git push heroku main
heroku config:set OPENAI_API_KEY=your-key SUPABASE_URL=your-url SUPABASE_KEY=your-key
```

## Option 4: Docker Deployment

### Step 1: Build the Docker Image

```bash
docker build -t personal-task-prioritizer .
```

### Step 2: Run the Docker Container

```bash
docker run -p 8501:8501 -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_KEY=your-key \
  -e LANGSERVE_API_KEY=your-key \
  personal-task-prioritizer
```

### Step 3: Using Docker Compose

```bash
docker-compose up
```

## Updating Supabase Configuration

1. Log in to your Supabase Dashboard
2. Go to Authentication → URL Configuration
3. Update the Site URL to your deployed application URL
4. Update the Redirect URLs to include your deployed application URL
5. Ensure Row Level Security is properly configured

## Troubleshooting

### Common Issues

1. **Environment Variables**: Ensure all environment variables are correctly set
2. **CORS Issues**: If your frontend can't communicate with your API, check CORS settings
3. **Database Connection**: Verify Supabase connection settings
4. **Memory/CPU Limitations**: If your app crashes, you might need to upgrade your deployment plan

### Checking Logs

- Streamlit Cloud: View logs in the dashboard
- Render.com: View logs in the dashboard
- Heroku: `heroku logs --tail`
- Docker: `docker logs container_id`

## Maintenance

1. **Updates**: Regularly update your dependencies
2. **Monitoring**: Set up monitoring for your application
3. **Backups**: Ensure your Supabase database is backed up regularly
