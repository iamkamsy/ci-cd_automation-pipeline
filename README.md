# Task Manager

A secure, account-based task manager for tracking personal tasks with deadlines and descriptions. Each user can only access their own data — no anonymous access, no shared task lists.

## Features

- Sign up and log in with email and password
- Create tasks with a name, deadline, and description
- Tasks automatically sort by nearest deadline
- Edit any task field inline — list re-sorts immediately on save
- Delete tasks
- Deadlines cannot be set in the past
- All changes update instantly without page refresh
- Responsive layout for desktop and mobile
- Session expiry automatically redirects to the login page

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python, Flask, Flask-CORS |
| Database | MongoDB Atlas |
| Auth | Signed cookie sessions with bcrypt password hashing |

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A MongoDB Atlas cluster (free tier is sufficient)

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```
MONGO_URI=your_mongodb_atlas_connection_string
SECRET_KEY=a_long_random_secret_key
```

Start the server:

```bash
flask run
```

Backend runs on `http://localhost:5000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

Open `http://localhost:5173` in your browser. Sign up for an account and start adding tasks.
