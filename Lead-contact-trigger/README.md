# Email Campaign Worker (Self-hosted)

This is a self-hosted worker that handles background email campaign processing and scheduled reply checking for the Lead Contact application.

## Features

- ✅ **Automatic Token Refresh**: Refreshes OAuth tokens during long-running campaigns
- ✅ **Batch Processing**: Sends emails in batches to avoid rate limits
- ✅ **Progress Tracking**: Updates campaign status and progress in real-time
- ✅ **Error Handling**: Robust error handling with retry logic
- ✅ **Personalization**: Supports template variables like {{name}}, {{email}}, etc.

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:

- `MONGO_URI`: MongoDB connection string (used for job queue storage via Agenda)
- `MONGO_DB_NAME`: Mongo database name (optional but recommended for Atlas URIs)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `BACKEND_URL`: URL of your backend API (e.g., http://localhost:8000)
- `WORKER_SECRET`: Shared secret for the backend to authenticate to this worker (optional but recommended)

### 3. Enable/Disable Scheduled Reply Checker

By default, the scheduled reply checker is disabled. Enable it by setting:

- `ENABLE_REPLY_CHECKER=true`

Optional schedule:

- `REPLY_CHECK_EVERY=1 minute`

## Development

### Run in Development Mode

```bash
npm run dev
```

This will:
- Start the worker HTTP server (default `http://localhost:8787`)
- Watch for file changes

### Test the Task

You can test the email campaign task by triggering it from your backend or using the Trigger.dev dashboard.

#### Test Payload Example:

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

## Deployment

## Deployment

Run this worker as a long-running Node process (VM, Docker, Render, etc.).

## Project Structure

```
trigger/
├── src/
│   ├── trigger/
│   │   └── emailCampaign.ts    # Main email campaign task
│   └── utils/
│       ├── tokenRefresh.ts     # OAuth token refresh utilities
│       └── gmailSender.ts      # Gmail API email sending
├── src/worker/index.ts         # Worker HTTP server + job queue
├── tsconfig.json              # TypeScript configuration
├── package.json               # Dependencies and scripts
└── .env                       # Environment variables (not in git)
```

## How It Works

### 1. Campaign Trigger

When a campaign is created in the backend, it triggers this worker with:
- Campaign details
- OAuth tokens (access + refresh)
- Template and contact information

### 2. Token Management

The worker automatically:
- Checks if the access token is expired
- Refreshes it using the refresh token if needed
- Updates the token before each batch of emails

### 3. Email Sending

Emails are sent in batches:
- Default batch size: 10 emails
- Delay between batches: 2 seconds
- Personalization applied to each email

### 4. Progress Updates

The worker sends progress updates to the backend:
- Status changes (running, completed, failed)
- Progress counters (processed, sent, failed)

## Token Refresh Flow

```
1. Check token expiry
   ↓
2. If expired or expiring soon (< 5 min)
   ↓
3. Use refresh token to get new access token
   ↓
4. Continue with new token
```

## API Endpoints Used

The worker calls these backend endpoints:

- `GET /api/contacts/by-source/{source}` - Fetch contacts
- `GET /api/templates/{id}` - Fetch email template
- `POST /api/webhooks/trigger/campaign-status` - Update campaign status
- `POST /api/webhooks/trigger/campaign-progress` - Update progress

## Error Handling

The worker handles errors gracefully:

1. **Token Refresh Failures**: Marks campaign as failed
2. **Email Send Failures**: Continues with remaining emails, tracks failures
3. **API Failures**: Retries with exponential backoff

## Rate Limiting

To avoid Gmail API rate limits:

- Batch size: 10 emails per batch
- Delay: 2 seconds between batches
- Max: ~300 emails per minute

## Monitoring

- Worker logs: whatever platform runs the worker process (local terminal, Render logs, VM logs)
- Backend status/progress: persisted via the webhook endpoints listed above
- Health check: `GET /health` on the worker (default `http://localhost:8787/health`)

## Troubleshooting

### Task Not Triggering

- Verify backend has `WORKER_URL` set (and `WORKER_SECRET` if enabled)
- Verify the worker is running and reachable from the backend
- Check worker logs for request/validation errors

### Token Refresh Failing

- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Ensure refresh token is valid
- Check that OAuth consent screen is configured

### Emails Not Sending

- Verify Gmail API is enabled in Google Cloud Console
- Check that OAuth scopes include Gmail send permission
- Review worker logs for Gmail API errors

## Support

For issues:
- Check worker logs
- Review backend logs
