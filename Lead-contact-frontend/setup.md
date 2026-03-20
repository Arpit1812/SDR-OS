# Frontend Setup Guide

This guide will help you set up the Lead Contact frontend application.

## Prerequisites

- Node.js 16.x or higher
- npm or yarn package manager
- Backend API running (see backend/setup.md)

## Installation Steps

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your backend URL:

```bash
cp .env.example .env
```

Edit `.env` with your backend API URL. In development, the Vite proxy will handle API requests automatically.

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- API requests are proxied to backend (configured in `vite.config.js`)

## Project Structure

```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── common/       # Shared/common components
│   │   └── ...           # Feature-specific components
│   ├── pages/            # Page components
│   ├── utils/            # Utility functions
│   │   └── api.js       # API client
│   ├── styles/           # Global styles
│   ├── App.jsx           # Main app component
│   └── main.jsx          # Entry point
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
└── package.json          # Dependencies
```

## Available Scripts

### Development

```bash
npm run dev
```

Starts the development server with hot module replacement (HMR).

### Build

```bash
npm run build
```

Creates a production build in the `dist` directory.

### Preview

```bash
npm run preview
```

Preview the production build locally.

## Configuration

### API Configuration

The frontend uses a proxy configuration in development mode. API requests to `/api/*` are automatically proxied to the backend server.

**Development:**
- Frontend runs on `http://localhost:3000`
- API requests to `/api/*` are proxied to backend (default: `http://localhost:8000`)

**Production:**
- Set `VITE_BACKEND_URL` environment variable to your backend URL
- Example: `VITE_BACKEND_URL=https://api.yourdomain.com`

### Environment Variables

- `VITE_BACKEND_URL` - Backend API URL (required in production)

## Features

### Pages

- **Dashboard** - Overview and statistics
- **Contacts** - Manage contacts and upload CSV files
- **Campaigns** - Create and manage email campaigns
- **Templates** - Email template management
- **Prompts** - AI prompt management
- **Settings** - Application settings
- **Logs** - View email sending logs

### Components

- **ContactModal** - Add/edit contacts
- **ContactsTable** - Display contacts with filtering
- **CsvUpload** - CSV file upload component
- **ProviderList** - OAuth provider management
- **PromptModal** - AI prompt editor
- **Layout** - Main application layout

## Development Tips

### Adding New Pages

1. Create component in `src/pages/`
2. Add route in `src/App.jsx`
3. Add navigation link in `Layout.jsx`

### API Calls

Use the `apiFetch` utility from `src/utils/api.js`:

```javascript
import { apiFetch } from '../utils/api';

// GET request
const response = await apiFetch('/api/contacts');
const data = await response.json();

// POST request
const response = await apiFetch('/api/contacts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'John', email: 'john@example.com' })
});
```

### Styling

- Global styles: `src/index.css`
- Component styles: Co-located CSS files (e.g., `ComponentName.css`)
- Design system: See `src/pages/DesignSystemDemo.jsx` for available components

## Building for Production

### 1. Set Environment Variables

Create `.env.production`:

```
VITE_BACKEND_URL=https://api.yourdomain.com
```

### 2. Build

```bash
npm run build
```

### 3. Deploy

The `dist` folder contains the production build. Deploy to your hosting service:

- **Vercel**: Already configured with `vercel.json`
- **Netlify**: Add `netlify.toml` configuration
- **Other**: Upload `dist` folder contents

## Troubleshooting

### API Requests Failing

- Verify backend is running
- Check `VITE_BACKEND_URL` is set correctly (production)
- Check browser console for CORS errors
- Verify proxy configuration in `vite.config.js` (development)

### Build Errors

- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 16+)
- Clear Vite cache: `rm -rf node_modules/.vite`

### Port Already in Use

Change the port in `vite.config.js`:

```javascript
server: {
  port: 3001, // Change to available port
}
```

## Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [React Router Documentation](https://reactrouter.com/)

