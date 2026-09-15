# SatQuery AI — Satellite Intelligence Platform

> Ask questions about satellite imagery. Get structured AI-powered intelligence.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Install Backend
```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend
```bash
cd frontend
npm install
```

### 3. Run (Demo Mode — No API Key Required)
```bash
# Windows
start_windows.bat

# Or manually:
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 4. Open
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

## Modes

### Demo Mode (Default)
- **No API key required**
- Works offline
- Bundled demo scenes + responses
- Badge shows: `● DEMO MODE`

### Live AI Mode (Optional)
Configure in `backend/.env`:
```env
AI_MODE=live
LIVE_AI_PROVIDER=gemini
LIVE_AI_API_KEY=your_key_here
LIVE_AI_MODEL=gemini-2.0-flash
```
Also install: `pip install google-generativeai`

If Live AI fails → automatic fallback to Demo Mode.

## Features
- Single-image analysis with natural-language queries
- **Before & After comparison** (flagship feature)
- Visual Change Map (pixel-difference heatmap)
- Evidence-based findings with confidence & regions
- Government insight engine
- Conversational follow-up questions
- PDF report generation
- Analysis history
- GeoTIFF metadata support

## Architecture
```
Browser → Next.js (3000) → FastAPI (8000) → AI Provider Abstraction → Structured JSON
                                                    ├── DemoAIProvider (guaranteed)
                                                    └── OptionalLiveAIProvider (plug-in)
```

## Disclaimer
AI-assisted interpretation for screening and decision-support. Not a substitute for official survey, legal determination, or field verification.
