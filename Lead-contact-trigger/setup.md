# Worker Setup Guide (Self-hosted)

This guide will help you set up the self-hosted worker for background email campaign processing and scheduled reply checking.

## Prerequisites

- Node.js 16.x or higher
- npm or yarn package manager
- MongoDB instance (local or Atlas)
- Backend API running (see backend/setup.md)
- Google OAuth credentials (same as backend)

## Installation Steps

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- MongoDB connection string and database name
- Google OAuth credentials
- Backend API URL

### 3. Verify Setup

Run the test script to verify everything is configured correctly:

```bash
npm run build
```

This will compile TypeScript and check for any configuration errors.

## Running the Worker

### Development Mode

```bash
npm run dev
```

This will:
- Start the worker HTTP server (default `http://localhost:8787`)
- Watch for file changes

To enable the scheduled reply checker, set `ENABLE_REPLY_CHECKER=true` in `.env`.

### Production Deployment

Run this as a long-running Node process (VM/Docker/Render/etc). Example:

```bash
npm run build
node dist/worker/index.js
```

## Project Structure

```
trigger/
├── src/
│   ├── trigger/          # Trigger.dev task definitions
│   │   ├── emailCampaign.ts    # Main email campaign task
│   │   └── replyChecker.ts     # Email reply checker task
│   ├── worker/           # Worker HTTP server + job queue
│   │   └── index.ts
│   ├── agents/           # AI agent implementations
│   │   └── replyAgent.ts # AI reply generation agent
│   ├── utils/            # Utility functions
│   │   ├── tokenRefresh.ts     # OAuth token refresh
│   │   └── gmailSender.ts      # Gmail API client
│   └── test.ts           # Test script
├── trigger.config.mjs    # Legacy stub (no longer used)
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependencies
└── .env                  # Environment variables (not in git)
```

## How It Works

### Email Campaign Task

When a campaign is created in the backend:

1. Backend triggers the `sendEmailCampaign` task
2. Task receives campaign details, OAuth tokens, and contact information
3. Worker processes emails in batches:
   - Checks and refreshes OAuth tokens if needed
   - Fetches contacts from backend
   - Loads email template
   - Personalizes emails with contact data
   - Sends emails via Gmail API
   - Updates progress to backend
4. Task completes and updates final campaign status

### Reply Checker Task

Periodically checks for email replies:

1. Fetches users with active campaigns
2. Checks Gmail for new replies
3. Uses AI agent to generate appropriate responses
4. Sends replies and updates conversation history

## Task Configuration

### Email Campaign Task

- **Batch Size**: 10 emails per batch
- **Batch Delay**: 2 seconds between batches
- **Max Duration**: 60 seconds (configurable)
- **Retries**: 3 attempts with exponential backoff

### Token Refresh

The worker automatically:
- Checks token expiry before each batch
- Refreshes tokens if expiring within 5 minutes
- Updates tokens in backend database
- Handles refresh failures gracefully

## Testing

### Test Locally

1. Start backend API
2. Start Trigger.dev dev server: `npm run dev`
3. Create a campaign in the frontend
4. Monitor task execution in Trigger.dev dashboard

### Test Payload Example

```json
{
  "campaignId": "test-campaign-123",
  "userId": "user-123",
  "csvSource": "test.csv",
  "templateId": "template-123",
  "accessToken": "ya29.a0...",
  "refreshToken": "1//0g...",
  "tokenExpiry": "2025-11-24T23:00:00Z",
  "backendUrl": "http://localhost:8000"
}
```

## Monitoring

### Logs

- Worker logs: the terminal/platform running the worker
- Backend receives campaign progress updates via webhooks
- Health check: `GET /health` (default `http://localhost:8787/health`)

## Troubleshooting

### Task Not Triggering

- Verify backend has `WORKER_URL` set (and `WORKER_SECRET` if enabled)
- Verify the worker is running and reachable from the backend
- Check worker logs for request/validation errors

### Token Refresh Failing

- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Ensure refresh token is valid
- Check that OAuth consent screen is configured
- Verify scopes include Gmail send permission

### Emails Not Sending

- Verify Gmail API is enabled in Google Cloud Console
- Check that OAuth scopes include Gmail send permission
- Review error logs in the worker process
- Verify access token has not expired

### Build Errors

- Check TypeScript version compatibility
- Verify all dependencies are installed: `npm install`
- Clear build cache: `rm -rf node_modules/.cache`
- Check `tsconfig.json` configuration

### Development Server Issues

- Ensure Node.js version is 16+
- Check that port is not already in use
- Verify `.env` file exists and is configured
- Check that port `8787` (or `PORT`) is free

## Environment Variables

See `.env.example` for all required environment variables.

## Additional Resources

- [Trigger.dev Documentation](https://trigger.dev/docs)
- [Trigger.dev Dashboard](https://cloud.trigger.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)

## Quick Start (Windows)

Use the provided `start.bat` script:

```bash
start.bat
```

This script will:
1. Check for `.env` file
2. Install dependencies if needed
3. Verify TypeScript compilation
4. Start the development server

