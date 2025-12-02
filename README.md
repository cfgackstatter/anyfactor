# AnyFactor

AI-powered SEC filing data extraction for quantitative factor analysis.

## Overview

AnyFactor uses LLMs (Perplexity API) to extract any numerical feature from SEC 10-K and 10-Q filings. Enter a feature like "book value" or "number of employees" along with ticker symbols, and the AI extracts the data automatically.

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
│ ├── app.py # Flask API endpoints
│ ├── sec.py # SEC EDGAR data retrieval
│ ├── parse.py # HTML parsing & cleaning
│ ├── llm.py # LLM feature extraction
│ ├── requirements.txt # Python dependencies
│ └── .env.example # Environment variables template
└── frontend/
├── src/
│ ├── components/ # React components
│ ├── App.jsx # Main app component
│ └── api.js # API client
└── package.json # Node dependencies
```


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

#### Edit .env and add your PERPLEXITY_API_KEY

#### Run development server

```
python app.py
```

Backend will run on `http://localhost:5000`

### Frontend Setup

```
cd frontend
```

#### Install dependencies

```
npm install
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