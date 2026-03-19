# Lead Contact - AI-Powered Email Marketing & Sales Automation Platform

A full-stack application for managing email marketing campaigns with AI-powered auto-reply management, OAuth integration, and automated meeting scheduling.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage Workflow](#usage-workflow)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)

---

## 📌 Overview

**Lead Contact** is an enterprise-grade email marketing platform designed for:
- **B2B Sales Teams** - Manage outbound prospecting campaigns
- **Marketing Teams** - Execute personalized bulk email campaigns
- **Sales Development Reps** - Auto-reply to prospects with AI, schedule meetings automatically
- **Growth Teams** - Nurture leads with intelligent conversation management

The platform automates the entire email campaign lifecycle: from contact import → personalized email sending → intelligent reply handling → meeting scheduling.

---

## ✨ Key Features

### 1. **Email Campaign Management**
- 📧 Upload CSV contact lists (email, name, company, phone, etc.)
- 🎨 Create dynamic email templates with variable personalization
- 📤 Send bulk personalized campaigns via Gmail OAuth
- 📊 Real-time campaign progress tracking
- 📝 Detailed email logs with delivery status
- 🔄 Batch processing with automatic rate limit management

### 2. **AI-Powered Auto-Reply System**
- 🤖 Intelligent auto-responses to prospect replies
- 💬 Create custom AI prompts for different campaign types
- 🧠 Google Gemini AI integration for natural language responses
- 🎯 Conversation threading with configurable reply limits
- 📈 Professional engagement without manual intervention

### 3. **Secure OAuth Integration**
- 🔐 Gmail OAuth 2.0 for secure email sending
- 🔄 Automatic token refresh during long-running campaigns
- 👥 Multi-user support (each user connects their own email)
- 🛡️ No password storage - secure credential management

### 4. **Calendar Integration**
- 📅 Cal.com integration for meeting scheduling
- ⚡ Auto-schedule meetings from AI conversations
- 📆 Calendar availability sync before outreach

### 5. **Analytics & Tracking**
- 📊 Campaign statistics (sent, failed, in-progress)
- 📋 Email delivery logs with error tracking
- ⏱️ Campaign timing and duration metrics
- 📈 Contact upload history and stats

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Lead Contact Platform                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │   React Frontend │    │  FastAPI Backend │                 │
│  │   (Port 3000)    │───▶│  (Port 8000)     │                 │
│  │                  │    │                  │                 │
│  │ • Campaign UI    │    │ • REST APIs      │                 │
│  │ • Contact Upload │    │ • OAuth Service  │                 │
│  │ • Templates      │    │ • MongoDB ORM    │                 │
│  └──────────────────┘    │ • Email Logs     │                 │
│                          │ • Cal.com Client │                 │
│                          └─────────┬────────┘                 │
│                                    │                           │
│                          ┌─────────▼────────┐                 │
│                          │    MongoDB       │                 │
│                          │ (Port 27017)     │                 │
│                          │                  │                 │
│                          │ • Campaigns      │                 │
│                          │ • Contacts       │                 │
│                          │ • Templates      │                 │
│                          │ • Email Logs     │                 │
│                          │ • Tokens         │                 │
│                          └──────────────────┘                 │
│                                    │                           │
│                          ┌─────────▼────────────┐              │
│                          │  Trigger.dev Worker  │              │
│                          │  (Background Jobs)   │              │
│                          │                      │              │
│                          │ • Email Sending      │              │
│                          │ • Token Refresh      │              │
│                          │ • Batch Processing   │              │
│                          │ • Progress Updates   │              │
│                          └──────────────────────┘              │
│                                    │                           │
│                    ┌───────────────┼───────────────┐            │
│                    │               │               │            │
│          ┌─────────▼──┐  ┌────────▼─────┐  ┌─────▼──────┐   │
│          │  Gmail API │  │  Cal.com API  │  │ Gemini API │   │
│          │ (Sending)  │  │ (Scheduling)  │  │   (AI)     │   │
│          └────────────┘  └───────────────┘  └────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: MongoDB with Motor async driver
- **Authentication**: Google OAuth 2.0, JWT (python-jose)
- **Async**: AsyncIO, Pydantic
- **External Services**: Gmail API, Cal.com API, Google Gemini AI

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **UI/Styling**: CSS Modules

### Background Worker
- **Runtime**: Node.js 18+
- **Task Queue**: Trigger.dev
- **AI**: Vercel AI SDK with Google Gemini
- **Validation**: Zod

### Data Storage
- **Primary DB**: MongoDB
- **Cache**: In-memory (can be extended with Redis)

---

## 💻 System Requirements

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **npm/yarn**: Package manager
- **MongoDB**: 5.0 or higher (local or MongoDB Atlas cloud)
- **Git**: Version control

### External Accounts Required
- **Google Cloud Project** - For Gmail OAuth & Gemini API
- **Trigger.dev Account** - For background job processing
- **Cal.com Account** - (Optional) For meeting scheduling
- **MongoDB Atlas** - (Optional) For cloud database

---

## 📦 Installation Guide

### Step 1: Clone the Repository

```bash
cd c:\Projects\Alerix-SDR
# Repository already cloned
```

### Step 2: Install Dependencies

#### Backend (FastAPI)
```bash
cd Lead-contact

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Frontend (React/Vite)
```bash
cd Lead-contact-frontend

# Install Node dependencies
npm install
```

#### Background Worker (Trigger.dev)
```bash
cd Lead-contact-trigger

# Install Node dependencies
npm install
```

### Step 3: Setup MongoDB

**Option A: Local MongoDB**
```bash
# Download from https://www.mongodb.com/try/download/community
# Install and start MongoDB service
# Default connection: mongodb://localhost:27017
```

**Option B: MongoDB Atlas (Cloud)**
```bash
# 1. Go to https://www.mongodb.com/cloud/atlas
# 2. Create free cluster
# 3. Get connection string: mongodb+srv://user:password@cluster.mongodb.net/dbname
```

### Step 4: Setup Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable these APIs:
   - Gmail API
   - Google Generative AI API (for Gemini)
4. Create OAuth 2.0 credentials:
   - Type: Web Application
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:3000/auth/callback`
5. Save your `Client ID` and `Client Secret`

### Step 5: Setup Trigger.dev (Optional)

1. Go to [Trigger.dev](https://trigger.dev)
2. Sign up and create a new project
3. Copy your `Project ID` and `Secret Key`
4. For local development, you can skip this initially

---

## ⚙️ Configuration

### Backend Environment Variables

Create `.env` file in `Lead-contact/` directory:

```plaintext
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Google Gemini AI (for auto-replies)
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key_here

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=lead_contact

# Trigger.dev (Background Job Processing)
TRIGGER_API_KEY=your_trigger_api_key_here
TRIGGER_WEBHOOK_SECRET=your_webhook_secret_here

# Backend Configuration
BACKEND_URL=http://localhost:8000
DEBUG=True
LOG_LEVEL=INFO
```

### Frontend Environment Variables

Create `.env.local` file in `Lead-contact-frontend/` directory:

```plaintext
VITE_BACKEND_URL=http://localhost:8000
```

### Trigger Worker Environment Variables

Create `.env` file in `Lead-contact-trigger/` directory:

```plaintext
TRIGGER_SECRET_KEY=your_trigger_secret_key
TRIGGER_PROJECT_ID=your_trigger_project_id

# Same Google credentials as backend
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Backend URL for callbacks
BACKEND_URL=http://localhost:8000
```

---

## 🚀 Running the Application

### Terminal Setup

You'll need 3 terminals running simultaneously:

#### Terminal 1: Start Backend (FastAPI)

```bash
cd Lead-contact

# Activate virtual environment (if not already activated)
# Windows:
venv\Scripts\activate

# Run backend
python main.py
```

Backend will be available at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

#### Terminal 2: Start Frontend (React/Vite)

```bash
cd Lead-contact-frontend

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

#### Terminal 3: Start Trigger Worker (Optional)

```bash
cd Lead-contact-trigger

# Run in development mode
npm run dev
```

---

## 📖 Usage Workflow

### 1. **Connect Gmail Account**
```
1. Open http://localhost:3000
2. Click "Connect Gmail"
3. Authorize the app with your Google account
4. System stores OAuth tokens securely
```

### 2. **Upload Contacts**
```
1. Go to "Contacts" section
2. Click "Upload CSV"
3. CSV Format (required columns: email, optional: name, company, phone):
   email,name,company,phone
   john@example.com,John Doe,Acme Inc,+1234567890
   jane@example.com,Jane Smith,Tech Corp,+1987654321
4. System validates and stores contacts
```

### 3. **Create Email Template**
```
1. Go to "Templates" section
2. Create new template:
   - Name: "Product Launch Outreach"
   - Subject: "Quick question about {{company}}"
   - Body: "Hi {{name}}, I noticed you work at {{company}}..."
3. System auto-detects variables for personalization
```

### 4. **Create AI Prompt (Optional)**
```
1. Go to "Prompts" section
2. Create new prompt:
   - Name: "Sales Follow-up"
   - Prompt: "You are a sales rep. Engage the prospect..."
3. System uses this for auto-replying to email responses
```

### 5. **Launch Campaign**
```
1. Go to "Campaigns" section
2. Click "New Campaign"
3. Select:
   - Contact list (CSV upload source)
   - Email template
   - AI prompt (optional)
4. Click "Send"
5. Campaign queues in background (Trigger.dev)
```

### 6. **Monitor Progress**
```
1. View real-time campaign stats:
   - Total contacts
   - Emails sent
   - Emails failed
   - In-progress count
2. View detailed email logs
3. Check error messages for failed sends
```

### 7. **Auto-Reply Management**
```
1. As prospects reply → System captures email
2. AI analyzes context using configured prompt
3. AI generates intelligent response
4. Response sent automatically (if enabled)
5. Conversation tracked in system
```

---

## 📂 Project Structure

```
Lead-contact/ (Backend - FastAPI)
├── main.py                          # Application entry point
├── config.py                        # Configuration & settings
├── requirements.txt                 # Python dependencies
├── api/
│   ├── routes/                      # REST API endpoints
│   │   ├── auth_routes.py          # OAuth login/callback
│   │   ├── campaign_routes.py       # Campaign management
│   │   ├── contact_routes.py        # Contact upload & list
│   │   ├── template_routes.py       # Email templates
│   │   ├── prompt_routes.py         # AI prompts
│   │   ├── provider_routes.py       # OAuth providers
│   │   ├── calendar_routes.py       # Calendar integration
│   │   └── internal_routes.py       # Internal endpoints
│   ├── dependencies/                # Dependency injection
│   │   ├── gmail_token.py          # Token validation
│   │   └── providers.py             # OAuth providers
│   └── webhooks/
│       └── trigger_webhooks.py      # Trigger.dev callbacks
├── core/                            # Business logic
│   ├── auth/                        # OAuth & authentication
│   ├── campaigns/                   # Campaign models
│   ├── csv/                         # CSV parsing
│   ├── templates/                   # Template service
│   ├── interfaces/                  # Abstract interfaces
│   └── calendar/                    # Calendar models
├── db/                              # Database layer
│   ├── repository_factory.py        # Factory pattern for repos
│   └── mongodb/                     # MongoDB implementation
│       ├── connection.py            # DB connection
│       ├── campaign_repository.py   # Campaign CRUD
│       ├── contact_repository.py    # Contact CRUD
│       ├── template_repository.py   # Template CRUD
│       ├── email_log_repository.py  # Email logs
│       ├── prompt_repository.py     # Prompts
│       └── schemas.py               # MongoDB schemas
├── integrations/
│   ├── trigger_client.py            # Trigger.dev API client
│   └── calcom_client.py             # Cal.com API client
├── providers/                       # OAuth implementations
│   ├── gmail/
│   │   ├── gmail_client.py         # Gmail API client
│   │   ├── gmail_oauth_provider.py # Gmail OAuth flow
│   │   └── gmail_send_service.py   # Email sending
│   └── __init__.py
└── utils/
    └── logger.py                    # Logging utility

Lead-contact-frontend/ (React/Vite)
├── vite.config.js                   # Vite configuration
├── package.json                     # Node dependencies
├── index.html                       # HTML entry point
└── src/
    ├── main.jsx                     # React entry point
    ├── App.jsx                      # Root component
    ├── App.css                      # Global styles
    ├── components/                  # React components
    │   ├── ContactsTable.jsx       # Contact list UI
    │   ├── CsvUpload.jsx           # File upload component
    │   ├── ContactModal.jsx        # Contact form
    │   ├── PromptModal.jsx         # Prompt editor
    │   ├── PromptTestChat.jsx      # AI testing
    │   ├── ProviderList.jsx        # OAuth connect
    │   └── common/                 # Shared components
    ├── pages/                       # Page components
    ├── utils/                       # Helper functions
    └── styles/                      # Component styles

Lead-contact-trigger/ (Background Worker - Node.js)
├── package.json                     # Node dependencies
├── tsconfig.json                    # TypeScript config
├── trigger.config.mjs               # Trigger.dev config
├── src/
│   ├── trigger/
│   │   └── emailCampaign.ts        # Main email task
│   ├── utils/                       # Helper functions
│   └── agents/                      # AI agents
└── README.md                        # Worker documentation
```

---

## 🔌 API Documentation

### Authentication Endpoints

```
GET /auth/{provider}/url
  Generate OAuth authorization URL
  
GET /oauth/callback/{provider}
  Handle OAuth callback
```

### Campaign Endpoints

```
POST /campaigns/send
  Launch email campaign
  Body: { csv_source, template_id, prompt_id?, name? }
  
GET /campaigns
  List all campaigns with pagination
  
GET /campaigns/{campaign_id}
  Get campaign details & stats
  
GET /campaigns/{campaign_id}/logs
  Get email logs for campaign
```

### Contact Endpoints

```
POST /contacts/upload
  Upload CSV file with contacts
  
GET /contacts
  List contacts with pagination
  
GET /contacts/stats
  Get contact statistics
```

### Template Endpoints

```
POST /templates
  Create email template
  Body: { name, subject, body }
  
GET /templates
  List all templates
  
PUT /templates/{template_id}
  Update template
  
DELETE /templates/{template_id}
  Delete template
  
POST /templates/preview
  Preview template with sample data
```

### Prompt Endpoints

```
POST /prompts
  Create AI prompt
  Body: { name, prompt_text, description? }
  
GET /prompts
  List all prompts
  
POST /prompts/test
  Test prompt with sample message
```

Full API documentation available at: `http://localhost:8000/docs`

---

## 🧪 Testing

### Test Endpoints

```bash
# Backend health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Test with example campaign
curl -X POST http://localhost:8000/campaigns/send \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user-123" \
  -d '{
    "csv_source": "test.csv",
    "template_id": "template-123",
    "name": "Test Campaign"
  }'
```

---

## 🔒 Security Considerations

- **OAuth Tokens**: Stored securely in MongoDB with encryption
- **No Password Storage**: Uses OAuth 2.0 - no user passwords
- **CORS**: Configure appropriately for production
- **JWT**: Token validation on protected endpoints
- **Input Validation**: Pydantic schemas validate all inputs
- **Error Handling**: Detailed errors logged, generic responses to clients

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [React Documentation](https://react.dev/)
- [Trigger.dev Documentation](https://trigger.dev/docs)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Documentation](https://developers.google.com/gmail/api)

---

## 🆘 Troubleshooting

### Backend won't start
```
1. Check Python version: python --version (need 3.10+)
2. Verify virtual environment activated
3. Check .env file exists and has correct values
4. Verify MongoDB connection: mongodb://localhost:27017
```

### Frontend shows 404 errors
```
1. Check backend is running on port 8000
2. Verify VITE_BACKEND_URL in .env.local
3. Check CORS configuration in FastAPI
4. Clear browser cache
```

### MongoDB connection error
```
1. Verify MongoDB service is running
2. Check MONGO_URI in .env
3. For MongoDB Atlas: verify IP whitelist includes your IP
4. Test connection: mongosh "mongodb://localhost:27017"
```

### OAuth callback fails
```
1. Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
2. Check redirect URI matches exactly: http://localhost:3000/auth/callback
3. Verify Google OAuth credentials are for Web Application type
4. Check browser console for specific error
```

---

## 📝 License

This project is proprietary. All rights reserved.

---

## 🤝 Support

For issues or questions, refer to the documentation or contact the development team.

---

**Last Updated**: January 29, 2026
**Version**: 1.0.0
