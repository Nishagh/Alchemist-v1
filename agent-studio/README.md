# Agent Studio Web

This is the web application for the Alchemist Agent Studio - the interface for creating, managing, and deploying AI agents. It's built with React and Material UI, and it communicates with the Alchemist platform backend.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file by copying the `.env.sample` file:
```bash
cp .env.sample .env
```

3. Update the `.env` file with your backend API URL and Firebase configuration if needed.

## Development

To run the application in development mode:

```bash
npm start
```

This will start the development server on port 3000. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## Build for Production

To build the application for production:

```bash
npm run build
```

This will create a `build` folder with the production-ready files.

## Deployment

### Netlify

The project includes a `netlify.toml` file for easy deployment to Netlify:

1. Install the Netlify CLI:
```bash
npm install -g netlify-cli
```

2. Login to Netlify:
```bash
netlify login
```

3. Deploy to Netlify:
```bash
netlify deploy
```

### Vercel

To deploy to Vercel:

1. Install the Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy to Vercel:
```bash
vercel
```

### Firebase Hosting

To deploy to Firebase Hosting:

1. Install the Firebase CLI:
```bash
npm install -g firebase-tools
```

2. Login to Firebase:
```bash
firebase login
```

3. Initialize Firebase (select Hosting):
```bash
firebase init
```

4. Deploy to Firebase:
```bash
firebase deploy
```

## Environment Variables

- `REACT_APP_API_BASE_URL` - The base URL of the backend API
- `REACT_APP_FIREBASE_API_KEY` - Firebase API key (optional if using backend proxy)
- `REACT_APP_FIREBASE_PROJECT_ID` - Firebase project ID (optional if using backend proxy)
- `REACT_APP_FIREBASE_AUTH_DOMAIN` - Firebase auth domain (optional if using backend proxy)
- `REACT_APP_FIREBASE_STORAGE_BUCKET` - Firebase storage bucket (optional if using backend proxy)

## Authentication

The application uses Firebase Authentication for user management. Make sure to configure Firebase correctly in the backend and provide the appropriate Firebase configuration in the frontend.
