# AnyFactor

AI-powered SEC filing data extraction for quantitative factor analysis.

## Overview

AnyFactor extracts numerical and qualitative features from SEC 10-K and 10-Q filings for quantitative factor research.

**Pipeline:**
1. Classify the feature (numeric vs qualitative)
2. For standard numeric metrics, read **SEC XBRL companyfacts** first (fast + accurate)
3. Otherwise: fetch filing HTML → section/table passages → keyword retrieval → closed-context LLM extract

## Features

- 🤖 AI-powered data extraction from SEC filings
- 📊 Support for multiple tickers simultaneously
- 🎯 Extract any numerical feature with natural language
- 🚀 Modern, responsive React interface
- ⚡ Real-time processing with loading states

## Tech Stack

**Backend:**
- Flask (Python)
- Perplexity API (LLM)
- BeautifulSoup (HTML parsing)
- SEC EDGAR API

**Frontend:**
- React
- Material-UI
- Axios

**Deployment:**
- AWS Elastic Beanstalk (backend)
- AWS S3 + CloudFront (frontend)

## Project Structure

```
anyfactor/
├── backend/
│   ├── app.py            # Flask routes
│   ├── auth.py           # API key checks
│   ├── config.py         # Settings from env
│   ├── extract.py        # XBRL-first orchestration + parallelism
│   ├── http_client.py    # Shared requests.Session
│   ├── llm.py            # Closed-context LLM extract (Perplexity/Ollama)
│   ├── metrics.py        # Feature synonyms + XBRL tag map
│   ├── models.py         # Dataclasses / enums
│   ├── parse.py          # HTML → sections/tables
│   ├── retrieve.py       # Passage ranking
│   ├── sec.py            # SEC EDGAR helpers
│   ├── validation.py     # Request validation
│   ├── xbrl.py           # companyfacts lookup
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── App.jsx
    │   ├── api.js
    │   └── constants.js
    └── package.json
```


## Quick start (Makefile)

```bash
make install   # backend venv + pip + npm install
make env       # create .env files if missing (then edit keys)
make dev       # backend :5000 + frontend :3000
```

Useful targets: `make backend`, `make frontend`, `make help`.

VS Code / Cursor terminals auto-activate `backend/venv` via `.vscode/settings.json`.

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Perplexity API key ([get one here](https://www.perplexity.ai/settings/api))

### Backend Setup

```
cd backend
```

#### Create virtual environment

```
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
```

#### Install dependencies

```
pip install -r requirements.txt
```

#### Configure environment
```
cp .env.example .env
```

Edit `.env` and set at least:
- `PERPLEXITY_API_KEY`
- `EXTRACT_API_KEY` (shared secret for `/api/extract`)
- `SEC_USER_AGENT` (real name + email required by SEC EDGAR)

#### Run development server

```
python app.py
```

Backend will run on `http://localhost:5000` (bound to `127.0.0.1` by default)

### Frontend Setup

```
cd frontend
```

#### Install dependencies

```
npm install
```

#### Configure environment

Create `frontend/.env`:

```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_EXTRACT_API_KEY=<same value as EXTRACT_API_KEY>
```

#### Run development server

```
npm start
```

Frontend will run on `http://localhost:3000`

## Usage

1. Enter a feature to extract (e.g., "total revenue", "book value")
2. Add ticker symbols by typing and pressing Enter
3. Click "Extract Data"
4. View extracted values with links to source filings

## Coming Soon

- 📈 Historical time series extraction
- 🔬 Factor backtesting engine
- 📊 Portfolio performance analytics
- 📅 Date range filtering
- 💾 Data persistence and export

## License

MIT