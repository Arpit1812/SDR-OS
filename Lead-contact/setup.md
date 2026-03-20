# Backend Setup Guide

This guide will help you set up the Lead Contact backend API.

## Prerequisites

- Python 3.8 or higher
- MongoDB instance (local or cloud)
- Google Cloud Project with OAuth credentials
- (Optional) Trigger.dev account for background job processing

## Installation Steps

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values. See `.env.example` for required variables.

### 4. Set Up MongoDB

#### Option A: Local MongoDB

1. Install MongoDB locally
2. Start MongoDB service
3. Use connection string: `mongodb://localhost:27017`

#### Option B: MongoDB Atlas (Cloud)

1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Get your connection string from the cluster settings
4. Update `MONGO_URI` in `.env`

### 5. Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs (e.g., `http://localhost:8000/api/auth/google/callback`)
5. Copy Client ID and Client Secret to `.env`

### 6. (Optional) Set Up Google Generative AI

If you want to use AI features:

1. Enable Generative AI API in Google Cloud Console
2. Create an API key
3. Add `GOOGLE_GENERATIVE_AI_API_KEY` to `.env`

### 7. (Optional) Set Up Trigger.dev

If you want background job processing:

1. Sign up at [Trigger.dev](https://trigger.dev)
2. Create a new project
3. Get your API key and project ID
4. Add `TRIGGER_API_KEY` and update `TRIGGER_API_URL` in `.env`

## Running the Application

### Development Mode

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
backend/
├── api/                    # API routes and dependencies
│   ├── routes/            # Route handlers
│   ├── dependencies/      # Shared dependencies
│   └── webhooks/          # Webhook handlers
├── core/                   # Core business logic
│   ├── auth/              # Authentication logic
│   ├── campaigns/         # Campaign models
│   ├── calendar/          # Calendar integration
│   ├── templates/         # Email templates
│   └── csv/               # CSV processing
├── db/                     # Database layer
│   └── mongodb/           # MongoDB repositories
├── providers/              # External provider integrations
│   └── gmail/             # Gmail provider
├── integrations/           # Third-party integrations
├── services/               # Business services
├── utils/                  # Utility functions
├── config.py              # Configuration settings
└── main.py                # Application entry point
```

## API Endpoints

### Authentication
- `POST /api/auth/google` - Initiate Google OAuth flow
- `GET /api/auth/google/callback` - OAuth callback handler
- `GET /api/auth/me` - Get current user info

### Providers
- `GET /api/providers` - List all providers
- `POST /api/providers` - Add a provider
- `DELETE /api/providers/{id}` - Remove a provider

### Contacts
- `GET /api/contacts` - List contacts
- `POST /api/contacts` - Create contact
- `GET /api/contacts/by-source/{source}` - Get contacts by CSV source
- `DELETE /api/contacts/{id}` - Delete contact

### Templates
- `GET /api/templates` - List templates
- `POST /api/templates` - Create template
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Campaigns
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign details
- `PUT /api/campaigns/{id}` - Update campaign

### Prompts
- `GET /api/prompts` - List prompts
- `POST /api/prompts` - Create prompt
- `PUT /api/prompts/{id}` - Update prompt
- `DELETE /api/prompts/{id}` - Delete prompt

### Calendar
- `GET /api/calendar/availability` - Get calendar availability
- `POST /api/calendar/book` - Book a meeting

## Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### Test Authentication Flow

1. Navigate to `http://localhost:8000/api/auth/google` in browser
2. Complete OAuth flow
3. Check callback endpoint receives tokens

## Troubleshooting

### MongoDB Connection Issues

- Verify MongoDB is running
- Check connection string format
- Ensure network access is allowed (for Atlas)

### OAuth Issues

- Verify redirect URI matches Google Cloud Console settings
- Check that Gmail API is enabled
- Ensure OAuth consent screen is configured

### Import Errors

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version compatibility

## Environment Variables

See `.env.example` for all required and optional environment variables.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)

