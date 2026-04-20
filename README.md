# Omni Copilot

An AI-powered productivity assistant that lets you control **Google Calendar, Google Drive, Gmail, and Notion** through a single chat interface — just type what you want done.

---

## Features

- **Gmail** — Send emails, list inbox, fetch email content
- **Google Calendar** — Create events, generate Google Meet links, delete events
- **Google Drive** — Search files, send Drive files via email
- **Notion** — Search pages, create new pages under a parent
- **File Upload** — Attach PDFs or DOCX files as context for your queries
- **Multi-turn Chat** — Persistent conversation sessions with tool execution trace

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 18, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11+ |
| AI | Groq API (`llama-3.3-70b-versatile`) |
| Database | MongoDB (Motor async driver) |
| Auth | Google OAuth 2.0 |
| Google APIs | Calendar v3, Drive v3, Gmail v1 |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or [Atlas](https://www.mongodb.com/atlas))
- [Groq API Key](https://console.groq.com/)
- Google Cloud project with OAuth 2.0 credentials

---

## Setup

### 1. Clone & configure environment

```bash
git clone <your-repo-url>
cd omni-copilot
```

Edit `backend/.env` with your credentials:

```env
MONGODB_URI=mongodb://localhost:27017
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
GROQ_API_KEY=your_groq_api_key
ENCRYPTION_KEY=your_32_byte_hex_key
SECRET_KEY=your_secret_key
FRONTEND_URL=http://localhost:3000
TIMEZONE=Asia/Kolkata
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:3000
```

### 4. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services → Credentials**
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add to **Authorized redirect URIs**:
   ```
   http://localhost:8000/api/auth/google/callback
   ```
4. Enable these APIs in your project:
   - Gmail API
   - Google Calendar API
   - Google Drive API

---

## Project Structure

```
omni-copilot/
├── backend/
│   ├── app/
│   │   ├── config/          # Settings & database connection
│   │   ├── integrations/    # Google OAuth flow
│   │   ├── models/          # Pydantic schemas
│   │   ├── routes/          # REST API endpoints
│   │   ├── services/        # AI agent pipeline & chat logic
│   │   ├── tools/           # Calendar, Drive, Gmail, Notion tool handlers
│   │   └── utils/           # Encryption, file parsing
│   ├── .env
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/             # Next.js pages & routing
        ├── components/      # Chat UI, Sidebar
        ├── hooks/           # useChat, useUser
        └── lib/             # Axios API client
```

---

## Example Commands

```
send a mail to john@example.com inviting him to a meeting at 5pm today with the meet link
show my latest 5 unread emails
delete all events for today from calendar
fetch ProjectReport from drive and send it to team@example.com
create a Notion page titled "Sprint Notes" with today's tasks
```

---

## Notes

- Notion integration requires a manually created integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations), added via the in-app settings.
- The AI agent uses a structured execution pipeline — tool outputs (like Meet links or Drive file IDs) are captured and injected into subsequent steps automatically, ensuring no placeholder values reach the APIs.
