# 🏢 NexaCorp CIO Intelligence Dashboard

An AI-powered enterprise operations dashboard that gives CXOs real-time visibility into infrastructure, security, ERP, logistics, and business KPIs — with role-based access and natural language AI chat.

---

## 🚀 Features

- **AI Morning Briefing** — Auto-generated executive summary on login
- **Ask CIO AI** — Chat with an AI that knows your live enterprise data
- **Blast Radius Analyzer** — Map full downstream business impact of any incident
- **Role-Based Access** — Each role (CIO, Security Manager, etc.) sees only their data
- **Anomaly Detection** — Auto-detects critical server, ERP, security, and revenue issues
- **Audit Trail** — Every AI interaction is logged for compliance

---

## 🧠 AI Stack

| Priority | Provider | When Used |
|---|---|---|
| 1st | **Ollama (local)** | Always tried first — unlimited, no API key, no internet |
| 2nd | **Google Gemini** | Fallback if Ollama not running |
| 3rd | **Smart Mock** | Always works — uses real enterprise data, no AI needed |

---

## 🗂️ Project Structure

```
cio-project/
├── backend/
│   ├── main.py              # FastAPI server — all routes + AI logic
│   └── requirements.txt     # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── Login.jsx
    │       ├── Dashboard.jsx
    │       ├── Chat.jsx
    │       ├── MorningBriefing.jsx
    │       ├── BlastRadius.jsx
    │       └── AuditTrail.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## ⚙️ Setup & Running

### Prerequisites

- Python 3.8+
- Node.js 18+
- [Ollama](https://ollama.com) (for local AI)

---

### 1. Clone the repo

```bash
git clone https://github.com/your-username/cio-project.git
cd cio-project
```

---

### 2. Set up Ollama (local AI)

```bash
# Install from https://ollama.com, then:
ollama pull llama3.2:1b

# Ollama starts automatically on Windows
# On Mac/Linux run: ollama serve
```

---

### 3. Start the Backend

```bash
cd backend
pip install fastapi uvicorn python-dotenv
python -m uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`

---

### 4. Start the Frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

### 5. Open the app

Go to `http://localhost:3000` in your browser and log in with any role.

---

## 👤 Available Roles

| Role | Access |
|---|---|
| `CIO` | Everything |
| `Security_Manager` | Security alerts only |
| `Operations_Head` | ERP, logistics, production |
| `Finance_Head` | KPIs, ERP |
| `IT_Manager` | Infrastructure, production |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check Ollama + server status |
| GET | `/dashboard-status` | Live anomalies + KPIs |
| GET | `/morning-briefing/{role}` | AI-generated briefing |
| POST | `/chat` | Chat with AI |
| POST | `/blast-radius` | Incident impact analysis |
| GET | `/audit-trail` | All logged interactions |

---

## 🔐 Optional: Gemini Fallback

Create a `.env` file in the `backend/` folder:

```
GEMINI_API_KEY=your_key_here
```

---

## 🛠️ Tech Stack

**Backend:** Python, FastAPI, Uvicorn  
**Frontend:** React, Vite  
**AI:** Ollama (llama3.2:1b), Google Gemini (fallback)  
**Styling:** Inline CSS, Courier New monospace theme  

---

## 📸 Demo

Login → select role → get AI briefing → ask questions → analyze blast radius → check audit trail.

Even without Ollama, the **smart mock mode** returns realistic enterprise data for demos.
