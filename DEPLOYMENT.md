# Deployment Guide

## Quick Setup

1. **Clone/Extract Project**
2. **Install Dependencies**: `pip install -r dependencies.txt`
3. **Set Environment Variables**:
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   export GOOGLE_AI_API_KEY="your_google_ai_studio_key"
   ```
4. **Initialize Database**: `python -c "from app import app, db; app.app_context().push(); db.create_all()"`
5. **Run**: `gunicorn --bind 0.0.0.0:5000 main:app`

## Environment Variables Required

- `DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_AI_API_KEY`: Get from aistudio.google.com (free tier available)

## Optional API Keys (for fallback)

- `OPENROUTER_API_KEY`: openrouter.ai
- `ANTHROPIC_API_KEY`: console.anthropic.com  
- `OPENAI_API_KEY`: platform.openai.com

## Database Setup

The application will automatically create tables on first run. Ensure PostgreSQL is running and accessible.

## File Uploads

Create `uploads/` directory with write permissions for document storage.

## Production Deployment

- Use nginx as reverse proxy
- Set up SSL certificates
- Configure environment-specific settings
- Monitor logs and performance